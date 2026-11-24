# Aplicación web: pérdida de cobertura arbórea y áreas protegidas en la Zona de los Santos 
# (Dota, León Cortés Castro y Tarrazú, Costa Rica).
# Proyecto final de GF-0657 Programación en SIG.

### Cargar las librerías con las que se trabajará en la aplicación web

import copy                          # para hacer una copia del mapa (se explica más abajo)
import branca.colormap as cm         # escala de color con leyenda para el mapa
import folium                        # mapas web interactivos
import geopandas as gpd              # datos vectoriales (cantones, áreas protegidas, ríos)
import pandas as pd                  # tablas
import plotly.express as px          # gráficos interactivos
import streamlit as st               # la aplicación web
from streamlit_folium import st_folium  # dibuja un mapa de folium dentro de streamlit

### st.set_page_config() Primera llamada a streamlit del archivo.
### Define el título de la pestaña del navegador y que la página use todo el ancho.
st.set_page_config(
    page_title="Cobertura arbórea en la Zona de los Santos",
    page_icon="🌳",
    layout="wide",
)

### Dirección del repositorio de GitHub donde están los datos de la tarea 3.
### No lleva "/" al final porque se agrega después, al armar cada dirección.
BASE_URL = "https://raw.githubusercontent.com/Gittorres2000/Fragmentaci-n-y-Conectividad_3/main"

### Archivos CSV de Global Forest Watch de cada cantón: (pérdida, extensión).
### Se guardan en un diccionario para recorrerlos con un ciclo for.
ARCHIVOS_CSV = {
    "Dota": ("treecover_loss_dota__ha.csv", "treecover_extent_dota_ha.csv"),
    "León Cortés": ("treecover_loss_leon_cortez_ha.csv", "treecover_extent_leon_cortez_ha.csv"),
    "Tarrazú": ("treecover_loss_tarrazu_ha.csv", "treecover_extent_tarrazu_ha.csv"),
}

### Sistemas de referencia de coordenadas (SRC):
### - CRTM05 (EPSG:8908) está en metros: sirve para calcular áreas.
### - WGS84 (EPSG:4326) está en grados: es el que necesitan los mapas web.
CRS_METROS = "EPSG:8908"
CRS_WEB = "EPSG:4326"

### Un color fijo por cantón, para que se vea igual en todos los gráficos.
COLORES = {"Dota": "#1b9e77", "León Cortés": "#d95f02", "Tarrazú": "#7570b3"}

### Nombres que se muestran en la tabla (incluyen las unidades).
ETIQUETAS = {
    "canton": "Cantón",
    "area_ha": "Área (ha)",
    "cobertura_2000_ha": "Cobertura 2000 (ha)",
    "perdida_ha": "Pérdida en el periodo (ha)",
    "porcentaje_perdido": "Pérdida (% de la cobertura 2000)",
    "area_protegida_ha": "Área protegida (ha)",
    "porcentaje_protegido": "Protegido (% del área)",
}


### ---------------------------------------------------------------------------
### 3. FUNCIONES AUXILIARES
### ---------------------------------------------------------------------------

def fmt(valor, decimales=0):
    """Da formato a un número: miles separados por espacio y coma decimal (ej. 3 172 y 7,0)."""
    texto = f"{valor:,.{decimales}f}"          # Python usa "," para miles y "." para decimales
    return texto.replace(",", "\u00a0").replace(".", ",")   # se cambian por espacio y coma


