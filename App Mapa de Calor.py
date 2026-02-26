import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import branca.colormap as cm
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analytics Racial Pro", layout="wide")

# Estilização CSS moderna
st.markdown("""
    <style>
    .main { background-color: #f1f3f6; }
    .stMetric { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PALETAS DE CORES ---
CORES_NEGRAS_5 = ['#ffffc1', '#fee08f', '#fda15f', '#f3624d', '#ca3351']
CORES_BRANCAS_5 = ['#ffffd6', '#d2edc3', '#67c5d0', '#5699c6', '#515da9']
COR_BRANCOS = '#1f3480'
COR_NEGROS = '#9d2417'

# --- 3. CARREGAMENTO DOS DADOS (OTIMIZADO) ---
@st.cache_data
def carregar_dados_parquet(caminho):
    try:
        gdf = gpd.read_parquet(caminho)
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        return gdf.fillna(0)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Parquet: {e}")
        return None

# BARRA LATERAL
st.sidebar.title("📁 Gestão de Dados")

caminho_local = "Banco de Dados.parquet"
gdf = None

if os.path.exists(caminho_local):
    gdf = carregar_dados_parquet(caminho_local)
else:
    st.sidebar.warning(f"Arquivo '{caminho_local}' não encontrado.")
    arquivo_upload = st.sidebar.file_uploader("Carregue o arquivo", type=["parquet", "geojson"])
    if arquivo_upload:
        if arquivo_upload.name.endswith('.parquet'):
            gdf = carregar_dados_parquet(arquivo_upload)
        else:
            gdf = gpd.read_file(arquivo_upload).to_crs(epsg=4326).fillna(0)

if gdf is not None:
    # --- 4. CONFIGURAÇÕES DOS FILTROS ---
    st.sidebar.markdown("---")
    st.sidebar.title("⚙️ Filtros do Mapa")
    
    with st.sidebar.expander("🌍 Estilo Visual", expanded=True):
        estilos = {
            "Mapa Claro": "cartodbpositron",
            "Mapa Escuro": "cartodbdark_matter",
            "Satélite (Híbrido)": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
        }
        fundo = st.selectbox("Escolha o fundo", list(estilos.keys()))

    with st.sidebar.expander("📍 Localização", expanded=True):
        municipios = sorted(gdf['NM_MUNICIP'].unique())
        mun_sel = st.selectbox("Município", ["Todos"] + municipios)
    
    with st.sidebar.expander("📊 Camada Racial", expanded=True):
        # OPÇÃO 1 APLICADA: Nomes reduzidos
        opcao = st.selectbox(
            "Visualização",
            ["Brancas: 5 Classes", "Negras: 5 Classes", 
             "50% Negras/Brancos", "60% Negras/Brancos", "75% Negras/Brancos"]
        )

    # --- 5. LÓGICA DE FILTRAGEM ---
    gdf_m = gdf.copy() if mun_sel == "Todos" else gdf[gdf['NM_MUNICIP'] == mun_sel].copy()
    
    colormap = None
    # Lógica ajustada para detectar os novos nomes reduzidos
    if "classes" in opcao.lower():
        is_br = "brancas" in opcao.lower()
        cores = CORES_BRANCAS_5 if is_br else CORES_NEGRAS_5
        colormap = cm.StepColormap(colors=cores, vmin=0, vmax=100, index=[0,20,40,60,80,100])
        gdf_final = gdf_m.copy()
        def style_fn(f):
            v = f['properties'].get("BRANCOS%" if is_br else "NEGROS%", 0)
            return {'fillColor': colormap(v), 'color': 'none', 'weight': 0, 'fillOpacity': 0.75}
    else:
        limite = int(opcao[:2])
        gdf_final = gdf_m[(gdf_m['BRANCOS%'] >= limite) | (gdf_m['NEGROS%'] >= limite)].copy()
        def style_fn(f):
            pb, pn = f['properties'].get('BRANCOS%', 0), f['properties'].get('NEGROS%', 0)
            cor = COR_BRANCOS if pb >= limite else (COR_NEGROS if pn >= limite else "transparent")
            return {'fillColor': cor, 'color': 'none', 'weight': 0, 'fillOpacity': 0.85}

    # --- 6. INTERFACE PRINCIPAL ---
    st.title(f"📊 Painel de Análise: {mun_sel}")
    
    c1, c2 = st.columns(2)
    c1.metric("Média Brancos", f"{gdf_m['BRANCOS%'].mean():.1f}%")
    c2.metric("Média Negras", f"{gdf_m['NEGROS%'].mean():.1f}%")

    col_mapa, col_rank = st.columns([3, 1])

    with col_mapa:
        m = folium.Map(tiles=estilos[fundo], attr="Provedores de Mapa")
        if not gdf_final.empty:
            b = gdf_final.total_bounds
            m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])
            folium.GeoJson(
                gdf_final, 
                style_function=style_fn,
                tooltip=folium.GeoJsonTooltip(
                    fields=['NM_BAIRRO', 'BRANCOS%', 'NEGROS%'],
                    aliases=['Bairro/Comunidade:', 'Brancos %:', 'Negras %:']
                )
            ).add_to(m)
            if colormap: colormap.add_to(m)
            st_folium(m, width="100%", height=550, key=f"{mun_sel}_{opcao}_{fundo}")
        else:
            st.warning("Nenhum dado encontrado para este filtro.")

    with col_rank:
        st.subheader("🏆 Top Concentrações")
        rank_col = "BRANCOS%" if "brancas" in opcao.lower() else "NEGROS%"
        top_5 = gdf_m.nlargest(5, rank_col)[['NM_BAIRRO', rank_col]]
        for _, row in top_5.iterrows():
            st.write(f"**{row['NM_BAIRRO']}**")
            st.progress(float(row[rank_col])/100)
            st.caption(f"{row[rank_col]}%")

    # LEGENDA NA BARRA LATERAL
    st.sidebar.markdown("---")
    if "classes" in opcao.lower():
        is_br = "brancas" in opcao.lower()
        cores = CORES_BRANCAS_5 if is_br else CORES_NEGRAS_5
        titulo = "População Branca" if is_br else "População Negras"
        faixas = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
        legend_html = f"<div style='padding:10px; border-radius:5px; border:1px solid #eee; background-color: white;'><strong>{titulo}</strong><br>"
        for i, cor in enumerate(cores):
            legend_html += f"<span style='color:{cor}; font-size:20px;'>■</span> {faixas[i]}<br>"
        legend_html += "</div>"
        st.sidebar.markdown(legend_html, unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"""
        <div style="padding:10px; border-radius:5px; border:1px solid #eee; background-color: white;">
            <strong>Legenda de Cores:</strong><br>
            <span style='color:{COR_BRANCOS}; font-size:20px;'>■</span> Brancos ({opcao[:2]}%+)<br>
            <span style='color:{COR_NEGROS}; font-size:20px;'>■</span> Negras ({opcao[:2]}%+)
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("👋 Verifique se o arquivo 'Banco de Dados.parquet' está na mesma pasta do script.")