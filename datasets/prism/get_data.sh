#!/bin/bash
set -euo pipefail

# TODO: Update the URL with the latest data from DepMap in the future.
# Example: https://depmap.org/portal/data_page/?tab=allData&releasename=PRISM%20Repurposing%20Public%2024Q2&filename=Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv

url="https://figshare.com/ndownloader/files/20237739"
file="secondary-screen-dose-response-curve-parameters.csv"

if curl --output /dev/null --silent --head --fail "$url"; then
    wget -O "$file" "$url"
else
    echo "URL not found: $url"
    exit 1
fi
