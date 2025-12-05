import pandas as pd
import pyproj
from calc_logic import calculate_factors

# Simulating the app's batch logic
df = pd.read_csv('dummy_data.csv')
print("Loaded DataFrame:")
print(df)

results_list = []
file_zone = 31
is_south_file = False
base_epsg = 32700 if is_south_file else 32600
crs_utm = pyproj.CRS.from_epsg(base_epsg + file_zone)
crs_wgs = pyproj.CRS.from_epsg(4326)
transformer = pyproj.Transformer.from_crs(crs_utm, crs_wgs, always_xy=True)

print("\nProcessing...")
for idx, row in df.iterrows():
    pts_id = row['ID']
    x_val = float(row['X'])
    y_val = float(row['Y'])
    z_val = float(row['Z'])
    
    lon_c, lat_c = transformer.transform(x_val, y_val)
    res = calculate_factors(lat_c, lon_c, z_val)
    
    results_list.append({
        "ID": pts_id,
        "Combined": res['k_combined']
    })
    print(f"Point {pts_id}: Combined Factor = {res['k_combined']:.10f}")

print("\nBatch simulated successfully.")
