'''
Buffer Analysis: Count GPS points within buffers around collection sites
to determine what drives high/low passage classifications (done years ago, do not remember the settings)
'''
# %% imports
import pandas as pd
import geopandas as gpd

# %% Load dataset
dataset = pd.read_csv('outputs/merged_dataset.csv', index_col=0)
dataset[['Longitude', 'Latitude']] = dataset[['Longitude', 'Latitude']].apply(
    lambda col: col.astype(str).str.replace(',', '.').astype(float)
)
gps_sources = {
    'Alltracks2018.csv': '2018',
    'Alltracks_2019_1.csv': '2019',
    'Alltracks_2019_2.csv': '2019',
    'Alltracks_subcohort_F1.csv': 'F1',
    'Alltracks_subcohort_F2.csv': 'F2',
}

# %% Buffer analysis with source breakdown
buffer_distances_m = [100, 500, 1000, 1500, 2000, 5000]
source_types = [
    '2018',
    '2019',
    '2018+2019',
    'F1',
    'F2',
    'F1+F2'
    'total'
]


# TODO: drop all rows where dataset.LU == 'village'

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

methods = ['intersects', 'within']
gps_utm = 'TODO'
# TODO: create spatial data from df

#%% classify data
for  src in source_types:
    for buffer in buffer_distances_m:
        # TODO: intersect src with buffer
        # TODO: store results into df: number
        points_in_buffer = gps_utm[gps_utm.geometry.intersects(buffer)] #TODO: try within if small accuracy
        point_count = len(points_in_buffer)

# TODO: create a confusion matrix to see which settings classify correctly the collections sites as Passage == 'high' or Passage 'low'
