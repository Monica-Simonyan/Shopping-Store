from flask import Flask, render_template, request, redirect, url_for, session
from db import fetch_products, add_to_cart, fetch_cart, register_customer, login_customer, fetch_products_by_category, fetch_categories, checkout_cart

app = Flask(__name__)
app.secret_key = "supersecret"   # required for session


@app.route("/")
def home():
    category_id = request.args.get("category", type=int)
    products = fetch_products_by_category(category_id)
    categories = fetch_categories()
    return render_template("index.html", products=products, categories=categories, selected_category=category_id)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        password = request.form["password"]
        address = request.form["address"]
        phone = request.form["phone"]

        result = register_customer(fname, lname, email, password, address, phone)

        if result == "exists":
            return render_template("register.html", error="Email already registered.")

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_id = login_customer(email, password)

        if not user_id:
            return render_template("login.html", error="Invalid email or password.")

        session["customer_id"] = user_id
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("customer_id", None)
    return redirect("/")


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_product_to_cart(product_id):
    customer_id = session.get("customer_id")
    if not customer_id:
        return redirect("/login")

    quantity = int(request.form.get("quantity", 1))
    add_to_cart(product_id, quantity, customer_id)
    return redirect(url_for("home"))


@app.route("/cart")
def view_cart():
    customer_id = session.get("customer_id")
    if not customer_id:
        return redirect("/login")

    items = fetch_cart(customer_id)
    total = sum([row[3] for row in items])
    return render_template("cart.html", items=items, total=total)

@app.route("/checkout", methods=["POST"])
def checkout():
    customer_id = session.get("customer_id")
    if not customer_id:
        return redirect("/login")

    delivery_address = request.form.get("address")
    if not delivery_address:
        # fallback to customer's registered address if needed
        return redirect(url_for("view_cart"))

    order_id = checkout_cart(customer_id, delivery_address)

    if isinstance(order_id, str) and order_id != "ok":
        # e.g., stock problem
        items = fetch_cart(customer_id)
        total = sum([row[3] for row in items])
        return render_template("cart.html", items=items, total=total, error=order_id)

    return render_template("checkout_success.html", order_id=order_id)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

