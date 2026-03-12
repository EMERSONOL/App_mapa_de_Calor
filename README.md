# 📊 Analise Racial Pro - Negram

**Analytics Racial Pro** é um ecossistema de inteligência geográfica desenvolvido em Python para mapear e analisar a distribuição demográfica em comunidades e bairros. Utilizando tecnologias de ponta como **Streamlit**, **Folium** e **Geopandas**, o painel transforma dados complexos em mapas interativos e métricas acionáveis.

---

## 🌟 Funcionalidades Principais

* **Processamento Geospacial Híbrido**: Suporte para carregamento dinâmico de arquivos `.geojson` ou `.json`, `.parquet` e leitura otimizada de bases locais.
* **Visualização Temática Avançada**:
    * **Modo Classes**: Divisão da população (Branca ou Negram) em 5 faixas de densidade (0-100%).
    * **Modo Concentração Crítica**: Filtros rápidos para identificar áreas com predominância de 50%, 60% ou 75% de um grupo específico.
* **Cartografia Multiprovedor**: Escolha entre estilos de mapa Claro, Escuro, Satélite Híbrido (Google) e Relevo Topográfico (OpenTopoMap).
* **Inteligência de Dados**:
    * Cálculo automático de médias demográficas por município.
    * Ranking interativo das 5 maiores concentrações com barras de progresso.
* **Legenda Adaptativa**: Interface que se reconstrói automaticamente conforme o tipo de filtro racial selecionado.

---

## 🛠️ Tecnologias Utilizadas

* **Streamlit**: Interface web e reatividade.
* **Folium & Streamlit-Folium**: Renderização de mapas interativos.
* **Geopandas**: Manipulação de dados geográficos e polígonos.
* **Branca**: Gerenciamento de colormaps e legendas.

---

## 🚀 Como Executar

1.  **Instalação das dependências**:
    ```bash
    pip install streamlit folium streamlit-folium geopandas branca pandas
    ```

2.  **Preparação dos dados**:
    O sistema busca automaticamente o arquivo local `50% ou mais.geojson` ou permite o upload manual pela barra lateral. O arquivo deve conter as colunas:
    * `NM_MUNICIP`: Nome do Município.
    * `NM_BAIRRO`: Nome do Bairro/Comunidade.
    * `BRANCOS%`: Percentual de população branca.
    * `NEGROS%`: Percentual de população Negram.

3.  **Iniciando o Painel**:
    ```bash
    streamlit run "App Mapa de Calor.py"
    ```

---

## 📂 Estrutura do Projeto

* `App Mapa de Calor.py`: Código-fonte principal da aplicação.
* `Banco de Dados.parquet`: Base de dados padrão.
* `README.md`: Documentação do sistema.

---

## 🎨 Estilos de Visualização

O painel oferece contextos visuais específicos para diferentes tipos de análise:
* **Satélite Híbrido**: Ideal para identificar a densidade habitacional real em morros e comunidades.
* **Relevo (Terrain)**: Essencial para compreender a topografia das áreas mapeadas no Rio de Janeiro.
* **Mapa Escuro**: Destaca os pontos de calor demográfico em apresentações de alto contraste.
