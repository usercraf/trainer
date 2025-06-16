from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram import Router, F
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date, timedelta
import calendar

from credentials import cur, base
from log import logger


client_router = Router()


class Coach(StatesGroup):
    name_coach = State()
    date_training = State()
    time_training = State()

def trainer_name():
    select_names = cur.execute('SELECT name FROM trainers').fetchall()
    logger.info(f'SQL {select_names}')
    names_for_builder = [names[0] for names in select_names]
    return names_for_builder

def day_on_month():
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    last_day = date(today.year, today.month, days_in_month)

    # Генеруємо список рядків
    date_list = []
    current = today
    while current <= last_day:
        date_list.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return date_list



# функція для виборки часу який визначив тренер для приймання
def time_trainer(name):
    time_trainers = cur.execute('''SELECT time FROM trainers WHERE name=?''', (name,)).fetchall()
    if time_trainers[0][0] is None:
        return ['Час не визначений тренером',]
    else:
        str_time = time_trainers[0][0].split(',')
        return str_time


# Хендлер для обробки натиснутої кнопки Запис до тренера
@client_router.message(F.text == 'Запис до тренера ⏺️')
async def from_coach(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for i in trainer_name():
        builder.add(types.InlineKeyboardButton(text=i, callback_data=f'list_trainer_{i}'))
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    builder.adjust(1)
    await message.answer(text='Лови список наших тренерів ⬇', reply_markup=builder.as_markup())
    await state.set_state(Coach.name_coach)

# Хендлер для обробки імені тренера до якого хоче записатись людина
@client_router.callback_query(F.data.startswith('list_trainer_'))
async def record_to_coach_date(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(name_coach=callback.data)
    builder = InlineKeyboardBuilder()
    for i in day_on_month():
        only_the_date = i.split('-')[2]
        builder.add(types.InlineKeyboardButton(text=only_the_date, callback_data=f'date_{i}'))
    builder.adjust(5)
    builder.row(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))  # Окрема кнопка
    await callback.message.edit_text('Виберіть дату яка тобі треба 🗓️', reply_markup=builder.as_markup())
    await state.set_state(Coach.date_training)


# Хендлер для обробки дати на яку хоче записатись людина
@client_router.callback_query(F.data.startswith('date_'))
async def record_to_coach_time(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(date_training=callback.data)
    state_data = await state.get_data()
    name_trainer = state_data['name_coach'].split('_')[2]
    reserved_time = cur.execute("""
            SELECT time_training FROM record_to_training
            WHERE name_coach = ? AND date_training = ?
        """, (name_trainer, state_data['date_training'].removeprefix('date_'))).fetchall()
    reservet_time_list = [i[0] for i in reserved_time]
    time_training = [item for item in time_trainer(name_trainer) if item not in reservet_time_list]
    builder = InlineKeyboardBuilder()
    if not time_training:
        builder.row(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))  # Окрема кнопка
        await callback.message.edit_text(' 😢 На сьогодні у тренера всі години зайняті. Виберіть інший день', reply_markup=builder.as_markup())
        await state.clear()
        await callback.answer()
        return

    for i in time_training:
        builder.add(types.InlineKeyboardButton(text=i, callback_data=f'time_{i}'))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))  # Окрема кнопка
    await callback.message.edit_text('Вибери час який тобі треба ⏰', reply_markup=builder.as_markup())
    await state.set_state(Coach.time_training)


# Хендлер для обробки часу на який хоче записатись людина
@client_router.callback_query(F.data.startswith('time_'))
async def time_training(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(time_training=callback.data)
    state_data = await state.get_data()
    await state.clear()  # Завершити FSM
    date_training = state_data['date_training'].split('_')[1]
    time_training = state_data['time_training'].split('_')[1]
    name_trainer = state_data['name_coach'].split('_')[2]
    id_trainer = cur.execute("""SELECT id_trainer FROM trainers WHERE name=?""", (name_trainer,)).fetchone()
    cur.execute("""
        INSERT INTO record_to_training (name_coach, id_trainer, name_client, id_client, date_training, time_training)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name_trainer, id_trainer[0], callback.from_user.first_name, callback.message.from_user.id,
          date_training, time_training))
    base.commit()
    id_telegram_trainer = cur.execute("""SELECT id_teleram_trainer FROM trainers WHERE id_trainer=?""",(id_trainer[0],)).fetchone()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))  # Окрема кнопка

    await callback.message.edit_text(f'🥳 Ви успішно записались до тренера {name_trainer} {date_training} числа на {time_training}', reply_markup=builder.as_markup())

    logger.info(
        f"Користувач {callback.from_user.first_name} (ID: {callback.from_user.id}) "
        f"записався до тренера {name_trainer} {date_training} числа на {time_training}")

    if id_telegram_trainer[0] is None:
        await callback.answer()
    else:
        await callback.bot.send_message(chat_id=int(id_telegram_trainer[0]), text=f'В Вас новий запис {date_training} числа на {time_training}')
        await callback.answer()

# Хендлер для повернення на головну сторінку та виходу з FSM
@client_router.callback_query(F.data == 'Home')
async def home_btn(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    record_to_coach = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Запис до тренера ⏺️")],
                  [types.KeyboardButton(text="Я тренер 💪")],],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await callback.message.answer(
        'Ви на початковій сторінці',
        reply_markup=record_to_coach
    )

    await callback.answer()
