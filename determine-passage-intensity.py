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

#%%
import pandas as pd

#%% import dataset
dataset = pd.read_csv('outputs/merged_dataset.csv', index_col=0 )
alltracks_2018 = pd.read_csv('gps_points/Alltracks2018.csv', index_col=0 )
# %%
print('\n ==== merged dataset characteristics ====')
print(dataset.columns)
print(dataset.shape)
print(dataset.sample(5))

print('\n ==== GPS tracks example ====')
print(alltracks_2018.columns)
print(alltracks_2018.shape)
print(alltracks_2018.sample(5))

#%%
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS
import numpy as np

# %% Load data
print("Loading data...")
dataset = pd.read_csv('outputs/merged_dataset.csv', index_col=0)
dataset[['Longitude', 'Latitude']] = dataset[['Longitude', 'Latitude']].apply(
    lambda col: col.astype(str).str.replace(',', '.').astype(float)
)
# %% Load  GPS files
alltracks = pd.DataFrame()
for gps_file in ['Alltracks2018.csv', 'Alltracks_2019_1.csv', 'Alltracks_2019_2.csv',
                 'Alltracks_subcohort_F1.csv', 'Alltracks_subcohort_F2.csv']:
    try:
        tracks = pd.read_csv(f'gps_points/{gps_file}', index_col=0)
        tracks[['y__geo_', 'x__geo_']] = tracks[['y__geo_', 'x__geo_']].replace(',', '.').astype(float)
        alltracks = pd.concat([alltracks, tracks], ignore_index=True)
        print(f"  Added {gps_file}: {len(tracks)} records")
    except FileNotFoundError as e:
        raise(e)
print(f"Collection sites: {len(dataset)}")

# %% Convert to GeoDataFrames
sites_gdf = gpd.GeoDataFrame(
    dataset,
    geometry=gpd.points_from_xy(
        dataset['Longitude'].astype(float),
        dataset['Latitude'].astype(float)
    ),
    crs="EPSG:4326"  # WGS84 (latitude/longitude)
)

# %% Create GPS points geometry
gps_gdf = gpd.GeoDataFrame(
    alltracks,
    geometry=gpd.points_from_xy(
        alltracks['x__geo_'].astype(float),
        alltracks['y__geo_'].astype(float)
    ),
    crs="EPSG:4326"
)

print(f"\nSites GeoDataFrame: {len(sites_gdf)} points")
print(f"GPS GeoDataFrame: {len(gps_gdf)} points")

# %% Define buffer distances (in meters)
buffer_distances_m = [500, 1000, 2000]  # 0.5, 1, 2 km
results = []

# %% Process each site
print("\nProcessing buffers...")
for _, site in sites_gdf.iterrows():
    site_code = site['Site_code']
    passage_class = site['Passage']

    # Project to appropriate UTM zone for accurate distance buffers
    # Estimate UTM zone from longitude
    lon = float(site['Longitude'])
    utm_zone = int((lon + 180) / 6) + 1
    epsg_code = 32600 + utm_zone  # Northern hemisphere
    site_utm = site_utm.to_crs(epsg=epsg_code)
    gps_utm = gps_gdf.to_crs(epsg=epsg_code)


    for buffer_m in buffer_distances_m:
        # Create buffer
        buffer_geom = site_utm.geometry.iloc[0].buffer(buffer_m)

        # Count points within buffer
        points_in_buffer = gps_utm[gps_utm.geometry.within(buffer_geom)]
        point_count = len(points_in_buffer)

        results.append({
            'Site_code': site_code,
            'Passage': passage_class,
            'Village': site.get('Village', ''),
            'Buffer_m': buffer_m,
            'Points_count': point_count,
            'Density_per_km2': point_count / (np.pi * (buffer_m/1000)**2)
        })

# %% Create results dataframe
results_df = pd.DataFrame(results)
print(f"\nResults created: {len(results_df)} rows")

# %% Save results
results_df.to_csv('outputs/buffer_analysis.csv', index=False)
print("Saved to: outputs/buffer_analysis.csv")

# %% Summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

for buffer_m in buffer_distances_m:
    subset = results_df[results_df['Buffer_m'] == buffer_m]
    print(f"\n--- Buffer: {buffer_m/1000:.1f} km ---")
    print(f"High passage sites:")
    print(subset[subset['Passage']=='high'][['Points_count', 'Density_per_km2']].describe())
    print(f"\nLow passage sites:")
    print(subset[subset['Passage']=='low'][['Points_count', 'Density_per_km2']].describe())

# %% Correlation analysis
print("\n" + "="*60)
print("CORRELATION WITH PASSAGE CLASS")
print("="*60)

# Convert Passage to numeric (high=1, low=0)
results_df['Passage_numeric'] = (results_df['Passage'] == 'high').astype(int)

for buffer_m in buffer_distances_m:
    subset = results_df[results_df['Buffer_m'] == buffer_m]
    corr = subset['Points_count'].corr(subset['Passage_numeric'])
    print(f"{buffer_m/1000:.1f}km buffer: correlation with Passage = {corr:.3f}")
# %%
