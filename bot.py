import asyncio
import json
import sys

import pymysql
import aiogram.utils.exceptions as exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text
from loguru import logger

import data.config as config
import functions.bot_functions as bot_func
import functions.keyboards as kb
import threads.wss_thread as wss
from functions.db_requests import DataBase_Requests

# -----------------Инициализация данных при старте бота----------------------------#

# получаем настройки бота
if config.API_TOKEN == '' and config.BXB_HOSTNAME == '' and len(config.BOT_CONFIG) == 0:
    # уровень Логов
    logger.add('data/logs/LogFile.log', format='{time} {level} {message}', level='DEBUG',
               rotation='00:00', retention='30 days', compression="zip")
    try:
        with open("data/local_config.json", "r") as local_config:
            data = json.load(local_config)
            try:
                connect_db = data['connect_db']
                if connect_db:
                    config.HOST_DB = connect_db['host']
                    config.PORT_DB = connect_db['port']
                    config.USER_DB = connect_db['user']
                    config.PASSWORD_DB = connect_db['password']
                    config.DATABASE = connect_db['database']
                    if config.HOST_DB and config.PORT_DB and config.USER_DB and config.PASSWORD_DB and config.DATABASE:

                        try:
                            config.CONNECTIONS = pymysql.connect(
                                host=config.HOST_DB,
                                port=config.PORT_DB,
                                user=config.USER_DB,
                                password=config.PASSWORD_DB,
                                database=config.DATABASE,
                                autocommit=True
                            )
                        except Exception as ex:
                            logger.critical(f'Connection resufed... {ex}')
                            sys.exit()

                        config.API_TOKEN = data['api_token']
                        config.BXB_HOSTNAME = data['bxb_hostname']
                        config.BOT_CONFIG = data['bot_config']
                        if config.API_TOKEN == '' or config.BXB_HOSTNAME == '' or len(config.BOT_CONFIG) == 0:
                            sys.exit()
                    else:
                        sys.exit()
            except KeyError as err:
                logger.critical(f'Error! The key was not found in the json string-{err}')
                sys.exit()
    except IOError:
        logger.critical("The file local_config.json was not found")
        sys.exit()

# инициализируем Бота
Bot_init = Bot(token=config.API_TOKEN)
dp = Dispatcher(Bot_init)

# Инициализация БД
db = DataBase_Requests(connect=config.CONNECTIONS)


# ----------------Обработчкики ошибок----------------------------#

@dp.errors_handler(exception=exceptions.Unauthorized)
async def UserDeactivated_handler(update: types.Update, exception: exceptions.Unauthorized):
    logger.warning(f'Unauthorized: {exception} \nUpdate: {update}')
    return True


@dp.errors_handler(exception=exceptions.NetworkError)
async def NetworkError_handler(update: types.Update, exception: exceptions.NetworkError):
    logger.warning(f'Network problem. NetworkError: {exception} \nUpdate: {update}')
    return True


@dp.errors_handler(exception=exceptions.TelegramAPIError)
async def TelegramAPIError_handler(update: types.Update, exception: exceptions.TelegramAPIError):
    logger.warning(f'TelegramAPIError: {exception} \nUpdate: {update}')
    return True


# ----------------Обработчкики кнопок----------------------------#

