import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from credentials import TOKEN
from log import logger

from trainer import trainer_router
from admin import admin_router
from client import client_router


bot = Bot(token=TOKEN)
dp = Dispatcher()



# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    logger.info(f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) почав взаємодію з ботом")
    record_to_coach = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Запис до тренера ⏺️")],
                  [types.KeyboardButton(text="Я тренер 💪")],],
        resize_keyboard=True,
        one_time_keyboard=True,
        # input_field_placeholder="Выберите способ подачи"
    )
    await message.answer("Привіт! Обери дію:", reply_markup=record_to_coach)


# Запуск процесса поллинга новых апдейтов
async def main():
    print('Bot run')
    dp.include_router(trainer_router)
    dp.include_router(admin_router)
    dp.include_router(client_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())