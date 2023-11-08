import logging, toml
import aiohttp

from logging.handlers import RotatingFileHandler
from datetime import datetime
from API import CosmosRequestApi

config_toml = toml.load('config.toml')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

log_s = logging.StreamHandler()
log_s.setLevel(logging.INFO)
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
log_s.setFormatter(formatter2)

log_f = RotatingFileHandler(f"logs/{__name__}.log",maxBytes=config_toml['logging']['max_log_size'] * 1024 * 1024, backupCount=config_toml['logging']['backup_count'])
log_f.setLevel(logging.DEBUG)
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
log_f.setFormatter(formatter2)

log.addHandler(log_s)
log.addHandler(log_f)



def to_tmpstmp_mc(
        date_str: str = '2023-09-30T09:26:05Z'
) -> int:
    date_obj = datetime.fromisoformat(date_str[:-1])  

    timestamp_ms = int(date_obj.timestamp() * 1000)

    return timestamp_ms

def get_amount_from_addr(origin_delegate: list, addr: str) -> str:
    for staker_user in origin_delegate:
        if staker_user['delegation']['delegator_address'] == addr:
            return staker_user['balance']['amount']    
    return "0"

async def get_APR_from(
        amountDelegated: int, 
        APR: float,
        time_wait: float,
        commission: float
        ) -> str:
    minute = 365 * 24 * 60
    hour = 365 * 24
    reward = f"{(amountDelegated * ( APR / 100 ) / minute) * time_wait:.10f}"

    return f"{float(reward) - float(reward) * commission:.10f}", f"{float(reward) * commission:.10f}" # amountDelegated * ( APR / 100 ) / minute

async def check_rpc(
        network: dict,
        name_network: str,
        id_log: int,
        settings: dict
):
    if type(dict()) != type(network):
        return
    
    for rpc in network['rpc']:

        url = f"{rpc}/status"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    
                    log.info(f"ID {id_log} -> {rpc} 200")
                    data = await response.json()
                    if data["result"]["sync_info"]["catching_up"] == True:
                        
                        log.info(f"ID {id_log} -> {name_network} not already")
                        settings['network'][name_network]['rpc'] = ""
                        continue
                    
                    log.info(f"ID {id_log} -> {name_network} already")
                    settings['network'][name_network]['rpc'] = rpc
                    break
                else:
                    
                    log.error(f"ID {id_log} -> {rpc} {response.status}")
                    settings['network'][name_network]['rpc'] = ""
                    
    for rest in network['rest']:

        url = f"{rest}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200 or response.status == 501:
                    
                    log.info(f"ID {id_log} -> {rest} 200, 501")
                    settings['network'][name_network]['rest'] = rest
                    break
                else:
                    
                    log.error(f"ID {id_log} -> {rest} {response.status}")
                    settings['network'][name_network]['rest'] = ""

    if settings['network'][name_network]['rpc'] == "" or settings['network'][name_network]['rest'] == "":
        log.info(f"Does not have a working rpc or rest :: {name_network}")
        del settings['network'][name_network]
                    
                
def check_existing_memo(
          cache_users: dict,
          id_network: str,
          address: str,
          id_memo: str
):
    for memo_id, users in cache_users[id_network].items():
        if address in list(users.keys()):
            return memo_id
        
def get_percent_memo(origin_amount_delegate, memo_amount_delegate) -> float:

    x =  ((memo_amount_delegate * 100) / origin_amount_delegate) / 100
    return round(x, 2)