def resumir(loss, extent, base, cantones_sel, anio_ini, anio_fin):
    """Calcula el resumen de cada cantón según los filtros elegidos.

    Recibe:
        loss          tabla de pérdida anual (cantón, año, hectáreas)
        extent        tabla de cobertura arbórea del año 2000 por cantón
        base          tabla con el área y el área protegida de cada cantón
        cantones_sel  lista de cantones elegidos en la barra lateral
        anio_ini, anio_fin  rango de años elegido

    Devuelve:
        loss_filter   pérdida filtrada (una fila por cantón y año)
        resumen  una fila por cantón con pérdida del periodo y % perdido
    """
    ### Paso 1: Se realiza un FILTRO para quedarse solo con los cantones y los años elegidos (cantones_sel, anio_ini, anio_fin)
    loss_filter = loss[
        loss["canton"].isin(cantones_sel) & loss["anio"].between(anio_ini, anio_fin)
    ]

    ### Paso 2: sumar la pérdida de cada cantón en ese rango de años (Separa la tabla por cantón y suma la columna "perdida_ha")
    perdida = loss_filter.groupby("canton", as_index=False)["perdida_ha"].sum()

    ### Paso 3: unir en una sola tabla el área, la cobertura del 2000 y la pérdida
    resumen = (
        base[base["canton"].isin(cantones_sel)]
        .merge(extent, on="canton")
        .merge(perdida, on="canton", how="left")
    )
    resumen["perdida_ha"] = resumen["perdida_ha"].fillna(0)   # sin datos = 0 ha

    ### Paso 4: porcentaje de la cobertura del año 2000 que se perdió
    resumen["porcentaje_perdido"] = (
        resumen["perdida_ha"] / resumen["cobertura_2000_ha"] * 100
    )
    return loss_filter, resumen ### Retorna la perdida para los cantones seleccionados y el porcentaje de la cobertura del año 2000 que se perdió

### 4. CARGA DE LOS DATOS (CON CACHÉ)



# guarda el resultado de la función. Así, los datos se descargan una sola vez
# "show_spinner" es el mensaje que aparece solo la primera vez que carga.
@st.cache_data(show_spinner="Cargando las tablas de cobertura arbórea...")
def cargar_tablas():
    """Carga los CSV de pérdida y de extensión de cobertura arbórea de los tres cantones."""
    perdidas, extensiones = [], []     # Listas vacías donde se irá guardando un DataFrame por cantón. (Tabla_loss y Tabla_extent)


    for canton, (archivo_loss, archivo_ext) in ARCHIVOS_CSV.items(): # clave es el nombre del cantón y el valor es una tupla con (archivo de pérdida, archivo de extensión)
## .items() entrega cada par y el for lo desempaqueta en tres variables.

#Se le pega el nombre del
# archivo con un f-string y pd.read_csv lee ese CSV y lo convierte
# en un DataFrame.
        tabla_loss = pd.read_csv(f"{BASE_URL}/{archivo_loss}")
        tabla_loss["canton"] = canton # Se crea una columna "canton" con el mismo valor en todas las filas,
        perdidas.append(tabla_loss) # Se guarda el DataFrame en la lista de pérdidas.

        # Mismo proceso: leer el CSV, etiquetarlo con el cantón y guardarlo.
        tabla_ext = pd.read_csv(f"{BASE_URL}/{archivo_ext}")
        tabla_ext["canton"] = canton
        extensiones.append(tabla_ext) # Se guarda el DataFrame en la lista de extensiones.

    # PARTE 2: unir las tablas de los tres cantones
    loss = pd.concat(perdidas, ignore_index=True)
    extent = pd.concat(extensiones, ignore_index=True)

    col_ext = [c for c in extent.columns if "extent" in c][0] #encontrar la columna de extensión, contienen la palabra "extent" y se toma la primera con [0].

    loss = loss.rename(
        columns={
            "umd_tree_cover_loss__year": "anio",        # año de la pérdida
            "umd_tree_cover_loss__ha": "perdida_ha",    # hectáreas perdidas
        }
    )[["canton", "anio", "perdida_ha"]]  ## RENOMBRAR COLUMNAS

    extent = extent.rename(columns={col_ext: "cobertura_2000_ha"})[
        ["canton", "cobertura_2000_ha"]
    ] ## RENOMBRAR COLUMNAS 

    # Se devuelven dos DataFrames limpios:
    # - loss: una fila por cantón y año, con las hectáreas perdidas.
    # - extent: una fila por cantón, con las hectáreas de cobertura en 2000.
    return loss, extent

