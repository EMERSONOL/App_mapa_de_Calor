import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import branca.colormap as cm
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analise Racial Pro", layout="wide")

# Estilização para tornar os menus e botões mais modernos
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

# --- 3. CARREGAMENTO DOS DADOS (CORRIGIDO) ---
@st.cache_data
def carregar_dados(arquivo):
    try:
        gdf = gpd.read_file(arquivo)
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        return gdf.fillna(0)
    except Exception as e:
        st.error(f"Erro ao ler o ficheiro: {e}")
        return None

# BARRA LATERAL - ÁREA DE UPLOAD
st.sidebar.title("📁 Gestão de Dados")
arquivo_selecionado = st.sidebar.file_uploader("Selecione o ficheiro parquet", type=["parquet", "parquet"])

# Tenta carregar o ficheiro do upload, se não houver, tenta o local
gdf = None
if arquivo_selecionado is not None:
    gdf = carregar_dados(arquivo_selecionado)
elif os.path.exists("Banco de Dados.parquet"):
    gdf = carregar_dados("Banco de Dados.parquet")

if gdf is not None:
    # --- 4. CONFIGURAÇÕES DOS FILTROS ---
    st.sidebar.markdown("---")
    st.sidebar.title("⚙️ Filtros do Mapa")
    
    with st.sidebar.expander("🌍 Estilo Visual", expanded=True):
        estilos = {
            "Mapa Claro": "cartodbpositron",
            "Mapa Escuro": "cartodbdark_matter",
            "Satélite": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
        }
        fundo = st.selectbox("Escolha o fundo", list(estilos.keys()))

    with st.sidebar.expander("📍 Localização", expanded=True):
        municipios = sorted(gdf['NM_MUNICIP'].unique())
        mun_sel = st.selectbox("Município", ["Todos"] + municipios)
    
    with st.sidebar.expander("📊 Camada Racial", expanded=True):
        opcao = st.selectbox(
            "Visualização",
            ["Pessoas brancas em 5 classes", "Pessoas negras em 5 classes", 
             "50% negros e brancos", "60% negros e brancos", "75% negros e brancos"]
        )

    # --- 5. LÓGICA DE FILTRAGEM ---
    gdf_m = gdf.copy() if mun_sel == "Todos" else gdf[gdf['NM_MUNICIP'] == mun_sel].copy()
    
    colormap = None
    if "classes" in opcao:
        is_br = "brancas" in opcao
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
    
    # Cards de Resumo
    c1, c2 = st.columns(2)
    c1.metric("Média Brancos", f"{gdf_m['BRANCOS%'].mean():.1f}%")
    c2.metric("Média Negros", f"{gdf_m['NEGROS%'].mean():.1f}%")

    # Mapa e Ranking
    col_mapa, col_rank = st.columns([3, 1])

    with col_mapa:
        m = folium.Map(tiles=estilos[fundo], attr="Google" if "Satélite" in fundo else "CartoDB")
        if not gdf_final.empty:
            b = gdf_final.total_bounds
            m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])
            folium.GeoJson(gdf_final, style_function=style_fn,
                           tooltip=folium.GeoJsonTooltip(fields=['NM_BAIRRO', 'BRANCOS%', 'NEGROS%'],
                                                       aliases=['Bairro:', 'Brancos:', 'Negros:'])).add_to(m)
            if colormap: colormap.add_to(m)
            st_folium(m, width="100%", height=550, key=f"{mun_sel}_{opcao}_{fundo}")
        else:
            st.warning("Nenhum bairro encontrado para este nível de concentração.")

    with col_rank:
        st.subheader("🏆 Maiores Concentrações")
        rank_col = "BRANCOS%" if "brancas" in opcao or "negros e brancos" in opcao else "NEGROS%"
        top_5 = gdf_m.nlargest(5, rank_col)[['NM_BAIRRO', rank_col]]
        for _, row in top_5.iterrows():
            st.write(f"**{row['NM_BAIRRO']}**")
            st.progress(row[rank_col]/100)
            st.caption(f"{row[rank_col]}%")

    # Legenda para os modos de comparação
    if "classes" not in opcao:
        st.sidebar.markdown(f"""
        <div style="padding:10px; border-radius:5px; border:1px solid #eee;">
            <strong>Legenda de Cores:</strong><br>
            <span style='color:{COR_BRANCOS}'>■</span> Brancos ({opcao[:2]}%+)<br>
            <span style='color:{COR_NEGROS}'>■</span> Negros ({opcao[:2]}%+)
        </div>
        """, unsafe_allow_html=True)

else:
    # Ecrã inicial caso não haja ficheiro
    st.info("👋 Bem-vindo! Por favor, utilize o botão na barra lateral à esquerda para carregar o seu ficheiro GeoJSON e começar a análise.")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:

        st.image("https://img.icons8.com/clouds/200/map-marker.png", width=200)

