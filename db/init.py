import random, datetime
from werkzeug.security import generate_password_hash
from db.utils import get_db
from service import create_post_office_for_address

def init_db():
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Street (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Address (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_street INTEGER NOT NULL,
                building TEXT,
                apartment TEXT,
                FOREIGN KEY(id_street) REFERENCES Street(id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS PostOffice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                office_number INTEGER,
                id_address INTEGER,
                FOREIGN KEY(id_address) REFERENCES Address(id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Subscriber (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lastname TEXT,
                firstname TEXT,
                middlename TEXT,
                id_address INTEGER,
                id_post_office INTEGER,
                FOREIGN KEY(id_address) REFERENCES Address(id) ON DELETE SET NULL,
                FOREIGN KEY(id_post_office) REFERENCES PostOffice(id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS MobileOperator (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                prefix TEXT
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS PhoneNumber (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT,
                type TEXT,
                id_subscriber INTEGER,
                id_operator INTEGER,
                active INTEGER DEFAULT 1,
                FOREIGN KEY(id_subscriber) REFERENCES Subscriber(id) ON DELETE CASCADE,
                FOREIGN KEY(id_operator) REFERENCES MobileOperator(id) ON DELETE SET NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Debt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_subscriber INTEGER,
                amount REAL,
                date_start TEXT,
                deadline TEXT,
                status TEXT,
                FOREIGN KEY(id_subscriber) REFERENCES Subscriber(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS NumberChangeRequest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_subscriber INTEGER,
                old_number TEXT,
                new_number TEXT,
                date_request TEXT,
                status TEXT,
                FOREIGN KEY(id_subscriber) REFERENCES Subscriber(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS SpecialService (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                id_number INTEGER,
                description TEXT,
                weekday TEXT,
                time_start TEXT,
                time_end TEXT,
                FOREIGN KEY(id_number) REFERENCES PhoneNumber(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS RepairWork (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_address INTEGER,
                date_start TEXT,
                date_end TEXT,
                description TEXT,
                FOREIGN KEY(id_address) REFERENCES Address(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS RegistrationRequest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT,
                password TEXT,
                status TEXT
            );
        """)

        print('БД створена!')


    print('Для тесту/демонстрації генерую рандом дані')
    create_admin()
    create_mobile_operators()
    create_special_services()
    create_random_subscribers(50)
    create_random_debts(9)
    create_random_number_change_requests(5)
    create_random_repairs(6)


def create_admin():
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM User")
        count = cur.fetchone()[0]

        if count == 0:
            hashed = generate_password_hash("admin")
            cur.execute("""
                INSERT INTO User (login, password, role)
                VALUES (?, ?, ?)
            """, ("admin", hashed, "admin"))
            print("[OK] Створено адміністратора з логіном admin , та паролем admin")

def create_mobile_operators():
    operators = [
        ("Kyivstar", "067"),
        ("Kyivstar", "097"),
        ("Vodafone", "095"),
        ("Vodafone", "050"),
        ("Lifecell", "093"),
    ]

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM MobileOperator")
        count = cur.fetchone()[0]

        if count == 0:
            cur.executemany("""
                INSERT INTO MobileOperator (name, prefix)
                VALUES (?, ?)
            """, operators)
            print("[OK] Додано мобільних операторів")
        else:
            print("[i] Оператори вже існують")

def create_special_services():
    services = [
        ("Пожежна служба", "101", "Надзвичайна служба, тушіння пожеж", "ПН - НД", "00:00", "23:59"),
        ("Поліція", "102", "Служба поліції", "ПН - НД", "00:00", "23:59"),
        ("Швидка допомога", "103", "Медична екстрена служба", "ПН - НД", "00:00", "23:59"),
        ("Газова служба", "104", "Аварії газових мереж", "ПН - НД", "00:00", "23:59"),
    ]

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM SpecialService")
        count = cur.fetchone()[0]

        if count > 0:
            print("[i] Спецслужби вже існують")
            return

        for name, number, desc, workday, time_start, time_end in services:
            cur.execute("""
                INSERT INTO PhoneNumber (number, type, id_subscriber, id_operator, active)
                VALUES (?, 'service', NULL, NULL, 1)
            """, (number,))
            phone_id = cur.lastrowid

            cur.execute("""
                INSERT INTO SpecialService (name, id_number, description, weekday, time_start, time_end)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, phone_id, desc, workday, time_start, time_end))

        print("[OK] Створено спецслужби")

def create_random_address(conn):
    streets = [
        ("Сторожинецька", "вул."),
        ("Шевченка", "вул."),
        ("Незалежності", "проспект."),
        ("Хотинська", "вул."),
        ("Гагаріна", "вул."),
        ("Головна", "вул."),
        ("Кобиляньської", "вул."),
    ]

    street_name, street_type = random.choice(streets)
    building = str(random.randint(1, 120))
    apartment = str(random.randint(1, 20))

    cur = conn.cursor()

    cur.execute("SELECT id FROM Street WHERE name=? AND type=?", (street_name, street_type))
    row = cur.fetchone()

    if row:
        street_id = row[0]
    else:
        cur.execute("INSERT INTO Street (name, type) VALUES (?, ?)", (street_name, street_type))
        street_id = cur.lastrowid

    cur.execute("""
        INSERT INTO Address (id_street, building, apartment)
        VALUES (?, ?, ?)
    """, (street_id, building, apartment))

    return cur.lastrowid

def create_random_subscribers(n=5):
    firstnames = [
        "Богдан", "Олександр", "Олег", "Іван", "Дмитро",
        "Євген", "Ілля", "Микита", "Роман", "Сергій",
        "Андрій", "Юрій", "Максим", "Степан", "Арсен",
        "Тарас", "Володимир", "Петро", "Гнат", "Лев"
    ]
    lastnames = [
        "Коваленко", "Шевченко", "Ткаченко", "Іванов", "Петренко",
        "Коваль", "Маргер", "Пастух", "Гуменюк", "Мельник",
        "Бондар", "Кравець", "Савчук", "Мороз", "Гриценко",
        "Сидоренко", "Ігнатенко", "Лисенко", "Гордійчук", "Проценко"
    ]
    middlenames = [
        "Олександрович", "Ігорович", "Іванович", "Михайлович", "Андрійович",
        "Богданович", "Євгенович", "Дмитрович", "Володимирович", "Сергійович",
        "Юрійович", "Петрович", "Степанович", "Романович", "Максимович",
        "Тарасович", "Гнатович", "Олегович", "Левович", "Микитович"
    ]

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM Subscriber")
        if cur.fetchone()[0] > 0:
            print("[i] Абоненти вже існують")
            return

        for _ in range(n):
            ln = random.choice(lastnames)
            fn = random.choice(firstnames)
            mn = random.choice(middlenames)

            addr_id = create_random_address(conn)

            po_id = create_post_office_for_address(conn, addr_id)

            cur.execute("""
                INSERT INTO Subscriber (lastname, firstname, middlename, id_address, id_post_office)
                VALUES (?, ?, ?, ?, ?)
            """, (ln, fn, mn, addr_id, po_id))

            sub_id = cur.lastrowid

            cur.execute("SELECT id, prefix FROM MobileOperator ORDER BY RANDOM() LIMIT 1")
            op = cur.fetchone()
            op_id = op["id"]
            prefix = op["prefix"]

            number = f"{prefix}{random.randint(0, 9999999):07d}"

            cur.execute("""
                INSERT INTO PhoneNumber (number, type, id_subscriber, id_operator, active)
                VALUES (?, 'mobile', ?, ?, 1)
            """, (number, sub_id, op_id))

        print(f"[OK] Створено {n} випадкових абонентів")

def create_random_number_change_requests(n):
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM NumberChangeRequest")
        if cur.fetchone()[0] > 0:
            print("[i] Заявки вже існують")
            return

        cur.execute("""
            SELECT PhoneNumber.number, Subscriber.id as sub_id
            FROM PhoneNumber
            JOIN Subscriber ON Subscriber.id = PhoneNumber.id_subscriber
            WHERE PhoneNumber.type = 'mobile'
        """)

        numbers = cur.fetchall()

        if not numbers:
            print("[i] Немає телефонів — заявки не створено")
            return

        for _ in range(n):
            row = random.choice(numbers)
            old_number = row["number"]
            sub_id = row["sub_id"]

            cur.execute("SELECT id, prefix FROM MobileOperator ORDER BY RANDOM() LIMIT 1")
            op = cur.fetchone()
            prefix = op["prefix"]
            new_number = f"{prefix}{random.randint(0, 9999999):07d}"

            date_request = f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

            status = random.choice(["new", "processing", "done"])

            cur.execute("""
                INSERT INTO NumberChangeRequest (id_subscriber, old_number, new_number, date_request, status)
                VALUES (?, ?, ?, ?, ?)
            """, (sub_id, old_number, new_number, date_request, status))

        print(f"[OK] Створено {n} заявок на зміну номера")

def create_random_repairs(n):
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM RepairWork")
        if cur.fetchone()[0] > 0:
            print("[i] Ремонти вже існують")
            return

        cur.execute("SELECT id FROM Address")
        addresses = [row["id"] for row in cur.fetchall()]

        if not addresses:
            print("[i] Немає адрес — ремонти не створено")
            return

        for _ in range(n):
            addr_id = random.choice(addresses)

            start = datetime.date(2025, random.randint(1, 12), random.randint(1, 28))
            duration = random.randint(1, 10)
            end = start + datetime.timedelta(days=duration)
            date_start = start.strftime("%Y-%m-%d")
            date_end = end.strftime("%Y-%m-%d")

            desc = random.choice([
                "Ремонт телефонної лінії",
                "Заміна оптоволоконного кабелю",
                "Планове обслуговування мережі",
                "Усунення аварії",
                "Реконструкція узлової точки звʼязку"
            ])

            cur.execute("""
                INSERT INTO RepairWork (id_address, date_start, date_end, description)
                VALUES (?, ?, ?, ?)
            """, (addr_id, date_start, date_end, desc))

        print(f"[OK] Створено {n} ремонтних робіт")

def create_random_debts(n):
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM Debt")
        if cur.fetchone()[0] > 0:
            print("[i] Борги вже існують")
            return

        cur.execute("SELECT id FROM Subscriber")
        subscribers = [row["id"] for row in cur.fetchall()]

        if not subscribers:
            print("[i] Немає абонентів — борги не створено")
            return

        for _ in range(n):
            sub_id = random.choice(subscribers)

            amount = round(random.uniform(50, 1500), 2)

            date_start = f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            deadline = f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

            status = random.choice(["active", "paid"])

            cur.execute("""
                INSERT INTO Debt (id_subscriber, amount, date_start, deadline, status)
                VALUES (?, ?, ?, ?, ?)
            """, (sub_id, amount, date_start, deadline, status))

        print(f"[OK] Створено {n} боргів")
