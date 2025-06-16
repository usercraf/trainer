import sqlite3
import aiosqlite
from main import cur, base



# Функція для створення таблиці в базі даних для запису на тренуванння
# def crete_table():
#     cur.execute('''CREATE TABLE IF NOT EXISTS record_to_training(
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name_coach TEXT,
#         id_trainer INT,
#         name_client TEXT,
#         id_client TEXT,
#         date_training TEXT,
#         time_training TEXT
#     )''')
#
#     cur.execute('''
#     CREATE TABLE IF NOT EXISTS trainers (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name TEXT,
#         id_trainer INT,
#         id_teleram_trainer TEXT
#     )''')
#
#     base.commit()


# add_trainer()

# cur.execute("""DELETE FROM trainers WHERE time='13:00'""")
# base.commit()