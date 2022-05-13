from loguru import logger
import data.config as conf
import asyncio
import websockets
import socket
import queue
import json
import bot
import decimal
from aiogram.utils.exceptions import BotBlocked
import functions.bot_functions as bot_func

ctx = decimal.Context()
trade_queue = queue.Queue()
symbols_dict = {}


# 1 поток, который постоянно слушает wss
async def listen_forever():
    url = "wss://" + conf.BXB_HOSTNAME + "/api/v2/ws"
    logger.debug('WSS start')
    while True:
        # Перезапускаем wss, если отвалился
        try:
            logger.debug('WSS connect')

            async with websockets.connect(url) as ws:
                while True:
                    # Ловим данные из wss
                    try:
                        reply = await asyncio.wait_for(ws.recv(), timeout=40)
                        reply_dict = json.loads(reply)
                        print(reply)
                        if reply_dict['method'] == "welcome":
                            symbols_dict.clear()
                            for item in reply_dict['data']['symbols']:
                                symbols_dict[item['symbol']] = item['alias']
                            continue

                        if reply_dict['method'] == "order_added":
                            trade_queue.put(reply)
                    except KeyError as key:
                        logger.error("Error! The key was not found in the json string. Key=", key)
                        continue
                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                        try:
                            pong = await ws.ping()
                            await asyncio.wait_for(pong, timeout=10)
                            logger.info('Ping OK, keeping connection alive...')
                            continue
                        except:
                            await asyncio.sleep(1)
                            break

        except socket.gaierror as err:
            logger.error("Error! The specified hostname is invalid. error: '%s'" % str(err))
            await asyncio.sleep(1)
            continue
        except websockets.exceptions.InvalidStatusCode:
            logger.error("Server rejected WebSocket connection: " + url)
            await asyncio.sleep(1)
            continue
        except ConnectionRefusedError as cnrefused:
            logger.error("No connection could be made ... ")
            await asyncio.sleep(1)
            continue


def float_to_str(f, prec=18):
    ctx.prec = prec
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')


async def send_rus_notification(chat_id, msg, data, bxb_id, username):
    try:
        id = data['id']
        id_edit = id.partition('-')[0]
        symbol = symbols_dict[data['symbol']]
        price = float_to_str(data['price'])
        volume = float_to_str(data['volume'])
    except KeyError as key:
        logger.error("Error! The key was not found in the json string. Key=", key)
        return
    try:
        text = msg + '\n\nid: ' + id_edit.upper() + '\nсимвол: ' + symbol.upper() + '\nцена: ' + price + '\nобъём: ' + volume
        logger.info("Send message tg_id: " + str(chat_id) + " username: " + username + " bxb_id: " + str(
            bxb_id) + " message: " + text.replace("\n", " "))
        await bot.Bot_init.send_message(chat_id=chat_id, text=text)
    except BotBlocked:
        if bot_func.unsubscribe(user_id=bxb_id, tg_id=chat_id, username=username) == 'Done':
            logger.warning(
                f'The user {username} has blocked the bot, I am deleting it from the database id: {chat_id}, bxb_id: {bxb_id}')
        else:
            return
    except:
        logger.error("I didn't send a message to the user: tg_id: " + str(
            chat_id) + " username: " + username + " bxb_id: " + str(
            bxb_id))
        return


async def send_eng_notification(chat_id, msg, data, bxb_id, username):
    try:
        id = data['id']
        id_edit = id.partition('-')[0]
        symbol = symbols_dict[data['symbol']]
        price = float_to_str(data['price'])
        volume = float_to_str(data['volume'])
    except KeyError as key:
        logger.error("Error! The key was not found in the json string. Key=", key)
        return
    try:
        text = msg + '\n\nid: ' + id_edit.upper() + '\nsymbol: ' + symbol.upper() + '\nprice: ' + price + '\nvolume: ' + volume
        logger.info("Send message tg_id: " + str(chat_id) + " username: " + username + " bxb_id: " + str(
            bxb_id) + " message: " + text.replace("\n", " "))
        await bot.Bot_init.send_message(chat_id=chat_id, text=text)
    except BotBlocked:
        if bot_func.unsubscribe(user_id=bxb_id, tg_id=chat_id, username=username) == 'Done':
            logger.warning(
                f'The user {username} has blocked the bot, I am deleting it from the database id: {chat_id}, bxb_id: {bxb_id}')
        else:
            return
    except:
        logger.error("I didn't send a message to the user: tg_id: " + str(
            chat_id) + " username: " + username + " bxb_id: " + str(
            bxb_id))
        return


# 3 потока, который разгребают очередь от wss. Так же здесь определяется какой мсдж отправить юзеру
async def parse_executed_trade():
    while True:
        if not trade_queue.empty():
            try:
                task = json.loads(trade_queue.get())['data']
            except queue.Empty:
                logger.error("Error! The queue was empty. ")
                continue

            try:
                try:
                    user_id = task['user_id']
                    buyer_user_id = task['buyer_user_id']
                except KeyError as key:
                    user_id = ''
                    buyer_user_id = ''
                    logger.error("Error! The key was not found in the json string. Key=", key)

                try:
                    user_id_request = bot.db.get_telegram_id(user_id)
                    buyer_user_id_request = bot.db.get_telegram_id(buyer_user_id)
                except Exception as ex:
                    logger.error("An error occurred when executing a request to the database. ", ex)
                    trade_queue.put(task)
                    continue

                if user_id == buyer_user_id and user_id_request and buyer_user_id_request:
                    user_chat_id = user_id_request[0][1]
                    username = user_id_request[0][3]
                    if user_id_request[0][4] == 'rus':
                        msg = 'Внимание! Вы совершили сделку со своим же ордером: '
                        await send_rus_notification(user_chat_id, msg, task, user_id, username)
                    elif user_id_request[0][4] == 'eng':
                        msg = 'Attention! You made a deal with your own order: '
                        await send_eng_notification(user_chat_id, msg, task, user_id, username)
                    continue

                if user_id_request:
                    user_chat_id = user_id_request[0][1]
                    username = user_id_request[0][3]
                    if user_id_request[0][4] == 'rus':
                        msg = 'Ваш ордер исполнен: '
                        await send_rus_notification(user_chat_id, msg, task, user_id, username)
                    elif user_id_request[0][4] == 'eng':
                        msg = 'Your order has been executed: '
                        await send_eng_notification(user_chat_id, msg, task, user_id, username)

                if buyer_user_id_request and buyer_user_id_request[0][5] == True:
                    buyer_user_chat_id = buyer_user_id_request[0][1]
                    username = buyer_user_id_request[0][3]
                    if buyer_user_id_request[0][4] == 'rus':
                        msg = 'Вы совершили сделку: '
                        await send_rus_notification(buyer_user_chat_id, msg, task, buyer_user_id, username)
                    elif buyer_user_id_request[0][4] == 'eng':
                        msg = 'You have made a trade transaction: '
                        await send_eng_notification(buyer_user_chat_id, msg, task, buyer_user_id, username)

            except Exception as ex:
                logger.error("Error! ", ex)
                continue
        else:
            await asyncio.sleep(1)
            continue
