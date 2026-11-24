## Pérdida de cobertura arbórea en la Zona de los Santos

Autor: Kevin Andrés Torres Torres
Curso: GF-0657 Programación en SIG, 2026-II, Universidad de Costa Rica
Aplicación publicada: [https://proyectofinal-lulc.streamlit.app/]

**Descripción**

Aplicación web interactiva, desarrollada con streamlit, que muestra la pérdida de cobertura arbórea entre 2001 y 2025 en los cantones de Dota, León Cortés Castro y Tarrazú (Zona de los Santos, provincia de San José, Costa Rica). La pérdida de cobertura arbórea es un indicador indirecto de la fragmentación de los paisajes cafetaleros. La aplicación la relaciona, de forma descriptiva, con la proporción de cada cantón que se encuentra dentro de áreas silvestres protegidas.

Reúne el análisis de las tareas 2 y 3 del curso. Con los filtros de la barra lateral (cantones y rango de años), los indicadores, el mapa, los gráficos y la tabla muestran siempre la misma selección:

Indicadores: pérdida acumulada, porcentaje de la cobertura de 2000 perdido, pérdida media anual, año de mayor pérdida y porcentaje de área protegida.
Mapa interactivo (folium): cantones coloreados por el porcentaje de cobertura perdida, áreas silvestres protegidas y ríos, con control de capas, etiquetas emergentes y leyenda.
Gráficos (plotly): pérdida anual por cantón y cobertura perdida por cantón.
Tabla: resumen por cantón, con descarga en CSV.

La pérdida es bruta: no descuenta la cobertura que pudo recuperarse en el mismo periodo, y los porcentajes parten de la cobertura arbórea del año 2000.

**Fuentes de los datos**

Los datos se cargan desde URL del repositorio Gittorres2000/Fragmentaci-n-y-Conectividad_3, por lo que este repositorio no incluye una carpeta datos/.

Global Forest Watch. (2026). Tree cover loss y Tree cover extension en Dota, León Cortés Castro y Tarrazú, San José, Costa Rica[Conjunto de datos]. World Resources Institute. https://www.globalforestwatch.org

Global Administrative Areas. (2018). GADM database of Global Administrative Areas (Versión 3.6) [Conjunto de datos]. https://gadm.org

Límite cantonal, Áreas silvestres protegidas y Ríos: Extraido del Sistema Nacional de Información Territorial (SNIT). Capas en CRTM05 (EPSG:8908) incluida en el [repositorio de datos] (https://github.com/Gittorres2000/Fragmentaci-n-y-Conectividad_3).
