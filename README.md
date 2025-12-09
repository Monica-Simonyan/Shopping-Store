For a project like your **Online Shopping System**, the README should clearly explain what the project is, how to set it up, and how to use it. Here’s a **Google Docs / GitHub friendly structure** you can use:

---

# Online Shopping System

## Description

This project is a full-stack e-commerce system with customer and admin functionalities. Customers can browse products, add them to the cart, place orders, and leave reviews. Admins can manage products, categories, suppliers, orders, and view activity logs.

Technologies used: **Python (Flask), PostgreSQL, HTML/CSS, SQL**.

---

## Features

### Customer

* User registration and login
* Browse and search products
* Add products to cart and checkout
* Payment recording (simulation)
* Write product reviews
* View order history

### Admin

* Add, update, delete products, categories, and suppliers
* View and update customer orders
* Track delivery status
* Activity logging
* Generate reports (best-selling products, low-stock alerts, revenue analysis)

---

## Setup

1. Clone the repository:

```bash
git clone git@github.com:Monica-Simonyan/Shopping-Store.git
cd Shopping-Store
```

2. Create a **config.py** file with your database credentials:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "your_db_name",
    "user": "your_db_user",
    "password": "your_password"
}
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize the database using the provided DDL and DML scripts.

5. Run the Flask app:

```bash
export FLASK_APP=app.py
flask run
```

---

## Notes

* Make sure PostgreSQL is running locally.
* The **config.py** is ignored in `.gitignore` for security reasons. You must create it manually.
* All queries, database scripts, and functions are included in the `sql` folder.
* Activity logging only works for admin actions.

