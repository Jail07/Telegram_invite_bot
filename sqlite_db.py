import sqlite3 as sq
from datetime import datetime

db = sq.connect('./tg.db')
cur = db.cursor()

async def db_start():
    global db, cur
    db = sq.connect('./tg.db')
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER)""")
    cur.execute("CREATE TABLE IF NOT EXISTS user("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "tg_id INTEGER,"
                "all_rent_account INTEGER,"
                "cash INTEGER)")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    own_id_tg INTEGER,
    name_group TEXT,
    from_groups TEXT,
    accounts INTEGER,
    added_user INTEGER,
    will_add_user INTEGER DEFAULT 0,
    date_start DATA,
    deposite INTEGER,
    accept BOOLEAN DEFAULT FALSE,
    process BOOLEAN DEFAULT False)""")
    # cur.execute("""CREATE TABLE IF NOT EXISTS account(
    # id INTEGER PRIMARY KEY AUTOINCREMENT,
    # own_id_tg INTEGER,
    # status BOOLEAN DEFAULT FALSE,
    # group_id INTEGER,
    # FOREIGN KEY (group_id) REFERENCES groups(id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS user_groups(
        user_id INTEGER,
        group_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES groups(id),
        FOREIGN KEY(group_id) REFERENCES user(id)
    );
    """)

    cur.execute("""CREATE TABLE IF NOT EXISTS group_accounts(
    group_id INTEGER,
    account_id INTEGER,
    FOREIGN KEY(account_id) REFERENCES accounts(id),
    FOREIGN KEY(group_id) REFERENCES groups(id))""")


    cur.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            api_id INTEGER NOT NULL,
            api_hash TEXT NOT NULL,
            session_tg TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0
        )
        ''')

    cur.execute("""
    CREATE TABLE IF NOT EXISTS queue(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        count_account INTEGER NOT NULL,
        date DATE NOT NULL)""")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            addr TEXT NOT NULL,
            port INTEGER NOT NULL,
            username TEXT,
            password TEXT
        )
        ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS account_proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            proxy_id INTEGER NOT NULL,
            FOREIGN KEY(account_id) REFERENCES accounts(id),
            FOREIGN KEY(proxy_id) REFERENCES proxies(id)
        )
        ''')
    cur.execute("""CREATE TABLE IF NOT EXISTS announcements (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            message TEXT,
                            sent INTEGER DEFAULT 0
                        )""")
    # cur.execute("INSERT INTO accounts(api_id, api_hash, session_accounts, is_active) VALUES (?, ?, ?, ?)",
    #             )
    bind_accounts_to_proxies()

    # cur.execute("INSERT INTO admins (tg_id) VALUES (?)", (7077796572,))
    db.commit()

async def check_admin(tg_id):
    cur.execute("SELECT tg_id FROM admins")
    admins = cur.fetchall()
    for admin in admins:
        if int(admin[0]) == int(tg_id):
            return True
        else:
            pass
    return False


async def accept_group(tg_id, link):
    cur.execute("UPDATE groups SET accept = ? AND process=? WHERE own_id_tg = ? AND name_group=?", (True, True, tg_id, link,))
    db.commit()

async def add_admin(tg_id):
    cur.execute(f"INSERT INTO admins(tg_id) VALUES({tg_id})")
    db.commit()


async def remove_admin(tg_id):
    cur.execute("DELETE FROM admins WHERE tg_id = ?", (tg_id,))
    db.commit()

async def delete_group(id, group_name):
    cur.execute("SELECT deposite, own_id_tg FROM groups WHERE id = ?", (id,))
    dep = cur.fetchall()[0][0]
    tg_id = cur.fetchall()[0][1]
    print(dep, 9834798759327594375)
    await cash(dep, tg_id)
    cur.execute("DELETE FROM groups WHERE id=? AND name_group=?", (id, group_name,))
    db.commit()

async def change_proccess(id, group_name):
    cur.execute("SELECT proccess FROM groups WHERE id = ? AND name_group=?", (id, group_name,))
    process = cur.fetchall()[0]
    if process == True:
        cur.execute("UPDATE groups SET process=? WHERE id = ? AND name_group=?", (False, id, group_name,))
    elif process == False:
        cur.execute("UPDATE groups SET process=? WHERE id = ? AND name_group=?", (True, id, group_name,))
    else:
        print(process)
    db.commit()


async def cancel_group(tg_id):
    try:
        cur.execute("SELECT id, name_group FROM groups WHERE own_id_tg = ? AND accept = ? ", (tg_id, False))
        groups = cur.fetchall()
        # print(name_group)
        if groups == None or len(groups) == 0:
            return None
        else:
            return groups

        print(name_group)
        # return [row for row in name_group]
    except RuntimeWarning:
        pass

async def get_admins():
    cur.execute("SELECT tg_id FROM admins")
    admins = cur.fetchall()
    print(admins)
    return admins

async def get_user():
    cur.execute("SELECT tg_id FROM user")
    user = cur.fetchall()
    print(user)
    return user

async def get_info_admin():
    cur.execute("SELECT * FROM groups WHERE accept=?", (True,))
    groups_ids = cur.fetchall()
    count_groups = len(groups_ids)
    cur.execute("SELECT id FROM accounts")
    accounts = cur.fetchall()
    accounts = len(accounts)
    cur.execute("SELECT id FROM accounts Where is_active = ? ", (True,))
    active_accounts = len(cur.fetchall())

    cur.execute("SELECT accounts FROM groups")
    rent_account = cur.fetchall()
    count_account = 0
    for i in rent_account:
        count_account += int(i[0])
    proxies = (int(count_account - accounts) / 2)
    if accounts//2 !=0:
        proxies += 1
    return f"""
