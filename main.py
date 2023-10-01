import logging, toml, time

from logging.handlers import RotatingFileHandler
from API import MemeApi, CosmosRequestApi
from function import * 


config_toml = toml.load('config.toml')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler2 = RotatingFileHandler(f"logs/{__name__}.log",maxBytes=config_toml['logging']['max_log_size'] * 1024 * 1024, backupCount=config_toml['logging']['backup_count'])
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler2.setFormatter(formatter2)
log.addHandler(handler2)


logging.basicConfig(level=logging.INFO, format="%(name)s %(asctime)s %(levelname)s %(message)s")
logging.getLogger


cache_users = None


def main():
    global cache_users
    data_memo_address_time = {}

    memo = MemeApi.MemeApi()

    while True:

        if cache_users == None:
            cache_users = memo.Get_Cache()

        

        for name_network in memo.Get_Available_Blockchains_Types():
            try: 
                id_network = str(name_network.get('id'))
                cosmos = CosmosRequestApi.CosmosRequestApi(
                    rest=config_toml['network'][name_network.get('name')]['rest'],
                    rpc=config_toml['network'][name_network.get('name')]['rpc'],
                    valoper_address=config_toml['network'][name_network.get('name')]['valoper_address'],
                )
                transactions_type =  memo.Get_Available_Transaction_Types()
                wallet_type = memo.Get_Available_Wallet_Types()


                data_memo_address_time = cosmos.Get_Block_Memo(transactions_type=transactions_type, wallet_type=wallet_type)

                for height in data_memo_address_time:
                    for address in data_memo_address_time[height].keys():
                        
                        if id_network not in cache_users:
                                cache_users[id_network] = {}
                                
                        if address not in cache_users[id_network]:
                            log.info(f"Add new user with: {address}")
                            userId = memo.Add_New_User(address=address, walletType=data_memo_address_time[height][address]['memo'], blockchain=name_network.get('id'))


                            cache_users[id_network][address] = userId

                        userId = cache_users[id_network][address]
                        memo.Add_New_Transactions(userId=userId, 
                                                  typeId=data_memo_address_time[height][address]['typeId'],
                                                  amount=str(data_memo_address_time[height][address]['amount']),
                                                  executedAt=str(to_tmpstmp_mc(data_memo_address_time[height][address]['time'])),
                                                  hash=data_memo_address_time[height][address]['hash']
                                                  )

                for address in cache_users[id_network]:

                    amountReward_user = cosmos.Get_All_Rewards(address)
                    amountReward_validator = cosmos.Get_All_Commission()
                    amountDelegate = cosmos.Get_Balance_Delegate(address)
                    log.info(f"All rewarsd: {amountReward_user}, {amountReward_validator}, {amountDelegate}")

                    userId = cache_users[id_network][address]
                    memo.Update_User_Stats(userId, str(amountDelegate), str(amountReward_user), str(amountReward_validator))

                log.info(f"wait {config_toml['time_update'] } min")
                time.sleep(config_toml['time_update'] * 60)
            except:
                log.exception("ERROR Main")
                log.info(f"wait {config_toml['time_update'] } min")
                time.sleep(config_toml['time_update'] * 60)
        




if __name__ == '__main__':
    main()