from aiogram import types

button_next = types.KeyboardButton('Продолжить')
button_about = types.KeyboardButton('О нас', callback_data="О нас")
button_phis = types.KeyboardButton('Физ. лицо')
button_ur = types.KeyboardButton('Юр. лицо')
button_site = types.KeyboardButton('Наш сайт', url='http://clickfi.ru/')
button_adminpnl = types.KeyboardButton('Админ панель')
InL_button_site = types.InlineKeyboardButton('Наш сайт', url='http://clickfi.ru/')
button_KRateCheck = types.InlineKeyboardButton(text='Проверить кредитный рейтинг',
                                               url='https://nbki.ru/nbki-history/kreditnyj-otchet/')


# inline_keyboard = types.InlineKeyboardMarkup().add(button_KRateCheck)
# webapp = WebAppInfo('')

def default_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(button_next)
    kb.add(button_about, button_site)
    return kb


def phis_or_ur_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(button_phis, button_ur)
    return kb


# def default_keyboard_admin():
#     kb.add(button_next)
#     kb.add(button_about, button_site, button_adminpnl)
#     return kb
#
# def admin_keyboard():
#     kb.add('Сделать рассылку')
#
def next_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('Продолжить')
    return kb


def credRatekb():
    kb = types.InlineKeyboardMarkup()
    kb.add(button_KRateCheck)
    return kb