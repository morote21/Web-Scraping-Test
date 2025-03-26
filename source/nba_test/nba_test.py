from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ChromeService
from urllib import robotparser


class NBAScraper():

    def __init__(self, user_agent, webdriver_path):
        self.rp = robotparser.RobotFileParser()
        self.user_agent = user_agent

        # https://developer.chrome.com/docs/chromedriver/capabilities?hl=es-419
        webdriver_options = ChromeOptions()
        webdriver_options.binary_location = webdriver_path
        # webdriver_options.add_argument("--headless")
        webdriver_options.add_argument(str("--user-agent=" + user_agent))
        
        webdriver_service = ChromeService(executable_path=webdriver_path)
        print(webdriver_options.arguments)

        self.driver = webdriver.Chrome()

    # Comprobar accesibilidad al sitio web
    def check_accessibility(self, url) -> bool:
        return self.rp.can_fetch(useragent=self.user_agent, url=url)

    def quit_driver(self):
        self.driver.quit()


def main():
    user_agent_linux = "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0"
    scraper = NBAScraper(user_agent=user_agent_linux, webdriver_path="chromedriver.exe")
    print(scraper.check_accessibility("https://www.nba.com/stats"))

    scraper.quit_driver()


if __name__ == "__main__":
    main()