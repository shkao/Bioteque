from pathlib import Path
import sys
import subprocess
import numpy as np
import csv
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, "../../code/kgraph/utils/")
import mappers as mps

output_dir = Path("../../graph/raw/CPD-trt-DIS")
current_path = Path(__file__).resolve().parent
source = current_path.name

# Download the data if not already present
data_script = current_path / "get_data.sh"
if not (output_dir / f"{source}.tsv").exists():
    subprocess.run(str(data_script), shell=True, check=True)

# Load DrugBank structures
drugbank_to_ikey = mps.get_drugbank2ikey()

# Load indications
indications = []
with open("./repodb.csv", "r") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    for row in reader:
        if row[5] in {"Withdrawn", "Suspended", "NA"}:
            continue
        drug_id = row[1]
        drug_id = drugbank_to_ikey.get(drug_id, None)
        if not drug_id:
            continue
        disease = row[3]
        phase_label = row[6]
        if row[5] == "Approved":
            phase = 4
        elif "Phase 3" in phase_label:
            phase = 3
        elif "Phase 2" in phase_label:
            phase = 2
        elif "Phase 1" in phase_label:
            phase = 1
        elif "Phase 0" in phase_label:
            phase = 0
        else:
            sys.exit(f"Unknown phase label: {phase_label}")

        indications.append([drug_id, disease, phase])

# Parse diseases and convert to DataFrame
indications_df = pd.DataFrame(indications, columns=["drug_id", "disease", "phase"])
indications_df["disease"] = mps.parse_diseaseID(indications_df["disease"])

# Write to file
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / f"{source}.tsv"
indications_df.to_csv(output_file, sep="\t", index=False, header=["n1", "n2", "phase"])

sys.stderr.write("Done!\n")