### CORRECCIÓN DE LAS CAPAS (NOMBRES, GEOMETRÍAS, ÁREAS, PROYECCIÓN)

@st.cache_data(show_spinner="Cargando las capas geoespaciales...")
def cargar_capas():
    """Carga los cantones, las áreas protegidas y los ríos, y los deja listos para el mapa.

    Primero se calculan las áreas en metros (CRTM05) y al final todo se
    reproyecta a WGS84, que es el sistema que usan los mapas web.

    Devuelve: (cantones, áreas protegidas, ríos), los tres en WGS84.
    """
    ### Lectura de las tres capas desde GitHub
    cantones = gpd.read_file(f"{BASE_URL}/limite_cantonal.gpkg")
    asp = gpd.read_file(f"{BASE_URL}/areas_protegidas.gpkg")
    rios = gpd.read_file(f"{BASE_URL}/rios.gpkg")

    ### La capa dice "León Cortés Castro" pero las tablas dicen "León Cortés".
    ### Se unifica el nombre para poder unir las tablas con la capa.
    cantones["canton"] = cantones["CANTÓN"].replace({"León Cortés Castro": "León Cortés"})

    ### Se dejan solo el nombre y la geometría, y se asegura que todo esté en metros
    cantones = cantones[["canton", "geometry"]].to_crs(CRS_METROS)
    asp = asp.to_crs(CRS_METROS)
    rios = rios.to_crs(CRS_METROS)

    cantones["area_ha"] = cantones.geometry.area / 10_000 # Conversion de metros cuadrados a hectáreas

    ### DISSOLVE: une los tres cantones en una sola geometría (la Zona de los Santos)
    zona = cantones[["geometry"]].dissolve()

# CORRECCION DE GEOMETRÍAS: (self-intersection, OVERLAY, CLIP)
    asp["geometry"] = asp.make_valid() 
    asp_zona = gpd.clip(asp, zona)
    asp_zona = asp_zona[asp_zona.geom_type.isin(["Polygon", "MultiPolygon"])]
    asp_total = asp_zona[["geometry"]].dissolve()

    ### OVERLAY (intersección): la parte de cada cantón que está dentro de un área protegida
    asp_en_cantones = gpd.overlay(
        cantones[["canton", "geometry"]], asp_total, how="intersection"
    )
    asp_en_cantones["area_protegida_ha"] = asp_en_cantones.geometry.area / 10_000
    protegida = asp_en_cantones.groupby("canton", as_index=False)["area_protegida_ha"].sum()

    ### Se agrega el área protegida a la capa de cantones.
    ### Un cantón sin área protegida quedaría vacío (NaN), por eso se rellena con 0.
    cantones = cantones.merge(protegida, on="canton", how="left")
    cantones["area_protegida_ha"] = cantones["area_protegida_ha"].fillna(0)
    cantones["porcentaje_protegido"] = (
        cantones["area_protegida_ha"] / cantones["area_ha"] * 100
    )

    ### Ríos: se recortan a la zona y se dejan solo las líneas
    rios_zona = gpd.clip(rios, zona)
    rios_zona = rios_zona[rios_zona.geom_type.isin(["LineString", "MultiLineString"])]

    ### CORRECCIÓN: en la capa de ríos la columna con el nombre se llama "nomb_río".
    ### Se renombra a "nombre_rio" (más fácil de usar) y los ríos sin nombre
    ### se rellenan con "Sin nombre", para que el mensaje emergente del mapa no muestre "None".
    rios_zona = rios_zona[["nomb_río", "geometry"]].rename(columns={"nomb_río": "nombre_rio"})
    rios_zona["nombre_rio"] = rios_zona["nombre_rio"].fillna("Sin nombre")

    ### Reproyección final de todas las capas a WGS84 (para folium)
    cantones_web = cantones.to_crs(CRS_WEB)
    asp_web = asp_zona[["nombre_asp", "cat_manejo", "geometry"]].to_crs(CRS_WEB)
    rios_web = rios_zona.to_crs(CRS_WEB)

    return cantones_web, asp_web, rios_web


