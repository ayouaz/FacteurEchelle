import math
import pyproj
import pandas as pd
from pyproj import Transformer, CRS

# WGS84 Constants
A = 6378137.0  # Semi-major axis
F = 1 / 298.257223563  # Flattening
E2 = 2 * F - F ** 2  # First eccentricity squared

def dms_to_dd(d, m, s, direction):
    dd = float(d) + float(m) / 60 + float(s) / 3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

def get_utm_zone(lon):
    return int((lon + 180) / 6) + 1

def wgs84_to_utm(lat, lon, zone=None):
    """
    Converts WGS84 Lat/Lon to UTM.
    If zone is not provided, it is calculated from longitude.
    Returns: zone, easting, northing, k_point (point scale factor)
    """
    if zone is None:
        zone = get_utm_zone(lon)
    
    # Determine hemisphere
    south = lat < 0
    
    # Create CRS
    crs_wgs84 = CRS.from_epsg(4326)
    
    # EPSG for UTM zone. 326xx for North, 327xx for South
    base_epsg = 32700 if south else 32600
    epsg_utm = base_epsg + zone
    
    crs_utm = CRS.from_epsg(epsg_utm)
    
    transformer = Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)
    easting, northing = transformer.transform(lon, lat)
    
    # Calculate Grid Scale Factor (k_grid)
    # This is a bit complex. Pyproj doesn't give point scale factor directly in simple transform.
    # We can use the formula or pyproj's get_factors if available, but simplest standard formula for UTM:
    # k = k0 * (1 + (E_prime^2 / 2*R^2)) where E_prime = E - 500000
    # Or rigorously using pyproj:
    
    # Let's use pyproj to get factors if possible, or rigorous formula.
    # Actually, pyproj does not easily expose get_factors for point. 
    # We will use the standard geometric formula for k_grid on the projection surface.
    
    k0 = 0.9996
    # Approximate R (Geometric mean radius of curvature)
    # This is sufficient for scale factor estimation usually, but let's be more precise if possible.
    # k = k0 / cos(psi) ... complex.
    
    # Let's use the explicit approximation for UTM scale factor:
    # k = k0 * (1 + (XVII * q^2) + (XVIII * q^4))
    # where q = (E - 500,000) * 10^-6
    # This is from survey manuals.
    
    # Alternatively, we can compute it using the projection properties.
    # Let's use the standard approximation which is widely used in civil engineering tools:
    # k ≈ k0 * (1 + (E - 500000)^2 / (2 * R_mean^2))
    # R_mean ≈ 6371000 or sqrt(M*N)
    
    # Let's calculate Radius of Curvature in the prime vertical (N) and meridian (M)
    sin_lat = math.sin(math.radians(lat))
    N = A / math.sqrt(1 - E2 * sin_lat ** 2)
    M = A * (1 - E2) / ((1 - E2 * sin_lat ** 2) ** 1.5)
    r_mean = math.sqrt(M * N)
    
    dl = (easting - 500000.0)
    k_grid = k0 * (1 + (dl ** 2) / (2 * r_mean ** 2))
    
    # Refined formula including higher order terms if needed, but the above is usually good for ppm level.
    # Let's stick to the example verification to measure our precision.
    
    return zone, easting, northing, k_grid, r_mean

