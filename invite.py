import logging
import json
import re
import random
import asyncio
import datetime
import traceback
from aiogram import Bot
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.types import ChatType
from aiogram.utils import exceptions
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, InputPeerUser
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import UserStatusEmpty
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError
import sqlite_db as db



API_TOKEN = '7106820685:AAEUFXhYrPL7hIVdQPQXuVeWmLA_5MtXOko'


async def on_startup():
    await db.db_start()
    print('Бот запущен!')

# Настройка журнала
logging.basicConfig(level=logging.WARNING)

# Путь к папке с сессиями
folder_session = './session_accounts/'

# Путь к конфигурационному файлу

# Инициализация бота и диспетчера
bot = Bot(API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

async def get_group_info_from_link(client, group_link):
    """Получение информации о группе по ссылке"""
    match = re.match(r'https?://t\.me/([a-zA-Z0-9_]+)', group_link)
    if not match:
        raise ValueError('Некорректная ссылка на группу')

    group_username = match.group(1)
    entity = await client.get_entity(group_username)

    if not isinstance(entity, InputPeerChannel):
        raise ValueError('Указанная ссылка не является ссылкой на группу или канал')

    return {
        'group_id': entity.channel_id,
        'access_hash': entity.access_hash,
        'title': entity.title
    }

async def main():
    await on_startup()
    clients = []

    accounts = await db.get_accounts_from_db()  # Получение данных аккаунтов из базы данных

    if not accounts:
        print("Нет доступных аккаунтов в базе данных.")
        return

    for account in accounts:
        api_id = account['api_id']
        api_hash = account['api_hash']
        session = account['session']
        phone = account['phone']

        client = TelegramClient(folder_session + session, api_id, api_hash)
        await client.connect()

        try:
            if not await client.is_user_authorized():
                print(f'{session} не удалось войти, пожалуйста, авторизуйтесь.')
                await client.start(phone)
                if await client.is_user_authorized():
                    # Обновление сессии в базе данных
                    await db.update_account_session(phone, session)
                else:
                    print(f'{session} не удалось авторизоваться, пропускаем.')
                    continue

            print(f'{session} успешно вошел в систему')

            if await client.is_user_authorized():
                clients.append({
                    'session_accounts': session,
                    'client': client
                })
            else:
                print(f'{session} не удалось войти')

        except Exception as e:
            print(f'Произошла ошибка для аккаунта {session}: {e}')
            continue

    groups = await db.get_groups_from_db()  # Получение данных групп из базы данных
    try:
        for group in groups:
            target_group_link = group['name_group']
            source_group_links = group['from_groups'].split(',')

            for my_client in clients:
                client = my_client['client']

                try:
                    target_group_info = await get_group_info_from_link(client, target_group_link)
                    target_group_entity = InputPeerChannel(target_group_info['group_id'], target_group_info['access_hash'])

                    users = []
                    for source_group_link in source_group_links:
                        source_group_info = await get_group_info_from_link(client, source_group_link)
                        source_group_entity = InputPeerChannel(source_group_info['group_id'], source_group_info['access_hash'])

                        participants = await client.get_participants(source_group_entity)

                        for user in participants:
                            if (not user.bot and
                                not isinstance(user.status, UserStatusEmpty) and
                                not user.deleted and
                                not user.is_self and
                                not user.is_admin and
                                not user.is_creator and
                                user.type == 'user' and
                                user.id not in [admin.user_id for admin in participants.admins]):
                                users.append(user)

                    for user in users:
                        try:
                            print(f"Добавление пользователя: {user.username}")
                            user_to_add = InputPeerUser(user.id, user.access_hash)
                            await client(InviteToChannelRequest(target_group_entity, [user_to_add]))
                            print(f"Успешно добавлен пользователь {user.username}")
                            await asyncio.sleep(random.randint(5, 10))  # Ждем случайное время перед добавлением следующего пользователя
                        except (PeerFloodError, FloodWaitError) as e:
                            print(f"Ошибка: {e}")
                            traceback.print_exc()
                            print(f"Удаление клиента: {my_client['session_accounts']}")
                            await client.disconnect()
                            clients.remove(my_client)
                            continue
                        except UserPrivacyRestrictedError:
                            print("Ошибка: UserPrivacyRestrictedError")
                        except exceptions.BotBlocked:
                            print("Ошибка: BotBlocked")
                        except exceptions.BotKicked:
                            print("Ошибка: BotKicked")
                        except exceptions.ChatNotFound:
                            print("Ошибка: ChatNotFound")
                        except exceptions.UserDeactivated:
                            print("Ошибка: UserDeactivated")
                        except exceptions.MessageToForwardNotFound:
                            print("Ошибка: MessageToForwardNotFound")
                        except exceptions.UserIsBlocked:
                            print("Ошибка: UserIsBlocked")
                        except exceptions.PeerIdInvalid:
                            print("Ошибка: PeerIdInvalid")
                except Exception as e:
                    print(f"Ошибка: {e}")
                    traceback.print_exc()

    except Exception as e:
        print(f"Ошибка при обработке группы {target_group_link}: {e}")
        traceback.print_exc()

    print("Работа завершена.")

if __name__ == "__main__":
    asyncio.run(main())
