import random

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import cur, base
from log import logger


admin_router = Router()


class Add_trainer(StatesGroup):
    add_trainer = State()


def generate_unique_code():
    while True:
        code = "{:06d}".format(random.randint(100000, 999999))
        exists = cur.execute(
            "SELECT 1 FROM trainers WHERE id_trainer = ?",
            (code,)
        ).fetchone()
        if not exists:
            return int(code)


# хендлер додавання тренера до бази даних
@admin_router.callback_query(F.data == 'add_trainer')
async def add_coach_to_db(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Користувач {callback.from_user.first_name} (ID: {callback.from_user.id}) виконав команду {callback.data}")
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    await callback.answer()
    await callback.message.edit_text("Надішли мені імʼя та прізвище і я тебе запишу до бази.", reply_markup=builder.as_markup())
    await state.set_state(Add_trainer.add_trainer)


@admin_router.message(Add_trainer.add_trainer)
async def record_coach(message: types.Message, state: FSMContext):
    name_coach = message.text
    id_trainer = generate_unique_code()
    exists = cur.execute(
        "SELECT 1 FROM trainers WHERE name = ?", (name_coach,)
    ).fetchone()
    builder = InlineKeyboardBuilder()
    if exists:
        builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
        await message.answer("❌ Таке імʼя вже існує. Спробуйте ще раз:", reply_markup=builder.as_markup())
    else:
        base.execute('INSERT INTO trainers (name, id_trainer) VALUES(?, ?)',
                     (name_coach, id_trainer,))
        base.commit()
        await state.clear()  # завершуємо FSM
        builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
        logger.info(
            f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) додав нового тренера {name_coach}")
        await message.answer(text=f'✅ Ви успішно зареєструвались.\n\nОсь Вас код для перегляду записів на тренування '
                                  + str(id_trainer) + '\n\n❗❗❗Треба визначити години в які тренер буде вести прийом.', reply_markup=builder.as_markup())

@admin_router.callback_query(F.data == 'remove_trainer')
async def list_trainers_all(callback: types.CallbackQuery):
    select_names = cur.execute('SELECT name, id_trainer FROM trainers').fetchall()
    builder = InlineKeyboardBuilder()
    for i in select_names:
        builder.add(types.InlineKeyboardButton(text=i[0], callback_data=f'kill_{i[1]}'))
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    builder.adjust(1)
    await callback.message.edit_text('Виберіть себе зі списку ⬇', reply_markup=builder.as_markup())
    await callback.answer()


@admin_router.callback_query(F.data.startswith('kill_'))
async def remove_coach(callback: types.CallbackQuery):
    id_trainer = callback.data.split('_')[1]
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    try:
        base.execute('DELETE FROM trainers WHERE id_trainer = ?', (id_trainer,))
        base.commit()
        logger.info(
            f"Користувач {callback.from_user.first_name} (ID: {callback.from_user.id}) видалив тренера")

        try:
            await callback.message.edit_text('✅ Тренера успішно видалено.', reply_markup=builder.as_markup())
        except TelegramBadRequest:
            await callback.message.answer('✅ Тренера успішно видалено.')

    except Exception as e:
        await callback.message.answer(f'❌ Помилка при видаленні: {e}', reply_markup=builder.as_markup())
    finally:
        await callback.answer()





