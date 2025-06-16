from main import cur, base

Administrator = 'Administrator'
admin_key = '11223344'

# Ця функція створить 2 таблиці у бази даних для тренерів та запису до них.
# Ви можете змінити admin_key проте не змінюйте назву адміністратора
def crete_table():
    cur.execute('''CREATE TABLE IF NOT EXISTS record_to_training(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_coach TEXT,
        id_trainer INT,
        name_client TEXT,
        id_client TEXT,
        date_training TEXT,
        time_training TEXT
    )''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS trainers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        id_trainer INT,
        id_teleram_trainer TEXT,
        time TEXT
    )''')

    base.execute('INSERT INTO trainers (name, id_trainer) VALUES(?, ?)',
                 (Administrator, admin_key,))
    base.commit()

    base.commit()

