import random
from db.utils import get_db
from werkzeug.security import generate_password_hash, check_password_hash

def get_user_by_login(login):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM User WHERE login = ?", (login,))
        return cur.fetchone()

def create_user(login: str, password: str, role: str):
    hashed = generate_password_hash(password)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO User (login, password, role)
            VALUES (?, ?, ?)
        """, (login, hashed, role))

def delete_user(user_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM User WHERE id = ?", (user_id,))

def update_user_role(user_id: int, new_role: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE User SET role = ? WHERE id = ?", (new_role, user_id))

def verify_password(user_row, password):
    if user_row is None:
        return False
    return check_password_hash(user_row["password"], password)

def get_all_users():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, login, role FROM User ORDER BY login")
        return cur.fetchall()



def create_registration_request(login: str, password: str):
    hashed = generate_password_hash(password)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO RegistrationRequest (login, password, status)
            VALUES (?, ?, 'new')
        """, (login, hashed))

def get_registration_requests():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, login, status
            FROM RegistrationRequest
            ORDER BY id DESC
        """)
        return cur.fetchall()

def get_registration_request(req_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, login, password, status
            FROM RegistrationRequest
            WHERE id = ?
        """, (req_id,))
        return cur.fetchone()

def approve_request(req_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT login, password FROM RegistrationRequest WHERE id = ?", (req_id,))
        row = cur.fetchone()
        if not row:
            return False

        login = row["login"]
        password_hash = row["password"]

        cur.execute("""
            INSERT INTO User (login, password, role)
            VALUES (?, ?, 'user')
        """, (login, password_hash))

        cur.execute("""
            UPDATE RegistrationRequest
            SET status = 'approved'
            WHERE id = ?
        """, (req_id,))
        return True

def reject_request(req_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE RegistrationRequest
            SET status = 'rejected'
            WHERE id = ?
        """, (req_id,))



def get_or_create_street(name, st_type="вул."):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Street WHERE name = ? AND type = ?", (name, st_type))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute("INSERT INTO Street (name, type) VALUES (?, ?)", (name, st_type))
        return cur.lastrowid

def create_address(street_name, street_type, building, apartment):
    street_id = get_or_create_street(street_name, street_type)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Address (id_street, building, apartment)
            VALUES (?, ?, ?)
        """, (street_id, building, apartment))
        return cur.lastrowid

def update_address(address_id, street_name, street_type, building, apartment):
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT id FROM Street WHERE name=? AND type=?", (street_name, street_type))
        row = cur.fetchone()

        if row:
            street_id = row["id"]
        else:
            cur.execute("INSERT INTO Street (name, type) VALUES (?, ?)", (street_name, street_type))
            street_id = cur.lastrowid

        cur.execute("""
            UPDATE Address
            SET id_street=?, building=?, apartment=?
            WHERE id=?
        """, (street_id, building, apartment, address_id))

def update_or_create_address(address_id, street_name, street_type, building, apartment):
    with get_db() as conn:
        cur = conn.cursor()

        # шукаємо або створюємо вулицю
        cur.execute("SELECT id FROM Street WHERE name=? AND type=?", (street_name, street_type))
        row = cur.fetchone()
        if row:
            street_id = row["id"]
        else:
            cur.execute("INSERT INTO Street (name, type) VALUES (?, ?)", (street_name, street_type))
            street_id = cur.lastrowid

        # якщо адреса існує — оновити
        if address_id:
            cur.execute("""
                UPDATE Address
                SET id_street = ?, building = ?, apartment = ?
                WHERE id = ?
            """, (street_id, building, apartment, address_id))
            return address_id

        # інакше створити нову
        cur.execute("""
            INSERT INTO Address (id_street, building, apartment)
            VALUES (?, ?, ?)
        """, (street_id, building, apartment))
        return cur.lastrowid

def get_address(address_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT Address.*, Street.name AS street_name, Street.type AS street_type
            FROM Address
            JOIN Street ON Street.id = Address.id_street
            WHERE Address.id = ?
        """, (address_id,))
        return cur.fetchone()


def get_all_post_offices():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT PostOffice.*, Street.name AS street_name, Street.type AS street_type,
                   Address.building, Address.apartment
            FROM PostOffice
            LEFT JOIN Address ON Address.id = PostOffice.id_address
            LEFT JOIN Street ON Street.id = Address.id_street
            ORDER BY office_number
        """)
        return cur.fetchall()

def create_post_office_for_address(conn, address_id):
    cur = conn.cursor()

    office_number = 58000 + random.randint(1, 25)

    cur.execute("""
        INSERT INTO PostOffice (office_number, id_address)
        VALUES (?, ?)
    """, (office_number, address_id))

    return cur.lastrowid

def update_or_create_post_office(post_office_id, office_number, address_id):
    with get_db() as conn:
        cur = conn.cursor()

        if post_office_id:
            cur.execute("""
                UPDATE PostOffice
                SET office_number=?, id_address=?
                WHERE id=?
            """, (office_number, address_id, post_office_id))
            return post_office_id

        # інакше створити нове
        cur.execute("""
            INSERT INTO PostOffice (office_number, id_address)
            VALUES (?, ?)
        """, (office_number, address_id))
        return cur.lastrowid

def update_subscriber_address_and_postoffice(sub_id, address_id, post_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE Subscriber
            SET id_address=?, id_post_office=?
            WHERE id=?
        """, (address_id, post_id, sub_id))



def get_all_subscribers():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                s.id,
                s.lastname,
                s.firstname,
                s.middlename,

                (
                    SELECT pn.number
                    FROM PhoneNumber pn
                    WHERE pn.id_subscriber = s.id AND pn.active = 1
                    ORDER BY 
                        (CASE pn.type 
                            WHEN 'mobile' THEN 0
                            WHEN 'home' THEN 1
                            WHEN 'service' THEN 2
                            ELSE 3 END),
                        pn.id ASC
                    LIMIT 1
                ) AS main_phone,

                st.type AS street_type,
                st.name AS street_name,
                a.building,
                a.apartment,

                (st.type || '. ' || st.name || ' ' || a.building ||
                    CASE WHEN a.apartment IS NOT NULL THEN ', кв. ' || a.apartment ELSE '' END
                ) AS full_address,
                
                po.office_number
                
            FROM Subscriber s
            LEFT JOIN Address a ON a.id = s.id_address
            LEFT JOIN Street st ON st.id = a.id_street
            LEFT JOIN PostOffice po ON po.id = s.id_post_office
            
            ORDER BY s.lastname, s.firstname
        """)
        return cur.fetchall()

def get_subscriber(sub_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                s.*,
                a.id AS address_id,
                a.building,
                a.apartment,
                st.name AS street_name,
                st.type AS street_type,
                po.id AS post_office_id,
                po.office_number
            FROM Subscriber s
            LEFT JOIN Address a ON a.id = s.id_address
            LEFT JOIN Street st ON st.id = a.id_street
            LEFT JOIN PostOffice po ON po.id = s.id_post_office
            WHERE s.id = ?
        """, (sub_id,))
        return cur.fetchone()

def create_subscriber(lastname, firstname, middlename, address_id, post_office_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Subscriber (lastname, firstname, middlename, id_address, id_post_office)
            VALUES (?, ?, ?, ?, ?)
        """, (lastname, firstname, middlename, address_id, post_office_id))
        return cur.lastrowid

def update_subscriber(sub_id, lastname, firstname, middlename):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE Subscriber
            SET lastname = ?, firstname = ?, middlename = ?
            WHERE id = ?
        """, (lastname, firstname, middlename, sub_id))

def delete_subscriber(sub_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Subscriber WHERE id = ?", (sub_id,))

def search_subscribers(pattern):
    like = pattern.replace("*", "%").replace("?", "_")

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT
                s.id,
                s.lastname,
                s.firstname,
                s.middlename,

                pn.number AS phone_number,

                st.type AS street_type,
                st.name AS street_name,
                a.building,
                a.apartment,

                (st.type || '. ' || st.name || ' ' || a.building ||
                    CASE WHEN a.apartment IS NOT NULL THEN ', кв. ' || a.apartment ELSE '' END
                ) AS full_address,

                po.office_number

            FROM Subscriber s
            LEFT JOIN PhoneNumber pn ON pn.id_subscriber = s.id AND pn.active = 1
            LEFT JOIN Address a ON a.id = s.id_address
            LEFT JOIN Street st ON st.id = a.id_street
            LEFT JOIN PostOffice po ON po.id = s.id_post_office

            WHERE s.lastname LIKE ?
               OR s.firstname LIKE ?
               OR s.middlename LIKE ?
               OR pn.number LIKE ?
               OR po.office_number LIKE ?
        """, (like, like, like, like, like))

        return cur.fetchall()




