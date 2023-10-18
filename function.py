import logging, toml

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


def get_APR_from(
        amountDelegated: int, 
        APR: float
        ) -> str:
    minute = 365 * 24 * 60
    hour = 365 * 24
    reward = f"{amountDelegated * ( APR / 100 ) / minute:.10f}"

    return f"{float(reward) - float(reward) * 0.02:.10f}", f"{float(reward) * 0.02:.10f}" # amountDelegated * ( APR / 100 ) / minute

def update_APR(
        reward_for_minute: int
):
    pass