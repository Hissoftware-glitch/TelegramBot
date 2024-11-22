import telebot
import schedule
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand

bot  = telebot.TeleBot('7765227220:AAFvzmET2L4chFc9DCCoajqI19_y727HgyM')
def create_db():    #База данных
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    #создаем таблицу
    cur.execute("""
    CREATE TABLE IF NOT EXISTS votes (
    id integer primary key autoincrement,
    user_id integer not null,
    user_name text,
    team_id integer not null,
    energy_level integer not null,
    vote_date date not null
    )""")

    cur.execute("""
    create table if not exists teams (
    team_id integer primary key autoincrement,
    manager_id integer not null,
    team_name text
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

def generate_recommendations(average_energy):
    if average_energy >= 8:
        return '✅ Отличный уровень энергии! Продолжайте в том же духе!'
    elif 5 <= average_energy < 8:
        return ("⚖️ Уровень энергии средний. Обратите внимание, чтобы нагрузка на команду была сбалансированной. "
                "Возможно, стоит провести тимбилдинг или организовать перерыв.")
    elif average_energy < 5:
        return ("❌ Низкий уровень энергии. Проверьте, не перегружена ли команда, и рассмотрите возможность уменьшения "
                "нагрузки или предоставления дополнительного времени для отдыха.")
    else:
        return 'Нет данных для анализа'


def send_reminder():
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM votes")  # получаем всех пользователей зарегистрированных для голосования
    users = cur.fetchall()

    for user in users:
        user_id = user[0]
        bot.send_message(user_id, "Напоминание: Пожалуйста, не забудьте проголосовать!")

    cur.close()
    conn.close()
def job():
    send_reminder()

# Напоминалка
schedule.every().day.at("10:00").do(job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Отденльный поток
threading.Thread(target=run_scheduler, daemon=True).start()

@bot.message_handler(commands=['start'])
def start(message):
    create_db()
    bot.send_message(message.chat.id, f'Привет, я бот для отслеживания энергии команды, если хочешь проголосовать не забудь сначала зарегистрироваться в команде!')
    bot.set_my_commands([
        BotCommand('start', 'Запустить бота'),
        BotCommand('vote', 'Запускает голосование'),
        BotCommand('reg', 'Регистрация в команде'),
        BotCommand('changeteam', 'Сменить команду'),
        BotCommand('stats', 'Статистика'),
        BotCommand('mystats', 'Твоя статистика'),
        BotCommand('statsteams', 'Статистика по командам'),
        BotCommand('regman', 'Регистрация для менеджера'),
        BotCommand('manteams','Управление командами')
    ])

@bot.message_handler(commands=['vote'])
def voting(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*[str(i) for i in range(1,11)])
    msg = bot.send_message(message.chat.id, 'Как ты себя чувствуешь от 1 до 10?', reply_markup=markup)
    bot.register_next_step_handler(msg, save_vote)

def save_vote(message):
    score = message.text
    if not (score.isdigit() and 1 <= int(score) <=10):
        bot.reply_to(message, 'Пожалуйста, отправьте число от 1 до 10')
    else:
        user_id = message.from_user.id
        team_id = get_user_team(user_id)

        if team_id is None:
            bot.reply_to(message, 'Вы не состоите в команде. Зарегистрируйтесь через /reg, чтобы проголосовать.')
        else:
            user_name = message.from_user.username
            date = datetime.now().strftime('%Y-%m-%d')
            save_to_db(message, user_id, user_name, team_id, score, date)
            bot.reply_to(message, 'Записал ваш голос, спасибо!')

def save_to_db(message, user_id, user_name, team_id, score, date):
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("insert into votes (user_id, user_name, team_id, energy_level, vote_date) values (?, ?, ?, ?, ?)",(user_id, user_name, team_id, score, date))
    conn.commit()
    conn.close()

@bot.message_handler(commands=['stats'])
def statistic(message):
    user_id = message.from_user.id
    if is_manager(user_id):
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        queries = {
            'Всё время': """
            select v.user_id, v.user_name, t.team_name, avg(v.energy_level)
            from votes v
            join teams t on v.team_id = t.team_id
            group by v.user_id, v.user_name, t.team_name
            """,
            'Последнюю неделю': """
            select v.user_id, v.user_name, t.team_name, avg(v.energy_level)
            from votes v
            join teams t on v.team_id = t.team_id
            where vote_date >= date('now', '-7 days')
            group by v.user_id, v.user_name, t.team_name
            """,
            'Сегодня': """
            select v.user_id, v.user_name, t.team_name, avg(v.energy_level)
            from votes v
            join teams t on v.team_id = t.team_id
            where vote_date >= date('now')
            group by v.user_id, v.user_name, t.team_name
            """
        }

        info = 'Статистика по участникам:\n'
        for period, query in queries.items():
            cur.execute(query)
            stats = cur.fetchall()
            info += f'\n--- {period} ---\n'
            for user_id, user_name, team_name, avg_score in stats:
                user_name = user_name if user_name else 'Без имени'
                recommendation = generate_recommendations(avg_score)
                info += (f'<b>ID Пользователя:</b> {user_id}\n'
                         f'<b>Имя пользователя:</b> {user_name}\n'
                         f'<b>Команда:</b> {team_name}\n'
                         f'<b>Средний уровень энергии:</b> {avg_score:.2f}\n'
                         f'<b>Рекомендация:</b> {recommendation}\n\n')
        cur.close()
        conn.close()
        bot.send_message(message.chat.id, info, parse_mode='html')
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к этой команде')

def is_manager(user_id):
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("select manager_id from teams where manager_id = ?", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def get_user_team(user_id):
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("SELECT team_id FROM votes WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None  # Возвращаем team_id или None

@bot.message_handler(commands=['reg'])
def register_employee(message):
    bot.send_message(message.chat.id, 'Введите название команды для регистрации:')
    bot.register_next_step_handler(message, register_team)

def register_team(message):
    team_name = message.text.strip()
    user_id = message.from_user.id
    user_name = message.from_user.username

    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()

    # Поиск команды
    cur.execute("SELECT team_id FROM teams WHERE team_name = ?", (team_name,))
    team = cur.fetchone()

    if team: # Если команда найдена
        team_id = team[0]
        # Проверка зарегистрирован ли уже челик
        cur.execute("SELECT * FROM votes WHERE user_id = ?", (user_id,))
        if cur.fetchone(): #Уже зареган
            bot.reply_to(message, 'Вы уже зарегистрированы в команде. Чтобы сменить команду, используйте /changeteam')
        else: # Ещё не зареган
            cur.execute(
                "INSERT INTO votes (user_id, user_name, team_id, energy_level, vote_date) VALUES (?, ?, ?, ?, ?)",(user_id, user_name, team_id, 0, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            bot.reply_to(message, f'Вы успешно зарегистрированы в команде "{team_name}"')
    else: #Команда не найдена
        bot.reply_to(message, f'Команда "{team_name}" не найдена. Пожалуйста, проверьте название')

    cur.close()
    conn.close()


@bot.message_handler(commands=['changeteam'])
def change_team(message):
    bot.send_message(message.chat.id, 'Введите новое название команды для смены:')
    bot.register_next_step_handler(message, change_user_team)


def change_user_team(message):
    new_team_name = message.text.strip()
    user_id = message.from_user.id

    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()

    # Проверка существования новой команды
    cur.execute('SELECT team_id FROM teams WHERE team_name = ?', (new_team_name,))
    team = cur.fetchone()

    if team:
        team_id = team[0]
        # Обновление команды пользователя
        cur.execute('UPDATE votes SET team_id = ? WHERE user_id = ?', (team_id, user_id))
        conn.commit()
        bot.reply_to(message, f'Вы успешно сменили команду на "{new_team_name}"')
    else:
        bot.reply_to(message, f'Команда "{new_team_name}" не найдена. Пожалуйста, проверьте название')

    cur.close()
    conn.close()

@bot.message_handler(commands=['manteams'])
def manage_teams(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("SELECT team_name FROM teams")
    teams = cur.fetchall()
    conn.close()
    if is_manager(user_id):
        teams_list = "\n".join([f"- {team[0]}" for team in teams])
        bot.send_message(message.chat.id, f'Список существующих команд:\n{teams_list}\n\nВыберите действие:\n1. Добавить команду: /addteam\n2. Удалить команду: /removeteam')
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к этой команде')

@bot.message_handler(commands=['addteam'])
def add_team(message):
    bot.send_message(message.chat.id, 'Введите название новой команды:')
    bot.register_next_step_handler(message, save_new_team)

def save_new_team(message):
    team_name = message.text.strip()
    user_id = message.from_user.id

    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("INSERT INTO teams (manager_id, team_name) VALUES (?, ?)", (user_id, team_name))
    conn.commit()
    bot.reply_to(message, f'Команда "{team_name}" успешно добавлена')
    cur.close()
    conn.close()

@bot.message_handler(commands=['removeteam'])
def remove_team(message):
    bot.send_message(message.chat.id, 'Введите название команды для удаления:')
    bot.register_next_step_handler(message, delete_team)


def delete_team(message):
    team_name = message.text.strip()

    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("DELETE FROM teams WHERE team_name = ?", (team_name,))
    if cur.rowcount > 0:
        conn.commit()
        bot.reply_to(message, f'Команда "{team_name}" успешно удалена')
    else:
        bot.reply_to(message, f'Команда "{team_name}" не найдена')

    cur.close()
    conn.close()

@bot.message_handler(commands=['statsteams'])
def statistic_teams(message):
    user_id = message.from_user.id
    if is_manager(user_id):
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        queries = {
            'Всё время': """
                        SELECT t.team_name, AVG(v.energy_level)
                        FROM votes v
                        JOIN teams t ON v.team_id = t.team_id
                        GROUP BY t.team_name
                    """,
            'Последнюю неделю': """
                        SELECT t.team_name, AVG(v.energy_level)
                        FROM votes v
                        JOIN teams t ON v.team_id = t.team_id
                        WHERE vote_date >= DATE('now', '-7 days')
                        GROUP BY t.team_name
                    """,
            'Сегодня': """
                        SELECT t.team_name, AVG(v.energy_level)
                        FROM votes v
                        JOIN teams t ON v.team_id = t.team_id
                        WHERE vote_date = DATE('now')
                        GROUP BY t.team_name
                    """
        }
        info = 'Статистика по командам: \n'
        for period, query in queries.items():
            cur.execute(query)
            stats = cur.fetchall()
            info += f'\n--- {period} --\n'
            for team_name, avg_score in stats:
                recommendation = generate_recommendations(avg_score)
                info += (f'<b>Команда:</b> {team_name}\n'
                         f'<b>Средний уровень энергии:</b> {avg_score:.2f}\n'
                         f'<b>Рекомендации:</b> {recommendation}\n')

        cur.close()
        conn.close()
        bot.send_message(message.chat.id, info, parse_mode='html')
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к этой команде')

@bot.message_handler(commands=['mystats'])
def personal_stats(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("""
            SELECT AVG(energy_level), COUNT(*)
            FROM votes
            WHERE user_id = ?
        """, (user_id,))
    avg_score, total_votes = cur.fetchone()
    conn.close()
    if avg_score:
        bot.send_message(message.chat.id, f"Ваша средняя энергия: {avg_score:.2f}\nВсего голосов: {total_votes}")
    else:
        bot.send_message(message.chat.id, "У вас пока нет голосов")


@bot.message_handler(commands=['regman'])
def register_manager(message):
    bot.send_message(message.chat.id, 'Введите секретный пароль для регистрации менеджера:')
    bot.register_next_step_handler(message, verify_secret_key)

def verify_secret_key(message):
    secret_key = 'Пароль'
    user_id = message.from_user.id
    team_name = "Админы" #команда для админов
    if message.text.strip() == secret_key:
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()
        cur.execute("select * from teams where manager_id = ?", (user_id,))
        if cur.fetchone():
            bot.reply_to(message, 'Вы уже зарегистрированы как менеджер')
        else:
            cur.execute('insert into teams (manager_id, team_name) values (?, ?)', (user_id, team_name))
            conn.commit()
            bot.reply_to(message,f'Поздравляю вы зарегестрированы как менеджер команды "{team_name}"')

        cur.close()
        conn.close()
    else:
        bot.reply_to(message, 'Неверный пароль попробуйте снова через /regman')

#Тестовые данные
@bot.message_handler(commands=['debug'])
def debug(message):
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    test_data = [
    (1, 'User1', 1, 7, (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d')),
    (2, 'User1', 1, 6, (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')),
    (3, 'User1', 1, 9, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')),
    (4, 'User1', 2, 8, datetime.now().strftime('%Y-%m-%d'))
]
    cur.executemany("INSERT INTO votes (user_id, user_name, team_id, energy_level, vote_date) VALUES (?, ?, ?, ?, ?)", test_data)
    conn.commit()

# Проверяем вставленные данные
    cur.execute("SELECT * FROM votes")
    rows = cur.fetchall()
    print("Тестовые данные:", rows)

    cur.close()
    conn.close()


#чтобы бот не прекращал работу
bot.infinity_polling()