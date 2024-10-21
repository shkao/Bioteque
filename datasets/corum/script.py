import os
import sys
import subprocess
import pandas as pd
from itertools import combinations
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "code/kgraph/utils")
)
import mappers as mps

guv = mps.get_human_reviewed_uniprot()

out_path = Path("../../graph/raw/")
current_path = Path(__file__).resolve().parent
source = current_path.name

# Download the data
data_file = Path("./allComplexes.txt")
if not data_file.exists():
    subprocess.run(["python", "get_data.py"], check=True)

edges = set()
df = pd.read_csv(data_file, sep="\t")

human_rows = df[df["organism"] == "Human"]
for subunits in human_rows["subunits_uniprot_id"].dropna():
    subunit_list = subunits.split(";")
    edges.update(
        tuple(sorted(pair))
        for pair in combinations(subunit_list, 2)
        if pair[0] != pair[1]
    )

output_dir = out_path / "GEN-ppi-GEN"
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_dir / f"{source}.tsv", "w") as o:
    o.write("n1\tn2\n")
    for edge in sorted(edges):
        o.write(f"{edge[0]}\t{edge[1]}\n")

sys.stderr.write("Done!\n")
