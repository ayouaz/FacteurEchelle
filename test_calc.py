from calc_logic import calculate_factors, dms_to_dd

# Example Data
lat_dms = (36, 30, 35.05)
lon_dms = (1, 18, 15.87)
h_ellip = 59.595

lat = dms_to_dd(*lat_dms, 'N')
lon = dms_to_dd(*lon_dms, 'E')

print(f"Lat DD: {lat}")
print(f"Lon DD: {lon}")

results = calculate_factors(lat, lon, h_ellip)

print("-" * 20)
print(f"Zone: {results['zone']}")
print(f"Easting: {results['easting']}")
print(f"Northing: {results['northing']}")
print(f"Grid Scale Factor: {results['k_grid']}")
print(f"Height Scale Factor: {results['hsf']}")
print(f"Combined Factor: {results['k_combined']}")
print("-" * 20)

target = 0.999874692048
diff = results['k_combined'] - target
print(f"Target: {target}")
print(f"Diff: {diff:.12f}")

if abs(diff) < 1e-6:
    print("SUCCESS: Matches target precision.")
else:
    print("FAILURE: Discrepancy found.")
