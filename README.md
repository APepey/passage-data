# Passage data - Buffer Analysis
## Description
Count GPS points within buffers around collection sites to determine what drives high/low passage classification.

## Usage
1. run `make install`
2. run `python determine-passage-cats.py` or directly within the file using the magic command `# %%`.

## Steps
- imports data
- creates buffers around collection sites
- selects overlapping data points from different origins to define passage classes with different parameters:
    - subcohort or GPS follow-up or some combination or all
    - buffer sizes
- saves median split results: which params combination can explain the split, specific to each LU type

## Constraints
- All villages location were considered 'high passage' regardless of the gps data points, so they are not included in the analysis.
- The analysis was executed on a subset of data, including only the first round of mosquito collection and HDN locations.

## Contact
Anaïs Pepey, PhD - [portfolio](https://apepey.notion.site/Ana-s-Pepey-PhD-5086e0b7c889490abfa67625339825f8) - [email](mailto:ana.pepey@posteo.net)
