import toml, logging, aiohttp

from logging.handlers import RotatingFileHandler



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

TOKEN = config_toml['telegram_bot']['TOKEN']



async def send_message(log_id: int, message: str):
        """
        type_bot_token | TOKEN_ERROR, TOKEN_PROPOSALS, TOKEN_SERVER, TOKEN_NODE
        """
        for chat_id in config_toml['telegram_bot']['admins']:
            log.info(f"Відправляю повідомлення -> {chat_id}")

            
            url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
            # url = url + f'/sendMessage?chat_id={chat_id}&text={message}'
            data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, data=data) as response:

                    if response.status == 200:
                        log.info(f"ID: {log_id} -> Повідомлення було відправиленно успішно код {response.status}")
                        log.debug(f"ID: {log_id} -> Отримано через папит:\n{await response.text()}")
                        return True
                    else:
                        log.error(f"ID: {log_id} -> Повідомлення отримало код {response.status}")
                        log.error(await response.text())
                        log.debug(f"ID: {log_id} -> url: {url}")
                        log.debug(f"ID: {log_id} -> data: {data}")

                        return False