# Обработчик команды старт
@logger.catch
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    temporary_key = message.get_args()
    tg_user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else message.from_user.first_name
    data_user = db.get_user(tg_user_id)
    user_exist = db.subscriber_exists(tg_user_id)

    if temporary_key and user_exist and not data_user[0][2]:
        # Если выполнили переход через сайт и были ранее подписаны (not data_user[0][2]-проверка что нет бхб id)
        try:
            db.update_username__tmp_key(tg_user_id, username, temporary_key)
            logger.info("The user made a new transition from the site although it was previously added. Updating the "
                        "username and temporary key. tg_user_id: " + str(tg_user_id) + " username: " + username)

            if data_user[0][4] == 'rus':
                await message.answer(bot_func.get_finished_stage(lang='restage_rus'), reply_markup=kb.subscribe_kb_rus)
                return
            elif data_user[0][4] == 'eng':
                await message.answer(bot_func.get_finished_stage(lang='restage_eng'), reply_markup=kb.subscribe_kb_eng)
                return

        except Exception:
            logger.error("The user's data was not updated in the database. tg_user_id: " + str(
                tg_user_id) + " username: " + username)
            return
    elif temporary_key and user_exist and data_user[0][2]:
        # сообщение о том что данный тг уже привязан
        #  мы выводим тг id . для связи с новым акк бхб, хотите отписать? и шлем уведомление чтобы перешел на сайт.
        if data_user[0][4] == 'rus':
            await message.answer(bot_func.get_check_bundle_error_phrase(key='rus') + data_user[0][2])
            await message.answer(bot_func.get_check_bundle_error_phrase(key='question_rus'),
                                 reply_markup=kb.unsubscribe_kb_rus)
            return
        elif data_user[0][4] == 'eng':
            await message.answer(bot_func.get_check_bundle_error_phrase(key='eng') + data_user[0][2])
            await message.answer(bot_func.get_check_bundle_error_phrase(key='question_eng'),
                                 reply_markup=kb.unsubscribe_kb_eng)
            return
    elif temporary_key and not user_exist:
        # Если выполнили переход через сайт, но не были подписаны(новый юзер)
        try:
            db.add_subscriber(tg_user_id=tg_user_id, tg_username=username,
                              temporary_key=temporary_key)
            logger.info("A new user has been added. tg_user_id: " + str(tg_user_id) + " username: " + username)
        except Exception:
            logger.error(
                "The user was not added to the database. tg_user_id: " + str(tg_user_id) + " username: " + username)
            await message.answer(bot_func.get_incorrect_start())
            return

    elif user_exist and not temporary_key:
        # Команда старт выполнена через тг, но мы были подписаны
        try:
            # Проверяем параметр menu_permission (есть ли доступ к главному меню)
            if data_user[0][7] == True:
                if data_user[0][4] == 'rus':
                    await message.answer('Привет 👋', reply_markup=kb.main_menu_rus)
                    return
                elif data_user[0][4] == 'eng':
                    await message.answer('Hi 👋!', reply_markup=kb.main_menu_eng)
                    return

        except Exception:
            return
    else:
        logger.info("An incorrect bot start was performed. tg_user_id: " + str(tg_user_id) + " username: " + username)
        await message.answer(bot_func.get_incorrect_start(), parse_mode='Markdown')
        return

    # Если новый юзер, то отправляем ему сообщения с для первичной настройки
    try:
        await message.answer(bot_func.get_first_stage(), reply_markup=kb.lang_kb, parse_mode='Markdown')
    except exceptions.BotBlocked:
        return


@logger.catch
async def lang_btn_func(username, tg_id, lang):
    reply = bot_func.upd_lang_user(tg_user_id=tg_id, lang=lang,
                                   username=username)

    if reply == 'Done':
        # Если юзер выполнил полную настройку и хочет просто изменить параметр
        await Bot_init.send_message(tg_id,
                                    bot_func.get_upd_lang_menu_phrase(lang=lang, status='done'),
                                    reply_markup=kb.sub_menu_rus if lang == 'rus' else kb.sub_menu_eng)
    elif reply == 'Continue setting up':
        # Если новый юзер
        await Bot_init.send_message(tg_id, bot_func.get_second_stage(lang),
                                    reply_markup=kb.taker_switch_kb_rus if lang == 'rus' else kb.taker_switch_kb_eng)
    else:
        await Bot_init.send_message(tg_id,
                                    bot_func.get_upd_lang_menu_phrase(lang=lang + '_err', status='error'))


@logger.catch
async def switch_taker(username, tg_id, lang):
    reply = bot_func.upd_taker_switch(tg_user_id=tg_id, taker_permission=True,
                                      username=username)

    if reply == 'Done':
        # Если юзер выполнил полную настройку и хочет просто изменить параметр
        await Bot_init.send_message(tg_id,
                                    bot_func.get_upd_taker_menu_phrase(lang=lang, status='done'))
    elif reply == 'Continue setting up':
        # Если новый юзер
        await Bot_init.send_message(tg_id, bot_func.get_finished_stage(lang),
                                    reply_markup=kb.subscribe_kb_rus if lang == 'rus' else kb.subscribe_kb_eng)
    else:
        await Bot_init.send_message(tg_id,
                                    bot_func.get_upd_taker_menu_phrase(lang=lang + '_err', status='error'))


