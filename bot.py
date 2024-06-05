import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery
from telethon import TelegramClient

import keyboards as kb
import sqlite_db as db
from datetime import datetime
import logging
import re
from aiogram.utils.exceptions import ChatNotFound

API_TOKEN = '6914750786:AAFyOGIcjW955NftwyaGI4Lcu-iGlPBni10'

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


class NewGroup(StatesGroup):
    link = State()
    links = State()
    accounts = State()


class Replenish_balance(StatesGroup):
    currency = State()
    amount = State()


async def on_startup(_):
    await db.db_start()
    print('Бот запущен!')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dp.message_handler(commands=['start'])
async def cmd_start_user(message: types.Message):
    logger.info("0Received start command from user %s", message.from_user.id)
    await message.answer_sticker('CAACAgIAAxkBAAEDZuVlx6DBQry15wn4Z03CwXTln4sWewAC2A8AAkjyYEsV-8TaeHRrmDQE')
    print(await db.check_user(message.from_user.id))
    if await db.check_user(message.from_user.id):
        cash = await db.get_cash(message.from_user.id)
    else:
        cash = 0
    if await db.return_group(message.from_user.id) == None:
        await message.answer("Вот краткая инструкция:", reply_markup=kb.user_kb)
        await message.answer(f"""


        1️⃣ Добавь группу/канал куда добавлять подписчиков
        2️⃣ Скажи группу/канал откуда взять пописчиков
        3️⃣ Добавь аккаунты которые для тебя инвайтить подписчиков
        4️⃣ Смотри отчеты в боте
        ⚠ Учти один аккаунт добавляет от 3 до 5 посписчиков в день ⚠
        Ваш баланс: {cash[0][0]}
        Выберите или добавь новую группу/канал
        👇
            """)
    else:
        markup2 = types.InlineKeyboardMarkup()
        print(await db.return_group(message.from_user.id))
        groups = await db.return_group(message.from_user.id)
        print(groups, 98342794)
        for group in groups:
            print(group[0])
            btn = types.InlineKeyboardButton(text=f'{group[1]}', callback_data=f'select_{group[0]}')
            markup2.add(btn)
        await message.answer("Вот краткая инструкция:", reply_markup=kb.user_kb)
        await message.answer(f"""
            1️⃣ Добавь группу/канал куда добавлять подписчиков
            2️⃣ Скажи группу/канал откуда взять пописчиков
            3️⃣ Добавь аккаунты которые для тебя инвайтить подписчиков
            4️⃣ Смотри отчеты в боте
            ⚠ Учти один аккаунт добавляет от 3 до 5 посписчиков в день ⚠
            Ваш баланс: {cash[0][0]}
            Выберите или добавь новую группу/канал
            👇
                """, reply_markup=markup2)

    print(message.from_user.id)


async def check_role(update: types.Update):
    user_id = int(update.from_user.id)
    if await db.check_admin(user_id):
        print('Admin', user_id)
        return 'admin'
    else:
        print('User', user_id)
        return 'user'

@dp.message_handler(commands=['groups'])
async def show_groups(message: types.Message):
    await message.answer(await db.get_groups())



@dp.message_handler(text=['Добавить новую группу или канал'])
async def new_group(message: types.Message):
    print(message.text)
    logger.info("1Received start command from user %s", message.from_user.id)
    await message.answer("""
Отправь сюда свою группу сообщением ➡
Пример: https//:sdfsfsd/""")
    await NewGroup.link.set()


@dp.message_handler(state=NewGroup.link)
async def add_sub(message: types.Message, state: FSMContext):
    logger.info("2Received message %s in state NewGroup.link", message.text)
    try:
        async with state.proxy() as data:
            data['link'] = message.text
        check = await check_group(message, data['link'])
        if check:
            await message.answer("""
Теперь добавь до 5 групп/каналов откуда будем брать подписчиков
Пример: 
https//:sdfsfsd1/ 
https//:sdfsfsd2/ 
https//:sdfsfsd3/""")
            await NewGroup.next()
        elif check == None:
            await state.finish()
        else:
            await NewGroup.first()
        print(data['link'])
    except Exception as e:
        print(e)


