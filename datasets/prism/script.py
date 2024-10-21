import sys
import os
import subprocess
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path

# Add utility path
sys.path.insert(0, "../../code/kgraph/utils/")
import mappers as mps
from transform_data import drug_sens_stratified_waterfall

# Set up output directory
output_dir = Path("../../graph/raw/CLL-sns-CPD")
output_dir.mkdir(parents=True, exist_ok=True)
current_path = Path(__file__).resolve().parent
source = current_path.name

# Download data
if not os.path.exists("./secondary-screen-dose-response-curve-parameters.csv"):
    subprocess.run("./get_data.sh", shell=True, check=True)

# Map drugs to IDs
drug_to_id = mps.get_prism2ikey()

# Read and map data
data_file = "./secondary-screen-dose-response-curve-parameters.csv"
mapped_data = []

df = pd.read_csv(
    data_file,
    usecols=["broad_id", "ccle_name", "auc"],
)
df = df.dropna(subset=["ccle_name"])
df = df[df["broad_id"].isin(drug_to_id.keys())]
df["broad_id"] = df["broad_id"].map(drug_to_id)
df["ccle_name"] = df["ccle_name"].str.split("_").str[0]
df["auc"] = pd.to_numeric(df["auc"], errors="coerce")

# Average repeated measures
df = df.groupby(["broad_id", "ccle_name"], as_index=False).mean()

# Map cell lines to IDs
cell_line_to_id = dict(
    zip(np.unique(df["ccle_name"]), mps.cl2ID(np.unique(df["ccle_name"])))
)
cell_line_to_id["TT"] = "CVCL_1774"
df["ccle_name"] = df["ccle_name"].map(cell_line_to_id)

# Remove unmapped cell lines
df = df.dropna(subset=["ccle_name"]).reset_index(drop=True)

# Create sensitivity matrix
drug_ids = np.unique(df["broad_id"])
cell_line_ids = np.unique(df["ccle_name"])
matrix = np.full((len(cell_line_ids), len(drug_ids)), np.nan)

for _, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing rows"):
    drug_index = np.where(drug_ids == row["broad_id"])[0][0]
    cell_line_index = np.where(cell_line_ids == row["ccle_name"])[0][0]
    matrix[cell_line_index, drug_index] = row["auc"]

df_sns = pd.DataFrame(matrix, index=cell_line_ids, columns=drug_ids)

# Binarize sensitivity matrix
df_sns = df_sns.transform(
    drug_sens_stratified_waterfall,
    axis=0,
    ternary=False,
    min_cls=0.01,
    max_cls=0.2,
    apply_uncertainty_at=0.8,
    min_sens_cutoff=0.9,
)

# Get sensitive drug-cell line pairs
sensitive_pairs = set()
for cell_line, sensitivities in df_sns.iterrows():
    sensitive_drugs = df_sns.columns[sensitivities == 1]
    sensitive_pairs.update(zip([cell_line] * len(sensitive_drugs), sensitive_drugs))

# Write output
output_file_path = output_dir / f"{source}.tsv"
with open(output_file_path, "w") as output_file:
    output_file.write("n1\tn2\n")
    for pair in sorted(sensitive_pairs):
        output_file.write(f"{pair[0]}\t{pair[1]}\n")

sys.stderr.write("Done!\n")
