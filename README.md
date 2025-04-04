# NBA Stats Web Scraper

Este proyecto automatiza la recolección de estadísticas de equipos de la NBA desde la web oficial [nba.com/stats](https://www.nba.com/stats), utilizando Selenium para interactuar con el sitio y BeautifulSoup para extraer los datos HTML renderizados.

El objetivo es construir un conjunto de datos con información ofensiva y defensiva agregada por posición (guard, forward, center) y temporada (desde 1996 hasta 2025), permitiendo analizar cómo ha evolucionado el estilo de juego en la liga.

## 📦 Requisitos

⚠️ Este proyecto utiliza Selenium con el navegador Chrome, por lo que es necesario tener `chromedriver` en el mismo directorio donde se ejecuta el script `.py`.

Puedes descargarlo desde: https://sites.google.com/chromium.org/driver/

Instala los paquetes necesarios con:

```bash
pip install -r requirements.txt
```

## 🚀 Uso

1. Ejecuta el script principal:

```bash
python nba_test.py.py
```

2. El script:
   - Accede a la web de estadísticas de la NBA
   - Acepta cookies y aplica filtros por temporada, conferencia y posición
   - Extrae datos de tiro y defensa por zonas y tipo de jugada
   - Verifica el acceso a las rutas mediante `robots.txt` usando `robotparser`
   - Simula un comportamiento humano con pausas aleatorias
   - Genera un archivo CSV con los datos agregados:
     📁 `dataset/nba_team_stats_dataset.csv`

## 📁 Estructura del proyecto

- `source/Scarp_NBA_Stats_Selenium_Beautifulsoup.py`: Script principal con Selenium + BeautifulSoup.
- `dataset/`: Carpeta donde se guarda el archivo CSV generado.
- `requirements.txt`: Lista de librerías necesarias (Selenium, BeautifulSoup, pandas, etc.).

## ⏱️ Tiempo de ejecución

El script imprime en consola el tiempo total que tardó en completarse el scraping.

## 📌 Origen de los datos

Los datos fueron extraídos del sitio oficial de estadísticas de la NBA:
> https://www.nba.com/stats  
Propiedad de NBA Media Ventures, LLC

Todo el contenido original sigue siendo propiedad intelectual de la NBA. El conjunto de datos generado es un trabajo derivado, construido únicamente con fines académicos y siguiendo prácticas de scraping responsables y legales.

## 📜 Licencia

Este proyecto y el dataset generado están licenciados bajo:

👉 **[CC BY-NC-SA 4.0 – Attribution-NonCommercial-ShareAlike](https://creativecommons.org/licenses/by-nc-sa/4.0/)**

Esto implica que:
- Puedes usar, compartir y adaptar el contenido para fines no comerciales
- Debes reconocer la fuente original (NBA.com) y los autores de este proyecto
- Cualquier trabajo derivado debe compartirse bajo la misma licencia
  
## 🧑‍💻 Autores

Proyecto desarrollado por :
Etel silva Garcia: esilgar@uoc.edu
José Morote: josemorote21@uoc.edu

