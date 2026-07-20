'''
Buffer Analysis: Count GPS points within buffers around collection sites
to determine what drives high/low passage classifications.

Steps
- creating buffers around collection sites (0.5, 1, 2km)
- overlapping data points from different origins to understand low/ high passage classes:
    - subcohort or GPS follow-up
    - positive, negative, or all
- [optional] create some maps

Notes:
- All villages location are considered 'high passage' regardless of the gps data points.
'''
# %% imports
import pandas as pd
import geopandas as gpd
import numpy as np

# %% Load dataset
dataset = pd.read_csv('outputs/merged_dataset.csv', index_col=0)
dataset[['Longitude', 'Latitude']] = dataset[['Longitude', 'Latitude']].apply(
    lambda col: col.astype(str).str.replace(',', '.').astype(float)
)

# %% Load GPS files — tag each with a source type
gps_sources = {
    'Alltracks2018.csv': '2018',
    'Alltracks_2019_1.csv': '2019',
    'Alltracks_2019_2.csv': '2019',
    'Alltracks_subcohort_F1.csv': 'F1',
    'Alltracks_subcohort_F2.csv': 'F2',
}

alltracks = pd.DataFrame()
for gps_file, source_label in gps_sources.items():
    try:
        tracks = pd.read_csv(f'gps_points/{gps_file}', index_col=0)
        tracks[['y__geo_', 'x__geo_']] = tracks[['y__geo_', 'x__geo_']].replace(',', '.').astype(float)
        tracks['source'] = source_label
        alltracks = pd.concat([alltracks, tracks], ignore_index=True)
        print(f"  Added {gps_file} ({source_label}): {len(tracks)} records")
    except FileNotFoundError as e:
        raise(e)

print(f"\nTotal GPS points: {len(alltracks)}")
print(f"Collection sites: {len(dataset)}")

# %% Convert to GeoDataFrames
sites_gdf = gpd.GeoDataFrame(
    dataset,
    geometry=gpd.points_from_xy(
        dataset['Longitude'].astype(float),
        dataset['Latitude'].astype(float)
    ),
    crs="EPSG:4326"
)

gps_gdf = gpd.GeoDataFrame(
    alltracks,
    geometry=gpd.points_from_xy(
        alltracks['x__geo_'].astype(float),
        alltracks['y__geo_'].astype(float)
    ),
    crs="EPSG:4326"
)

# %% Buffer analysis with source breakdown
buffer_distances_m = [500, 1000, 2000]
source_types = [
    '2018',
    '2019',
    '2018+2019',
    'F1',
    'F2',
    'F1+F2'
]
results = []

print("\nProcessing buffers...")
for idx, site in sites_gdf.iterrows():
    site_code = site['Site_code']
    passage_class = site['Passage']

    lon = float(site['Longitude'])
    lat = float(site['Latitude'])
    utm_zone = int((lon + 180) / 6) + 1
    # Correct hemisphere: 326xx = North, 327xx = South
    epsg_code = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

    # Create site GeoDataFrame and reproject
    site_utm = gpd.GeoDataFrame([site], geometry=[site.geometry], crs="EPSG:4326")
    site_utm = site_utm.to_crs(epsg=epsg_code)
    gps_utm = gps_gdf.to_crs(epsg=epsg_code)

    for buffer_m in buffer_distances_m:
        buffer_geom = site_utm.geometry.iloc[0].buffer(buffer_m)

        # Total count
        points_in_buffer = gps_utm[gps_utm.geometry.intersects(buffer_geom)] #TODO: try within if small accuracy
        point_count = len(points_in_buffer)

        row = {
            'Site_code': site_code,
            'Passage': passage_class,
            'Village': site.get('Village', ''),
            'Buffer_m': buffer_m,
            'Points_total': point_count,
            'Density_per_km2': point_count / (np.pi * (buffer_m/1000)**2)
        }

        # Per-source breakdown
        for src in source_types:

            if src == '2018+2019':
                src_count = len(
                    points_in_buffer[
                        points_in_buffer['source'].isin(['2018', '2019'])
                    ]
                )

            elif src == 'F1+F2':
                src_count = len(
                    points_in_buffer[
                        points_in_buffer['source'].isin(['F1', 'F2'])
                    ]
                )

            else:
                src_count = len(
                    points_in_buffer[
                        points_in_buffer['source'] == src
                    ]
                )

            row[f'Points_{src}'] = src_count

        results.append(row)

    if (idx + 1) % 10 == 0:
        print(f"  Processed {idx + 1}/{len(sites_gdf)} sites")

# %% Results
results_df = pd.DataFrame(results)
print(f"\nResults: {len(results_df)} rows")
results_df.to_csv('outputs/buffer_analysis.csv', index=False)
print("Saved to: outputs/buffer_analysis.csv")

# %% Diagnostics — check for zero-count sites
total_zeros = (results_df[results_df['Buffer_m'] == 500]['Points_total'] == 0).sum()
print(f"\nSites with 0 GPS points in 500m buffer: {total_zeros}/{len(sites_gdf)}")
print(f"Passage class distribution:\n{dataset['Passage'].value_counts()}")

# %% Summary statistics
print("\n" + "="*70)
print("SUMMARY STATISTICS")
print("="*70)

source_cols = [
    'Points_total',
    'Points_2018',
    'Points_2019',
    'Points_2018+2019',
    'Points_F1',
    'Points_F2',
    'Points_F1+F2'
]

for buffer_m in buffer_distances_m:
    subset = results_df[results_df['Buffer_m'] == buffer_m]
    print(f"\n--- Buffer: {buffer_m/1000:.1f} km ---")
    for passage in ['high', 'low']:
        sub = subset[subset['Passage'] == passage]
        if len(sub) == 0:
            print(f"  {passage} passage: 0 sites")
            continue
        print(f"\n  {passage} passage ({len(sub)} sites):")
        cols_to_show = source_cols
        print(sub[cols_to_show].describe())

# %% Correlation analysis
print("\n" + "="*70)
print("CORRELATION WITH PASSAGE CLASS")
print("="*70)

results_df['Passage_numeric'] = (results_df['Passage'] == 'high').astype(int)


for threshold in [500, 1000, 2000, 3000, 5000]:
    pred = results_df["Points_total"] > threshold
    acc = (pred == (results_df["Passage"] == "high")).mean()
    print(threshold, acc)

# Check for constant values
if results_df['Passage_numeric'].std() == 0:
    print("\n⚠ Passage is constant (all 'high' or all 'low') — correlation undefined.")
    print("   You need both classes represented to compute correlation.")
else:
    corr_cols = source_cols
    for buffer_m in buffer_distances_m:
        subset = results_df[results_df['Buffer_m'] == buffer_m]
        print(f"\n  {buffer_m/1000:.1f} km buffer:")
        for col in corr_cols:
            if subset[col].std() == 0:
                print(f"    {col}: no variance (all zeros?) — correlation undefined")
            else:
                corr = subset[col].corr(subset['Passage_numeric'])
                print(f"    {col}: r = {corr:.3f}")
# %%
