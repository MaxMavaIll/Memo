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


async def get_APR_from(
        amountDelegated: int, 
        APR: float,
        time_wait: float
        ) -> str:
    minute = 365 * 24 * 60
    hour = 365 * 24
    reward = f"{(amountDelegated * ( APR / 100 ) / minute) * time_wait:.10f}"

    return f"{float(reward) - float(reward) * 0.02:.10f}", f"{float(reward) * 0.02:.10f}" # amountDelegated * ( APR / 100 ) / minute

async def check_rpc(
        network: dict,
        name_network: str,
        id_log: int,
        settings: dict
):
    if type(dict()) != type(network):
        return
    
    url = f"{network['rpc']}/status"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                log.info(f"ID {id_log} -> {network['rpc']} 200")
                data = await response.json()
                if data["result"]["sync_info"]["catching_up"] == True:
                    log.info(f"ID {id_log} -> {name_network} not already")
                    del settings['network'][name_network]
                log.info(f"ID {id_log} -> {name_network} already")
            else:
                log.error(f"ID {id_log} -> {network['rpc']} {response.status}")
                del settings['network'][name_network]
                
def check_existing_memo(
          cache_users: dict,
          id_network: str,
          address: str,
          id_memo: str
):
    for memo_id, users in cache_users[id_network].items():
        if address in list(users.keys()):
            if memo_id == id_memo:
                return memo_id, True, False
            return memo_id, False, False
    
    return id_memo, True, True