@logger.catch
async def switch_maker(username, tg_id, lang):
    reply = bot_func.upd_taker_switch(tg_user_id=tg_id, taker_permission=False,
                                      username=username)

    if reply == 'Done':
        # Если юзер выполнил полную настройку и хочет просто изменить параметр
        await Bot_init.send_message(tg_id,
                                    bot_func.get_upd_taker_menu_phrase(lang=lang + '_1', status='done'))
    elif reply == 'Continue setting up':
        # Если новый юзер
        await Bot_init.send_message(tg_id, bot_func.get_finished_stage(lang),
                                    reply_markup=kb.subscribe_kb_rus if lang == 'rus' else kb.subscribe_kb_eng)
    else:
        await Bot_init.send_message(tg_id,
                                    bot_func.get_upd_taker_menu_phrase(lang=lang + '_err', status='error'))


@logger.catch
async def subscribe(tg_id, lang_btn):
    data_user = db.get_user(tg_id)
    try:
        lang = data_user[0][4]
        if data_user[0][2]:
            await Bot_init.send_message(tg_id, bot_func.get_subscribe_phrase(key=lang + '_err_sub'))
            return
        reply = await bot_func.get_bxb_id_subscribe(tg_id=tg_id, tempopary_key=data_user[0][6],
                                                    username=data_user[0][3],
                                                    lang=lang)

        if reply == 'Done':
            await Bot_init.send_message(tg_id, bot_func.get_subscribe_phrase(key=lang),
                                        reply_markup=kb.main_menu_rus if lang == 'rus' else kb.main_menu_eng)
        elif reply and reply.split('_')[0] == 'ExistingUser':
            btnname_lang = ''
            text_btn = ''
            key_phrase = ''

            if lang == 'rus':
                btnname_lang = 'resubscribe_rus_'
                text_btn = 'Обновить подписку'
                key_phrase = 'existing_user_rus1'
            elif lang == 'eng':
                btnname_lang = 'resubscribe_eng_'
                text_btn = 'Renew Subscription'
                key_phrase = 'existing_user_eng1'

            btnname_lang_bxbid = btnname_lang + reply.split('_')[1]
            await Bot_init.send_message(tg_id, bot_func.get_subscribe_phrase(key=key_phrase),
                                        reply_markup=InlineKeyboardMarkup().row(
                                            InlineKeyboardButton(text=text_btn, callback_data=btnname_lang_bxbid)))
        else:
            await Bot_init.send_message(tg_id, bot_func.get_subscribe_phrase(key='error_' + lang),
                                        parse_mode='Markdown')
    except:
        await Bot_init.send_message(tg_id, bot_func.get_subscribe_phrase(key='error_' + lang_btn),
                                    parse_mode='Markdown')


@logger.catch
async def unsubscribe(tg_id, bxb_id, username, lang):
    reply = bot_func.unsubscribe(user_id=bxb_id, tg_id=tg_id, username=username)
    if reply == 'Done':
        await Bot_init.send_message(tg_id, bot_func.get_unsubscribe_phrase(key=lang),
                                    reply_markup=ReplyKeyboardRemove())
    else:
        await Bot_init.send_message(tg_id,
                                    bot_func.get_upd_taker_menu_phrase(lang=lang + '_err', status='error'))


@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'rus_btn')
async def process_callback_langbtn_rus(callback_query: types.CallbackQuery):
    username = callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name
    await lang_btn_func(username=username, tg_id=callback_query.from_user.id, lang='rus')
    await callback_query.answer()


@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'eng_btn')
async def process_callback_langbtn_eng(callback_query: types.CallbackQuery):
    username = callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name
    await lang_btn_func(username=username, tg_id=callback_query.from_user.id, lang='eng')
    await callback_query.answer()