def get_all_operators():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM MobileOperator ORDER BY name")
        return cur.fetchall()

def create_operator(name, prefix):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO MobileOperator (name, prefix) VALUES (?, ?)", (name, prefix))
        return cur.lastrowid



def get_phones_by_subscriber(sub_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT PhoneNumber.*, MobileOperator.name AS operator_name
            FROM PhoneNumber
            LEFT JOIN MobileOperator ON MobileOperator.id = PhoneNumber.id_operator
            WHERE PhoneNumber.id_subscriber = ?
            ORDER BY PhoneNumber.number
        """, (sub_id,))
        return cur.fetchall()

def create_phone(number, ptype, sub_id, operator_id, active=1):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO PhoneNumber (number, type, id_subscriber, id_operator, active)
            VALUES (?, ?, ?, ?, ?)
        """, (number, ptype, sub_id, operator_id, active))
        return cur.lastrowid

def delete_phone(phone_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM PhoneNumber WHERE id = ?", (phone_id,))



def get_all_number_change_requests():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, 
                   s.lastname, s.firstname, s.middlename
            FROM NumberChangeRequest r
            LEFT JOIN Subscriber s ON s.id = r.id_subscriber
            ORDER BY r.date_request DESC
        """)
        return cur.fetchall()

def get_request(req_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM NumberChangeRequest WHERE id=?", (req_id,))
        return cur.fetchone()

def update_request_status(request_id, status):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE NumberChangeRequest
            SET status=?
            WHERE id=?
        """, (status, request_id))

