import requests, logging, toml, json
from logging.handlers import RotatingFileHandler

config_toml = toml.load('config.toml')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler2 = RotatingFileHandler(f"logs/Meme/{__name__}.log",maxBytes=config_toml['logging']['max_log_size'] * 1024 * 1024, backupCount=config_toml['logging']['backup_count'])
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler2.setFormatter(formatter2)
log.addHandler(handler2)


class MemeApi():

    HOSTNAME = "https://memo.w3coins.io"

    def Get_Available_Wallet_Types(self) -> list(dict()):
        log.info("#--Get_Available_Wallet_Types--#")
        answer = requests.get(f"{self.HOSTNAME}/api/wallets/types")

        if answer.status_code == 200:
            log.info("Success, I get 200")
            log.debug(answer.text)
            return json.loads(answer.text)
        
        else:
            log.error(f"Fail, I get {answer.status_code}")
            log.error(f"Answer with server: {answer.text}")


    def Get_Available_Transaction_Types(self) -> list():
        log.info("#--Get_Available_Transaction_Types--#")
        answer = requests.get(f"{self.HOSTNAME}/api/transactions/types")

        if answer.status_code == 200:
            log.info("Success, I get 200")
            log.debug(answer.text)
            return json.loads(answer.text)
        
        else:
            log.error(f"Fail, I get {answer.status_code}")
            log.error(f"Answer with server: {answer.text}")


    def Get_Available_Blockchains_Types(self) -> list:
        log.info("#--Get_Available_Blockchains_Types--#")
        answer = requests.get(f"{self.HOSTNAME}/api/blockchains/types")

        if answer.status_code == 200:
            log.info("Success, I get 200")
            log.debug(answer.text)
            return json.loads(answer.text)
        
        else:
            log.error(f"Fail, I get {answer.status_code}")
            log.error(f"Answer with server: {answer.text}")


    def Get_Cache(self) -> list(dict()):
        log.info("#--Get_Cache--#")

        answer = requests.get(f"{self.HOSTNAME}/api/users/cache")

        if answer.status_code == 200:
            log.info("Success, I get 200")
            log.debug(answer.text)
            return json.loads(answer.text)
        
        else:
            log.error(f"Fail, I get {answer.status_code}")
            log.error(f"Answer with server: {answer.text}")

    def Add_New_User(
            self, 
            address: str, 
            walletType: int, 
            blockchain: int
            ) -> int:
        log.info("#--Add_New_User--#")

        payload = json.dumps({
            "address": address,
            "walletType": walletType,
            "blockchain": blockchain
            })
        
        headers = {
            'Content-Type': 'application/json'
            }
        
        log.debug(payload)

        answer = requests.post(f"{self.HOSTNAME}/api/users", headers=headers, data=payload)

        if answer.status_code == 201:
            log.info("Success, I get 200")
            log.debug(answer.text)
            data = json.loads(answer.text)
            return data.get('id')
        
        else:
            log.error(f"Fail, I get {answer.status_code}")
            log.error(f"Answer with server: {answer.text}")


    def Add_New_Transactions(
            self, 
            userId: int, 
            typeId: int, 
            amount: str,
            executedAt: str,
            hash: str
            ):
        log.info("#--Add_New_User--#")
        payload = json.dumps({
            "userId": userId,
            "typeId": typeId,
            "amount": amount,
            "executedAt": executedAt,
            "hash": hash
            })
        
        headers = {
            'Content-Type': 'application/json'
            }

        answer = requests.request("POST", f"{self.HOSTNAME}/api/transactions", headers=headers, data=payload)


        if answer.status_code == 201:
            log.info("Success, I get 200")
            log.debug(answer.text)
        
        else:
            log.error(f"Fail, I get {answer.status_code}")
            log.error(f"Answer with server: {answer.text}")


    def Update_User_Stats(
            self, 
            userId: int, 
            amountDelegated: str, 
            amountRewards: str,
            amountValidatorRewards: str
            ):
        log.info("#--Add_New_User--#")

        payload = json.dumps({
        "userId": userId,
        "amountDelegated": amountDelegated,
        "amountRewards": amountRewards,
        "amountValidatorRewards": amountValidatorRewards
        })

        headers = {
        'Content-Type': 'application/json'
        }

        answer = requests.request("PATCH", f"{self.HOSTNAME}/api/users/stats", headers=headers, data=payload)


        if answer.status_code == 200:
            log.info("Success, I get 200")
            log.debug(answer.text)
        
        else:
            log.error(f"Fail, I get {answer.status_code}")
            log.error(f"Answer with server: {answer.text}")

# a = MemeApi()
# a.Add_New_User('sljgksldjglskjfioijoejirjls', 1, 1)
