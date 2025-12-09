import psycopg2
from config import DB_CONFIG
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# -------------------------------
# PRODUCT FUNCTIONS
# -------------------------------

def fetch_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ProductID, ProductName, Price, StockQuantity FROM Product;")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return products

# -------------------------------
# CART FUNCTIONS
# -------------------------------

def create_cart(customer_id):
    conn = get_connection()
    cur = conn.cursor()

    # Check if cart exists
    cur.execute("SELECT CartID FROM Cart WHERE CustomerID=%s;", (customer_id,))
    res = cur.fetchone()

    if res:
        cart_id = res[0]
    else:
        cur.execute(
            "INSERT INTO Cart (CustomerID, CreatedDate) VALUES (%s, %s) RETURNING CartID;",
            (customer_id, datetime.now())
        )
        cart_id = cur.fetchone()[0]
        conn.commit()

    cur.close()
    conn.close()
    return cart_id


def add_to_cart(product_id, quantity=1, customer_id=1):
    cart_id = create_cart(customer_id)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT Quantity FROM CartItem WHERE CartID=%s AND ProductID=%s;",
                (cart_id, product_id))
    res = cur.fetchone()

    if res:
        new_qty = res[0] + quantity
        cur.execute("UPDATE CartItem SET Quantity=%s WHERE CartID=%s AND ProductID=%s;",
                    (new_qty, cart_id, product_id))
    else:
        cur.execute("INSERT INTO CartItem (CartID, ProductID, Quantity) VALUES (%s, %s, %s);",
                    (cart_id, product_id, quantity))

    conn.commit()
    cur.close()
    conn.close()


def fetch_cart(customer_id=1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.ProductName, p.Price, c.Quantity, (p.Price * c.Quantity) AS Subtotal
        FROM CartItem c
        JOIN Cart cart ON c.CartID = cart.CartID
        JOIN Product p ON c.ProductID = p.ProductID
        WHERE cart.CustomerID=%s;
    """, (customer_id,))
    
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

# -------------------------------
# AUTH: REGISTER + LOGIN
# -------------------------------

def register_customer(fname, lname, email, password, address, phone):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM Customer WHERE Email=%s;", (email,))
    if cur.fetchone():
        conn.close()
        return "exists"

    hashed = generate_password_hash(password)

    cur.execute("""
        INSERT INTO Customer (FirstName, LastName, Email, Phone, Address, Password)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (fname, lname, email, phone, address, hashed))

    conn.commit()
    conn.close()
    return "ok"


def login_customer(email, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT CustomerID, Password FROM Customer WHERE Email=%s;", (email,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None
    
    customer_id, hash_pw = row
    if check_password_hash(hash_pw, password):
        return customer_id
    
    return None

def fetch_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT CategoryID, CategoryName FROM Category;")
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return categories

def fetch_products_by_category(category_id=None):
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
    SELECT p.ProductID, p.ProductName, p.Description, p.Price, p.StockQuantity, s.SupplierName
    FROM Product p
    JOIN Supplier s ON p.SupplierID = s.SupplierID
    """
    
    if category_id:
        query += " WHERE p.CategoryID = %s"
        cur.execute(query, (category_id,))
    else:
        cur.execute(query)
    
    products = cur.fetchall()
    cur.close()
    conn.close()
    return products

def checkout_cart(customer_id, delivery_address):
    conn = get_connection()
    cur = conn.cursor()

    # Get cart items
    cur.execute("""
        SELECT c.productid, p.productname, p.price, c.quantity, p.stockquantity
        FROM cartitem c
        JOIN cart cart ON c.cartid = cart.cartid
        JOIN product p ON c.productid = p.productid
        WHERE cart.customerid = %s
    """, (customer_id,))
    items = cur.fetchall()

    if not items:
        conn.close()
        return "empty"

    # Check stock availability
    for item in items:
        product_id, name, price, qty, stock = item
        if qty > stock:
            conn.close()
            return f"Not enough stock for {name}"

    # Calculate total
    total = sum(item[2] * item[3] for item in items)

    # Create order in "Order" table (ORDER is reserved, so keep quotes)
    cur.execute("""
        INSERT INTO "Order" (customerid, totalamount, status)
        VALUES (%s, %s, %s) RETURNING orderid
    """, (customer_id, total, "Pending"))
    order_id = cur.fetchone()[0]

    # Insert order items & reduce stock
    for item in items:
        product_id, name, price, qty, stock = item

        # Insert into OrderDetail
        cur.execute("""
            INSERT INTO orderdetail (orderid, productid, quantity, subtotal)
            VALUES (%s, %s, %s, %s)
        """, (order_id, product_id, qty, price * qty))

        # Update product stock
        cur.execute("""
            UPDATE product SET stockquantity = stockquantity - %s WHERE productid = %s
        """, (qty, product_id))

    # Insert delivery info
    cur.execute("""
        INSERT INTO delivery (orderid, deliveryaddress, deliverystatus)
        VALUES (%s, %s, %s)
    """, (order_id, delivery_address, "Pending"))

    # Clear cart
    cur.execute("""
        DELETE FROM cartitem WHERE cartid = (SELECT cartid FROM cart WHERE customerid = %s)
    """, (customer_id,))

    conn.commit()
    cur.close()
    conn.close()

    return order_id
