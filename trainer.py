from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date, timedelta
import calendar

from db import cur, base
from credentials import all_time
from log import logger


trainer_router = Router()

# клас для перевірки тренером запису на свої занятт
class Check_coach(StatesGroup):
    waiting_for_code = State()
    name_trainer = State()


class TimeTrainerFSM(StatesGroup):
    choose_trainer = State()
    choose_time = State()

def trainer_id():
    select_names = cur.execute('SELECT id_trainer FROM trainers').fetchall()
    names_for_builder = [str(item[0]) for item in select_names]
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


@trainer_router.message(F.text == 'Я тренер 💪')
async def trainer_meny(message: types.Message):
    logger.info(
        f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) зайшов до тренер меню")
    select_names = cur.execute('SELECT name, id_trainer FROM trainers').fetchall()
    builder = InlineKeyboardBuilder()
    for i in select_names:
        builder.add(types.InlineKeyboardButton(text=i[0], callback_data=f'use_trainer_{i[1]}'))
    builder.add(types.InlineKeyboardButton(text='Додати тренера 🧘', callback_data='add_trainer'))
    builder.add(types.InlineKeyboardButton(text='Видалити тренера 🧨', callback_data='remove_trainer'))
    builder.add(types.InlineKeyboardButton(text='Визначити часи прийому ⏰', callback_data='hours_for_trainer'))
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    builder.adjust(1)
    await message.answer('Виберіть себе зі списку ⬇', reply_markup=builder.as_markup())

@trainer_router.callback_query(F.data.startswith('use_trainer_'))
async def check_trainer(callback: types.CallbackQuery, state:FSMContext):
    await callback.message.edit_text('Надійшли свій ID 👮')
    await state.update_data(name_coach=callback.data.split('_')[2])
    await state.set_state(Check_coach.waiting_for_code)
    await callback.answer()

@trainer_router.message(Check_coach.waiting_for_code)
async def trainer_code(message: types.Message, state: FSMContext):
    logger.info(
        f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) вводить id_trainer")
    code_entered = message.text.strip()
    await state.update_data(id_trainer=code_entered)
    result = cur.execute(
        "SELECT name FROM trainers WHERE id_trainer = ?",
        (code_entered,)
    ).fetchone()
    builder = InlineKeyboardBuilder()
    if result:
        name = result[0]
        await message.answer(f"✅ Код вірний. Вітаю, {name}!")

        for i in day_on_month():
            only_the_date = i.split('-')[2]
            builder.add(types.InlineKeyboardButton(text=only_the_date, callback_data=f'trainer_date_{i}'))
        builder.adjust(5)
        builder.row(types.InlineKeyboardButton(text='Надати свій Telgram ID', callback_data='telegram_id'))  # Окрема кнопка
        builder.row(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))  # Окрема кнопка
        await message.answer('Виберіть дату яка тобі треба 📅', reply_markup=builder.as_markup())
        await state.set_state(Check_coach.name_trainer)

    else:
        logger.warning(
            f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) ввів НЕ ПРАВИЛЬНИЙ id_trainer")
        builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
        await message.answer("❌ Код невірний. Спробуйте ще раз:", reply_markup=builder.as_markup())


@trainer_router.callback_query(F.data.startswith('trainer_date_'))
async def trainer_info(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(day_training=callback.data.split('_')[2])
    state_data = await state.get_data()
    records = cur.execute('''SELECT time_training, name_client FROM record_to_training WHERE id_trainer=? AND date_training=?''',
                          (state_data['name_coach'], state_data['day_training'])).fetchall()
    builder = InlineKeyboardBuilder()
    if not records:
        builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
        await callback.message.answer('На сьогодні немає жодного запису 😢', reply_markup=builder.as_markup())
        await callback.answer()
    else:
        result_string = ''
        for i in records:
            result_string = result_string + 'Час ' + i[0] + ' Нікнейм ' + i[1] + '\n'
        builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
        await callback.message.answer(text=f'🤩 До Вас сьогодні записані:{'\n\n'}{result_string}', reply_markup=builder.as_markup())
        await callback.answer()


@trainer_router.callback_query(F.data == 'hours_for_trainer')
async def list_trainers(callback: types.CallbackQuery, state: FSMContext):
    select_names = cur.execute('SELECT name, id_trainer FROM trainers').fetchall()
    builder = InlineKeyboardBuilder()
    for name, trainer_id in select_names:
        builder.add(types.InlineKeyboardButton(text=name, callback_data=f'trainer_time_{trainer_id}'))
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    builder.adjust(1)

    await callback.message.edit_text('Вибери своє імʼя:', reply_markup=builder.as_markup())
    await state.set_state(TimeTrainerFSM.choose_trainer)

@trainer_router.callback_query(F.data.startswith('trainer_time_'))
async def choose_hours(callback: types.CallbackQuery, state: FSMContext):
    trainer_id = callback.data.removeprefix('trainer_time_')
    await state.update_data(id_trainer=trainer_id, selected_hours=[])

    builder = InlineKeyboardBuilder()
    for t in all_time:
        builder.add(types.InlineKeyboardButton(text=f'❌ {t}', callback_data=f'hours_{t.replace(":", "")}'))
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    builder.adjust(3)
    builder.row(types.InlineKeyboardButton(text='✅ Зберегти', callback_data='save_hours'))

    await callback.message.answer('⏰ Вибери години, коли ти приймаєш учнів:', reply_markup=builder.as_markup())
    await state.set_state(TimeTrainerFSM.choose_time)


@trainer_router.callback_query(TimeTrainerFSM.choose_time, F.data.startswith('hours_'))
async def toggle_hour(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_hours", [])
    time_val = callback.data.removeprefix('hours_')
    time_val = f"{time_val[:2]}:{time_val[2:]}"

    if time_val in selected:
        selected.remove(time_val)
    else:
        selected.append(time_val)
    await state.update_data(selected_hours=selected)

    # Оновити клавіатуру
    builder = InlineKeyboardBuilder()
    for t in all_time:
        status = '✅' if t in selected else '❌'
        builder.add(types.InlineKeyboardButton(text=f'{status} {t}', callback_data=f'hours_{t.replace(":", "")}'))
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    builder.adjust(3)
    builder.row(types.InlineKeyboardButton(text='✅ Зберегти', callback_data='save_hours'))

    try:
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except TelegramBadRequest:
        pass
    await callback.answer()


@trainer_router.callback_query(TimeTrainerFSM.choose_time, F.data == 'save_hours')
async def save_selected_hours(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    trainer_id = data['id_trainer']
    selected = data.get("selected_hours", [])
    times_string = ','.join(selected)
    cur.execute("UPDATE trainers SET time = ? WHERE id_trainer = ?", (times_string, trainer_id))
    base.commit()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))
    await callback.message.edit_text(f"✅ Години збережено: {', '.join(selected)}", reply_markup=builder.as_markup())
    await state.clear()
    await callback.answer()

@trainer_router.callback_query(F.data == 'telegram_id')
async def update_telegram_id(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='На головну 🏠', callback_data='Home'))  # Окрема кнопка
    try:
        cur.execute("UPDATE trainers SET id_teleram_trainer = ? WHERE id_trainer = ?", (callback.from_user.id, state_data['id_trainer']))
        base.commit()

        await callback.message.edit_text('Ви оновили свій телеграм ID', reply_markup=builder.as_markup())
        await state.clear()
        await callback.answer()

    except Exception:
        await callback.message.edit_text('😪 Щось пійшло не так зверніться до адміністратора', reply_markup=builder.as_markup())
        await state.clear()
        await callback.answer()