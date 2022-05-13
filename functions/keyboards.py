from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура выбора языка
lang_kb = InlineKeyboardMarkup().row(InlineKeyboardButton('Русский', callback_data='rus_btn'),
                                     InlineKeyboardButton('English', callback_data='eng_btn'))

# Клавиатуры Taker-сделки и Maker-сделки
taker_switch_kb_rus = InlineKeyboardMarkup().row(
    InlineKeyboardButton('Получать Taker-сделки', callback_data='taker_rus'),
    InlineKeyboardButton('Только Maker-сделки', callback_data='maker_rus'))
taker_switch_kb_eng = InlineKeyboardMarkup().row(InlineKeyboardButton('Get Taker Deals', callback_data='taker_eng'),
                                                 InlineKeyboardButton('Get only Maker Deals',
                                                                      callback_data='maker_eng'))
# Клавиатуры Subscribe
subscribe_kb_rus = InlineKeyboardMarkup().row(
    InlineKeyboardButton('🔔 Подписаться', callback_data='subscribe_rus'))
subscribe_kb_eng = InlineKeyboardMarkup().row(InlineKeyboardButton('🔔 Subscribe', callback_data='subscribe_eng'))

# Клавиатуры Unsubscribe
unsubscribe_kb_rus = InlineKeyboardMarkup().row(
    InlineKeyboardButton('Отписаться', callback_data='unsubscribe_rus'))
unsubscribe_kb_eng = InlineKeyboardMarkup().row(InlineKeyboardButton('Unsubscribe', callback_data='unsubscribe_eng'))

# Меню на русском
settings_rus = KeyboardButton('⚙️ Настройки')
contacts_rus = KeyboardButton('☎️ Служба поддержки клиентов')
unsubscribe_rus = KeyboardButton('🔕️ Отписаться')

main_menu_rus = ReplyKeyboardMarkup(resize_keyboard=True).add(settings_rus).add(
    contacts_rus).add(unsubscribe_rus)

# Меню "Настройки"
sett_lang_rus = KeyboardButton('Смена языка')
sett_taker_rus = KeyboardButton('Настройка Taker-ордеров')
back_rus = KeyboardButton('⏪ Назад')

sub_menu_rus = ReplyKeyboardMarkup(resize_keyboard=True).add(sett_lang_rus).add(
    sett_taker_rus).add(back_rus)

# Меню на английском

settings_eng = KeyboardButton('⚙️ Settings')
contacts_eng = KeyboardButton('☎️ Customer support service')
unsubscribe_eng = KeyboardButton('🔕️ Unsubcribe')

main_menu_eng = ReplyKeyboardMarkup(resize_keyboard=True).add(settings_eng).add(
    contacts_eng).add(unsubscribe_eng)

# Меню "Настройки"
sett_lang_eng = KeyboardButton('Change language')
sett_taker_eng = KeyboardButton('Setting up Taker orders')
back_eng = KeyboardButton('⏪ Back')

sub_menu_eng = ReplyKeyboardMarkup(resize_keyboard=True).add(sett_lang_eng).add(
    sett_taker_eng).add(back_eng)
