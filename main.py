import logging, toml, time, asyncio, copy
from datetime import datetime

from logging.handlers import RotatingFileHandler
from function import * 
from API import MemeApi, CosmosRequestApi
from WorkJson import WorkWithJson


config_toml = toml.load('config.toml')
work_json = WorkWithJson('settings.json')



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




cache_users = None
user_delegates = None

async def process_network(
        name_network: dict, 
        data: dict,
        transactions_type: list,
        wallet_type: list,
        settings: dict
        ):

    id_log = data["id"]
    memo = MemeApi.MemeApi(id=id_log, network=name_network.get('name'))

    try: 
        id_network = str(name_network.get('id'))
        

        cosmos = CosmosRequestApi.CosmosRequestApi(
            rest=settings['network'][name_network.get('name')]['rest'],
            rpc=settings['network'][name_network.get('name')]['rpc'],
            valoper_address=settings['network'][name_network.get('name')]['valoper_address'],
            id=id_log,
            network=name_network.get("name")
        )

        log.info(f"{id_log} | {name_network.get('name')}  ->  Wallet_type ")
       
        if id_network not in cache_users:
            cache_users[id_network] = {}

        if id_network not in user_delegates:
            user_delegates[id_network] = {}

        data_memo_address_time = await cosmos.Get_Block_Memo(transactions_type=transactions_type, wallet_type=wallet_type, address_user=cache_users[id_network], settings_json=data)

        log.info(f"{id_log} | {name_network.get('name')}  ->  New info {data_memo_address_time}")
        log.debug(f'Cache_users <-> {cache_users} || User_delegates <-> {user_delegates}')
        for height in data_memo_address_time:
            for address in data_memo_address_time[height]:
                memo_id = str(data_memo_address_time[height][address]["memo"])
                if memo_id not in  cache_users[id_network]:
                    cache_users[id_network][memo_id] = {}
                
                if memo_id not in  user_delegates[id_network]:
                    user_delegates[id_network][memo_id] = {}
                

                if address not in cache_users[id_network][memo_id]:
                    log.info(f"{id_log} | {name_network.get('name')}  ->  Add new user with: {address}")
                    userId = memo.Add_New_User(address=address, walletType=data_memo_address_time[height][address]['memo'], blockchain=name_network.get('id'))
                    cache_users[id_network][memo_id][address] = userId
                    user_delegates[id_network][memo_id][address] = 0

                if data_memo_address_time[height][address]['typeId'] == 1:
                    user_delegates[id_network][memo_id][address] += float(data_memo_address_time[height][address]['amount'])
                elif data_memo_address_time[height][address]['typeId'] == 2 and user_delegates[id_network][memo_id][address] >= float(data_memo_address_time[height][address]['amount']):
                    user_delegates[id_network][memo_id][address] -= float(data_memo_address_time[height][address]['amount'])
                else:
                    user_delegates[id_network][memo_id][address] = 0

                userId = cache_users[id_network][memo_id][address]
                memo.Add_New_Transactions(userId=userId, 
                                        typeId=data_memo_address_time[height][address]['typeId'],
                                        amount=data_memo_address_time[height][address]['amount'],
                                        executedAt=str(to_tmpstmp_mc(data_memo_address_time[height][address]['time'])),
                                        hash=data_memo_address_time[height][address]['hash']
                                        )
                
    except:
        log.exception("ERROR process_network")

async def process_reward(
        memo: MemeApi.MemeApi,
        user_delegates_all: int,
        data: dict,
        id_log: int,
        memo_id: str,
        name_network: dict,
        address: str,
        time_wait: float

):
    id_network = str(name_network.get('id'))
    
    if user_delegates_all == 0:
        return
    
    amountReward_user, amountReward_Validator = await get_APR_from(user_delegates[id_network][memo_id][address], data["APR"][name_network.get('name')], time_wait)
    log.info(f"{id_log} | {name_network.get('name')}  ->  | Address {address} :: id {name_network.get('id')} ")
    log.info(f"{id_log} | {name_network.get('name')}  ->  | All rewards user: {amountReward_user} + commission {amountReward_Validator}  APR {data['APR'][name_network.get('name')]}")

    userId = cache_users[id_network][memo_id][address]
    await memo.Update_User_Stats(userId, amountReward_user, amountReward_Validator)


async def main():
    global cache_users, user_delegates
    data = work_json.get_json()
    id_log = data["id"]
    memo = MemeApi.MemeApi(id=id_log, network="TYPE START")

    while True:
        log.info("Start")
        urls_kepler_json = WorkWithJson('Update/network_price.json')
        data2 = urls_kepler_json.get_json()
        settings = copy.deepcopy(config_toml)

        # Провірка RPC
        tasks = [check_rpc(settings["network"][network], network, id_log, settings) for network in settings['network']]
        await asyncio.gather(*tasks)
        
        log.info(config_toml)

        star_time = time.time()
        change_blockchain = []

        if cache_users == None:
            cache_users = memo.Get_Cache()
        
        if user_delegates == None:
            user_delegates = memo.Get_Users_Delegated_Amounts()

        for blockchain in memo.Get_Available_Blockchains_Types():
            if settings['network']['isMainnet'] == blockchain.get('isMainnet'):
                change_blockchain.append(blockchain)
        
        transactions_type = await memo.Get_Available_Transaction_Types()
        wallet_type = await memo.Get_Available_Wallet_Types()
        log.debug(change_blockchain)
        
        # Запуск моніторингу мереж
        tasks = [process_network(name_network, data, transactions_type, wallet_type, settings) for name_network in change_blockchain]
        await asyncio.gather(*tasks)


        # Запуск обраховування Rewards
        if data['last_completion_time'] != None:
            last_time = datetime.fromisoformat(data['last_completion_time'])
            now_time = datetime.now()
            time_wait = (now_time - last_time).total_seconds() / 60

            log.info(f"ID {id_log} -> Time Wait ::  {time_wait}")
            for name_network in change_blockchain:
                for id_network in cache_users:
                    if str(name_network.get('id')) != id_network:
                        continue
                    log.info(f"\nID {id_log} | {name_network.get('name')}  -> REWARDS")
                    for memo_id in cache_users[id_network]:
                        log.info(f"{id_log} | {name_network.get('name')}  -> Memo :: {memo_id}")
                        
                        tasks = [process_reward(memo=memo, user_delegates_all=user_delegates[id_network][memo_id][address], data=data2, 
                                                id_log=id_log, memo_id=memo_id, name_network=name_network, address=address, time_wait=time_wait) for address in cache_users[id_network][memo_id]]
                        await asyncio.gather(*tasks)

        data["last_completion_time"] = datetime.now().isoformat()
        data["id"] += 1
        work_json.set_json(data=data)
        log.info(f"Time work: {time.time() - star_time:.4f}")
        log.info(f"wait {settings['time_update'] } min\n\n")
        time.sleep(settings['time_update'] * 60)
        




if __name__ == '__main__':
    asyncio.run(main())