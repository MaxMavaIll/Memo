import time, logging, toml

from logging.handlers import RotatingFileHandler
from WorkJson import WorkWithJson
from API import MemeApi, CosmosRequestApi

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains



config_toml = toml.load('config.toml')
work_json = WorkWithJson('settings.json')
price_json = WorkWithJson('network_price.json')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

log_s = logging.StreamHandler()
log_s.setLevel(logging.INFO)
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
log_s.setFormatter(formatter2)

log_f = RotatingFileHandler(f"logs/Update/Update.log",maxBytes=config_toml['logging']['max_log_size'] * 1024 * 1024, backupCount=config_toml['logging']['backup_count'])
log_f.setLevel(logging.DEBUG)
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
log_f.setFormatter(formatter2)

log.addHandler(log_s)
log.addHandler(log_f)


def get_url_network_Keplr(driver: webdriver.Chrome, driver2: webdriver.Chrome, symbs: list):
    resul = dict()

    url = "https://wallet.keplr.app"
    three_stripes = "/html/body/div/div/div[2]/div/div[1]/button"
    deployment_network = "/html/body/div/div/div[3]/div[2]/div/div/div[2]/div[1]/div[1]/div[2]/div[1]/div/button"
    url_element = "/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/div/span/span"

    data = price_json.get_json()


    if data == {}:
        log.info("Data == {}")
        
        driver.get(url)

        log.info("Wait 2 sec")
        time.sleep(1)
        driver.find_element(By.XPATH, three_stripes).click()
        time.sleep(1)
        driver.find_element(By.XPATH, deployment_network).click()

        tmp = "/html/body/div/div/div[3]/div[2]/div/div/div[2]/div[1]/div[1]/div[2]/div[2]/div/div"

        get_elements = driver.find_elements(By.XPATH, tmp)

        for i in get_elements:
            a = i.find_element(By.XPATH, "a")
            href = a.get_attribute("href")


            element = get_price_token(driver=driver2, url=href)


            token = element[0].split(' $')[0]
            price = element[1].split(' $')[-1]
            # token_price = get_price_token(href)

            if ' <' in token or not price.replace('.', '', 1).isdigit():
                continue
            
            data[token] = {'url': href}

            log.info(f"Add {token} <-> {href}")
            
        log.debug(f"Data network_price: {data}")
        price_json.set_json(data)
        
            
    

    # for symb_save, conf in data.items():

    # log.info(f"Symb: {symb_save}")

    for symb in symbs:
        log.info(f"Symb: {symb}")

        if symb.upper() not in data:
            resul[symb] = 0
            continue

        element = get_price_token(driver=driver2, url=data[symb.upper()]['url'])

        token = element[0].split(' $')[0]
        price = element[1].split(' $')[-1]
        log.info(f"Get token: {token}, price: {price}")
        # token_price = get_price_token(href)

        if '<' in token or not price.replace('.', '', 1).isdigit():
            continue

        resul[symb] = float(price)

    return resul


def get_price_token(driver: webdriver.Chrome, url: str = "https://wallet.keplr.app/chains/osmosis") -> list:

    url_element = "/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/div/span/span"
                # "/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/div/span/span"

    driver.get(url)

    time.sleep(5)
    element = driver.find_element(By.XPATH, url_element)

    return [element.text.split(' $')[0], element.text.split(' $')[-1]]

def get_apr_keplr(driver: webdriver.Chrome):
    path = '/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/p/span'

    driver.get("https://wallet.keplr.app/chains/cosmos-hub")
    time.sleep(4)

    a = driver.find_element(By.XPATH, path)

    return float(a.text[-6:-1])

def get_apr_math():
    return 1

def get_validator_commision():
    pass

def main():
    memo = MemeApi.MemeApi()

    

    while 1: 
        start_time = time.time()
        try:
            
            log.info("Start APR monitoring")
            data = work_json.get_json()

            driver = webdriver.Remote(
            command_executor=f"{config_toml['Update']['url_driver']}/wd/hub",
            options=webdriver.ChromeOptions(),
            )

            driver2 = webdriver.Remote(
                command_executor=f"{config_toml['Update']['url_driver']}/wd/hub",
                options=webdriver.ChromeOptions(),
            )
            
            data['APR'] = get_apr_keplr(driver) if config_toml['Update']['enable_chromeDriver'] else get_apr_math()
            
            log.info(f"APR : { data['APR']}")

            # get_validator_commision()
            symbs = memo.Get_Available_Blockchains_Symbols()
            
            resul = get_url_network_Keplr(driver=driver, driver2=driver2, symbs=symbs)
            log.info(f"Get price token: {resul}")
            

            driver2.quit()
            driver.quit()

        except:
            log.exception("Error APR")
            driver2.quit()
            driver.quit()
    


        work_json.set_json(data)
        log.info(f"Time work {time.time() - start_time} sec")
        log.info(f"Wait {config_toml['Update']['time']} hour")
        time.sleep(config_toml['Update']['time'] * 60 * 60)

if __name__ == "__main__":
    main()