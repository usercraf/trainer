from credentials import admin_key, Administrator, cur, base



# Ця функція створить 3 таблиці у бази даних для тренерів та запису до них.
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

    cur.execute('''
    CREATE TABLE IF NOT EXISTS admin_base(
        name TEXT,
        id_admin TEXT
    )''')
    base.execute('INSERT INTO admin_base (name, id_admin) VALUES(?, ?)',
                 (Administrator, admin_key,))
    base.commit()

crete_table()

# base.execute('DELETE FROM admin_base WHERE id_admin = ?', ('11223344',))
# base.commit()