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
urls_kepler_json = WorkWithJson('network_price.json')

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


def get_url_network_Keplr(driver: webdriver.Chrome, driver2: webdriver.Chrome, symbs: list, data: dict):
    resul = dict()

    url = "https://wallet.keplr.app"
    three_stripes = "/html/body/div/div/div[2]/div/div[1]/button"
    deployment_network = "/html/body/div/div/div[3]/div[2]/div/div/div[2]/div[1]/div[1]/div[2]/div[1]/div/button"
    url_element = "/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/div/span/span"

    if data['network_url'] == None:
        data['network_url'] = {}
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

            network = element[0]
            token = element[1].split(' $')[0]
            price = element[-1].split(' $')[-1]
            # token_price = get_price_token(href)

            if ' <' in token or not price.replace('.', '', 1).isdigit():
                continue
            
            data['network_url'][network] = {"token": token, "url": href}

            log.info(f"Add {token} <-> {href}")
            
        log.debug(f"Data network_price: {data}")
        urls_kepler_json.set_json(data)
        

    # for symb_save, conf in data.items():

    # log.info(f"Symb: {symb_save}")

    for symb in symbs:
        log.info(f"Symb: {symb}")

        for network in  data['network_url']:
            if symb.upper() not in  data['network_url'][network]['token']:
                continue

            element = get_price_token(driver=driver2, url=data['network_url'][network]['url'])

            token = element[1].split(' $')[0]
            price = element[-1].split(' $')[-1]
            log.info(f"Get token: {token}, price: {price}")
            # token_price = get_price_token(href)

            if '<' in token or not price.replace('.', '', 1).isdigit():
                break

            resul[symb] = price

        if symb == 'band':
            path_price = "/html/body/div[2]/div[2]/div/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/section/div/div/div[3]/div/div[1]/div/div/div[1]/div[1]/div/div/div/div/div/div[2]/div"
            driver.get("https://www.mintscan.io/band")
            log.info(f"Wait 5")
            time.sleep(5)
            price = driver.find_element(By.XPATH, path_price)
            log.info(f"Get token: {symb}, price: {price.text.strip('$ ')}")

            resul[symb] = price.text.strip("$ ")

        if symb == 'arch':
            path_price = "/html/body/div[2]/div[2]/div/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/section/div/div/div[3]/div/div[1]/div/div/div[1]/div[1]/div/div/div/div/div/div[2]/div"
            driver.get("https://www.mintscan.io/archway")
            log.info(f"Wait 5")
            time.sleep(5)
            price = driver.find_element(By.XPATH, path_price)
            log.info(f"Get token: {symb}, price: {price.text.strip('$ ')}")

            resul[symb] = price.text.strip("$ ")


    return resul

def get_price_token(driver: webdriver.Chrome, url: str = "https://wallet.keplr.app/chains/osmosis") -> list:

    price = "/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/div/span/span"
    network = "/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/div/h2/span"

    driver.get(url)

    time.sleep(3)
    price = driver.find_element(By.XPATH, price)
    network = driver.find_element(By.XPATH, network)

    return [network.text.title(), price.text.split(' $')[0], price.text.split(' $')[-1]]

def get_apr_keplr(driver: webdriver.Chrome, data: dict):
    tmp = {}

    for network in data['network_url']:
        log.info(f"I get APR <-> {network}")
        path = '/html/body/div/div/div[3]/div[1]/div[3]/div[2]/div/div/div/div[1]/div[2]/p/span'

        driver.get(data['network_url'][network]['url'])
        log.info("Wait 2 sec")
        time.sleep(2)

        a = driver.find_element(By.XPATH, path)
        if "-" in a.text[-6:-1]:
            log.info(f"{network} error")
            continue

        tmp[network] = float(a.text[-6:-1])

    if "Band" not in tmp:
        log.info(f"I get APR <-> Band")
        path_integer = "/html/body/div[2]/div[2]/div/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div/div[2]/div/div/div[3]/section/div/div/div[6]/div/div/div/div[2]/div/div[2]/div"
        path_price = "/html/body/div[2]/div[2]/div/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/section/div/div/div[3]/div/div[1]/div/div/div[1]/div[1]/div/div/div/div/div/div[2]/div"
        driver.get("https://www.mintscan.io/band")
        log.info(f"Wait 5")
        time.sleep(5)
        a = driver.find_element(By.XPATH, path_integer)

        tmp["Band"] =  float(a.text.strip("%"))

    if "Archway" not in tmp:
        log.info(f"I get APR <-> Archway")
        path_integer = "/html/body/div[2]/div[2]/div/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div/div[2]/div/div/div[3]/section/div/div/div[6]/div/div/div/div[2]/div/div[2]/div"
        driver.get("https://www.mintscan.io/archway")
        log.info(f"Wait 5")
        time.sleep(5)
        a = driver.find_element(By.XPATH, path_integer)
        tmp["Archway"] =  float(a.text.strip("%"))
        
    
    log.debug(f"TMP APR: {tmp}")
    return tmp

def get_apr_math():
    return 1

def get_validator_commision():
    pass

def main():
    

    while 1: 
        start_time = time.time()
        try:
            
            log.info("Start APR monitoring")
            data = work_json.get_json()
            data2 = urls_kepler_json.get_json()
            memo = MemeApi.MemeApi(data["id"], "Get_APR")

            driver = webdriver.Remote(
            command_executor=f"{config_toml['Update']['url_driver']}/wd/hub",
            options=webdriver.ChromeOptions(),
            )

            driver2 = webdriver.Remote(
                command_executor=f"{config_toml['Update']['url_driver']}/wd/hub",
                options=webdriver.ChromeOptions(),
            )

            symbs = memo.Get_Available_Blockchains_Symbols()
            log.info(f"Symbs :: {symbs}")

            resul = get_url_network_Keplr(driver=driver, driver2=driver2, symbs=symbs, data=data2)
            memo.Update_Symbols_Price(data=resul)
            log.info(f"Get price token: {resul}")
            
            # data2['APR'] = get_apr_keplr(driver, data2) if config_toml['Update']['enable_chromeDriver'] else get_apr_math()
            
            # get_validator_commision()
            # log.info(f"Get price token: {resul} {data2['APR']}")
            

            driver2.quit()
            driver2.close()
            driver.quit()
            driver.close()

        except:
            log.exception("Error APR")
            driver2.quit()
            driver2.close()
            driver.quit()
            driver.close()
    


        urls_kepler_json.set_json(data2)
        log.info(f"Time work {time.time() - start_time} sec")
        log.info(f"Wait {config_toml['Update']['time']} hour")
        time.sleep(config_toml['Update']['time'] * 60 * 60)

if __name__ == "__main__":
    main()