# Обработчик русской кнопки taker_rus
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'taker_rus')
async def process_callback_switch_taker_rus(callback_query: types.CallbackQuery):
    username = callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name
    await switch_taker(username=username, tg_id=callback_query.from_user.id, lang='rus')
    await callback_query.answer()


# Обработчик русской кнопки maker_rus
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'maker_rus')
async def process_callback_switch_maker_rus(callback_query: types.CallbackQuery):
    username = callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name
    await switch_maker(username=username, tg_id=callback_query.from_user.id, lang='rus')
    await callback_query.answer()


# Обработчик английской кнопки taker_eng
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'taker_eng')
async def process_callback_switch_taker_eng(callback_query: types.CallbackQuery):
    username = callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name
    await switch_taker(username=username, tg_id=callback_query.from_user.id, lang='eng')
    await callback_query.answer()


# Обработчик английской кнопки maker_eng
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'maker_eng')
async def process_callback_switch_maker_eng(callback_query: types.CallbackQuery):
    username = callback_query.from_user.username if callback_query.from_user.username else callback_query.from_user.first_name
    await switch_maker(username=username, tg_id=callback_query.from_user.id, lang='eng')
    await callback_query.answer()


# Обработчик русской кнопки subscribe_rus
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'subscribe_rus')
async def process_callback_subscribe_rus(callback_query: types.CallbackQuery):
    await subscribe(tg_id=callback_query.from_user.id, lang_btn='rus')
    await callback_query.answer()


# Обработчик английской кнопки subscribe_eng
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'subscribe_eng')
async def process_callback_subscribe_eng(callback_query: types.CallbackQuery):
    await subscribe(tg_id=callback_query.from_user.id, lang_btn='eng')
    await callback_query.answer()


@logger.catch
@dp.callback_query_handler(Text(startswith='resubscribe'))
async def process_callback_resubscribe_btn(callback: types.CallbackQuery):
    lang = None
    current_tg_id = callback.from_user.id
    current_username = callback.from_user.username if callback.from_user.username else callback.from_user.first_name
    try:
        lang = callback.data.split('_')[1]
        id_bxb = callback.data.split('_')[2]
        old_data_user = db.get_telegram_id(id_bxb)
        if old_data_user:
            tgid_old_user = old_data_user[0][1]
            db.delete_subscriber(tgid_old_user)
            logger.info(
                f'The old account of the user {old_data_user[0][3]} was deleted from the database. tg_id {old_data_user[0][1]}')
            db.update_bxb_user_id(tg_user_id=current_tg_id, bxb_user_id=id_bxb)
            logger.info(
                f'Updated the subscription for the user {current_username}. tg_id {current_tg_id}')
            await Bot_init.delete_message(current_tg_id, int(callback.message.message_id))
            await Bot_init.send_message(current_tg_id, bot_func.get_subscribe_phrase(key=lang),
                                        reply_markup=kb.main_menu_rus if lang == 'rus' else kb.main_menu_eng)
    except:
        await Bot_init.send_message(current_tg_id,
                                    bot_func.get_subscribe_phrase(key='error_' + lang if lang else 'eng'),
                                    parse_mode='Markdown')
    await callback.answer()


# Обработчик русской кнопки unsubscribe_rus
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'unsubscribe_rus')
async def process_callback_unsubscribe_question_rus(callback_query: types.CallbackQuery):
    tg_id = callback_query.from_user.id
    data_user = db.get_user(tg_id)
    await unsubscribe(tg_id=tg_id, bxb_id=data_user[0][2], username=data_user[0][3], lang=data_user[0][4])
    await Bot_init.send_message(tg_id, bot_func.get_unsubscribe_phrase(key='reped_sub_rus'), parse_mode='Markdown')
    await callback_query.answer()


