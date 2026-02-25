import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import branca.colormap as cm  # Biblioteca para criar as legendas personalizadas

# Configuração da página
st.set_page_config(page_title="Mapa Racial Faixas", layout="wide")
st.title("🗺️ Mapa de Distribuição Racial por Faixas")

# --- 1. UPLOAD DE ARQUIVO ---
st.sidebar.header("Dados")
arquivo_upload = st.sidebar.file_uploader("Carregue o GeoJSON", type=["geojson", "json"])

@st.cache_data
def carregar_geojson(arquivo):
    if arquivo is not None:
        gdf = gpd.read_file(arquivo)
        if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        return gdf
    return None

gdf = carregar_geojson(arquivo_upload)

if gdf is None:
    st.info("👆 Por favor, faça o upload do arquivo GeoJSON.")
    st.stop()
# --- CORREÇÃO DO ERRO ---
# Preenche qualquer valor vazio (NaN/None) com 0 para não quebrar o mapa
gdf = gdf.fillna(0)
# ------------------------
# --- 2. CONFIGURAÇÃO DAS REGRAS DE CORES ---

# Definição das faixas (bins)
faixas = [0, 20, 40, 60, 80, 100]

# Cores para Pessoas Negras

cores_negras = ['#ffffc1', '#fee08f', '#fda15f', '#f3624d', '#ca3351']

# Cores para Pessoas Brancas
cores_brancas = ['#ffffd6', '#d2edc3', '#67c5d0', '#5699c6', '#515da9']

# --- 3. INTERFACE DE SELEÇÃO ---
grupo = st.sidebar.radio("Visualizar distribuição de:", ("Pessoas Negras", "Pessoas Brancas"))

if grupo == "Pessoas Negras":
    coluna_alvo = "NEGRAS%"
    lista_cores = cores_negras
    titulo_legenda = "Pessoas Negras (%)"
else:
    coluna_alvo = "BRANCAS%"
    lista_cores = cores_brancas
    titulo_legenda = "Pessoas Brancas (%)"

# Cria a Colormap (Mapa de Cores) Linear com degraus (Step)
colormap = cm.StepColormap(
    colors=lista_cores,
    index=faixas,
    vmin=0,
    vmax=100,
    caption=titulo_legenda
)

# --- 4. CONSTRUÇÃO DO MAPA ---
# Centro do mapa
centro_lat = gdf.geometry.centroid.y.mean()
centro_lon = gdf.geometry.centroid.x.mean()

m = folium.Map(
    location=[centro_lat, centro_lon],
    zoom_start=12,
    tiles="CartoDB positron" # Fundo claro para não brigar com as cores
)

# Função de estilo que aplica a cor baseada no valor da coluna e na nossa colormap
def style_function(feature):
    # Tenta pegar o valor. Se a chave não existir, retorna None
    valor = feature['properties'].get(coluna_alvo)
    
    # SEGURO DE VIDA: Se o valor for None (vazio), definimos como 0
    if valor is None:
        valor = 0
        
    return {
        'fillColor': colormap(valor), 
        'color': 'black',             
        'weight': 0.5,                
        'fillOpacity': 0.8
    }

# Adiciona o GeoJSON ao mapa
folium.GeoJson(
    gdf,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=['NM_BAIRRO', coluna_alvo],
        aliases=['Bairro:', 'Porcentagem:'],
        localize=True
    )
).add_to(m)

# Adiciona a legenda ao mapa
colormap.add_to(m)

# Renderiza no Streamlit
st_folium(m, width="100%", height=700)

# --- 5. TABELA DE REFERÊNCIA (Opcional, para ajudar a visualizar) ---
st.markdown("### 📋 Legenda de Referência")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Faixas e Cores Atuais:**")
    for i in range(len(lista_cores)):
        inicio = faixas[i]
        fim = faixas[i+1]
        cor = lista_cores[i]
        # Cria um pequeno quadrado colorido com HTML para mostrar na tela
        st.markdown(
            f'<div style="display: flex; align-items: center; margin-bottom: 5px;">'
            f'<div style="width: 20px; height: 20px; background-color: {cor}; margin-right: 10px; border: 1px solid #ccc;"></div>'
            f'<span>{inicio}% a {fim}% ({cor})</span>'
            f'</div>', 
            unsafe_allow_html=True
        )
