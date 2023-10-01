import logging, toml

from logging.handlers import RotatingFileHandler
from datetime import datetime

config_toml = toml.load('config.toml')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler2 = RotatingFileHandler(f"logs/{__name__}.log",maxBytes=config_toml['logging']['max_log_size'] * 1024 * 1024, backupCount=config_toml['logging']['backup_count'])
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler2.setFormatter(formatter2)
log.addHandler(handler2)

def to_tmpstmp_mc(
        date_str: str = '2023-09-30T09:26:05Z'
) -> int:
    date_obj = datetime.fromisoformat(date_str[:-1])  

    timestamp_ms = int(date_obj.timestamp() * 1000)

    return timestamp_ms

