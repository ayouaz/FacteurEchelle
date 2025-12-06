import streamlit as st
import pandas as pd
from calc_logic import calculate_factors, dms_to_dd, wgs84_to_utm, calculate_height_scale_factor

__version__ = "0.8.0"

st.set_page_config(page_title="Calculateur Facteur d'Échelle", layout="wide")

st.title("Calculateur de Facteurs d'Échelle")
st.markdown("""
Cet outil permet de calculer les facteurs d'échelle de projection (Grid Scale Factor), 
vertical (Height Scale Factor) et combiné, à partir de coordonnées WGS84, UTM ou d'un fichier.
""")

st.sidebar.title("À propos")
st.sidebar.info("""
**Développé par :**  
Ing. AYOUAZ Maamar

**Email :**  
ayouaz@geosmatic.dz
""")

tabs = st.tabs(["📍 Point WGS84", "📍 Point UTM", "📂 Import Fichier"])

# --- TAB 1: WGS84 ---
with tabs[0]:
    st.header("Saisie Coordonnées WGS84")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Latitude")
        lat_mode = st.radio("Format Latitude", ["Degrés Décimaux (DD)", "DMS"], key='lat_mode')
        if lat_mode == "Degrés Décimaux (DD)":
            lat = st.number_input("Latitude (DD)", value=36.509736, format="%.8f")
        else:
            c1, c2, c3 = st.columns(3)
            d_lat = c1.number_input("Degrés", value=36, step=1)
            m_lat = c2.number_input("Minutes", value=30, step=1)
            s_lat = c3.number_input("Secondes", value=35.05, format="%.2f")
            hem_lat = st.selectbox("Hémisphère", ["N", "S"])
            lat = dms_to_dd(d_lat, m_lat, s_lat, hem_lat)

    with col2:
        st.subheader("Longitude")
        lon_mode = st.radio("Format Longitude", ["Degrés Décimaux (DD)", "DMS"], key='lon_mode')
        if lon_mode == "Degrés Décimaux (DD)":
            lon = st.number_input("Longitude (DD)", value=1.304408, format="%.8f")
        else:
            c1, c2, c3 = st.columns(3)
            d_lon = c1.number_input("Degrés", value=1, step=1)
            m_lon = c2.number_input("Minutes", value=18, step=1)
            s_lon = c3.number_input("Secondes", value=15.87, format="%.2f")
            hem_lon = st.selectbox("Hémisphère (E/O)", ["E", "W"])
            lon = dms_to_dd(d_lon, m_lon, s_lon, hem_lon)
            
    h_ellip = st.number_input("Hauteur Ellipsoïdale (h) en mètres", value=59.595, format="%.3f")
    
    if st.button("Calculer (WGS84)", key='calc_wgs84'):
        results = calculate_factors(lat, lon, h_ellip)
        
        st.success("Calcul effectué !")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.info(f"**Zone UTM**: {results['zone']}")
            st.info(f"**Easting (X)**: {results['easting']:.3f} m")
            st.info(f"**Northing (Y)**: {results['northing']:.3f} m")
            
        with res_col2:
            st.metric("Grid Scale Factor", f"{results['k_grid']:.10f}")
            st.metric("Height Scale Factor", f"{results['hsf']:.10f}")
            st.metric("Facteur Combiné", f"{results['k_combined']:.10f}")


