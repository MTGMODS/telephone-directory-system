# Telephone Directory Information System

University course project (2025).  
A web-based information system for managing telephone directory data.

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

## Installation

```bash
git clone https://github.com/yourusername/telephone-directory-is.git
cd telephone-directory-is
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
App runs at:
http://localhost:5000

-

# Documentation
Full university documentation (113 pages) is available in the /docs directory.

-

Author: Bogdan M.
Year: 2025
