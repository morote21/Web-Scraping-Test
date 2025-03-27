from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ChromeService
from urllib import robotparser


class NBAScraper():

    def __init__(self, user_agent):
        self.rp = robotparser.RobotFileParser()
        self.user_agent = user_agent

        # https://developer.chrome.com/docs/chromedriver/capabilities?hl=es-419
        webdriver_options = ChromeOptions()
        # webdriver_options.add_argument("--headless")
        webdriver_options.add_argument(f"--user-agent={user_agent}")
        self.driver = webdriver.Chrome(options=webdriver_options)
        

    # Comprobar accesibilidad al sitio web
    def check_accessibility(self, url_robots, url) -> bool:
        # https://docs.python.org/3/library/urllib.robotparser.html

        # Establece en el parser la url a robots.txt
        self.rp.set_url(url=url_robots)
        # Parsea robots.txt
        self.rp.read()
        # Examina que user_agent pueda acceder en base al robots.txt parseado
        return self.rp.can_fetch(useragent=self.user_agent, url=url)
    

    # Cerrar driver
    def quit_driver(self):
        self.driver.quit()


def main():
    user_agent_windows = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    scraper = NBAScraper(user_agent=user_agent_windows)
    print(scraper.check_accessibility("https://www.nba.com/robots.txt", "https://www.nba.com/stats"))

    scraper.quit_driver()


if __name__ == "__main__":
    main()