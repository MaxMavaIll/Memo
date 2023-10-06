import time, logging, toml

from logging.handlers import RotatingFileHandler
from WorkJson import WorkWithJson

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


config_toml = toml.load('config.toml')
work_json = WorkWithJson('settings.json')


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler2 = RotatingFileHandler(f"logs/Update/Update.log",maxBytes=config_toml['logging']['max_log_size'] * 1024 * 1024, backupCount=config_toml['logging']['backup_count'])
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler2.setFormatter(formatter2)
log.addHandler(handler2)

logging.basicConfig(level=logging.INFO, format="%(name)s %(asctime)s %(levelname)s %(message)s")


def get_apr_keplr():
    path = '/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/p/span/'  # Для Chrome
    path = '/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/p/span'

    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Remote(
        command_executor=f"{config_toml['Update']['url_driver']}/wd/hub",
        options=webdriver.ChromeOptions()
    )

    driver.get("https://wallet.keplr.app/chains/cosmos-hub")
    time.sleep(4)

    a = driver.find_element(By.XPATH, path)

    


    return float(a.text[-6:-1])

def get_apr_math():
    return 1

def get_validator_commision():
    pass

def main():
    while 1: 
        log.info("Start APR monitoring")

        data = work_json.get_json()
        data['APR'] = get_apr_keplr() if config_toml['Update']['enable_chromeDriver'] else get_apr_math()
        log.info(f"APR : { data['APR']}")

        # get_validator_commision()


        work_json.set_json(data)
        time.sleep(config_toml['Update']['time'] * 60 * 60)

if __name__ == "__main__":
    main()