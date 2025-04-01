from urllib import robotparser
import pandas as pd
import time
import numpy as np
import random

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


class NBAScraper():

    def __init__(self, user_agent: str, proxy_list: list[str] = None):
        self.rp = robotparser.RobotFileParser()
        self.user_agent = user_agent
        self.base_url = "https://www.nba.com/"
        self.proxy_list = proxy_list or []

        # Inicializamos el driver en la función del proxy

        self.driver = self._init_driver_with_proxy()
        

    # Comprobar accesibilidad al sitio web
    def check_accessibility(self, url_robots: str, url: str) -> bool:
        # https://docs.python.org/3/library/urllib.robotparser.html

        # Establece en el parser la url a robots.txt
        self.rp.set_url(url=url_robots)
        # Parsea robots.txt
        self.rp.read()
        # Examina que user_agent pueda acceder en base al robots.txt parseado
        return self.rp.can_fetch(useragent=self.user_agent, url=url)

    # Inicializamos Selenium con un proxy y comprobamos que no de error
    def _init_driver_with_proxy(self):
        if not self.proxy_list:
            raise ValueError("No hay proxies disponibles para probar.")

        while self.proxy_list:
            proxy = random.choice(self.proxy_list)
            print(f"[INFO] Intentando con proxy: {proxy}")

            webdriver_options = ChromeOptions()
            webdriver_options.add_argument(f"--user-agent={self.user_agent}")
            webdriver_options.add_argument('--disable-blink-features=AutomationControlled')
            webdriver_options.add_argument(f'--proxy-server=http://{proxy}')

            try:
                driver = webdriver.Chrome(options=webdriver_options)
                # ✅ Test rápido: accedemos a nba.com solo para verificar conexión
                driver.set_page_load_timeout(15)
                driver.get("https://www.nba.com/")
                print(f"[SUCCESS] Conexión exitosa con proxy: {proxy}")
                return driver
            except WebDriverException as e:
                print(f"[WARNING] Proxy fallido: {proxy}. Error: {str(e)}")
                self.proxy_list.remove(proxy)
                continue

        raise RuntimeError("No se pudo establecer conexión con ningún proxy.")

    def extract_teams_shooting_ds(self) -> None:
        url_robots = f"{self.base_url}robots.txt"
        url_stats = f"{self.base_url}stats/teams/shooting"

        def get_table_contents(html, season, conference, position):
            # Creamos objeto BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Extraemos la tabla de estadisticas
            teams_table = soup.find("table", class_="Crom_table__p1iZz")

            # Obtenemos las columnas de cada estadistica
            table_head = teams_table.find("thead")

            # Crom_headers__mzI_m -> Cabecera perteneciente a FGM, FGA, FG%
            # el apartado field contiene adicionalmente a que rango de tiro pertenece
            categories = [col.get("field") for col in table_head.find("tr", class_="Crom_headers__mzI_m").find_all("th")[1:]]
            df = pd.DataFrame(columns=["Team", "Season", "Conference", "Position"] + categories)
            table_body = teams_table.find("tbody").find_all("tr")
            for tr in table_body:
                team_info = tr.find_all("td")
                team_name = team_info[0].get_text()
                team_stats = [float(stats.get_text()) for stats in team_info[1:]]
                
                # Categorias y estadisticas deben tener la misma longitud, deberia cumplirse siempre
                assert len(categories) == len(team_stats)
                df = pd.concat([df, pd.DataFrame(data=np.array([[team_name, season, conference, position] + team_stats]), columns=df.columns)])
            
            return df


        # Comprobamos accesibilidad a la pagina
        if self.check_accessibility(url_robots=url_robots, url=url_stats):
            print(f"{url_stats} visited!")
            self.driver.get(url_stats)
            wait = WebDriverWait(self.driver, 20)
           
            try:
                # https://stackoverflow.com/questions/64032271/handling-accept-cookies-popup-with-selenium-in-python
                print("Waiting...")
                wait.until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                ).click()
                print("Cookies accepted!")
            except:
                print("Wait failed!")
                self.quit_driver()
                return
            
            # Esperamos para que la accion de aceptar las cookies no se solape con empezar la extraccion de las tablas, o el programa peta
            time.sleep(5)

            # Cargamos los filtros avanzados para poder hacer búsqueda por conferencias
            try:
                print("Intentando abrir Advanced Filters...")
                toggle_button = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.StatsAdvancedFiltersPanel_safArrow__EqRgu")
                ))
                toggle_button.click()
                time.sleep(3)  # Pequeña espera para que los filtros se desplieguen correctamente
                print("Advanced Filters abiertos.")
            except Exception as e:
                print("No se pudo abrir el panel de filtros avanzados.")
                print(str(e))
                self.quit_driver()
                return

            # Obtenemos el boton para aplicar los filtros
            get_stats_button = None
            try:
                for button in self.driver.find_elements(by=By.CLASS_NAME, value="Button_button__L2wUb"):
                    if button.text.lower() == "get stats":
                        get_stats_button = button
            except:
                print("No se pudo acceder a los botones.")
                print(str(e))
                self.quit_driver()
                return
            
            # Nos aseguramos de tener boton para aplicar los filtros
            assert get_stats_button != None
            
            # Obtenemos el elemento que contiene todos los filtros
            overall_filters = self.driver.find_element(by=By.CLASS_NAME, value="nba-stats-primary-split-block")
            # Obtenemos los filtros que aparecen al inicio
            initial_filters = overall_filters.find_elements(by=By.CLASS_NAME, value="DropDown_label__lttfI")

            # Obtenemos todas las temporadas
            season_options = []
            for filt in initial_filters:
                tag = filt.find_element(by=By.TAG_NAME, value="p").text
                if tag.upper() == "SEASON":
                    season_options = filt.find_elements(by=By.TAG_NAME, value="option")
                    break
            
            # Obtenemos todas las conferencias
            conference_options = []
            for filt in initial_filters:
                tag = filt.find_element(by=By.TAG_NAME, value="p").text
                if tag.upper() == "CONFERENCE":
                        conference_options = [
                            opt for opt in filt.find_elements(by=By.TAG_NAME, value="option")
                            if opt.text in ["East", "West"]
                        ]
                        break
            
            # Obtenemos todas las posiciones de jugador
            positions_options = []
            for filt in initial_filters:
                tag = filt.find_element(by=By.TAG_NAME, value="p").text
                if tag.upper() == "POSITION":
                        positions_options = [
                            opt for opt in filt.find_elements(by=By.TAG_NAME, value="option")
                            if opt.text in ["Center", "Guard", "Forward"]
                        ]
                        break
   

            # Inicializamos la variable para el dataset
            final_df = None

            # Iteramos por todas las combinaciones de filtros
            for season_op in season_options:
                season_text = season_op.text
                try:
                    wait.until(EC.element_to_be_clickable(season_op)).click()
                    time.sleep(1)
                except:
                    print("Wait failed!")
                    self.quit_driver()
                
                for conf_op in conference_options:
                    conf_text = conf_op.text
                    try:
                        wait.until(EC.element_to_be_clickable(conf_op)).click()
                        time.sleep(1)
                    except:
                        print("Wait failed!")
                        self.quit_driver()
                    
                    for pos_op in positions_options:
                        pos_text = pos_op.text
                        time.sleep(1)
                        try:
                            wait.until(EC.element_to_be_clickable(pos_op)).click()
                        except:
                            print("Wait failed!")
                            self.quit_driver()
                        
                        # Aplicamos los filtros
                        try:
                            wait.until(EC.element_to_be_clickable(get_stats_button)).click()
                        except:
                            print("Wait failed!")
                            self.quit_driver()

                        time.sleep(1)
                        # Esperamos a que la tabla sea visible
                        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "Crom_table__p1iZz")))
                        # Extraemos el dataframe inicial
                        html = self.driver.page_source

                        curr_df = get_table_contents(html=html, season=season_text, conference=conf_text, position=pos_text)
                        if final_df is None:
                            final_df = curr_df
                        else:
                            final_df = pd.concat([final_df, curr_df]) 

            # Guardanis resultados en ambos formatos
            final_df.to_csv("..\\..\\dataset\\nba_test_dataset.csv", sep=",", index=False)
            final_df.to_csv("..\\..\\dataset\\nba_test_dataset_excel.csv", sep=";", index=False)
            

    # Cerrar driver
    def quit_driver(self):
        self.driver.quit()


def main():
    user_agent_windows = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    proxies = [
        "8.217.124.178:49440",
        "43.153.118.253: 13001"
    ]
    scraper = NBAScraper(user_agent=user_agent_windows, proxy_list=proxies)
    scraper.extract_teams_shooting_ds()

    scraper.quit_driver()


if __name__ == "__main__":
    main()