def delete_request(request_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM NumberChangeRequest WHERE id=?", (request_id,))

def apply_number_change(request_row):
    with get_db() as conn:
        cur = conn.cursor()

        sub_id = request_row["id_subscriber"]
        old_number = request_row["old_number"]
        new_number = request_row["new_number"]

        cur.execute("""
            DELETE FROM PhoneNumber
            WHERE number=? AND id_subscriber=?
        """, (old_number, sub_id))

        cur.execute("""
            INSERT INTO PhoneNumber (number, type, id_subscriber, id_operator)
            VALUES (?, 'mobile', ?, NULL)
        """, (new_number, sub_id))



def create_number_change_request(sub_id, old_number, new_number, date_request, status="new"):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO NumberChangeRequest (id_subscriber, old_number, new_number, date_request, status)
            VALUES (?, ?, ?, ?, ?)
        """, (sub_id, old_number, new_number, date_request, status))
        return cur.lastrowid

def update_number_change_status(req_id, status):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE NumberChangeRequest
            SET status = ?
            WHERE id = ?
        """, (status, req_id))




def get_debts_by_subscriber(sub_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM Debt
            WHERE id_subscriber = ?
            ORDER BY date_start DESC
        """, (sub_id,))
        return cur.fetchall()

def create_debt(sub_id, amount, date_start, deadline, status="active"):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Debt (id_subscriber, amount, date_start, deadline, status)
            VALUES (?, ?, ?, ?, ?)
        """, (sub_id, amount, date_start, deadline, status))
        return cur.lastrowid

