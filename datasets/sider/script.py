from pathlib import Path
import sys
import subprocess
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, "../../code/kgraph/utils/")
import mappers as mps

output_dir = Path("../../graph/raw/")
output_dir.mkdir(parents=True, exist_ok=True)
current_dir = Path(__file__).resolve().parent
source = current_dir.name

# Parameters
cutoff_values = [0.05, 0.05]
placebo_margins = [0.05, 0]


def extract_disease_from_drug(
    drug_data,
    cutoff,
    placebo_margin,
    accepted_tags={"common", "very frequent", "frequent", "very common"},
):
    results = []

    for disease, data in drug_data.groupby("umls"):
        if "real" not in data["placebo"].unique():
            continue

        median_real_bounds = data[data["placebo"] == "real"][
            ["lbound", "ubound"]
        ].median()
        mean_real = median_real_bounds.mean()

        # Check for well-known side effects
        known_effects = (
            set(data["freq. desc."][data["placebo"] == "real"]) & accepted_tags
        )
        if known_effects:
            results.append([disease, "|".join(known_effects), ""])
            continue

        # Check if disease is prevalent in the population
        if mean_real >= cutoff:
            description = f"{median_real_bounds['lbound']*100:.0f}-{median_real_bounds['ubound']*100:.0f}%"

            if "placebo" in data["placebo"].unique():
                median_placebo_bounds = data[data["placebo"] == "placebo"][
                    ["lbound", "ubound"]
                ].median()
                mean_placebo = median_placebo_bounds.mean()

                if mean_real > (placebo_margin + mean_placebo):
                    placebo_desc = f"{median_placebo_bounds['lbound']*100:.0f}-{median_placebo_bounds['ubound']*100:.0f}%"
                    results.append([disease, description, placebo_desc])
            else:
                results.append([disease, description, ""])

    return results


# Download data if not present
data_file = current_dir / "meddra_freq.tsv"
if not data_file.exists():
    subprocess.Popen("./get_data.sh", shell=True).wait()

# Read data
drug_df = pd.read_csv(
    data_file,
    sep="\t",
    header=None,
    names=[
        "stitch flat",
        "stitch stereo",
        "umls",
        "placebo",
        "freq. desc.",
        "lbound",
        "ubound",
        "meddra_hierarchy",
        "meddra id",
        "name",
    ],
)

# Filter out rare side effects
drug_df = drug_df[
    ~drug_df["freq. desc."].isin(["very rare", "uncommon", "infrequent", "rare"])
]
drug_df["placebo"] = drug_df["placebo"].fillna("real")

# Extract relevant compound-disease associations
associations = []
for drug_id, drug_data in tqdm(drug_df.groupby("stitch stereo")):
    diseases = extract_disease_from_drug(
        drug_data, cutoff_values[0], placebo_margins[0]
    )

    if not diseases:
        diseases = extract_disease_from_drug(
            drug_data, cutoff_values[1], placebo_margins[1]
        )

    associations.extend([[drug_id] + disease for disease in diseases])

result_df = pd.DataFrame(
    associations, columns=["compound", "disease", "description", "placebo"]
)

# Map compounds and diseases
compound_to_id = mps.get_sider2ikey()
result_df["compound"] = result_df["compound"].map(compound_to_id).dropna()

result_df["disease"] = mps.mapping(result_df["disease"].to_numpy(), "Disease")

# Write to file
output_file = output_dir / f"CPD-cau-DIS/{source}.tsv"
output_file.parent.mkdir(parents=True, exist_ok=True)
result_df.sort_values(["compound", "disease"]).to_csv(
    output_file, sep="\t", index=False, header=["n1", "n2", "desc", "placebo"]
)

sys.stderr.write("Done!\n")
