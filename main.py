import logging, toml, time, asyncio, copy
from datetime import datetime

from logging.handlers import RotatingFileHandler
from function import * 
from API import MemeApi, CosmosRequestApi
from WorkJson import WorkWithJson


config_toml = toml.load('config.toml')
work_json = WorkWithJson('settings.json')
rewards_json = WorkWithJson('Rewards/rewards.json')



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


async def Update_Rewards(
        cosmos: CosmosRequestApi.CosmosRequestApi,
        memo: MemeApi.MemeApi,
        network_id: str,
        memo_delegate: dict,
        rewards_save: dict,
        

):
    log.info("#Update_Rewards")
    
    async def process_addrres_reward(
            addrres: str,
            origin_delegate: list,
            memo_amount_delegate: float,
            rewards_save: dict,
            user_id: str
    ):
        log.info("#process_addrres_reward")
        origin_amount_delegate = float (get_amount_from_addr(origin_delegate=origin_delegate, addr=addrres))
        rewards_save_f = float(rewards_save[addrres])

        if origin_amount_delegate == 0 or memo_amount_delegate == 0:
            return

        rewards_user = float(await cosmos.Get_Rewards_User(address_user=address))
        percent_memo = get_percent_memo(origin_amount_delegate=origin_amount_delegate, memo_amount_delegate=memo_amount_delegate)
        log.info(f"{address}: origin {origin_amount_delegate} ## memo {memo_amount_delegate} || {percent_memo}%")
        
        log.info(f"{rewards_user, type(rewards_user), rewards_save_f, type(rewards_save_f)}")
        if rewards_user < rewards_save_f: 
            rewards_save[addrres] = "0.0"
            return
        
        tmp = (rewards_user - rewards_save_f) * percent_memo
        validator_commisstion = f"{(tmp / (100 - 0.05 * 100)) * (0.05 * 100) / 10 ** 6:.10f}"
        user_get_rewards = f"{tmp / 10 ** 6 :.10f}"
        log.info(f"Get Validator: {validator_commisstion}, User:  {user_get_rewards}")

        await memo.Update_User_Stats_Amount(userId=user_id, amountUserRewards=user_get_rewards, amountValidatorRewards=validator_commisstion)
        rewards_save[addrres] = str(rewards_user)

    origin_delegate = await cosmos.Get_Stakers()
    

    for memo_id, memo_values  in memo_delegate[network_id].items():
        log.info(f"#Memo Id {memo_id}")
        for address in memo_values:
            log.info(f"#Memo {address}")

            if address not in rewards_save:
                continue

            await process_addrres_reward(addrres=address, 
                                   origin_delegate=origin_delegate, 
                                   memo_amount_delegate=memo_values[address] * 10 ** 6,
                                   rewards_save=rewards_save,
                                   user_id = cache_users[network_id][memo_id][address])
            
        # tasks = [process_addrres_reward(addrres=address,
        #                                 origin_delegate=origin_delegate,
        #                                 memo_amount_delegate=memo_values[address]) for address in memo_values]
        # await asyncio.gather(*tasks)


