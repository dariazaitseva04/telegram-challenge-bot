import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            challenge_days INTEGER DEFAULT 21,
            current_day INTEGER DEFAULT 1,
            start_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            sport INTEGER DEFAULT 0,
            study INTEGER DEFAULT 0,
            work INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Фразы для напоминаний
PHRASES = {
    'anytime': [
        "Слышал слух, что сегодня идеальный день для выполнения челленджа. Проверим?",
        "Галочки сами себя не поставят! 💪",
        "Просто напоминание: ты способен на большее, чем думаешь.",
        "Не забывай про свою тройную корону! (Спорт, учёба, работа).",
        "Маленькие шаги каждый день приводят к большим результатам. Как твои шаги сегодня?"
    ],
    'lunch': [
        "День в разгаре! Отличный момент зарядиться спортом или запланировать вечернюю учёбу.",
        "Половина дня прошла. Давай проверим, как продвигается твой челлендж?",
        "Обеденный перерыв — идеальное время, чтобы сделать что-то одно из списка. Спорт? Или пара страниц для учёбы?",
        "Не жди вечера! Разгонись уже сейчас, чтобы вечером быть свободным.",
        "Утренняя рутина позади, вечерняя ещё не началась. Самое время вклинить туда спорт или 30 минут учёбы!"
    ],
    'evening': [
        "Финишная прямая! 6 вечера — время закрывать минимум один пункт.",
        "Вечер — твоё время сиять! Спорт, учёба, работа — что следующим будет?",
        "Ужин подождёт? Сначала — маленькая победа в челлендже!",
        "Твой челлендж ещё не в курсе, что ты планируешь его забросить. Исправим это?",
        "Идеальное время для спорта, чтобы разгонать усталость после работы!"
    ],
    'late': [
        "Я смотрю в статистику и вижу... пустоту. Это грустит. 😢",
        "Кажется, твой челлендж сегодня объявил выходной без твоего согласия.",
        "Я верю, что твои невыполненные пункты превратились в суперсилу на завтра. Но лучше бы они просто были выполнены сегодня.",
        "Эй, а что это там за три призрачные задачи в твоём дне? 👻",
        "Напоминание: завтра ты будешь жалеть, что не начал сегодня. Но ещё не полночь! Чудеса случаются!",
        "Твой внутренний Дуолинго-советник в ярости! Он недвусмысленно смотрит на часы. ⏰"
    ]
}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Добавляем пользователя в базу
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name) 
        VALUES (?, ?, ?)
    ''', (user_id, user.username, user.first_name))
    
    conn.commit()
    conn.close()
    
    welcome_text = f"""
Привет, {user.first_name}! 🎯

Я помогу тебе и твоим друзьям пройти челлендж трёх дел:
✅ Спорт
✅ Учёба  
✅ Работа

Команды:
/start - начать
/new_challenge - создать новый челлендж
/today - задачи на сегодня
/remind - отправить напоминалку другу
/stats - статистика

Давай начнём челлендж! Используй /new_challenge
    """
    
    await update.message.reply_text(welcome_text)

# Создание нового челленджа
async def new_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("7 дней", callback_data="challenge_7")],
        [InlineKeyboardButton("21 день", callback_data="challenge_21")],
        [InlineKeyboardButton("30 дней", callback_data="challenge_30")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выбери длительность челленджа:",
        reply_markup=reply_markup
    )

# Обработка выбора длительности
async def challenge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    days = int(data.split('_')[1])
    
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    
    # Обновляем данные пользователя
    cursor.execute('''
        UPDATE users 
        SET challenge_days = ?, current_day = 1, start_date = ?
        WHERE user_id = ?
    ''', (days, datetime.now().isoformat(), user_id))
    
    # Создаем запись прогресса на сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT OR REPLACE INTO progress (user_id, date, sport, study, work)
        VALUES (?, ?, 0, 0, 0)
    ''', (user_id, today))
    
    conn.commit()
    conn.close()
    
    await query.edit_message_text(
        f"🎉 Отлично! Челлендж на {days} дней начат!\n\n"
        f"Ежедневные задачи:\n"
        f"🏃 Спорт\n"
        f"📚 Учёба\n"
        f"💼 Работа\n\n"
        f"Используй /today чтобы отметить выполнение задач!"
    )