# --- TAB 2: UTM ---
with tabs[1]:
    st.header("Saisie Coordonnées UTM")
    # UTM input requires reverse conversion to get Lat/Lon for some rigorous calc, 
    # OR we can just use the provided X, Y, Zone.
    # We DO need Lat for rigorous Height Factor (specifically R at that Lat), 
    # but R doesn't vary THAT much.
    # However, to be consistent, we might want to approximate Lat from UTM.
    # Wait, my logic `wgs84_to_utm` went WGS -> UTM.
    # For UTM inputs, I need to convert UTM -> WGS84 to get 'Lat' for 'R' calculation if I want to be precise,
    # OR I just use a standard R. But Lat is better.
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        utm_zone = st.number_input("Fuseau UTM", value=31, step=1)
        hemisphere = st.selectbox("Hémisphère", ["Nord", "Sud"], key='utm_hem2')
        is_south = hemisphere == "Sud"
        
    with col_u2:
        utm_x = st.number_input("Est (X)", value=348163.320, format="%.3f")
        utm_y = st.number_input("Nord (Y)", value=4041824.970, format="%.3f")
        
    utm_h = st.number_input("Hauteur Ellipsoïdale (h)", value=59.595)
    
    if st.button("Calculer (UTM)", key='calc_utm'):
        # Convert UTM to WGS84 to get Lat/Lon for R calculation
        # and re-verify.
        import pyproj
        base_epsg = 32700 if is_south else 32600
        crs_utm = pyproj.CRS.from_epsg(base_epsg + utm_zone)
        crs_wgs = pyproj.CRS.from_epsg(4326)
        transformer = pyproj.Transformer.from_crs(crs_utm, crs_wgs, always_xy=True)
        lon_c, lat_c = transformer.transform(utm_x, utm_y)
        
        # Now use the standard function
        results = calculate_factors(lat_c, lon_c, utm_h)
        # We trust the input X/Y, but the result might slightly differ if we recalc from lat/lon.
        # Let's display the factors.
        
        st.success("Calcul effectué !")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.write(f"**Latitude Calculée**: {lat_c:.8f}°")
            st.write(f"**Longitude Calculée**: {lon_c:.8f}°")
            
        with res_col2:
            st.metric("Grid Scale Factor", f"{results['k_grid']:.10f}")
            st.metric("Height Scale Factor", f"{results['hsf']:.10f}")
            st.metric("Facteur Combiné", f"{results['k_combined']:.10f}")

# --- TAB 3: FILE IMPORT ---
with tabs[2]:
    st.header("Import de Fichier (Batch)")
    st.markdown("Format attendu: **Numéro, X, Y, Z** (CSV ou Excel). Colonnes détectées automatiquement si en-tête manquant, sinon ordre par défaut.")
    
    uploaded_file = st.file_uploader("Choisir un fichier", type=["csv", "xlsx", "xls"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("Aperçu du fichier:", df.head())
            
            # Map columns
            cols = df.columns.tolist()
            c1, c2, c3, c4, c5 = st.columns(5)
            col_id = c1.selectbox("Colonne ID", cols, index=0)
            col_x = c2.selectbox("Colonne X (Est)", cols, index=1 if len(cols)>1 else 0)
            col_y = c3.selectbox("Colonne Y (Nord)", cols, index=2 if len(cols)>2 else 0)
            col_z = c4.selectbox("Colonne Z (Hauteur)", cols, index=3 if len(cols)>3 else 0)
            
            file_zone = c5.number_input("Fuseau UTM pour ce fichier", value=31, step=1)
            file_hem = st.selectbox("Hémisphère Fichier", ["Nord", "Sud"])
            is_south_file = file_hem == "Sud"
            
            if st.button("Lancer le traitement par lot"):
                # Processing
                results_list = []
                
                # Setup Transformer once
                import pyproj
                base_epsg = 32700 if is_south_file else 32600
                crs_utm = pyproj.CRS.from_epsg(base_epsg + file_zone)
                crs_wgs = pyproj.CRS.from_epsg(4326)
                transformer = pyproj.Transformer.from_crs(crs_utm, crs_wgs, always_xy=True)
                
                progress_bar = st.progress(0)
                
                for idx, row in df.iterrows():
                    try:
                        pts_id = row[col_id]
                        x_val = float(row[col_x])
                        y_val = float(row[col_y])
                        z_val = float(row[col_z])
                        
                        # Convert to Lat/Lon
                        lon_c, lat_c = transformer.transform(x_val, y_val)
                        
                        # Calc Factors
                        res = calculate_factors(lat_c, lon_c, z_val)
                        
                        results_list.append({
                            "Numéro": pts_id,
                            "X_UTM": x_val,
                            "Y_UTM": y_val,
                            "Z": z_val,
                            "Grid Scale Factor": res['k_grid'],
                            "Height Scale Factor": res['hsf'],
                            "Facteur Échelle Combiné": res['k_combined']
                        })
                    except Exception as e:
                        st.error(f"Erreur ligne {idx}: {e}")
                    
                    if idx % 10 == 0:
                        progress_bar.progress(min(1.0, (idx+1)/len(df)))
                
                progress_bar.progress(1.0)
                
                res_df = pd.DataFrame(results_list)
                st.success(f"Traitement terminé pour {len(res_df)} points.")
                st.dataframe(res_df)
                
                # Export CSV
                csv = res_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Télécharger CSV",
                    csv,
                    "resultats_facteurs.csv",
                    "text/csv",
                    key='download-csv'
                )
                
        except Exception as e:
            st.error(f"Erreur de lecture du fichier: {e}")