# Обработчик английской кнопки unsubscribe_eng
@logger.catch
@dp.callback_query_handler(lambda c: c.data == 'unsubscribe_eng')
async def process_callback_unsubscribe_question_eng(callback_query: types.CallbackQuery):
    tg_id = callback_query.from_user.id
    data_user = db.get_user(tg_id)
    await unsubscribe(tg_id=tg_id, bxb_id=data_user[0][2], username=data_user[0][3], lang=data_user[0][4])
    await Bot_init.send_message(tg_id, bot_func.get_unsubscribe_phrase(key='reped_sub_eng'), parse_mode='Markdown')
    await callback_query.answer()


# Обработчик всех приходящих сообщений от юзера
@logger.catch
@dp.message_handler()
async def Echo(message: types.Message):
    try:
        data_user = db.get_user(message.from_user.id)
        user_lang = data_user[0][4]
        menu_permission = data_user[0][7]
    except Exception:
        # Выполнится если юзер совершил некорректный переход и он новый юзер.
        return

    if message.text == '⚙️ Настройки' and menu_permission == True and user_lang == 'rus':
        await message.answer(bot_func.get_next_menu_settings_phrase('rus'), reply_markup=kb.sub_menu_rus)
    elif message.text == '⚙️ Settings' and menu_permission == True and user_lang == 'eng':
        await message.answer(bot_func.get_next_menu_settings_phrase('eng'), reply_markup=kb.sub_menu_eng)
    elif message.text == '☎️ Служба поддержки клиентов' and menu_permission == True and user_lang == 'rus':
        await message.answer(bot_func.get_support_service_phrase('rus'), parse_mode='Markdown')
    elif message.text == '☎️ Customer support service' and menu_permission == True and user_lang == 'eng':
        await message.answer(bot_func.get_support_service_phrase('eng'), parse_mode='Markdown')
    elif message.text == '🔕️ Отписаться' and menu_permission == True and user_lang == 'rus':
        await unsubscribe(tg_id=message.from_user.id, bxb_id=data_user[0][2], username=data_user[0][3], lang=user_lang)
    elif message.text == '🔕️ Unsubcribe' and menu_permission == True and user_lang == 'eng':
        await unsubscribe(tg_id=message.from_user.id, bxb_id=data_user[0][2], username=data_user[0][3], lang=user_lang)
    elif message.text == 'Смена языка' and menu_permission == True and user_lang == 'rus':
        await message.answer(bot_func.get_change_language_phrase('rus'), reply_markup=kb.lang_kb)
    elif message.text == 'Change language' and menu_permission == True and user_lang == 'eng':
        await message.answer(bot_func.get_change_language_phrase('eng'), reply_markup=kb.lang_kb)
    elif message.text == 'Настройка Taker-ордеров' and menu_permission == True and user_lang == 'rus':
        await message.answer(bot_func.get_change_taker_phrase('rus'), reply_markup=kb.taker_switch_kb_rus)
    elif message.text == 'Setting up Taker orders' and menu_permission == True and user_lang == 'eng':
        await message.answer(bot_func.get_change_taker_phrase('eng'), reply_markup=kb.taker_switch_kb_eng)
    elif message.text == '⏪ Назад' and menu_permission == True and user_lang == 'rus':
        await message.answer(bot_func.get_back_menu_settings_phrase('rus'), reply_markup=kb.main_menu_rus)
    elif message.text == '⏪ Back' and menu_permission == True and user_lang == 'eng':
        await message.answer(bot_func.get_back_menu_settings_phrase('eng'), reply_markup=kb.main_menu_eng)
    elif not user_lang and menu_permission == False:
        await message.answer(bot_func.not_user_lang_phrase())
    else:
        await message.answer(bot_func.get_failure_phrase(user_lang), parse_mode='Markdown')


# При старте бота получаем основной цикл потоков и в этом цикле создаем
# 1 поток для улавливаниея wss и 3 для обработки очереди wss
@logger.catch
async def on_startup(x):
    loop = asyncio.get_event_loop()
    loop.create_task(wss.listen_forever())
    loop.create_task(wss.parse_executed_trade())
    loop.create_task(wss.parse_executed_trade())
    loop.create_task(wss.parse_executed_trade())


if __name__ == '__main__':
    logger.debug('Start Bot')
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    logger.debug('Stop Bot')
