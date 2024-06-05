from mailbox import Message

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
# from main import process_message

main = ReplyKeyboardMarkup(resize_keyboard=True)
main.add('Отчет').add('Изменить настройки')

group_options = ReplyKeyboardMarkup(resize_keyboard=True)
group_options.add('Пауза/Запустить инвайт').add('Удалить инвайт').add('Настроить заново').add('Пополнить баланс').add('Назад')

popolnit = InlineKeyboardMarkup()
button_popolnit = InlineKeyboardButton(text='Пополнить баланс', callback_data='popolnit')
popolnit.add(button_popolnit)

currency = ReplyKeyboardMarkup(resize_keyboard=True)
currency.add('RUB').add('USD').add('USDT')

admin_check = InlineKeyboardMarkup()
ac = InlineKeyboardButton('Принять', callback_data='accept')
re = InlineKeyboardButton('Отказать', callback_data='reject')
admin_check.row(ac, re)

reject_select = InlineKeyboardMarkup()
support = InlineKeyboardButton('Написать сапорту', callback_data='support')
menu = InlineKeyboardButton('На главную', callback_data='menu')
reject_select.add(support, menu)

user_kb = ReplyKeyboardMarkup(resize_keyboard=True)
user_kb.add('Добавить новую группу или канал').add('Пополнить баланс')

settings = ReplyKeyboardMarkup(resize_keyboard=True)
settings.add('Добавить аккаунты').add('Добавить группу/канал').add('Отменить')

cancel = InlineKeyboardMarkup()
cancel.add(InlineKeyboardButton('Отменить', callback_data='cancel'))

main_menu = InlineKeyboardMarkup(resize_keyboard=True)
menu = InlineKeyboardButton('На главную', callback_data='menu')
main_menu.add(menu)

adminka = ReplyKeyboardMarkup(resize_keyboard=True)
adminka.add('Добавить аккаунты').add('Добавить прокси').add('Сделать объявления')



# async def create_staff_keyboard():
#     staff_names = await get_staff_names()
#     staff_list = ReplyKeyboardMarkup(resize_keyboard=True)
#
#     for i, staff_name in enumerate(staff_names):
#         staff_list.add(KeyboardButton(f'{staff_name} {i+1}'))
#     staff_list.add('Завершить')
#     return staff_list
