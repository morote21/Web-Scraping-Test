from urllib import robotparser
import pandas as pd
import time
import numpy as np

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class NBAScraper():

    def __init__(self, user_agent: str):
        self.rp = robotparser.RobotFileParser()
        self.user_agent = user_agent
        self.base_url = "https://www.nba.com/"

        # TODO: Implementar proxy para que la pagina no me bloquee cuando hago muchas ejecuciones

        # https://developer.chrome.com/docs/chromedriver/capabilities?hl=es-419
        webdriver_options = ChromeOptions()
        # webdriver_options.add_argument("--headless")
        webdriver_options.add_argument(f"--user-agent={user_agent}")
        # evitar deteccion como bot (https://stackoverflow.com/questions/71885891/urllib3-exceptions-maxretryerror-httpconnectionpoolhost-localhost-port-5958)
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = webdriver.Chrome(options=webdriver_options)
        

    # Comprobar accesibilidad al sitio web
    def check_accessibility(self, url_robots: str, url: str) -> bool:
        # https://docs.python.org/3/library/urllib.robotparser.html

        # Establece en el parser la url a robots.txt
        self.rp.set_url(url=url_robots)
        # Parsea robots.txt
        self.rp.read()
        # Examina que user_agent pueda acceder en base al robots.txt parseado
        return self.rp.can_fetch(useragent=self.user_agent, url=url)
    


    def extract_teams_shooting_ds(self) -> None:
        url_robots = f"{self.base_url}robots.txt"
        url_stats = f"{self.base_url}stats/teams/shooting"

        def get_table_contents(html, season):
            # Creamos objeto BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Extraemos la tabla de estadisticas
            teams_table = soup.find("table", class_="Crom_table__p1iZz")

            # Obtenemos las columnas de cada estadistica
            table_head = teams_table.find("thead")

            # Crom_headers__mzI_m -> Cabecera perteneciente a FGM, FGA, FG%
            # el apartado field contiene adicionalmente a que rango de tiro pertenece
            categories = [col.get("field") for col in table_head.find("tr", class_="Crom_headers__mzI_m").find_all("th")[1:]]
            df = pd.DataFrame(columns=["Team", "Season"] + categories)
            table_body = teams_table.find("tbody").find_all("tr")
            for tr in table_body:
                team_info = tr.find_all("td")
                team_name = team_info[0].get_text()
                team_stats = [float(stats.get_text()) for stats in team_info[1:]]
                
                # Categorias y estadisticas deben tener la misma longitud, deberia cumplirse siempre
                assert len(categories) == len(team_stats)
                df = pd.concat([df, pd.DataFrame(data=np.array([[team_name, season] + team_stats]), columns=df.columns)])
            
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
            
            # Obtenemos el elemento que contiene todos los filtros
            overall_filters = self.driver.find_element(by=By.CLASS_NAME, value="nba-stats-primary-split-block")
            # Obtenemos los filtros que aparecen al inicio
            initial_filters = overall_filters.find_elements(by=By.CLASS_NAME, value="DropDown_label__lttfI")

            # Inicializamos la variable para el dataset
            final_df = None

            for filt in initial_filters:
                # Titulo del filtro
                tag = filt.find_element(by=By.TAG_NAME, value="p").text
                if tag == "SEASON":
                    # Obtenemos todas las opciones (años)
                    options = filt.find_elements(by=By.TAG_NAME, value="option")

                    initial_season = options[0].text

                    # Extraemos el dataframe inicial
                    html = self.driver.page_source
                    # Esperamos a que la tabla sea visible
                    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "Crom_table__p1iZz")))
                    final_df = get_table_contents(html=html, season=initial_season)

                    for op in options:
                        try:
                            wait.until(
                                EC.element_to_be_clickable(op)
                            ).click()
                        except:
                            print("Wait failed!")
                            self.quit_driver()


                        curr_season = op.text
                        # Extraemos el dataframe y lo añadimos al final
                        html = self.driver.page_source
                        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "Crom_table__p1iZz")))
                        curr_df = get_table_contents(html=html, season=curr_season)

                        if final_df is None:
                            final_df = curr_df
                        else:
                            final_df = pd.concat([final_df, curr_df]) 
                        

                    break
            
            final_df.to_csv("..\\..\\dataset\\nba_test_dataset.csv", sep=",", index=False)
            

    # Cerrar driver
    def quit_driver(self):
        self.driver.quit()


def main():
    user_agent_windows = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    scraper = NBAScraper(user_agent=user_agent_windows)
    scraper.extract_teams_shooting_ds()

    scraper.quit_driver()


if __name__ == "__main__":
    main()