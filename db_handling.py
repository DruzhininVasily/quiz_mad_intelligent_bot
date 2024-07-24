import aiosqlite
from data import DB_NAME





# Создание таблицы в БД
async def create_table():
    # Создаём соединение с БД
    async with aiosqlite.connect('quiz_bot.db') as db:
        # SQL запрос к БД на создание таблицы
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, user_name STRING, question_index INTEGER)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_results (user_id INTEGER, question_index INTEGER, result BOOLEAN)''')
        # Сохраняем изменения
        await db.commit()


async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0
            


async def update_quiz_index(user_id, user_name, index):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, user_name, question_index) VALUES(?, ?, ?)', (user_id, user_name, index))
        # Сохраняем изменения
        await db.commit()
        
# Обновляем записи результатов, если не существует создаём
async def update_quiz_results(user_id, index, result):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM quiz_results WHERE user_id = ? AND question_index = ?", (user_id, index)) as cursor:
            exists = await cursor.fetchone()
            if exists is None:
                await db.execute('INSERT INTO quiz_results (user_id, question_index, result) VALUES(?, ?, ?)', (user_id, index, result))
            else:
                await db.execute('UPDATE quiz_results SET result = ? WHERE user_id= ? AND question_index= ?', (result, user_id, index))
        await db.commit()

# Функция для получения результата игрока
async def get_result(user_id, index):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT result FROM quiz_results WHERE user_id = ? AND question_index = ?", (user_id, index)) as cursor:
            result = await cursor.fetchone()
            return result[0]
        
# Функция для сбора статистики игроков
async def get_statistic():
    async with aiosqlite.connect(DB_NAME) as db:
         async with db.execute("SELECT user_id, user_name FROM quiz_state") as cursor:
            users = await cursor.fetchall()
            results = {}
            for us in users:
                async with db.execute("SELECT result FROM quiz_results WHERE user_id = ?", (us[0],)) as cursor_2:
                    us_stat = 0
                    for res in await cursor_2.fetchall():
                        us_stat += res[0]
                    results[us[1]] = us_stat
            return results