def delete_debt(debt_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Debt WHERE id=?", (debt_id,))

def update_debt(debt_id, amount, status):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE Debt
            SET amount = ?, status = ?
            WHERE id = ?
        """, (amount, status, debt_id))

def get_subscribers_with_debts():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.*, SUM(d.amount) AS total_debt
            FROM Subscriber s
            JOIN Debt d ON d.id_subscriber = s.id
            WHERE d.status = 'active'
            GROUP BY s.id
            HAVING total_debt > 0
            ORDER BY total_debt DESC
        """)
        return cur.fetchall()

def search_debtors(query: str):
    wild = query.replace("*", "%").replace("?", "_")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.lastname, s.firstname, s.middlename,
                   d.amount, d.date_start, d.deadline, d.status
            FROM Debt d
            JOIN Subscriber s ON s.id = d.id_subscriber
            WHERE s.lastname LIKE ?
               OR s.firstname LIKE ?
               OR s.middlename LIKE ?
            ORDER BY s.lastname
        """, (wild, wild, wild))
        return cur.fetchall()



def get_all_repairs():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT rw.*, 
                   st.name AS street_name, st.type AS street_type,
                   a.building, a.apartment
            FROM RepairWork rw
            LEFT JOIN Address a ON a.id = rw.id_address
            LEFT JOIN Street st ON st.id = a.id_street
            ORDER BY date_start DESC
        """)
        return cur.fetchall()

def get_repair(repair_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, 
                   st.name AS street_name, st.type AS street_type,
                   a.building, a.apartment
            FROM RepairWork r
            LEFT JOIN Address a ON a.id = r.id_address
            LEFT JOIN Street st ON st.id = a.id_street
            WHERE r.id = ?
        """, (repair_id,))
        return cur.fetchone()

def create_repair(id_address, date_start, date_end, description):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO RepairWork (id_address, date_start, date_end, description)
            VALUES (?, ?, ?, ?)
        """, (id_address, date_start, date_end, description))
        return cur.lastrowid

def update_repair(repair_id, address_id, date_start, date_end, description):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE RepairWork
            SET id_address = ?, date_start = ?, date_end = ?, description = ?
            WHERE id = ?
        """, (address_id, date_start, date_end, description, repair_id))

def delete_repair(repair_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM RepairWork WHERE id=?", (repair_id,))

def search_repairs(query: str):
    wild = query.replace("*", "%").replace("?", "_")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, 
                   st.name AS street_name, st.type AS street_type,
                   a.building, a.apartment
            FROM RepairWork r
            JOIN Address a ON a.id = r.id_address
            JOIN Street st ON st.id = a.id_street
            WHERE st.name LIKE ?
               OR a.building LIKE ?
               OR a.apartment LIKE ?
        """, (wild, wild, wild))
        return cur.fetchall()