# Показать задачи на сегодня
async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    
    # Получаем данные пользователя и прогресс
    cursor.execute('''
        SELECT u.current_day, u.challenge_days, p.sport, p.study, p.work 
        FROM users u 
        LEFT JOIN progress p ON u.user_id = p.user_id AND p.date = ?
        WHERE u.user_id = ?
    ''', (today, user_id))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        await update.message.reply_text("Сначала создай челлендж командой /new_challenge")
        return
    
    current_day, total_days, sport, study, work = result
    
    # Создаем клавиатуру для отметки задач
    keyboard = [
        [
            InlineKeyboardButton("✅ Спорт" if sport else "🏃 Спорт", callback_data="toggle_sport"),
            InlineKeyboardButton("✅ Учёба" if study else "📚 Учёба", callback_data="toggle_study"),
        ],
        [
            InlineKeyboardButton("✅ Работа" if work else "💼 Работа", callback_data="toggle_work"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    progress_text = f"День {current_day} из {total_days}\n\n"
    progress_text += f"🏃 Спорт: {'✅' if sport else '❌'}\n"
    progress_text += f"📚 Учёба: {'✅' if study else '❌'}\n"
    progress_text += f"💼 Работа: {'✅' if work else '❌'}\n"
    
    if sport and study and work:
        progress_text += "\n🎉 Все задачи выполнены! Так держать!"
    
    await update.message.reply_text(progress_text, reply_markup=reply_markup)

# Обработка отметки задач
async def task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    task_type = query.data
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    
    # Определяем какое поле обновлять
    field = task_type.split('_')[1]  # sport, study, work
    
    # Получаем текущее значение
    cursor.execute(f'''
        SELECT {field} FROM progress 
        WHERE user_id = ? AND date = ?
    ''', (user_id, today))
    
    result = cursor.fetchone()
    current_value = 0
    if result:
        current_value = result[0]
    
    # Переключаем значение
    new_value = 1 if current_value == 0 else 0
    
    # Обновляем или создаем запись
    if result:
        cursor.execute(f'''
            UPDATE progress SET {field} = ? 
            WHERE user_id = ? AND date = ?
        ''', (new_value, user_id, today))
    else:
        cursor.execute('''
            INSERT INTO progress (user_id, date, sport, study, work)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, today, 
              1 if field == 'sport' else 0,
              1 if field == 'study' else 0, 
              1 if field == 'work' else 0))
    
    conn.commit()
    
    # Получаем обновленные данные для отображения
    cursor.execute('''
        SELECT sport, study, work FROM progress 
        WHERE user_id = ? AND date = ?
    ''', (user_id, today))
    
    result = cursor.fetchone()
    if result:
        sport, study, work = result
    else:
        sport, study, work = 0, 0, 0
        
    conn.close()
    
    # Обновляем сообщение
    keyboard = [
        [
            InlineKeyboardButton("✅ Спорт" if sport else "🏃 Спорт", callback_data="toggle_sport"),
            InlineKeyboardButton("✅ Учёба" if study else "📚 Учёба", callback_data="toggle_study"),
        ],
        [
            InlineKeyboardButton("✅ Работа" if work else "💼 Работа", callback_data="toggle_work"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Получаем номер дня
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    cursor.execute('SELECT current_day, challenge_days FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        current_day, total_days = result
    else:
        current_day, total_days = 1, 21
    conn.close()
    
    progress_text = f"День {current_day} из {total_days}\n\n"
    progress_text += f"🏃 Спорт: {'✅' if sport else '❌'}\n"
    progress_text += f"📚 Учёба: {'✅' if study else '❌'}\n"
    progress_text += f"💼 Работа: {'✅' if work else '❌'}\n"
    
    if sport and study and work:
        progress_text += "\n🎉 Все задачи выполнены! Так держать!"
    
    await query.edit_message_text(progress_text, reply_markup=reply_markup)

# Статистика
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    
    # Получаем общую статистику
    cursor.execute('''
        SELECT 
            COUNT(*) as total_days,
            SUM(sport + study + work) as total_tasks,
            SUM(CASE WHEN sport = 1 AND study = 1 AND work = 1 THEN 1 ELSE 0 END) as perfect_days
        FROM progress 
        WHERE user_id = ?
    ''', (user_id,))
    
    stats = cursor.fetchone()
    conn.close()
    
    if stats and stats[0] > 0:
        total_days, total_tasks, perfect_days = stats
        avg_tasks = total_tasks / total_days if total_days > 0 else 0
        
        stats_text = f"📊 Твоя статистика:\n\n"
        stats_text += f"Всего дней: {total_days}\n"
        stats_text += f"Идеальных дней: {perfect_days}\n"
        stats_text += f"Выполнено задач: {total_tasks}\n"
        stats_text += f"Среднее в день: {avg_tasks:.1f}\n"
        stats_text += f"Процент успеха: {(perfect_days/total_days*100):.1f}%"
    else:
        stats_text = "У тебя пока нет статистики. Начни челлендж!"
    
    await update.message.reply_text(stats_text)

# Отправка напоминалки
async def send_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    
    reminder_type = random.choice(['anytime', 'lunch', 'evening', 'late'])
    phrase = random.choice(PHRASES[reminder_type])
    
    await update.message.reply_text(
        f"📨 Напоминалка для друга:\n\n\"{phrase}\"\n\n"
        f"Скопируй и отправь другу!"
    )

# Основная функция
def main():
    # Инициализируем базу данных
    init_db()
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("new_challenge", new_challenge))
    application.add_handler(CommandHandler("today", show_today))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("remind", send_reminder))
    
    application.add_handler(CallbackQueryHandler(challenge_callback, pattern="^challenge_"))
    application.add_handler(CallbackQueryHandler(task_callback, pattern="^toggle_"))
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
