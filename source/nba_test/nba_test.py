from urllib import robotparser
import pandas as pd
import time

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

        # https://developer.chrome.com/docs/chromedriver/capabilities?hl=es-419
        webdriver_options = ChromeOptions()
        # webdriver_options.add_argument("--headless")
        webdriver_options.add_argument(f"--user-agent={user_agent}")
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
    

    def navigate_to(self):
        url_robots = f"{self.base_url}robots.txt"
        url_stats = f"{self.base_url}stats"

        if self.check_accessibility(url_robots=url_robots, url=url_stats):
            print(f"{url_stats} visited!")
            self.driver.get(url_stats)
            wait = WebDriverWait(self.driver, 10)
           
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
            
            time.sleep(2)

            buttons = self.driver.find_elements(by=By.CLASS_NAME, value="SubNavItem_subnavLink__pF1m7")
            text_button = None
            for b in buttons:
                if b.text == "Teams":
                    text_button = b
                    break
                    
            try:
                wait.until(
                    EC.element_to_be_clickable(text_button)
                ).click()
                time.sleep(5)
            except:
                print("Wait failed!")
                self.quit_driver()


    def extract_teams_shooting_ds(self) -> pd.DataFrame:
        url_robots = f"{self.base_url}robots.txt"
        url_stats = f"{self.base_url}stats/teams/shooting"

        def get_table_contents(html):
            # Creamos objeto BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Extraemos la tabla de estadisticas
            teams_table = soup.find("table", class_="Crom_table__p1iZz")

            # Obtenemos las columnas de cada estadistica
            table_head = teams_table.find("thead")

            # Crom_headers__mzI_m -> Cabecera perteneciente a FGM, FGA, FG%
            # el apartado field contiene adicionalmente a que rango de tiro pertenece
            categories = [col.get("field") for col in table_head.find("tr", class_="Crom_headers__mzI_m").find_all("th")[1:]]
            teams_content = dict()
            table_body = teams_table.find("tbody").find_all("tr")
            for tr in table_body:
                team_info = tr.find_all("td")
                team_name = team_info[0].get_text()
                team_stats = [float(stats.get_text()) for stats in team_info[1:]]
                
                # Categorias y estadisticas deben tener la misma longitud, deberia cumplirse siempre
                assert len(categories) == len(team_stats)
                # Inicializamos diccionario dentro de cada equipo que contendra las estadisticas y la categoria de cada estadistica
                teams_content[team_name] = {}
                for category, stat in zip(categories, team_stats):
                    teams_content[team_name][category] = stat
            
            # Creamos DataFrame con los datos
            df = pd.DataFrame.from_dict(teams_content)
            print(df)



        if self.check_accessibility(url_robots=url_robots, url=url_stats):
            print(f"{url_stats} visited!")
            self.driver.get(url_stats)
            wait = WebDriverWait(self.driver, 10)
           
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
            
            html = self.driver.page_source
            get_table_contents(html)


            # filters = self.driver.find_elements(by=By.CLASS_NAME, value="DropDown_label__lttfI")
            # print(filters)
            # time.sleep(4)

            # try:
            #     wait.until(
            #         EC.element_to_be_clickable((By.CLASS_NAME, "DropDown_content__Bsm3h SplitSelect_select__L8_El nba-stats-primary-split"))
            #     ).click()
            #     time.sleep(5)
            # except:
            #     print("Wait failed!")
            #     self.quit_driver()
            



        


        return


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