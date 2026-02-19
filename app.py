from flask import Flask, render_template, request, redirect, url_for, session, flash
from db.init import init_db
import service
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "very-secret-key"


def get_current_user():
    user = session.get("user")
    if not user:
        return {"id": None, "login": "Guest", "role": "guest"}
    return user

@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}

def allow(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user["role"] not in roles:
                flash("Недостатньо прав для доступу", "warning")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def login_required(role: str | None = None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user["role"] == "guest":
                flash("Потрібна авторизація", "warning")
                return redirect(url_for("login"))
            if role and user["role"] != role:
                flash("Недостатньо прав", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
@allow("user", "operator", "admin")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        flash("Введіть критерій пошуку", "warning")
        return redirect(url_for("index"))
    results = service.search_subscribers(q)
    return render_template("search_results.html", query=q, results=results)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_ = request.form.get("login")
        password = request.form.get("password")

        user = service.get_user_by_login(login_)
        if user and service.verify_password(user, password):
            session["user"] = {
                "id": user["id"],
                "login": user["login"],
                "role": user["role"]
            }
            flash("Успішний вхід", "success")
            return redirect(url_for("index"))

        flash("Невірний логін або пароль", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Ви вийшли із системи", "info")
    return redirect(url_for("index"))

@app.route("/request-access", methods=["GET", "POST"])
@allow("guest")
def request_access():
    if request.method == "POST":
        login = request.form["login"].strip()
        password = request.form["password"].strip()

        if not login or not password:
            flash("Логін та пароль обов'язкові", "danger")
            return redirect(url_for("request_access"))

        service.create_registration_request(login, password)
        flash("Заявку відправлено адміністратору", "success")
        return redirect(url_for("index"))

    return render_template("registration_request.html")

@app.route("/admin/requests")
@allow("admin")
def admin_requests():
    requests_list = service.get_registration_requests()
    return render_template("admin_requests.html", requests=requests_list)

@app.route("/admin/requests/approve/<int:req_id>")
@allow("admin")
def admin_approve_request(req_id):
    ok = service.approve_request(req_id)
    if ok:
        flash("Заявку схвалено, користувача створено", "success")
    else:
        flash("Заявку не знайдено", "danger")
    return redirect(url_for("admin_requests"))

@app.route("/admin/requests/reject/<int:req_id>")
@allow("admin")
def admin_reject_request(req_id):
    service.reject_request(req_id)
    flash("Заявку відхилено", "info")
    return redirect(url_for("admin_requests"))


@app.route("/admin/users")
@allow("admin")
def admin_users():
    users = service.get_all_users()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/create", methods=["GET", "POST"])
@allow("admin")
def admin_create_user():
    if request.method == "POST":
        login = request.form["login"].strip()
        password = request.form["password"].strip()
        role = request.form["role"]

        if not login or not password:
            flash("Логін і пароль обов'язкові", "danger")
            return redirect(url_for("admin_create_user"))

        service.create_user(login, password, role)
        flash("Користувача створено", "success")
        return redirect(url_for("admin_users"))

    return render_template("admin_create_user.html")


@app.route("/admin/users/<int:user_id>/delete")
@allow("admin")
def admin_delete_user(user_id):
    service.delete_user(user_id)
    flash("Користувача видалено", "info")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@allow("admin")
def admin_change_role(user_id):
    new_role = request.form["role"]
    service.update_user_role(user_id, new_role)
    flash("Роль оновлено", "success")
    return redirect(url_for("admin_users"))


@app.route("/subscribers")
@allow("guest", "user", "operator", "admin")
def subscribers():
    subs = service.get_all_subscribers()
    return render_template("subscribers.html", subscribers=subs)


@app.route("/subscriber/<int:sub_id>")
@allow("guest", "user", "operator", "admin")
def subscriber_view(sub_id):
    sub = service.get_subscriber(sub_id)
    if not sub:
        flash("Абонента не знайдено", "danger")
        return redirect(url_for("subscribers"))
    phones = service.get_phones_by_subscriber(sub_id)
    debts = service.get_debts_by_subscriber(sub_id)
    return render_template(
        "subscriber_view.html",
        subscriber=sub, phones=phones, debts=debts
    )

@app.route("/subscriber/add", methods=["GET", "POST"])
@allow("operator", "admin")
def subscriber_add():
    if request.method == "POST":
        lastname = request.form.get("lastname")
        firstname = request.form.get("firstname")
        middlename = request.form.get("middlename")

        street_name = request.form.get("street_name")
        street_type = request.form.get("street_type", "вул.")
        building = request.form.get("building")
        apartment = request.form.get("apartment")

        addr_id = None
        if street_name and building:
            addr_id = service.create_address(street_name, street_type, building, apartment)

        service.create_subscriber(lastname, firstname, middlename, addr_id, None)
        flash("Абонент створений", "success")
        return redirect(url_for("subscribers"))

    return render_template("subscriber_form.html", mode="add")

@app.route("/subscriber/edit/<int:sub_id>", methods=["GET", "POST"])
@allow("operator", "admin")
def subscriber_edit(sub_id):
    sub = service.get_subscriber(sub_id)
    if not sub:
        flash("Абонента не знайдено", "danger")
        return redirect(url_for("subscribers"))

    if request.method == "POST":
        lastname = request.form.get("lastname")
        firstname = request.form.get("firstname")
        middlename = request.form.get("middlename")

        street_type = request.form.get("street_type")
        street_name = request.form.get("street_name")
        building = request.form.get("building")
        apartment = request.form.get("apartment")

        office_number = request.form.get("post_office")

        service.update_subscriber(sub_id, lastname, firstname, middlename)

        address_id = service.update_or_create_address(
            sub["address_id"],
            street_name,
            street_type,
            building,
            apartment
        )

        post_office_id = service.update_or_create_post_office(
            sub["id_post_office"],
            office_number,
            address_id
        )

        service.update_subscriber_address_and_postoffice(sub_id, address_id, post_office_id)

        flash("Абонента та адресу оновлено", "success")
        return redirect(url_for("subscriber_view", sub_id=sub_id))

    return render_template("subscriber_form.html", mode="edit", subscriber=sub)

@app.route("/subscriber/delete/<int:sub_id>")
@allow("admin")
def subscriber_delete(sub_id):
    service.delete_subscriber(sub_id)
    flash("Абонента видалено", "info")
    return redirect(url_for("subscribers"))



@app.route("/subscriber/<int:sub_id>/phones/add", methods=["POST"])
@allow("operator", "admin")
def phone_add(sub_id):
    number = request.form.get("number")
    ptype = request.form.get("type") or "mobile"
    operator_id = request.form.get("operator_id") or None
    operator_id = int(operator_id) if operator_id else None

    if not number:
        flash("Номер не може бути порожнім", "warning")
    else:
        service.create_phone(number, ptype, sub_id, operator_id, 1)
        flash("Номер додано", "success")

    return redirect(url_for("subscriber_view", sub_id=sub_id))

@app.route("/subscriber/<int:sub_id>/phones/delete/<int:phone_id>")
@allow("operator", "admin")
def phone_delete(sub_id, phone_id):
    service.delete_phone(phone_id)
    flash("Номер видалено", "info")
    return redirect(url_for("subscriber_view", sub_id=sub_id))



@app.route("/debts")
@allow("guest", "user", "operator", "admin")
def debts():
    q = request.args.get("q", "").strip()

    if q and get_current_user()["role"] != "guest":
        debtors = service.search_debtors(q)
    else:
        debtors = service.get_subscribers_with_debts()

    return render_template("debts.html", debtors=debtors, query=q)

@app.route("/subscriber/<int:sub_id>/debts/delete/<int:debt_id>")
@allow("operator", "admin")
def debt_delete(sub_id, debt_id):
    service.delete_debt(debt_id)
    flash("Борг видалено", "info")
    return redirect(url_for("subscriber_view", sub_id=sub_id))

@app.route("/subscriber/<int:sub_id>/debts/add", methods=["POST"])
@allow("operator", "admin")
def debt_add(sub_id):
    amount = float(request.form.get("amount", 0))
    date_start = request.form.get("date_start") or datetime.now().strftime("%Y-%m-%d")
    deadline = request.form.get("deadline") or None
    service.create_debt(sub_id, amount, date_start, deadline, "active")
    flash("Борг додано", "success")
    return redirect(url_for("subscriber_view", sub_id=sub_id))




@app.route("/requests")
@allow("operator", "admin")
def requests_list():
    reqs = service.get_all_number_change_requests()
    return render_template("requests.html", requests=reqs)

@app.route("/requests/change/<int:sub_id>/<old_number>")
@allow("user")
def request_number_page(sub_id, old_number):
    return render_template("request_number_form.html", sub_id=sub_id, old_number=old_number)

@app.route("/requests/add", methods=["POST"])
@allow("user", "operator", "admin")
def request_add():
    sub_id = int(request.form.get("subscriber_id"))
    old_number = request.form.get("old_number")
    new_number = request.form.get("new_number")
    date_request = datetime.now().strftime("%Y-%m-%d")
    service.create_number_change_request(sub_id, old_number, new_number, date_request)
    flash("Заявку на зміну номера створено", "success")
    return redirect(url_for("requests_list"))

@app.route("/requests/approve/<int:req_id>")
@allow("operator", "admin")
def request_approve(req_id):
    req = service.get_request(req_id)
    if not req:
        flash("Заявку не знайдено", "danger")
        return redirect(url_for("requests_list"))

    service.apply_number_change(req)

    service.delete_request(req_id)

    flash("Заявку прийнято. Номер оновлено.", "success")
    return redirect(url_for("requests_list"))

@app.route("/requests/reject/<int:req_id>")
@allow("operator", "admin")
def request_reject(req_id):
    service.delete_request(req_id)
    flash("Заявку відхилено.", "info")
    return redirect(url_for("requests_list"))




@app.route("/repairs")
def repairs():
    q = request.args.get("q", "").strip()

    if q and get_current_user()["role"] != "guest":
        repairs = service.search_repairs(q)
    else:
        repairs = service.get_all_repairs()

    return render_template("repairs.html", repairs=repairs, query=q)

@app.route("/repair/add", methods=["GET", "POST"])
@allow("operator", "admin")
def repair_add():
    if request.method == "POST":
        street_type = request.form["street_type"]
        street_name = request.form["street_name"]
        building = request.form["building"]
        apartment = request.form["apartment"]
        date_start = request.form["date_start"]
        date_end = request.form["date_end"]
        description = request.form["description"]

        # створити адресу
        address_id = service.create_address(street_name, street_type, building, apartment)

        # створити ремонт
        service.create_repair(address_id, date_start, date_end, description)
        flash("Ремонтні роботи додано", "success")
        return redirect(url_for("repairs"))

    return render_template("repair_add.html")

@app.route("/repair/edit/<int:repair_id>", methods=["GET", "POST"])
@allow("operator", "admin")
def repair_edit(repair_id):
    repair = service.get_repair(repair_id)
    if not repair:
        flash("Ремонт не знайдено", "danger")
        return redirect(url_for("repairs"))

    if request.method == "POST":
        street_type = request.form["street_type"]
        street_name = request.form["street_name"]
        building = request.form["building"]
        apartment = request.form["apartment"]
        date_start = request.form["date_start"]
        date_end = request.form["date_end"]
        description = request.form["description"]

        service.update_address(repair["id_address"], street_name, street_type, building, apartment)

        service.update_repair(repair_id, repair["id_address"], date_start, date_end, description)

        flash("Дані ремонту оновлено", "success")
        return redirect(url_for("repairs"))

    return render_template("repair_edit.html", repair=repair)

@app.route("/repair/delete/<int:repair_id>")
@allow("operator", "admin")
def repair_delete(repair_id):
    service.delete_repair(repair_id)
    flash("Ремонт видалено", "info")
    return redirect(url_for("repairs"))


@app.route("/services")
@allow("guest", "user", "operator", "admin")
def services_list():
    services = service.get_all_special_services()
    return render_template("services.html", services=services)




@app.route("/sql/reports", methods=["GET", "POST"])
@allow("user", "operator", "admin")
def sql_reports():
    result = None
    selected = None
    params = {}

    if request.method == "POST":
        selected = request.form.get("query_id")

        params = {
            "lastname": request.form.get("lastname", "").strip(),
            "firstname": request.form.get("firstname", "").strip(),
            "street_name": request.form.get("street_name", "").strip()
        }

        result = service.run_builtin_query(selected, params)

    return render_template("sql_reports.html",
                           selected=selected,
                           result=result)




@app.route("/sql/custom", methods=["GET", "POST"])
@allow("operator", "admin")
def sql_custom():
    cols = []
    rows = []
    sql_text = ""

    if request.method == "POST":
        sql_text = request.form.get("sql_text", "")
        if sql_text.strip():
            try:
                cols, rows = service.run_custom_sql(sql_text)
                flash("Запит виконано", "success")
            except Exception as e:
                flash(f"Помилка: {e}", "danger")

    return render_template("sql_custom.html",
                           cols=cols, rows=rows, sql_text=sql_text)



if __name__ == "__main__":
    if not os.path.exists('db/db.sqlite'):
        print('Створення БД')
        init_db()

    app.run(debug=True)