### 5. CONSTRUCCIÓN DEL MAPA (CON CACHÉ)

### Se usa @st.cache_resource (y no cache_data) porque un mapa de folium no se
### puede "serializar". El mapa solo se vuelve a construir cuando cambian los
### valores de los argumentos: cantones elegidos y rango de años.

@st.cache_resource(show_spinner="Construyendo el mapa...")
def construir_mapa(cantones_sel, anio_ini, anio_fin):
    """Construye el mapa de folium para los cantones y el rango de años elegidos."""

    ### Se obtienen los datos ya guardados en caché (no se vuelven a descargar)
    loss, extent = cargar_tablas()
    cantones_web, asp_web, rios_web = cargar_capas()

    ### Se calcula el resumen de pérdida con los mismos filtros que usa el resto de la página
    base = pd.DataFrame(cantones_web.drop(columns="geometry"))
    _, resumen = resumir(loss, extent, base, cantones_sel, anio_ini, anio_fin)

    ### Capa de cantones elegidos, con los datos de pérdida y protección en sus atributos
    capa = cantones_web[["canton", "geometry"]].merge(resumen, on="canton").round(1)

    ### Las áreas protegidas y los ríos se recortan a los cantones elegidos,
    ### para que el mapa muestre la misma selección que la tabla y los gráficos
    asp_sel = gpd.clip(asp_web, capa[["geometry"]])
    asp_sel = asp_sel[asp_sel.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    if not asp_sel.empty:
        ### Área de cada pedazo de área protegida (se mide en metros y se pasa a hectáreas)
        asp_sel["area_ha"] = (asp_sel.to_crs(CRS_METROS).geometry.area / 10_000).round(1)

    rios_sel = gpd.clip(rios_web, capa[["geometry"]])
    rios_sel = rios_sel[rios_sel.geom_type.isin(["LineString", "MultiLineString"])]

    ### Escala de color con leyenda: de amarillo (poca pérdida) a rojo oscuro (mucha pérdida)
    vmax = max(float(capa["porcentaje_perdido"].max()), 0.1)
    escala = cm.LinearColormap(
        ["#FFFFB2", "#FED976", "#FD8D3C", "#E31A1C", "#800026"],
        vmin=0,
        vmax=vmax,
        caption=(
            f"Cobertura arbórea perdida, {anio_ini}-{anio_fin} "
            "(% de la cobertura de 2000)"
        ),
    )

    def estilo_perdida(entidad):
        """Pinta cada cantón con el color que le corresponde a su porcentaje de pérdida."""
        valor = entidad["properties"]["porcentaje_perdido"]
        color = "#E6E6E6" if valor is None else escala(valor)   # gris si no hay dato
        return {"fillColor": color, "color": "white", "weight": 1, "fillOpacity": 0.8}

    ### Mapa base: se centra en los cantones elegidos y se agrega un segundo mapa base
    minx, miny, maxx, maxy = capa.total_bounds
    mapa = folium.Map(
        location=[(miny + maxy) / 2, (minx + maxx) / 2],
        zoom_start=10,
        tiles="Esri.WorldGrayCanvas",
        control_scale=True,
    )
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(mapa)

    ### CAPA 1 (la del tema): cantones coloreados por el porcentaje de pérdida.
    ### El tooltip es el mensaje que aparece al pasar el cursor.
    folium.GeoJson(
        capa,
        name="Pérdida de cobertura arbórea por cantón",
        style_function=estilo_perdida,
        highlight_function=lambda entidad: {"weight": 3, "color": "black", "fillOpacity": 0.95},
        tooltip=folium.GeoJsonTooltip(
            fields=["canton", "porcentaje_perdido", "perdida_ha",
                    "cobertura_2000_ha", "porcentaje_protegido"],
            aliases=["Cantón",
                     "Pérdida (% de la cobertura 2000)",
                     f"Pérdida {anio_ini}-{anio_fin} (ha)",
                     "Cobertura 2000 (ha)",
                     "Área protegida (% del cantón)"],
            localize=True,
        ),
    ).add_to(mapa)

    ### CAPA 2 (de referencia): áreas silvestres protegidas (si hay en la selección)
    if not asp_sel.empty:
        folium.GeoJson(
            asp_sel,
            name="Áreas silvestres protegidas",
            style_function=lambda entidad: {
                "color": "darkgreen", "weight": 2,
                "fillColor": "darkgreen", "fillOpacity": 0.25,
            },
            highlight_function=lambda entidad: {"weight": 4, "fillOpacity": 0.5},
            tooltip=folium.GeoJsonTooltip(
                fields=["nombre_asp", "cat_manejo", "area_ha"],
                aliases=["Área protegida", "Categoría de manejo",
                         "Área dentro de la selección (ha)"],
                localize=True,
            ),
        ).add_to(mapa)

    ### CAPA 3 (de referencia): ríos. CORRECCIÓN: ahora siempre tienen tooltip con el nombre
    if not rios_sel.empty:
        folium.GeoJson(
            rios_sel,
            name="Ríos principales",
            style_function=lambda entidad: {"color": "steelblue", "weight": 1.5},
            highlight_function=lambda entidad: {"weight": 4},
            tooltip=folium.GeoJsonTooltip(fields=["nombre_rio"], aliases=["Río"]),
        ).add_to(mapa)

    ### Leyenda de colores y control para mostrar u ocultar capas
    escala.add_to(mapa)
    folium.LayerControl(collapsed=False).add_to(mapa)

    ### El mapa se acerca para que se vean justo los cantones elegidos
    mapa.fit_bounds([[miny, minx], [maxy, maxx]])
    return mapa

### 6. ENCABEZADO DE LA PÁGINA Y FUENTES

def mostrar_fuentes():
    """Muestra las fuentes de los datos al pie de la página."""
    st.divider()
    st.markdown("**Fuentes de los datos**")
    st.caption(
        "Pérdida y extensión de la cobertura arbórea: Global Forest Watch. (2026).\n\n"
        "*Tree cover loss y Tree cover extension en Dota, León Cortés Castro y Tarrazú, San José, Costa Rica*"
        "[Conjunto de datos]. World Resources Institute. "
        "[globalforestwatch.org](https://www.globalforestwatch.org). "
    )

    st.caption(
        "Límite cantonal, Áreas silvestres protegidas y Ríos: Extraido del Sistema Nacional de Información Territorial (SNIT). "
        "Capas en CRTM05 (EPSG:8908) "
        "incluida en el [repositorio de datos]"
        "(https://github.com/Gittorres2000/Fragmentaci-n-y-Conectividad_3)."
    )


### Título y párrafo introductorio: de qué trata la app, qué datos usa y cómo se usa
st.title("Pérdida de cobertura arbórea en la Zona de los Santos")
st.markdown(
    "Esta aplicación muestra la **pérdida de cobertura arbórea entre 2001 y 2025** en la Zona de los Santos, que comprende los "
    "cantones de Dota, León Cortés Castro y Tarrazú (provincia de San José, Costa Rica), "
    "un indicador indirecto de la fragmentación de los paisajes cafetaleros, y la compara "
    "de forma descriptiva con la proporción de cada cantón que está dentro de áreas "
    "silvestres protegidas."
)

st.markdown(
    "**Preguntas de investigación**\n\n"
    "1. ¿Qué cantón perdió más superficie de cobertura arbórea entre 2001 y 2025, "
    "y cuál perdió la mayor proporción de la que tenía en el año 2000?\n\n"
    "2. ¿Cómo evolucionó la pérdida anual de cobertura arbórea en cada cantón "
    "durante el periodo?\n\n"
    "3. ¿Cómo se distribuye la pérdida anual y existen años con pérdidas "
    "excepcionalmente altas?"
)

st.markdown(
    "**Cómo usarla:** elija los cantones y el rango de años en la barra lateral. Los "
    "indicadores, el mapa, los gráficos y la tabla se actualizan con la misma selección. "
    "La pérdida es bruta: no descuenta la cobertura que pudo recuperarse, y el porcentaje "
    "se calcula respecto a la cobertura arbórea del año 2000."
)

### Se cargan los datos (la primera vez se descargan; después salen del caché)
loss, extent = cargar_tablas()
cantones_web, asp_web, rios_web = cargar_capas()
base = pd.DataFrame(cantones_web.drop(columns="geometry"))   # tabla sin geometría

### 7. CONTROLES DE LA BARRA LATERAL (FILTROS)

st.sidebar.header("Filtros")

### Control 1: lista de selección múltiple de cantones (por defecto, los tres)
todos_los_cantones = sorted(loss["canton"].unique())
cantones_sel = st.sidebar.multiselect(
    "Cantones",
    options=todos_los_cantones,
    default=todos_los_cantones,
    help="Cantones que se incluyen en los indicadores, el mapa, los gráficos y la tabla.",
)

### Control 2: deslizador con rango de años (de 2001 a 2025)
anio_min, anio_max = int(loss["anio"].min()), int(loss["anio"].max())
anio_ini, anio_fin = st.sidebar.slider(
    "Rango de años",
    min_value=anio_min,
    max_value=anio_max,
    value=(anio_min, anio_max),
    help="Años en que se suma la pérdida de cobertura arbórea.",
)

### Si no se eligió ningún cantón, se avisa con un mensaje en lugar de dar error.
### st.stop() detiene la ejecución: no se dibuja nada más debajo.
if not cantones_sel:
    st.warning("Seleccione al menos un cantón en la barra lateral para ver los resultados.")
    mostrar_fuentes()
    st.stop()

### Se calcula el resumen con los filtros. Todo lo que sigue usa estos mismos datos filtrados,
### por eso indicadores, mapa, gráficos y tabla siempre muestran la misma selección.
loss_f, resumen = resumir(loss, extent, base, cantones_sel, anio_ini, anio_fin)

### Segundo aviso: por si la combinación de filtros no tiene ninguna fila
if loss_f.empty or resumen.empty:
    st.warning(
        "No hay datos para la combinación de cantones y años elegida. "
        "Cambie los filtros de la barra lateral."
    )
    mostrar_fuentes()
    st.stop()

### ---------------------------------------------------------------------------
### 8. INDICADORES
### ---------------------------------------------------------------------------

### Cifras de resumen de la selección actual
n_anios = anio_fin - anio_ini + 1
perdida_total = resumen["perdida_ha"].sum()
cobertura_total = resumen["cobertura_2000_ha"].sum()
porcentaje_total = perdida_total / cobertura_total * 100
perdida_media = perdida_total / n_anios

### Año con más pérdida: se suma la pérdida de todos los cantones por año y se busca el máximo
por_anio = loss_f.groupby("anio")["perdida_ha"].sum()
anio_pico = int(por_anio.idxmax())
perdida_pico = por_anio.max()

porcentaje_protegido_total = (
    resumen["area_protegida_ha"].sum() / resumen["area_ha"].sum() * 100
)

st.subheader(f"Resumen de la selección, {anio_ini}-{anio_fin}")
col1, col2, col3, col4, col5 = st.columns(5)   # cinco columnas, un indicador en cada una
col1.metric(
    "Pérdida acumulada",
    f"{fmt(perdida_total)} ha",
    help="Suma de la pérdida de cobertura arbórea de los cantones y años elegidos.",
)
col2.metric(
    "Cobertura perdida",
    f"{fmt(porcentaje_total, 1)} %",
    help="Pérdida acumulada como porcentaje de la cobertura arbórea del año 2000.",
)
col3.metric(
    "Pérdida media anual",
    f"{fmt(perdida_media, 1)} ha/año",
    help="Pérdida acumulada dividida entre el número de años del rango.",
)
col4.metric(
    "Año de mayor pérdida",
    f"{anio_pico}",
    delta=f"{fmt(perdida_pico)} ha perdidas",
    delta_color="off",      # sin color rojo/verde: no es "bueno" ni "malo", solo informa
    delta_arrow="off",
)
col5.metric(
    "Área protegida",
    f"{fmt(porcentaje_protegido_total, 1)} %",
    help="Porcentaje del área de los cantones elegidos que está dentro de áreas silvestres protegidas.",
)

### ---------------------------------------------------------------------------
### 9. PESTAÑAS: MAPA, GRÁFICOS Y TABLA
### ---------------------------------------------------------------------------

tab_mapa, tab_graficos, tab_tabla = st.tabs(["Mapa", "Gráficos", "Tabla"])

### ----- Pestaña del mapa -----
with tab_mapa:
    st.subheader("Mapa de la pérdida de cobertura arbórea por cantón")
    st.caption(
        "Cada cantón se colorea según el porcentaje de su cobertura arbórea del año 2000 "
        "que se perdió en el periodo elegido. Pase el cursor sobre un elemento para ver "
        "sus datos y use el control de capas para mostrar u ocultar capas."
    )
    ### Se pide el mapa al caché. Los cantones se pasan como tupla ordenada porque
    ### el caché necesita argumentos que no cambien de forma (las listas no sirven).
    mapa = construir_mapa(tuple(sorted(cantones_sel)), anio_ini, anio_fin)

    ### Se dibuja una COPIA del mapa (copy.deepcopy). Así streamlit-folium reconoce
    ### el mismo mapa en cada ejecución y conserva el centro y el acercamiento
    ### cuando la persona hace clic, en lugar de redibujarlo desde cero.
    st_folium(
        copy.deepcopy(mapa),
        height=600,
        use_container_width=True,
        returned_objects=[],     # no se devuelve nada del mapa: esta app no responde a clics
        key="mapa_zona_de_los_santos",
    )

### ----- Pestaña de los gráficos -----
with tab_graficos:
    st.subheader("Evolución y comparación de la pérdida")
    col_linea, col_barras = st.columns([3, 2])   # la columna del gráfico de líneas es más ancha

    ### Gráfico 1: líneas, pérdida anual de cada cantón
    with col_linea:
        fig_linea = px.line(
            loss_f.sort_values(["canton", "anio"]),
            x="anio",
            y="perdida_ha",
            color="canton",
            markers=True,
            color_discrete_map=COLORES,
            labels={
                "anio": "Año",
                "perdida_ha": "Pérdida de cobertura arbórea (ha)",
                "canton": "Cantón",
            },
            title=f"Pérdida anual de cobertura arbórea por cantón, {anio_ini}-{anio_fin}",
        )
        ### Marca cada año si el rango es corto; si es largo, uno de cada dos
        fig_linea.update_xaxes(dtick=1 if n_anios <= 12 else 2)
        fig_linea.update_layout(hovermode="x unified", separators=",\u00a0")
        st.plotly_chart(fig_linea, width="stretch")

    ### Gráfico 2: barras, porcentaje de cobertura perdido por cantón
    with col_barras:
        datos_barras = resumen.sort_values("porcentaje_perdido", ascending=False)
        fig_barras = px.bar(
            datos_barras,
            x="canton",
            y="porcentaje_perdido",
            color="canton",
            color_discrete_map=COLORES,
            text=datos_barras["porcentaje_perdido"].map(lambda v: f"{fmt(v, 1)} %"),
            labels={
                "canton": "Cantón",
                "porcentaje_perdido": "Cobertura perdida (% de la de 2000)",
            },
            title=f"Cobertura perdida por cantón, {anio_ini}-{anio_fin}",
        )
        fig_barras.update_traces(textposition="outside")    # el valor se escribe sobre cada barra
        fig_barras.update_layout(showlegend=False, separators=",\u00a0")
        st.plotly_chart(fig_barras, width="stretch")

    ### Texto que responde a la pregunta: ¿qué tan concentrada está la pérdida en pocos años?
    n_top = min(3, len(por_anio))               # los 3 años con más pérdida (o menos, si el rango es corto)
    anios_top = por_anio.nlargest(n_top)
    if perdida_total > 0:
        lista_anios = ", ".join(str(int(a)) for a in anios_top.index)
        st.markdown(
            f"**Concentración de la pérdida:** los {n_top} años de mayor pérdida "
            f"({lista_anios}) reúnen el **{fmt(anios_top.sum() / perdida_total * 100, 1)} %** "
            f"de las {fmt(perdida_total)} ha perdidas en la selección."
        )

### ----- Pestaña de la tabla -----
with tab_tabla:
    st.subheader("Tabla de pérdida y protección por cantón")

    ### Se ordena de mayor a menor pérdida relativa (la tabla no lleva geometría)
    columnas = list(ETIQUETAS)
    tabla = resumen[columnas].sort_values("porcentaje_perdido", ascending=False)

    ### Si hay más de un cantón, se agrega una fila con los totales de la selección
    if len(tabla) > 1:
        total = pd.DataFrame([{
            "canton": "Total de la selección",
            "area_ha": tabla["area_ha"].sum(),
            "cobertura_2000_ha": tabla["cobertura_2000_ha"].sum(),
            "perdida_ha": tabla["perdida_ha"].sum(),
            "porcentaje_perdido": porcentaje_total,
            "area_protegida_ha": tabla["area_protegida_ha"].sum(),
            "porcentaje_protegido": porcentaje_protegido_total,
        }])
        tabla = pd.concat([tabla, total], ignore_index=True)

    ### column_config pone el nombre con unidades y el formato numérico de cada columna
    st.dataframe(
        tabla,
        hide_index=True,
        width="stretch",
        column_config={
            "canton": st.column_config.TextColumn(ETIQUETAS["canton"]),
            "area_ha": st.column_config.NumberColumn(ETIQUETAS["area_ha"], format="%.0f"),
            "cobertura_2000_ha": st.column_config.NumberColumn(
                ETIQUETAS["cobertura_2000_ha"], format="%.0f"
            ),
            "perdida_ha": st.column_config.NumberColumn(
                ETIQUETAS["perdida_ha"], format="%.0f"
            ),
            "porcentaje_perdido": st.column_config.NumberColumn(
                ETIQUETAS["porcentaje_perdido"], format="%.1f"
            ),
            "area_protegida_ha": st.column_config.NumberColumn(
                ETIQUETAS["area_protegida_ha"], format="%.0f"
            ),
            "porcentaje_protegido": st.column_config.NumberColumn(
                ETIQUETAS["porcentaje_protegido"], format="%.1f"
            ),
        },
    )
    st.caption(
        f"Pérdida acumulada entre {anio_ini} y {anio_fin}. La cobertura y el área "
        "protegida no dependen del rango de años."
    )

    ### Botón para descargar la tabla como CSV (con los nombres de columna con unidades)
    st.download_button(
        "Descargar la tabla (CSV)",
        data=tabla.rename(columns=ETIQUETAS).to_csv(index=False).encode("utf-8"),
        file_name="perdida_cobertura_zona_de_los_santos.csv",
        mime="text/csv",
    )

### Fuentes de los datos al pie de la página
mostrar_fuentes()