Бот запущен: {count_groups} клиентов
На сервере: {accounts} акк.
Клиенты ждут: {count_account-accounts} акк.
Требуется : {proxies} прокси   
В работе у юзеров: {active_accounts} акк."""

async def add_user(tg_id, rent_account, cash):
        cur.execute("INSERT INTO user (tg_id, all_rent_account, cash) VALUES (?, ?, ?)",
                    (tg_id, rent_account, cash))
        db.commit()

async def add_group(tg_id, your_group, from_groups, rent_account, date, deposite):
    check = True
    try:
        cur.execute("SELECT id FROM groups WHERE own_id_tg = ? AND name_group=?",(tg_id, your_group,))
        id = cur.fetchall()[0]
        await delete_group(tg_id, your_group)
        cur.execute(
            "INSERT INTO groups(own_id_tg, name_group, from_groups, accounts, added_user, date_start, deposite) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tg_id, your_group, from_groups, rent_account, 0, date, deposite))
        db.commit()
        cur.execute(f"""SELECT id FROM groups WHERE name_group = '{your_group}'""")
        group_id = cur.fetchall()[0]
        print(group_id, 348756348925634)
        cur.execute("""INSERT INTO user_groups (user_id, group_id) VALUES (?, ?)""",
                    (tg_id, group_id))
        await cash(deposite, tg_id)
        # check = await check_free_account(rent_account, group_id, tg_id, date)
        if check:
            return """Ваши изменения сохранены, ждите принятия модератора"""
        else:
            return """Ваши изменения сохранены, ждите принятия модератора и свободных аккаунтов(это займет 1-2часа)"""
        db.commit()

    except:
        cur.execute(
            "INSERT INTO groups(own_id_tg, name_group, from_groups, accounts, added_user, date_start, deposite) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tg_id, your_group, from_groups, rent_account, 0, date, deposite))
        db.commit()
        cur.execute(f"""SELECT id FROM groups WHERE name_group = '{your_group}'""")
        group_id = cur.fetchone()[0]
        print(group_id, 348756348925634)
        cur.execute("""INSERT INTO user_groups (user_id, group_id) VALUES (?, ?)""",
                    (tg_id, group_id))
        await cash(deposite, tg_id)
        # check = await check_free_account(rent_account, group_id, tg_id, date)
        if check:
            return """Ваша группа добавлена, ждите принятия модератора"""
        else:
            return """Ваша группа добавлена,, ждите принятия модератора и свободных аккаунтов(это займет 1-2часа)"""
        db.commit()


async def check_free_account(count_account, group_id, tg_id, date):
    cur.execute("SELECT id FROM accounts WHERE is_active = ?", (False,))
    account_ids = cur.fetchall()
    print(account_ids)

    print(tg_id, group_id, count_account, date)

    if len(account_ids) >= int(count_account):
        for i in count_account:
            cur.execute("INSERT INTO group_account(account_id, group_id) VALUES (?,?)",
                    (account_ids[i][0], group_id))
        return True
    else:
        cur.execute("INSERT INTO queue(user_id, group_id, count_account, date) VALUES (?,?,?,?)", (tg_id, group_id, count_account, date))
        return False
    db.commit()



async def check_user(tg_id):
    cur.execute("SELECT * FROM user WHERE tg_id = ?", (tg_id,))
    user = cur.fetchone()
    if user is None:
        await add_user(tg_id, None, 0)
        return False
    else:
        return True


async def cash(cash, id_tg):
    print(cash)
    if cash == 0:
        cur.execute("UPDATE user SET cash = ? WHERE tg_id = ?", (int(cash), id_tg))
    else:
        cur.execute(f"""SELECT cash FROM user WHERE tg_id=?""", (id_tg,))
        cash_or = cur.fetchall()[0][0]
        print(cash_or, 1231)
        add_cash = int(cash_or) + int(cash)
        print(add_cash, 134)
        cur.execute("UPDATE user SET cash = ? WHERE tg_id = ?", (add_cash, id_tg))
        db.commit()

async def return_group(tg_id):
    try:
        cur.execute("SELECT id, name_group FROM groups WHERE own_id_tg = ? AND accept = ? ", (tg_id, True))
        groups = cur.fetchall()
        # print(name_group)
        if groups == None or len(groups) == 0:
            return None
        else:
            return groups

        print(name_group)
        # return [row for row in name_group]
    except RuntimeWarning:
        pass

async def get_groups_from_db():
    cur.execute("SELECT * FROM groups")
    groups = cur.fetchall()
    return groups


async def get_info_group(id):
    try:
        print(id, 39847)
        cur.execute("SELECT * FROM groups WHERE id = ?", (id,))
        group = cur.fetchall()[0]
        print(group)
        if group == None or len(group) == 0:
            print(87648723658346587436583)
            return "Нет информации"
        else:
            return f"""