def get_all_special_services():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT ss.*, pn.number
            FROM SpecialService ss
            LEFT JOIN PhoneNumber pn ON pn.id = ss.id_number
            ORDER BY ss.name
        """)
        return cur.fetchall()



def run_custom_sql(sql_text: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(sql_text)
        try:
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            return cols, rows
        except Exception:
            return [], []


def run_builtin_query(query_id, params):
    with get_db() as conn:
        cur = conn.cursor()

        if query_id == "1":
            cur.execute("""
                SELECT 
                    name AS "Назва служби",
                    weekday AS "Дні роботи",
                    time_start AS "Початок прийому",
                    time_end AS "Кінець прийому"
                FROM SpecialService
                ORDER BY name
            """)
            return cur.fetchall()

        if query_id == "2":
            cur.execute("""
                SELECT 
                    s.lastname AS "Прізвище",
                    s.firstname AS "Ім’я",
                    s.middlename AS "По батькові",
                    r.old_number AS "Старий номер",
                    r.new_number AS "Новий номер",
                    r.date_request AS "Дата заявки"
                FROM NumberChangeRequest r
                JOIN Subscriber s ON s.id = r.id_subscriber
                ORDER BY r.date_request DESC
            """)
            return cur.fetchall()


        if query_id == "3":
            cur.execute("""
                SELECT 
                    st.type || '. ' || st.name AS "Вулиця",
                    a.building AS "Будинок",
                    a.apartment AS "Квартира",
                    rw.date_start AS "Початок ремонту",
                    rw.date_end AS "Кінець ремонту",
                    rw.description AS "Опис робіт"
                FROM RepairWork rw
                JOIN Address a ON a.id = rw.id_address
                JOIN Street st ON st.id = a.id_street
                ORDER BY rw.date_start
            """)
            return cur.fetchall()


        if query_id == "4":
            cur.execute("""
                SELECT 
                    ss.name AS "Назва служби",
                    pn.number AS "Телефон"
                FROM SpecialService ss
                JOIN PhoneNumber pn ON pn.id = ss.id_number
                ORDER BY ss.name
            """)
            return cur.fetchall()


        if query_id == "5":
            lastname = params.get("lastname", "")
            firstname = params.get("firstname", "")

            cur.execute("""
                SELECT 
                    s.lastname AS "Прізвище",
                    s.firstname AS "Ім’я",
                    s.middlename AS "По батькові"
                FROM Subscriber s
                WHERE s.lastname LIKE ? AND s.firstname LIKE ?
            """, (lastname + "%", firstname + "%"))

            rows = cur.fetchall()
            return rows, len(rows)


        if query_id == "6":
            cur.execute("""
                SELECT 
                    mo.name AS "Оператор",
                    COUNT(pn.id) AS "Кількість абонентів"
                FROM PhoneNumber pn
                JOIN MobileOperator mo ON mo.id = pn.id_operator
                WHERE pn.active = 1
                GROUP BY mo.id
                ORDER BY COUNT(pn.id) DESC
            """)
            return cur.fetchall()


        if query_id == "7":
            cur.execute("""
                SELECT 
                    s.lastname AS "Прізвище",
                    s.firstname AS "Ім’я",
                    s.middlename AS "По батькові",
                    SUM(d.amount) AS "Загальна заборгованість"
                FROM Debt d
                JOIN Subscriber s ON s.id = d.id_subscriber
                WHERE d.status = 'active'
                GROUP BY s.id
                ORDER BY SUM(d.amount) DESC
            """)
            return cur.fetchall()


        if query_id == "8":
            cur.execute("""
                SELECT 
                    s.lastname AS "Прізвище",
                    s.firstname AS "Ім’я",
                    s.middlename AS "По батькові",
                    r.old_number AS "Старий номер",
                    r.new_number AS "Новий номер",
                    st.type || '. ' || st.name || ' ' || a.building ||
                        CASE WHEN a.apartment IS NOT NULL 
                             THEN ', кв. ' || a.apartment 
                             ELSE '' END AS "Поточна адреса"
                FROM NumberChangeRequest r
                JOIN Subscriber s ON s.id = r.id_subscriber
                JOIN Address a ON a.id = s.id_address
                JOIN Street st ON st.id = a.id_street
                ORDER BY r.date_request DESC
            """)
            return cur.fetchall()


        if query_id == "9":
            street = params.get("street_name", "")

            cur.execute("""
                SELECT 
                    s.lastname AS "Прізвище",
                    s.firstname AS "Ім’я",
                    s.middlename AS "По батькові",
                    st.type AS "Тип вулиці",
                    st.name AS "Назва вулиці",
                    a.building AS "Будинок",
                    a.apartment AS "Квартира"
                FROM Subscriber s
                JOIN Address a ON a.id = s.id_address
                JOIN Street st ON st.id = a.id_street
                WHERE st.name LIKE ?
                ORDER BY s.lastname, s.firstname
            """, (street + "%",))

            rows = cur.fetchall()
            return rows, len(rows)


        if query_id == "10":
            cur.execute("""
                SELECT 
                    st.type || '. ' || st.name AS "Вулиця",
                    COUNT(s.id) AS "Кількість мешканців"
                FROM Subscriber s
                JOIN Address a ON a.id = s.id_address
                JOIN Street st ON st.id = a.id_street
                GROUP BY st.id
                ORDER BY COUNT(s.id) DESC
            """)
            return cur.fetchall()

        return []
