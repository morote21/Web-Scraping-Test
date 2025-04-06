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




class NBAScraper():

    def __init__(self, user_agent: str):
        self.rp = robotparser.RobotFileParser()
        self.user_agent = user_agent
        self.base_url = "https://www.nba.com/"
        
        self.output = None

        # TODO: Implementar proxy para que la pagina no me bloquee cuando hago muchas ejecuciones

        # https://developer.chrome.com/docs/chromedriver/capabilities?hl=es-419
        webdriver_options = ChromeOptions()
        # webdriver_options.add_argument("--headless")
        webdriver_options.add_argument(f"--user-agent={user_agent}")
        # evitar deteccion como bot (https://stackoverflow.com/questions/71885891/urllib3-exceptions-maxretryerror-httpconnectionpoolhost-localhost-port-5958)
        webdriver_options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver = webdriver.Chrome(options=webdriver_options)

        # Configuración de timeouts del navegador
        self.driver.set_page_load_timeout(60)  # Máximo 20 segundos para cargar una página
        self.driver.implicitly_wait(5)  # Espera máxima para encontrar elementos antes de lanzar error
        

    # Comprobar accesibilidad al sitio web
    def check_accessibility(self, url_robots: str, url: str) -> bool:
        # https://docs.python.org/3/library/urllib.robotparser.html

        # Establece en el parser la url a robots.txt
        self.rp.set_url(url=url_robots)
        # Parsea robots.txt
        self.rp.read()
        # Examina que user_agent pueda acceder en base al robots.txt parseado
        return self.rp.can_fetch(useragent=self.user_agent, url=url)
    

    
    def extract_teams_shooting_ds(self) -> pd.DataFrame:
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
                team_name = team_info[0].get_text().strip()
                team_stats = [float(stats.get_text()) for stats in team_info[1:]]
                
                # Categorias y estadisticas deben tener la misma longitud, deberia cumplirse siempre
                assert len(categories) == len(team_stats)
                df = pd.concat([df, pd.DataFrame(data=np.array([[team_name, season, conference, position] + team_stats]), columns=df.columns)])
            
            return df
        

        final_df = None


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

                        # Añadimos espaciado de peticiones HTTP:
                        # Introducimos un retraso un retraso aleatorio, así simulamos comportamiento más humano
                        response_delay = random.uniform(2.0, 5.0)
                        print(f"[INFO] Esperando {response_delay:.2f} segundos antes de la siguiente petición...")
                        time.sleep(response_delay)
        
        return final_df

    

    def extract_teams_contested_shoots(self, check_accept_cookies=False) -> pd.DataFrame:
        url_robots = f"{self.base_url}robots.txt"
        url_stats = f"{self.base_url}stats/teams/hustle"

        def get_table_contents(html, season, conference, position):
            # Creamos objeto BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Extraemos la tabla de estadisticas
            teams_table = soup.find("table", class_="Crom_table__p1iZz")

            # Obtenemos las columnas de cada estadistica
            table_head = teams_table.find("thead")

            # Categorias que nos interesan
            cats_of_interest = ["contested_shots_2pt", "contested_shots_3pt"]

            # Crom_headers__mzI_m -> Cabecera de la tabla
            categories = [col.get("field").lower() for col in table_head.find("tr", class_="Crom_headers__mzI_m").find_all("th")[1:]]

            # Indices de las categorias de interes dentro de todas las categoria 
            categories_idx = [categories.index(c) for c in cats_of_interest]

            df = pd.DataFrame(columns=["Team", "Season", "Conference", "Position"] + cats_of_interest)
            table_body = teams_table.find("tbody").find_all("tr")
            for tr in table_body:
                team_info = tr.find_all("td")
                team_name = team_info[0].get_text().strip()
                # Cogemos unicamente las estadisticas de interes
                team_stats = [float(team_info[1:][i].get_text()) for i in categories_idx]
                
                # Categorias y estadisticas deben tener la misma longitud, deberia cumplirse siempre
                assert len(categories_idx) == len(team_stats)
                print(team_stats)
                df = pd.concat([df, pd.DataFrame(data=np.array([[team_name, season, conference, position] + team_stats]), columns=df.columns)])
            
            return df


        final_df = None
        
        # Comprobamos accesibilidad a la pagina
        if self.check_accessibility(url_robots=url_robots, url=url_stats):
            print(f"{url_stats} visited!")
            self.driver.get(url_stats)
            wait = WebDriverWait(self.driver, 20)

            # No aparecerá el boton de aceptar cookies si ya se ha aceptado en el link anterior
            if check_accept_cookies:
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

                        # Añadimos espaciado de peticiones HTTP:
                        # Introducimos un retraso un retraso aleatorio, así simulamos comportamiento más humano
                        response_delay = random.uniform(2.0, 5.0)
                        print(f"[INFO] Esperando {response_delay:.2f} segundos antes de la siguiente petición...")
                        time.sleep(response_delay)
            

        return final_df   


    def extract_teams_boxouts(self, check_accept_cookies=False) -> pd.DataFrame:
        url_robots = f"{self.base_url}robots.txt"
        url_stats = f"{self.base_url}stats/teams/box-outs"

        def get_table_contents(html, season, conference, position):
            # Creamos objeto BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Extraemos la tabla de estadisticas
            teams_table = soup.find("table", class_="Crom_table__p1iZz")

            # Obtenemos las columnas de cada estadistica
            table_head = teams_table.find("thead")

            # Categorias que nos interesan
            cats_of_interest = ["off_boxouts", "def_boxouts"]

            # Crom_headers__mzI_m -> Cabecera de la tabla
            categories = [col.get("field").lower() for col in table_head.find("tr", class_="Crom_headers__mzI_m").find_all("th")[1:]]
            print(categories)

            # Indices de las categorias de interes dentro de todas las categoria 
            categories_idx = [categories.index(c) for c in cats_of_interest]

            df = pd.DataFrame(columns=["Team", "Season", "Conference", "Position"] + cats_of_interest)
            table_body = teams_table.find("tbody").find_all("tr")
            for tr in table_body:
                team_info = tr.find_all("td")
                team_name = team_info[0].get_text().strip()
                # Cogemos unicamente las estadisticas de interes
                team_stats = [float(team_info[1:][i].get_text()) for i in categories_idx]
                
                # Categorias y estadisticas deben tener la misma longitud, deberia cumplirse siempre
                assert len(categories_idx) == len(team_stats)
                print(team_stats)
                df = pd.concat([df, pd.DataFrame(data=np.array([[team_name, season, conference, position] + team_stats]), columns=df.columns)])
            
            return df


        final_df = None
        
        # Comprobamos accesibilidad a la pagina
        if self.check_accessibility(url_robots=url_robots, url=url_stats):
            print(f"{url_stats} visited!")
            self.driver.get(url_stats)
            wait = WebDriverWait(self.driver, 20)

            # No aparecerá el boton de aceptar cookies si ya se ha aceptado en el link anterior
            if check_accept_cookies:
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

                        # Añadimos espaciado de peticiones HTTP:
                        # Introducimos un retraso un retraso aleatorio, así simulamos comportamiento más humano
                        response_delay = random.uniform(2.0, 5.0)
                        print(f"[INFO] Esperando {response_delay:.2f} segundos antes de la siguiente petición...")
                        time.sleep(response_delay)
            

        return final_df



    def execute_scraping(self):
        # Extraemos tiros
        df1 = self.extract_teams_shooting_ds()
        # Extraemos tiros defendidos
        df2 = self.extract_teams_contested_shoots(check_accept_cookies=False)

        # Reseteamos indices para evitar problemas al hacer el merge
        df1 = df1.reset_index(drop=True)
        df2 = df2.reset_index(drop=True)
        
        # Realizamos el merge con LEFT
        df3 = pd.merge(df1, df2, on=["Team", "Season", "Conference", "Position"], how="left")

        # Extraemos rebotes defendidos
        df4 = self.extract_teams_boxouts(check_accept_cookies=False)
        df4 = df4.reset_index(drop=True)
        
        # Ultimo merge para obtener el output final
        self.output = pd.merge(df3, df4, on=["Team", "Season", "Conference", "Position"], how="left")     
        print(self.output) 



    # Cerrar driver
    def quit_driver(self):
        self.driver.quit()


    # Guardar resultados en ambos formatos de csv
    def get_csv(self):
        self.output.to_csv("..\\..\\dataset\\nba_test_dataset.csv", sep=",", index=False)
        self.output.to_csv("..\\..\\dataset\\nba_test_dataset_excel.csv", sep=";", index=False)
        


def main():
    # INICIAMOS EL CONTADOR DE TIEMPO
    start_time = time.time()

    user_agent_windows = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    scraper = NBAScraper(user_agent=user_agent_windows)
    scraper.execute_scraping()
    scraper.get_csv()
    scraper.quit_driver()

    # TIEMPO FINAL
    end_time = time.time()
    duration = end_time - start_time
    print(f"⏱️ Tiempo total de ejecución: {duration:.2f} segundos")

if __name__ == "__main__":
    main()