@dp.message_handler(state=NewGroup.links)
async def add_account(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        text = message.text  # Ваш текст сообщения
        data['links'] = set(
            re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text))
        data['links'] = {link.rstrip(',') for link in data['links']}
    print(data['links'])
    # cleaned_urls = [url.strip().replace(" ", "") for url in data['links']]
    for link in data['links']:
        print(link, 123)
        if link.startswith('https'):
            print(link, 382724238)
            check = True
        else:
            check = False
            await message.reply('Не правильная ссылка или формат2')
            await NewGroup.previous()
    if check:
        await message.answer("Сколько аккаунтов вы хотите арендовать?\nПример: 3")
        await NewGroup.next()


@dp.message_handler(state=NewGroup.accounts)
async def add_group(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['accounts'] = message.text
            accounts = int(data['accounts'])
        except:
            await NewGroup.previous()
    print(data['accounts'])
    print(isinstance(accounts, int))
    if isinstance(accounts, int):
        print(accounts, 1000)
        #     check group
        links = ''
        links_cancel = ''
        print(data['links'])
        l = data['links'].copy()
        members_count = 0
        for link in l:
            if 't.me' in link:
                chat_id = link.split('/')[-1]
                if chat_id.startswith('+'):
                    chat_id = chat_id[1:]
                elif chat_id.startswith('@'):
                    chat_id = chat_id[1:]
                else:
                    chat_id = f"@{chat_id}"
            else:
                await message.reply("Неправильная ссылка или такой группы не существет")
                return False
            try:
                chat = await bot.get_chat(chat_id)
                members_count += await chat.get_members_count()
                print(await chat.get_members_count())
            except:
                pass

            print(link)
            check = await check_group(message, link)
            if check:
                links += f'{chat.title}({link}) ✅\n'
            else:
                try:
                    links_cancel += f'{chat.title}({link}) ⛔\n'
                except Exception as e:
                    links_cancel += f'{link} ⛔\n'
                data['links'].remove(link)

        if links_cancel != '':
            await message.answer(f"Эти группы не могут быть запарсены:\n{links_cancel}")
        else:
            pass
        cost = 50
        user_id = message.from_user.id
        cash_result = await db.get_cash(user_id)  # Ожидаем выполнение корутины и сохраняем результат
        balance = int(cash_result[0][0])

        await message.answer(f"""
✅Источники успешно добавлены:
{links}
💻-Совокупно после парсинга мы получим {members_count} новых подписчиков - (Услуга входит в стоимость аренды аккаунтов)""")
        if (cost * accounts) > balance:
            await message.answer("У вас недостаточно средств для совершение услуги", reply_markup=kb.popolnit)
            await state.finish()
        else:
            await message.answer(f"""
Добавьте сколько вам нужно аккаунтов
🔸 Ваш общий баланс: {balance}
🔹Будет списано: {cost * accounts} рублей 
🤖Вы выбрали {accounts} аккаунтов

💰Цена за 1 аккаунта 50 руб./месяц
➕Включено: прокси, сервер, парсинг базы и страховка от бана  арендованного вами аккаунта!
⚠Один аккаунт  безопасно для всех интайтит от 3 до 5 юзеров в вышу группу в день! 

🤩1 аккаунт за 50 руб. = 100-150 инвайтов в месяц🤩""", reply_markup=kb.popolnit)
            deposite = int(cost * accounts) * -1
            await state.finish()
            date_obj = datetime.today().strftime('%d.%m.%Y 12:00:00')
            print(date_obj)
            print(type(int(data['accounts'])))
            await send_admin(message, user_id, data['link'], data['links'], data['accounts'], date_obj, deposite)
            await message.answer(
                (await db.add_group(user_id, data['link'], links, data['accounts'], date_obj, deposite)))
            # await db.cash(deposite, user_id)


    else:
        await message.reply('Не правильная ссылка или формат3')
        await NewGroup.previous()


async def send_admin(message, user_tg_id, link, links, account, date_obj, deposite):
    admins = await db.get_admins()
    print(admins, 9387)
    admin_check = InlineKeyboardMarkup()
    ac = InlineKeyboardButton('Принять', callback_data=f'accept_{user_tg_id}_{link}_{deposite}')
    re = InlineKeyboardButton('Отказать', callback_data=f'reject_{user_tg_id}_{link}_{deposite}')
    admin_check.row(ac, re)
    for admin in admins:
        admin = admin[0]
        print(admin)
        await bot.send_message(admin, text=f"""
Клиент: @{message.from_user.username}
Группа/канал: {link}
Источник юзеров: {links}
Выбрано аккаунтов: {account}""", reply_markup=admin_check)


@dp.message_handler(text='''Ваша компание не прошла модерацию.
Пожалуйста найстройте заново или напишите саппорту''')
async def accept_group(message):
    user_id = message.from_user.id


@dp.callback_query_handler(lambda call: call.data.startswith('select_'))
async def callback_handler(call: CallbackQuery):
    group = call.data.split('_')[1]
    print(group)
    info = await db.get_info_group(group)
    group_options = InlineKeyboardMarkup()
    process_b = InlineKeyboardButton('Пауза/Запустить инвайт', callback_data=f'process_{group}')
    delete_b = InlineKeyboardButton('Удалить инвайт', callback_data=f'delete_{group}')
    change_b = InlineKeyboardButton('Настроить заново', callback_data=f'change_{group}')
    popolnit = InlineKeyboardButton('Пополнить баланс', callback_data=f'popolnit')
    main_menu = InlineKeyboardButton('На главное', callback_data=f'menu')
    group_options.add(process_b, delete_b, change_b, popolnit, main_menu)
    if group:
        await call.message.answer(info, reply_markup=kb.group_options)
    else:
        await call.message.answer('Такой группы в Базе данных нет')


@dp.callback_query_handler(lambda call: call.data.startswith('process_'))
async def process(call: CallbackQuery):
    group = int(call.data.split('_')[1])
    user_id = call.message.from_user.id
    await db.change_proccess(user_id, group)


@dp.callback_query_handler(lambda call: call.data.startswith('delete_'))
async def delete(call: CallbackQuery):
    group = int(call.data.split('_')[1])
    user_id = call.message.from_user.id
    await db.delete_group(user_id, group)


@dp.callback_query_handler(lambda call: call.data.startswith('change_'))
async def process(call: CallbackQuery):
    group = call.data.split('_')[1]
    await call.message.answer('Введите новые данные')
    await new_group(call.message)


@dp.message_handler(commands=['id'])
async def cmd_id(message: types.Message):
    await message.answer(f'ID: {message.from_user.id}')


@dp.message_handler(commands=['accounts'])
async def invite_group(message: types.Message):
    accounts = await db.get_accounts_from_db()
    print(accounts)
    for account in accounts:
        await message.answer(f"""
api_id:{account['api_id']}
api_hash:{account['api_hash']}
phone:{account['phone']}
session:{account['session_tg']}""")


async def check_group(message: types.Message, link):
    if 't.me' in link:
        chat_id = link.split('/')[-1]
        if chat_id.startswith('+'):
            chat_id = chat_id[1:]
        elif chat_id.startswith('@'):
            chat_id = chat_id[1:]
        else:
            chat_id = f"@{chat_id}"
    else:
        await message.reply("Неправильная ссылка или такой группы не существет", reply_markup=kb.cancel)
        return None

    try:
        chat = await bot.get_chat(chat_id)
        print(chat_id, chat.type)
        if chat.type in ['group', 'supergroup', 'channel']:
            # await message.reply(f"Группа {chat.title} успешно добавлена!")
            return True
        else:
            await message.reply("В эту группу/канал невозможно добавлять новых юзеров1")
            return False
    except ChatNotFound:
        await message.reply("В эту группу/канал невозможно добавлять новых юзеров. ChatNotFound")
        return False
    except Exception as e:
        await message.reply(f"В эту группу/канал невозможно добавлять новых юзеров. Ошибка: {str(e)}")
        return False


@dp.message_handler(text='Пополнить баланс')
@dp.callback_query_handler(text="popolnit")
async def replenish(call):
    try:
        message = call.message
    except:
        message = call
        user_id = message.from_user.id
        cash_result = await db.get_cash(user_id)
        if cash_result == []:
            balance = 0
        else:
            balance = cash_result[0][0]
        await message.answer(f'Текущий баланс {balance} руб.', reply_markup=kb.currency)
        await Replenish_balance.currency.set()


@dp.message_handler(state=Replenish_balance.currency)
async def get_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['currency'] = message.text
        print(data['currency'])
    if data['currency'] == 'RUB' or data['currency'] =='USD' or data['currency'] == 'USDT':
        await message.answer(
            f"Введите сумму {data['currency']} которую хотите добавить:\n(минимум 100руб/1$)\nПример: 500")
        await Replenish_balance.next()
    else:
        await message.reply('Не правильно верли валюту')
        await Replenish_balance.previous()



@dp.message_handler(state=Replenish_balance.amount)
async def check_replenish(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = message.text
    try:
        amount = int(data['amount'])
        if isinstance(amount, float or int):
            if data['amount'] < 100 and data['currency'] == 'RUB':
                await message.answer('Вы вели маньше минимума средств, ведите заново сумму\nМинимум 100руб./1$')
                await Replenish_balance.previous()
            elif data['amount'] < 1 and data['currency'] == 'USD':
                await message.answer('Вы вели маньше минимума средств, ведите заново сумму\nМинимум 100руб./1$')
                await Replenish_balance.previous()
            elif data['amount'] < 1 and data['currency'] == 'USDT':
                await message.answer('Вы вели маньше минимума средств, ведите заново сумму\nМинимум 100руб./1$')
                await Replenish_balance.previous()
            else:
                pass
            await message.answer(f"""
    Отправьте: {data['amount']} {data['currency']}
    На счет: 4444 5555 6666 (Сбер)

    Ваш ID: {message.from_user.id}
    *после оплаты оябзательно пришли скрин перевода со своим ID  - @vicm_pro""", reply_markup=kb.main_menu)
            admin_ids = await db.get_admins()
            for id in admin_ids:
                await bot.send_message(id[0], f"Юзер {message.from_user.username}(ID:{message.from_user.id}) хотел пополнить баланс на {data['amount']}{data['currency']}")

            await state.finish()
        else:
            await message.answer("Вы не правильно вели сумма, ведите только целое число")
            await Replenish_balance.previous()
    except:
        await message.answer("Вы не правильно вели сумму, ведите только целое число")
        await Replenish_balance.previous()


async def weekly_report():
    sent_notifications = set()
    while True:
        try:
            groups = await db.get_groups()
            dates = await db.get_date()

            for date in dates:
                print(date)
                for project in groups:
                    deadline_date = datetime.strptime(date[0], '%Y-%m-%d %H:%M:%S')
                    current_time = datetime.now()
                    days_left = (current_time - deadline_date).days
                    group_id, project_name, _, _ = project

                    if days_left == 7 and group_id not in sent_notifications:
                        group = await db.get_info_group(group_id)
                        mess = await bot.send_message(975713395,
                                                      f"""Отчет за неделю!
🔸{group[2]}
🤖 - {group[4]}
➕ за неделю добавлено {group[5]} юзеров
🔜 на следующей неделе ожидается {group[6]}""")
                        sent_notifications.add(group_id)
                        print("Отправка сообщения:", mess)

                    elif days_left < 7 and group_id not in sent_notifications:
                        pass
                    else:
                        print("qwe")
        except Exception as e:
            print("Ошибка при отправке отчета:", e)
        await asyncio.sleep(3600)


loop = asyncio.get_event_loop()
loop.create_task(weekly_report())

@dp.callback_query_handler(text="support")
async def support(call):
    await call.message.answer('Напишите нашему специалисту - @vicm_pro', kb.main_menu)


@dp.message_handler(text='На главную')
@dp.callback_query_handler(text="menu")
async def back_to_main_menu(call):
    await cmd_start_user(call.message)


class Announcement(StatesGroup):
    message_text = State()

class Account(StatesGroup):
    api_id = State()
    api_hash = State()
    phone = State()
    code = State()

class Proxy(StatesGroup):
    addr = State()
    port = State()
    name = State()
    password = State()


def admin_access(func):
    async def wrapper(message: types.Message):
        user_id = str(message.from_user.id)
        if await db.check_admin(user_id):
            await message.answer('Вы админ')
            await func(message)
        else:
            await message.answer('У вас нету доступа')
    return wrapper

@admin_access
@dp.message_handler(commands=['add'])
async def add_cash(message: types.Message):
    print(message.text.split(' '))
    user_id = message.text.split(' ')[1]
    cash = message.text.split(' ')[2]
    await db.cash(cash, user_id)
    await message.answer("Изменения баланса внесены")

@admin_access
@dp.message_handler(commands=['adminka'])
async def cmd_start_admin(message: types.Message):
    await message.answer_sticker('CAACAgIAAxkBAAEDZuVlx6DBQry15wn4Z03CwXTln4sWewAC2A8AAkjyYEsV-8TaeHRrmDQE')
    await message.answer(f'{message.from_user.first_name}, добро пожаловать в InviteBot!')
    await message.answer(await db.get_info_admin(), reply_markup=kb.adminka)

@admin_access
@dp.message_handler(commands=['adminka_on'])
async def add_admin(message: types.Message):
    try:
        user_id = int(message.text.split(' ')[1])
        if await db.check_admin(user_id) is not True:
            await db.add_admin(user_id)
            await message.answer('Админ добавлен')
        else:
            await message.answer('Админ уже существует')
    except (IndexError, ValueError):
        await message.answer('Попробуйте еще раз, указав правильный ID')

@admin_access
@dp.message_handler(commands=['adminka_off'])
async def remove_admin(message: types.Message):
    try:
        user_id = int(message.text.split(' ')[1])
        print(user_id)
        if await db.check_admin(user_id):
            await db.remove_admin(user_id)
            await message.answer('Админ удален')
        else:
            await message.answer('Такого админа в БД нет')
    except (IndexError, ValueError):
        await message.answer('Попробуйте еще раз, указав правильный ID')

@admin_access
@dp.message_handler(text='Сделать объявления')
async def handle_announcement_initiation(message: types.Message):
    await message.answer("Напишите текст для рассылки:")
    await Announcement.message_text.set()



@dp.message_handler(state=Announcement.message_text)
async def receive_announcement(message: types.Message, state: FSMContext):
    announcement_text = message.text
    user_ids = await db.get_user()
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, announcement_text)
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
    await message.answer("Рассылка отправлена")
    await state.finish()

@admin_access
@dp.callback_query_handler(lambda call: call.data.startswith('accept_'))
async def accept_group(call):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    user_id = int(call.data.split('_')[1])
    group_name =call.data.split('_')[2]
    deposite = call.data.split('_')[3]
    print(group_name, 421243)
    await bot.send_message(user_id, """
Модерация прошла успешно.
Инвайт запущен
Каждые 7 дней вы будете получать отчет за неделю""", reply_markup=kb.main_menu)
    await db.accept_group(user_id, group_name)
    await db.cash(deposite, user_id)

@admin_access
@dp.callback_query_handler(lambda call: call.data.startswith('cancel_'))
async def cancel_group(call):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    user_id = int(call.data.split('_')[1])
    group_name = call.data.split('_')[2]
    print(group_name, 421243)
    await bot.send_message(user_id, """
Ваша компание не прошла модерацию.
Пожалуйста найстройте заново или напишите саппорту""", reply_markup=kb.main_menu)

@admin_access
@dp.message_handler(commands=['cash'])
async def add_cash(message: types.Message):
    print(message.text.split(' '))
    user_id = message.text.split(' ')[1]
    cash = message.text.split(' ')[2]
    await db.cash(cash, user_id)
    await message.answer("Изменения баланса внесены")

@admin_access
@dp.message_handler(commands=['accounts'])
async def cmd_accounts(message: types.Message):
    await message.answer(await db.get_accounts_from_db())

@admin_access
@dp.message_handler(text='Добавить аккаунты')
async def add_account(message: types.Message):
    await message.answer('Введите API ID:')
    await Account.api_id.set()


@dp.message_handler(state=Account.api_id)
async def api_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_id'] = int(message.text)
    await message.answer("Введите API HASH:")
    await Account.next()


@dp.message_handler(state=Account.api_hash)
async def api_hash(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_hash'] = message.text
    await message.answer('Введите номер аккаунта: \nПример: +996998123456')
    await Account.next()


@dp.message_handler(state=Account.phone)
async def phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text
    if data['phone'][0] == "+":
        await Account.next()
    else:
        await message.answer('Вы не правильно ввели номер, введите как в примере')
        await state.reset_state()

    # Создаем экземпляр бота для отправки сообщений
    bot = message.bot

    # Подключаемся к Telegram с использованием введенного номера телефона
    client = TelegramClient(data['phone'], int(data['api_id']), data['api_hash'])

    try:
        await client.connect()

        # Проверяем, авторизован ли пользователь
        if not await client.is_user_authorized():
            # Если нет, запрашиваем код подтверждения
            await client.send_code_request(data['phone'])
            await bot.send_message(message.chat.id, "Код подтверждения отправлен. Введите код подтверждения:")
            await Account.code.set() # Переходим к следующему состоянию
        else:
            await message.answer("Пользователь уже авторизован.")
            await state.finish()  # Завершаем состояние
            return

    except Exception as e:
        await message.answer(f"Ошибка при подключении к Telegram: {e}")
        await state.finish()  # Завершаем состояние
        return


@dp.message_handler(state=Account.code)
async def code_confirmation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['code'] = int(message.text)
        print(data['code'])
        session = f'./bot/session_accounts/{data["phone"]}.session'

    # Создаем экземпляр бота для отправки сообщений
    # bot = message.bot
    print((data['api_id'], data['api_hash'], session))
    await message.answer((data['api_id'], data['api_hash'], session))
    print(1234)
    if data['code'] == '.':
        print(1000101010010)
        await Account.previous()
    try:
        async with TelegramClient(session, int(data['api_id']), data['api_hash']) as client:
            print(4321)
            await client.connect()
            print(11111)
            # Подтверждаем код подтверждения
        if not await client.is_user_authorized():
            await client.sign_in(data['phone'], data['code'])
            print(2222)
            await message.answer(f"Вы успешно авторизовали аккаунт {data['phone']}.")
            print(333)
            await db.add_account(data['api_id'], data['api_hash'], data['phone'], session)

    except Exception as e:
        await message.answer(f"Ошибка при подтверждении кода: {e}")

    await state.finish()  # Завершаем состояние

@admin_access
@dp.message_handler(commands=['proxy'])
async def add_proxy(message: types.Message):
    await message.answer(await db.get_proxies_from_db())

@admin_access
@dp.message_handler(text='Добавить прокси')
async def add_proxy(message: types.Message):
    await message.answer('Введите адрес прокси (IP или доменное имя):')
    await Proxy.addr.set()

@dp.message_handler(state=Proxy.addr)
async def proxy_addr(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['addr'] = message.text
    await message.answer("Введите порт прокси:")
    await Proxy.port.set()  # Устанавливаем следующее состояние

@dp.message_handler(state=Proxy.port)
async def proxy_port(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['port'] = int(message.text)
    await message.answer('Введите имя пользователя для прокси (или оставьте пустым, если не требуется):')
    await Proxy.name.set()  # Устанавливаем следующее состояние

@dp.message_handler(state=Proxy.name)
async def proxy_username(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text
    await message.answer('Введите пароль для прокси (или оставьте пустым, если не требуется):')
    await Proxy.password.set()  # Устанавливаем следующее состояние

@dp.message_handler(state=Proxy.password)
async def proxy_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['password'] = message.text

    # Проверяем работоспособность прокси
    try:
        # Настройки прокси
        proxy = {
            'proxy_type': 'socks5',  # Тип прокси (http, socks5, etc.)
            'addr': data['addr'],
            'port': data['port'],
            'username': data['username'],
            'password': data['password']
        }
        proxies = await db.get_proxies_from_db()
        count_proxy = int(len(proxies))
        session_proxy = f'./bot/session_proxy/proxy_{count_proxy+1}'

        # Создаем экземпляр клиента Telegram с прокси
        client = TelegramClient(session_proxy, 'api_id', 'api_hash', proxy=proxy)
        await client.connect()

        if await client.is_user_authorized():
            await db.add_proxy(state)
            await message.answer('Прокси успешно добавлен и проверен.')
        else:
            await message.answer('Не удалось авторизоваться через этот прокси.')

        await client.disconnect()

        # Сохраняем прокси в базе данных
        # db.add_proxy(data['addr'], data['port'], data['username'], data['password'])
        await message.answer('Прокси добавлен в базу данных.')

    except Exception as e:
        await message.answer(f'Ошибка при подключении через прокси: {e}')
    await state.finish()  # Завершаем FSMContext


@dp.message_handler(text='На главную')
@dp.callback_query_handler(text="menu")
async def back_to_main_menu(call):
    try:
        message = call.message
    except:
        message = call
        if check_role() == 'admin':
            await cmd_start_admin(message)
        else:
            await cmd_start_user(message)


@dp.message_handler(text=['Назад', 'Отменить'])
@dp.callback_query_handler(text="cancel")
async def back(call):
    try:
        message = call.message
    except:
        message = call
        if check_role() == 'admin':
            await cmd_start_admin(message)
        else:
            await cmd_start_user(message)

@dp.message_handler()
async def answer(message: types.Message):
    await message.reply('Я тебя не понимаю')


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
