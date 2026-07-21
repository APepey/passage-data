# %% imports
import pandas as pd
import numpy as np
import geopandas as gpd
from sklearn.metrics import accuracy_score

# Search parameters
buffer_distances_m = [100, 200, 500, 1000, 1500, 2000]
source_types = ["2018", "2019", "2018+2019", "F1", "F2", "F1+F2", "total"]

# %% Load dataset
dataset = pd.read_csv("outputs/merged_dataset.csv", sep=";")
dataset[["Longitude", "Latitude"]] = dataset[["Longitude", "Latitude"]].apply(
    lambda col: col.astype(str).str.replace(",", ".").astype(float)
)

# %% drop village category (all were defined as high passage)
dataset = dataset[dataset.LU != "village"].copy()

# keep only HDN traps
dataset = dataset[dataset.TrapType == "hdn"].copy()

gps_sources = {
    "Alltracks2018.csv": "2018",
    "Alltracks_2019_1.csv": "2019",
    "Alltracks_2019_2.csv": "2019",
    "Alltracks_subcohort_F1.csv": "F1",
    "Alltracks_subcohort_F2.csv": "F2",
}

# %% Load GPS tracks
alltracks = pd.DataFrame()

for gps_file, source_label in gps_sources.items():
    tracks = pd.read_csv(f"gps_points/{gps_file}", index_col=0)

    tracks[["y__geo_", "x__geo_"]] = tracks[["y__geo_", "x__geo_"]].apply(
        lambda col: col.astype(str).str.replace(",", ".").astype(float)
    )

    tracks["source"] = source_label
    alltracks = pd.concat([alltracks, tracks], ignore_index=True)

    print(f"Added {gps_file} ({source_label}): {len(tracks)} records")

print(f"\nTotal GPS points: {len(alltracks)}")
print(f"Collection sites: {len(dataset)}")

# %% Create GeoDataFrames (Cambodia: UTM 48N)
sites_utm = gpd.GeoDataFrame(
    dataset, geometry=gpd.points_from_xy(dataset.Longitude, dataset.Latitude), crs="EPSG:4326"
).to_crs("EPSG:32648")

gps_utm = gpd.GeoDataFrame(
    alltracks, geometry=gpd.points_from_xy(alltracks.x__geo_, alltracks.y__geo_), crs="EPSG:4326"
).to_crs("EPSG:32648")

# %% Initialise lists
results = []
count_tables = []
median_results = []

# %% Grid search
for src in source_types:

    if src == "2018":
        gps_subset = gps_utm[gps_utm.source == "2018"]
    elif src == "2019":
        gps_subset = gps_utm[gps_utm.source == "2019"]
    elif src == "2018+2019":
        gps_subset = gps_utm[gps_utm.source.isin(["2018", "2019"])]
    elif src == "F1":
        gps_subset = gps_utm[gps_utm.source == "F1"]
    elif src == "F2":
        gps_subset = gps_utm[gps_utm.source == "F2"]
    elif src == "F1+F2":
        gps_subset = gps_utm[gps_utm.source.isin(["F1", "F2"])]
    else:
        gps_subset = gps_utm

    for buffer in buffer_distances_m:

        buffers = sites_utm.copy()
        buffers.geometry = buffers.geometry.buffer(buffer)

        joined = gpd.sjoin(gps_subset, buffers, how="inner", predicate="within")

        counts = joined.groupby("index_right").size()

        gps_count = pd.Series(0, index=sites_utm.index)
        gps_count.loc[counts.index] = counts

        tmp = dataset.copy()
        tmp["source"] = src
        tmp["buffer"] = buffer
        tmp["gps_count"] = gps_count.values

        count_tables.append(tmp)
        thresholds = np.unique(gps_count.astype(int))

        # threshold method
        for threshold in thresholds:

            predicted = pd.Series("low", index=sites_utm.index)
            predicted[gps_count >= threshold] = "high"

            for lu in dataset.LU.unique():

                mask = dataset.LU == lu

                agreement = accuracy_score(dataset.loc[mask, "Passage"], predicted.loc[mask])

                results.append(
                    {"LU": lu, "source": src, "buffer": buffer, "threshold": threshold, "agreement": agreement}
                )

        # median split method (once per source-buffer)
        for lu in dataset.LU.unique():

            mask = dataset.LU == lu

            ranks = gps_count.loc[mask].rank(method="first")

            predicted = pd.Series(index=gps_count.index, dtype=object)
            predicted.loc[mask] = np.where(ranks > len(ranks) / 2, "high", "low")

            agreement = accuracy_score(dataset.loc[mask, "Passage"], predicted.loc[mask])

            median_results.append({"LU": lu, "source": src, "buffer": buffer, "agreement": agreement})


# %% agreement results
results = pd.DataFrame(results).sort_values("agreement", ascending=False)
results.to_csv("outputs/agreement_results.csv", index=False)

print("\nBest threshold results")
print(results.head(20))

# %% median results
median_results = pd.DataFrame(median_results).sort_values("agreement", ascending=False)

count_tables = pd.concat(count_tables, ignore_index=True)
count_tables.to_csv("outputs/buffer_point_counts.csv", index=False)

print("\nBest median-split results")
print(median_results.head(20))

# %%