async def process_network(
        name_network: dict, 
        data: dict,
        transactions_type: list,
        wallet_type: list,
        settings: dict,
        data2: dict
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

        rewards_save = rewards_json.get_json()
        # for network in ['4']:
        #     await Update_Rewards(network=network,memo_delegate=memo_delegate, rewards_save=rewards_save)
        # log.info(f"User Delegate: {user_delegates}")
        await Update_Rewards(cosmos=cosmos, memo=memo, network_id=str(name_network.get("id")),
                            memo_delegate=user_delegates, rewards_save=rewards_save)
        
        # await asyncio.gather(*task)
        rewards_json.set_json(rewards_save)
        
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

                # memo_id, delegate_answer, answer = check_existing_memo(cache_users, id_network, address, memo_id)
                # log.info(f"{memo_id}, {delegate_answer}, {answer}")
                #Add New User
                if address not in cache_users[id_network][memo_id]:
                    log.info(f"{id_log} | {name_network.get('name')}  ->  Add new user with: {address}")
                    userId = await memo.Add_New_User(address=address, walletType=data_memo_address_time[height][address]['memo'], blockchain=name_network.get('id'))
                    if userId != None:
                        cache_users[id_network][memo_id][address] = userId
                        user_delegates[id_network][memo_id][address] = 0
                    else:
                        memo_id = check_existing_memo(cache_users, id_network, address, memo_id)

                        log.info(f"User's already created!")

                #Add New Transactions
                userId = cache_users[id_network][memo_id][address]
                answer_delegate = memo.Add_New_Transactions(userId=userId, 
                                        typeId=data_memo_address_time[height][address]['typeId'],
                                        amount=data_memo_address_time[height][address]['amount'],
                                        executedAt=str(to_tmpstmp_mc(data_memo_address_time[height][address]['time'])),
                                        hash=data_memo_address_time[height][address]['hash'],
                                        transactionMark=data_memo_address_time[height][address]['transactionMark']
                                        )
                #Add delegate sum
                if answer_delegate.get('message') == "Transaction was successfully registered!": 
                    if data_memo_address_time[height][address]['typeId'] == 1:
                        log.info(f"{id_log} | {name_network.get('name')}  ->  User: {address} Delegate: {data_memo_address_time[height][address]['amount']}")
                        user_delegates[id_network][memo_id][address] += float(data_memo_address_time[height][address]['amount'])
                    elif data_memo_address_time[height][address]['typeId'] == 2 and user_delegates[id_network][memo_id][address] >= float(data_memo_address_time[height][address]['amount']):
                        log.info(f"{id_log} | {name_network.get('name')}  ->  User: {address} UnDelegate: {data_memo_address_time[height][address]['amount']}")
                        user_delegates[id_network][memo_id][address] -= float(data_memo_address_time[height][address]['amount'])
                    else:
                        log.info(f"{id_log} | {name_network.get('name')}  ->  User: {address} have 0")
                        user_delegates[id_network][memo_id][address] = 0
                

                if address not in rewards_save:
                    rewards_save = rewards_json.get_json()
                    rewards_save[address] = await cosmos.Get_Rewards_User(address_user=address)
                    rewards_json.set_json(rewards_save)
        
        # log.info(f"\n{id_log} | {name_network.get('name')}  -> REWARDS")
        # if data['last_completion_time'] != None:
        #     last_time = datetime.fromisoformat(data['last_completion_time'][name_network.get('name')])
        #     now_time = datetime.now()
        #     time_wait = (now_time - last_time).total_seconds() / 60

        #     log.info(f"ID {id_log} -> Time Wait in sleep ::  {time_wait}")
        #     for memo_id in cache_users[id_network]:
        #         log.info(f"{id_log} | {name_network.get('name')}  -> Memo :: {memo_id}")

        #         tasks = [process_reward(memo=memo, user_delegates_all=user_delegates[id_network][memo_id][address], data=data2, 
        #                                             id_log=id_log, memo_id=memo_id, name_network=name_network, address=address, time_wait=time_wait, 
        #                                             commission=settings["network"][name_network.get('name')]["commission"]) for address in cache_users[id_network][memo_id]]
        #         await asyncio.gather(*tasks)
        # else:
        #     data["last_completion_time"] = {}

        # data["last_completion_time"][name_network.get('name')] = datetime.now().isoformat()
        
        
                # log.info(f"{id_log} | {name_network.get('name')}  ->")
                # amountReward_user, amountReward_Validator = get_APR_from(user_delegates[id_network][memo_id][address], data2["APR"][name_network.get('name')])
                # log.info(f"{id_log} | {name_network.get('name')}  ->  | Address {address}  | All rewards user: {amountReward_user} + commission {amountReward_Validator}  APR {data2['APR'][name_network.get('name')]}")

                # userId = cache_users[id_network][memo_id][address]
                # memo.Update_User_Stats(userId, amountReward_user, amountReward_Validator)

        # for name_network in change_blockchain:
        #             for id_network in cache_users:
        #                 if str(name_network.get('id')) != id_network:
        #                     continue
        #                 log.info(f"\nID {id_log} | {name_network.get('name')}  -> REWARDS")
        #                 for memo_id in cache_users[id_network]:
        #                     log.info(f"{id_log} | {name_network.get('name')}  -> Memo :: {memo_id}")
                            
        #                     tasks = [process_reward(memo=memo, user_delegates_all=user_delegates[id_network][memo_id][address], data=data2, 
        #                                             id_log=id_log, memo_id=memo_id, name_network=name_network, address=address, time_wait=time_wait) for address in cache_users[id_network][memo_id]]
        #                     await asyncio.gather(*tasks)       
                
    except:
        log.exception("ERROR process_network")


async def main():
    global cache_users, user_delegates
    data = work_json.get_json()
    id_log = data["id"]
    memo = MemeApi.MemeApi(id=id_log, network="TYPE START")

    while True:
        try:
            log.info("Start")
            urls_kepler_json = WorkWithJson('Update/network_price.json')
            data2 = urls_kepler_json.get_json()
            settings = copy.deepcopy(config_toml)

            # Провірка RPC
            tasks = [check_rpc(settings["network"][network], network, id_log, settings) for network in settings['network']]
            await asyncio.gather(*tasks)
            
            # log.info(config_toml)
            # log.info(settings)

            star_time = time.time()
            change_blockchain = []

            if cache_users == None:
                cache_users = memo.Get_Cache()
            
            if user_delegates == None:
                user_delegates = memo.Get_Users_Delegated_Amounts()

            # log.info(f"{memo.Get_Available_Blockchains_Types()}\n\n")
            for blockchain in memo.Get_Available_Blockchains_Types():
                if settings['network']['isMainnet'] == blockchain.get('isMainnet'):
                    for name in settings['network']:
                        if name == blockchain.get('name'):
                            change_blockchain.append(blockchain)
            
            transactions_type = await memo.Get_Available_Transaction_Types()
            wallet_type = await memo.Get_Available_Wallet_Types()
            # log.info(change_blockchain)
            
            # Запуск моніторингу мереж
            
            tasks = [process_network(name_network, data, transactions_type, wallet_type, settings, data2) for name_network in change_blockchain]
            await asyncio.gather(*tasks)

            data["id"] += 1
            work_json.set_json(data=data)
            log.info(f"Time work: {time.time() - star_time:.4f}")
            log.info(f"wait {settings['time_update'] } sec\n\n")
            time.sleep(settings['time_update'] )
        except:
            log.exception("Error Main")
            log.info(f"wait {settings['time_update'] } sec\n\n")
            time.sleep(settings['time_update'] )
        




if __name__ == '__main__':
    asyncio.run(main())