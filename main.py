import asyncio
import logging
from db_handling import create_table, get_quiz_index, update_quiz_index, update_quiz_results, get_result, get_statistic
from markups import generate_main_keyboard, get_question
from data import API_TOKEN, quiz_data
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command 


# Включаем логирование, что бы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)


# Объект бота
bot = Bot(token=API_TOKEN)
# Диспатчер
dp = Dispatcher()



# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = generate_main_keyboard()
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команду /quiz
@dp.message(F.text=='Начать игру')
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer("Давайте начнём квиз!")
    # Запускаем новый квиз
    await new_quiz(message)


@dp.message(F.text=='Показать статистику')
@dp.message(Command('stat'))
async def cmd_stat(message: types.Message):
    results = await get_statistic()
    msg = 'Статистика игроков:\n'
    for us in results.keys():
        msg += f"{us} - {(len(quiz_data) / results[us]) * (100 / (len(quiz_data)))}% правильных ответов"

    await message.answer(msg)


@dp.callback_query(F.data == "right_answer")
@dp.callback_query(F.data == 'wrong_answer')
async def answers(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    correct_option = quiz_data[current_question_index]['correct_option']

    if callback.data == "wrong_answer":
        # Отправляем в чат сообщение об ошибке с указанием верного ответа
        await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")
        await update_quiz_results(callback.from_user.id, current_question_index, False)
    elif callback.data == 'right_answer':
        # Отправляем в чат сообщение, что ответ верный
        await callback.message.answer("Верно!")
        await update_quiz_results(callback.from_user.id, current_question_index, True)
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, callback.from_user.first_name, current_question_index)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        msg = 'Ваши результаты:\n'
        for i, j in enumerate(quiz_data):
            msg += f"{i+1}. {j['question']} - {'Правильно' if await get_result(callback.from_user.id, i) else 'Не правильно'}\n" 
        await callback.message.answer(msg)
        
            

async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await update_quiz_index(user_id, user_name, current_question_index)

    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)




# Запуск процесса поллинга новых апдейтов
async def main():
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())