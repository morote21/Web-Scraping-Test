# NBA Stats Web Scraper

Este proyecto automatiza la recolección de estadísticas de jugadores de la NBA desde la web oficial [nba.com/stats]((https://www.nba.com/stats/teams/shooting)), utilizando Selenium para interactuar con el sitio y BeautifulSoup para parsear el HTML renderizado.

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
   - Accede a la web de la NBA.
   - Acepta cookies y hace clic en “See All Player Stats”.
   - Espera que se cargue la tabla con JavaScript.
   - ***MODIFICAR****
   - Extrae la tabla de estadísticas de jugadores usando BeautifulSoup.
   - Recorre todas las páginas hasta obtener todos los datos.
   - Genera un archivo CSV con los resultados:  
     📁 `Tests_NBA_Stats/dataset/nba_player_stats_beautifulsoup.csv`

## 📁 Estructura del proyecto

- `source/Scarp_NBA_Stats_Selenium_Beautifulsoup.py`: Script principal con Selenium + BeautifulSoup.
- `dataset/`: Carpeta donde se guarda el archivo CSV generado.
- `requirements.txt`: Lista de librerías necesarias (Selenium, BeautifulSoup, pandas, etc.).

## ⏱️ Tiempo de ejecución

El script imprime en consola el tiempo total que tardó en completarse el scraping.

## 🧑‍💻 Autor

Proyecto desarrollado por :
Etel silva Garcia: esilgar@gmail.om
José Morote: josemorote21@gmail.com