Отчет за неделю!
🔸{group[2]}
🤖 - {group[4]}
➕ за неделю добавлено {group[5]} юзеров
🔜 на следующей неделе ожидается {group[6]}"""
        print(name_group)

    except RuntimeWarning:
        print('adsjkfhasdkjfhkdsfhjh')


async def get_cash(tg_id):
    cur.execute('SELECT cash FROM user WHERE tg_id =?', (tg_id,))
    cash = cur.fetchall()
    return cash

async def get_groups():
    cur.execute("SELECT * FROM groups")
    groups = cur.fetchall()
    print("Найдены проекты:", groups)
    return groups

async def get_date():
    try:
        cur.execute("SELECT date_start FROM groups WHERE date_start >= DATE('now', '+7 days')")
        dates = cur.fetchall()
        print(dates)
        return dates
    except Exception as e:
        print("Ошибка при проверке даты:", e)


def bind_accounts_to_proxies():
    cur.execute("SELECT id FROM proxies WHERE is_active = 1")
    proxy_ids = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT id FROM accounts WHERE is_active = 1")
    account_ids = [row[0] for row in cur.fetchall()]

    for i in range(0, len(account_ids), 2):
        proxy_id = proxy_ids[i // 2 % len(proxy_ids)]
        cur.execute(
            "INSERT INTO account_proxies (account_id, proxy_id) VALUES (?, ?), (?, ?)",
            (account_ids[i], proxy_id, account_ids[i + 1], proxy_id)
        )
    db.commit()


async def send_notification_to_user(bot, tg_id, message):
    try:
        await bot.send_message(chat_id=tg_id, text=message)
    except Exception as e:
        print(f"Failed to send message to {tg_id}: {str(e)}")


async def get_accounts_from_db():
    cur.execute('SELECT api_id, api_hash, session_tg, phone FROM accounts')
    accounts = cur.fetchall()
    return [{'api_id': api_id, 'api_hash': api_hash, 'session': session_tg, 'phone': phone} for api_id, api_hash, session_tg, phone in accounts]


async def update_account_session(phone, session):
    cur.execute('''
        UPDATE accounts
        SET session_accounts = ?
        WHERE phone = ?
    ''', (session, phone))
    db.commit()

async def add_account(api_id, api_hash, phone, session):
    cur.execute("INSERT INTO accounts(api_id, api_hash, phone, session_accounts=) VALUES (?, ?, ?, ?)",
                (api_id, api_hash, phone, session))
    db.commit()


async def add_proxy(state):
    try:
        async with state.proxy() as data:
            cur.execute("INSERT INTO proxies(addr, port, username, password) VALUES(?, ?, ?, ?)",
                        (data['addr'], data['port'], data['username'], data['password']))
            db.commit()
            print('qwerty')
    except Exception as e:
        print(e)

async def get_proxies_from_db():
    cur.execute('SELECT * FROM proxies')
    proxies = cur.fetchall()
    return proxies




