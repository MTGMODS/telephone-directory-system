# Telephone Directory Information System
<img width="2559" height="1230" alt="image" src="https://github.com/user-attachments/assets/05e5e0df-e08c-4174-8884-716de6c9755b" />
-

This project is a web-based Telephone Directory Information System developed as a university course project (Software Engineering, 3rd year).

The system provides centralized management of subscriber data, including:

- Personal information
- Addresses and streets
- Phone numbers and mobile operators
- Debts and payment tracking
- Repair works
- Special services directory
- Registration and number change request workflows

The application is built with Python and Flask, using SQLite as the relational database.  
It supports CRUD operations, role-based access control, built-in SQL reports and custom SQL execution.

The system focuses on structured data management, role separation, and extensible database architecture.

## Tech Stack

- Python 3.10+
- Flask
- SQLite
- Bootstrap 5
- Jinja2
- Git

## Features

- Role-based access control (guest / user / operator / admin)
- Authentication & password hashing
- Full CRUD for:
  - Subscribers
  - Addresses
  - Phone numbers
  - Debts
  - Repair works
  - Special services
- Number change request workflow
- Registration request approval system
- Built-in SQL reports (10 queries)
- Custom SQL console (operator/admin)
- Mask-based search (* and ? support)

## Database

- Relational schema (3NF)
- 12 core entities:
  Subscriber, Address, Street, PhoneNumber, MobileOperator,
  Debt, SpecialService, RepairWork, PostOffice,
  NumberChangeRequest, User, RegistrationRequest

- SQLite local database (`db/db.sqlite`)

## Installation (local)

```bash
git clone https://github.com/yourusername/telephone-directory-is.git
cd telephone-directory-is
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
pip install flask
python app.py
```

App runs at http://localhost:5000

### Production (optional)
For production deployment you may use Gunicorn:
```bash
pip install gunicorn
gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
```

## Documentation
- Full university documentation (113 pages) is available in the /docs directory.
- Author: Bogdan M.
- Year: 2025
