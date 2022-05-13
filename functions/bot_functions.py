from requests.exceptions import HTTPError
import data.config as config
from loguru import logger
import requests
import asyncio
import json
import bot


@logger.catch
def get_incorrect_start():
    return config.BOT_CONFIG['failure_phrase']['incorrect_start']


@logger.catch
def get_first_stage():
    return config.BOT_CONFIG['intents']['first_stage']


@logger.catch
def get_second_stage(lang):
    return config.BOT_CONFIG['intents']['second_stage'][lang]


@logger.catch
def get_finished_stage(lang):
    return config.BOT_CONFIG['intents']['finished_stage'][lang]


@logger.catch
def get_upd_lang_menu_phrase(lang, status):
    if lang == 'rus' and status == 'done':
        return config.BOT_CONFIG['intents']['upd_lang_menu'][lang]
    elif lang == 'eng' and status == 'done':
        return config.BOT_CONFIG['intents']['upd_lang_menu'][lang]
    elif lang == 'rus_err' and status == 'error':
        return config.BOT_CONFIG['failure_phrase']['upd_settings_err'][lang]
    elif lang == 'eng_err' and status == 'error':
        return config.BOT_CONFIG['failure_phrase']['upd_settings_err'][lang]


@logger.catch
def get_upd_taker_menu_phrase(lang, status):
    if lang == 'rus' and status == 'done':
        return config.BOT_CONFIG['intents']['upd_maker_taker_menu'][lang]
    elif lang == 'eng' and status == 'done':
        return config.BOT_CONFIG['intents']['upd_maker_taker_menu'][lang]
    elif lang == 'rus_1' and status == 'done':
        return config.BOT_CONFIG['intents']['upd_maker_taker_menu'][lang]
    elif lang == 'eng_1' and status == 'done':
        return config.BOT_CONFIG['intents']['upd_maker_taker_menu'][lang]
    elif lang == 'rus_err' and status == 'error':
        return config.BOT_CONFIG['failure_phrase']['upd_settings_err'][lang]
    elif lang == 'eng_err' and status == 'error':
        return config.BOT_CONFIG['failure_phrase']['upd_settings_err'][lang]


def upd_lang_user(tg_user_id, lang, username):

    try:
        data_user = bot.db.get_user(tg_user_id)
        menu_permission = data_user[0][7]
        bot.db.update_tg_lang(tg_user_id, lang)
        logger.info(
            'The user username: ' + username + ' has updated the language parameter. tg_user_id: ' + str(
                tg_user_id) + ' language: ' + lang)
        if menu_permission == True:
            return 'Done'
        else:
            return 'Continue setting up'
    except Exception as ex:
        logger.error('DB request error', ex)
        return 'Error'


@logger.catch
def upd_taker_switch(tg_user_id, taker_permission, username):
    try:
        data_user = bot.db.get_user(tg_user_id)
        menu_permission = data_user[0][7]
        bot.db.update_taker_switch(tg_user_id, taker_permission)
        logger.info('The user username: ' + username + ' has updated the Taker parameter. tg_user_id: ' + str(
            tg_user_id) + ' taker_permission: ' + str(taker_permission))
        if menu_permission == True:
            return 'Done'
        else:
            return 'Continue setting up'
    except Exception as ex:
        logger.error('DB request error', ex)
        return 'Error'


# Запрос на подписку
@logger.catch
async def get_bxb_id_subscribe(tg_id, tempopary_key, username, lang):
    url = 'https://' + config.BXB_HOSTNAME + '/api/v2/tg/activate'
    param = {'uuid': str(tempopary_key), 'tg_id': tg_id, 'tg_name': username}
    try:
        i = 0
        for _ in range(3):
            i += 1
            response = requests.post(url, json=param)
            response.raise_for_status()

            if response.status_code == 200:
                bxb_user_id = json.loads(response.text)['data']['user_id']
                data_user = bot.db.get_telegram_id(bxb_user_id)

                if data_user:
                    # Ситуация если юзер бхб уже подписан на какой-то тг
                    await bot.Bot_init.send_message(tg_id, get_subscribe_phrase
                    (key='existing_user_rus' if lang == 'rus' else 'existing_user_eng') + username)
                    return 'ExistingUser_' + str(bxb_user_id)

                bot.db.update_bxb_user_id(tg_user_id=tg_id, bxb_user_id=bxb_user_id)
                logger.info(f'The user {username} has been subscribed to the notification newsletter. tg_id: {tg_id}')
                return 'Done'
            elif response.status_code != 200 and i == 3:
                logger.warning(
                    f'Error! The user {username} (tg_id: {tg_id}) was not subscribed. Status code: {response.status_code}')
                return

    except HTTPError as http_err:
        logger.error(f'HTTP error occurred: {http_err}')
        return
    except Exception as err:
        logger.error(f'Other error occurred: {err}')
        return


# Запрос на отписку
@logger.catch
def unsubscribe(user_id, tg_id, username):
    url = 'https://' + config.BXB_HOSTNAME + '/api/v2/tg/deactivate'
    param = {'user_id': int(user_id), 'tg_id': int(tg_id)}
    try:
        i = 0
        for _ in range(3):
            i += 1
            response = requests.post(url, json=param)
            response.raise_for_status()

            if response.status_code == 200:
                bot.db.delete_subscriber(tg_user_id=tg_id)
                logger.info(f'The user {username} has unsubscribed from sending notifications. tg_id: {tg_id}')
                return 'Done'
            elif response.status_code != 200 and i == 3:
                logger.warning(
                    f'Error! The user {username} (tg_id: {tg_id}) was not unsubscribed. Status code: {response.status_code}')
                return

    except HTTPError as http_err:
        logger.error(f'HTTP error occurred: {http_err}')
        return
    except Exception as err:
        logger.error(f'Other error occurred: {err}')
        return


@logger.catch
def get_next_menu_settings_phrase(lang):
    return config.BOT_CONFIG['intents']['next_menu_settings'][lang]


@logger.catch
def get_back_menu_settings_phrase(lang):
    return config.BOT_CONFIG['intents']['back_menu_settings'][lang]


@logger.catch
def get_support_service_phrase(lang):
    return config.BOT_CONFIG['intents']['support_service'][lang]


@logger.catch
def get_failure_phrase(lang):
    return config.BOT_CONFIG['failure_phrase']['no_questions_asked'][lang]


@logger.catch
def get_change_language_phrase(lang):
    return config.BOT_CONFIG['intents']['change_lang'][lang]


@logger.catch
def get_change_taker_phrase(lang):
    return config.BOT_CONFIG['intents']['change_taker_switch'][lang]


@logger.catch
def not_user_lang_phrase():
    return config.BOT_CONFIG['failure_phrase']['not_user_lang_phrase']


@logger.catch
def get_subscribe_phrase(key):
    return config.BOT_CONFIG['intents']['subscribe_phrase'][key]


@logger.catch
def get_unsubscribe_phrase(key):
    return config.BOT_CONFIG['intents']['unsubscribe_phrase'][key]


@logger.catch
def get_check_bundle_error_phrase(key):
    return config.BOT_CONFIG['intents']['bundle_error'][key]
