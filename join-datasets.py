"""
Finding the definition of low and high passage sites from the available data.
Data source: Kaev Seima's mosquito collections (Dropbox)
"""

# %%
import pandas as pd

# %%
codes = pd.read_csv("data/sitecodes.csv", sep=";")
values = pd.read_csv("data/values.csv", sep=";")

# %%
values["Site_code"] = values["TrapID"].str.split("_", n=1).str[0]
values["Site_code"] = values["Site_code"].str.lower()
# %%
values_clean = values.dropna(axis=1).drop(columns=["TrapID", "LU"])
values_clean

# %%
codes["Site_code"] = codes["Site_code"].str.lower()

# %%
full_dataset = values_clean.merge(on=["Site_code"], right=codes)
# %%
full_dataset.to_csv("outputs/merged_dataset.csv")
# %%
cols = [
    "Count2018",
    "CountPos2019",
    "Count2019",
    "CountSubCohortF1",
    "CountSubCohortF2",
    "CountSubCohort",
    "CountTotal",
]

result = full_dataset.groupby("Passage")[cols].agg(["min", "max", "mean"])
result.to_csv("outputs/stats.csv")
# %% only HDN
result_hdn = full_dataset[full_dataset["TrapType"] == "hdn"].groupby("Passage")[cols].agg(["min", "max", "mean"])
result_hdn.to_csv("outputs/stats_hdn.csv")

# %% only HDN, no village
result_hdn_novillage = (
    full_dataset[(full_dataset["TrapType"] == "hdn") & (full_dataset["LU"] != "village")]
    .groupby("Passage")[cols]
    .agg(["min", "max", "mean"])
)
result_hdn_novillage.to_csv("outputs/stats_hdn_novillage.csv")
# %%