def calculate_height_scale_factor(h_ortho_or_ellip, r_mean):
    """
    Calculates Height Scale Factor (HSF).
    HSF = R / (R + H)
    Wait, the prompt says: hsf = 1 + H/R ?? No, usually it is R / (R+H) to convert Ground to Grid.
    Let's check the user prompt explicitly:
    "hsf = 1 + H/R" was written in the prompt?
    Actually prompt says: "hsf = 1 + H/R" -- Wait.
    If H is positive (above ellipsoid), the distance on ground is LARGER than on ellipsoid.
    So to convert Ground Distance to Ellipsoid Distance, we multiply by R/(R+H).
    
    But Scale Factor is often defined as Grid / Ground.
    Combined Scale Factor = Grid Scale Factor * Elevation Factor.
    Grid Factor = Grid Dist / Ellipsoid Dist
    Elevation Factor = Ellipsoid Dist / Ground Dist = R / (R + H)
    
    Let's re-read prompt carefully:
    "hsf = 1 + H/R" ... This looks like it might be an approximation for (R+H)/R ? Which would be > 1.
    If hsf > 1, then Ground = Ellipsoid * hsf.
    Usually Combined Factor (CSF) converts Ground to Grid: Grid = Ground * CSF.
    CSF = GridFactor * ElevationFactor
    ElevationFactor = R / (R + H) ≈ 1 - H/R
    
    PROMPT TEXT: 
    "hsf = 1 + H / R" ... ?? 
    Maybe the user means "Reduction to Ellipsoid"? Or maybe they made a typo?
    Let's look at the example.
    Lat: 36.5 deg, H = 12m or 59m.
    Factor typically is < 1 for elevation factor.
    
    Let's check the result example: "Facteur d’échelle combiné ≈ 0.999874692048"
    If k0 is 0.9996. The point is likely near central meridian (Zone 31 usually for 1 deg E, wait 1 deg E is Zone 31).
    Longitude 1deg E is in Zone 31 (0 to 6 deg E).
    Meridian is 3 deg E. 1 deg E is 2 degrees away.
    So it's not central.
    
    Let's verify with the example data later. I will implement a flexible function we can adjust or I will stick to standard Elevation Factor = R / (R+h).
    
    However, the user EXPLICITLY computed: "hsf=1+ H/R" (Maybe they meant "1 / (1 + H/R)"? Or maybe they meant "Multiplier to get Ground from Ellipsoid"?).
    
    Let's assume standard definitions first: CSF = Grid / Ground.
    Elevation Factor (EF) = R / (R + H).
    Grid Factor (GF) = k_grid.
    CSF = GF * EF.
    
    The prompt says "kcombined = kgrid * hsf".
    And "hsf = 1 + R_H" -- Wait, the prompt text says "hsf=1+ R over H" ?? No.
    Likely text formatting issue in prompt "hsf=1+ \n R \n H".
    
    Let's look at the prompt again:
    "hsf=1+HR" (might mean H/R or something).
    "hsf=1+ R H" (Visual artifact).
    
    Common formula: EF = R / (R + H).
    If I use hsf = 1 - H/R (approx), that matches R/(R+H).
    
    Let's Assume standard engineering practice: Combined Factor converts Ground -> Grid.
    So EF should be < 1 for H > 0.
    I will implement EF = R / (R + H).
    
    Note: The user Prompt says "hsf=1+HR" which is very suspicious.
    Wait, if I interpret as "1 + H/R" that is > 1.
    If I interpret as "1 / (1 + H/R)" that is < 1.
    
    Let's rely on the Example Value verification to tune this.
    I will write the standard one first.
    """
    # Standard Elevation Factor = R / (R + H)
    # Which is approximately 1 - H/R
    return r_mean / (r_mean + h_ortho_or_ellip)

def calculate_factors(lat, lon, h, h_is_ellipsoidal=True):
    zone, easting, northing, k_grid, r_mean = wgs84_to_utm(lat, lon)
    
    # H to use:
    # Strict elevation factor uses Ellipsoidal Height (h).
    # If user provides Orthometric (H), h = H + N_geoid.
    # The prompt gives both. "Hauteur ellipsoïdale : 59.595 m", "Hauteur orthométrique EGM08 : 12.041 m".
    # And Result.
    # We should use Ellipsoidal height if available for geometric reduction.
    # If only orthometric is available, we use that as approx.
    
    h_use = h
    
    hsf = calculate_height_scale_factor(h_use, r_mean)
    k_combined = k_grid * hsf
    
    return {
        'zone': zone,
        'easting': easting,
        'northing': northing,
        'k_grid': k_grid,
        'hsf': hsf,
        'k_combined': k_combined
    }
