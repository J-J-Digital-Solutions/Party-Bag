from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from sqlalchemy.sql.expression import func
import stripe
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database/products.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'ht7r884932t7cr84392tbrc743829tbrv473829btrcv743829bycr478329cnbyr78xm8u'

stripe.api_key = "sk_test_51PuEkj03NN6R2KGdl6yihdeFRc0df3BXF2CHdBbTNQO5eGkqvn5rlp065zP1SXNsGTsYFOnmlg7zEob4fgD3ooZT00hBYbaaVa"

db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(300))
    image = db.Column(db.String(100))
    price = db.Column(db.Float)
    stock = db.Column(db.Boolean)


@app.route("/")
def homepage():
    return render_template("home.html")


@app.route("/product/<int:product_id>")
def product(product_id):
    product = Product.query.get_or_404(product_id)
    suggestions = Product.query.filter(Product.id != product_id).order_by(func.random()).limit(3).all()
    return render_template("product.html", product=product, suggestions=suggestions)


################################## ADDING PRODUCTS ##################################
def add_product(name, description, image, price, stock):
    new_product = Product(
        name=name,
        description=description,
        image=image,
        price=price,
        stock=stock
    )
    db.session.add(new_product)
    db.session.commit()
    print(f"Product '{name}' added successfully.")
################################## ADDING PRODUCTS ##################################


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        product = Product.query.get_or_404(product_id)
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': product.name,
                        'description': product.description,
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url='http://192.168.0.14:81/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://192.168.0.14:81',
            billing_address_collection='required',
            shipping_address_collection={'allowed_countries': ['GB']}
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e), 500


@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = 'your_webhook_secret'

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"Payment for session {session['id']} was successful.")

    return 'Success', 200


######### Function runs when payment is successful (secure do to webhooks) grabs customer info from stripe form and sends order email then redirects to the home page with a success message #########
@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    if not session_id:
        return "Invalid session.", 400

    session = stripe.checkout.Session.retrieve(session_id)
    if not session or session.payment_status != 'paid':
        return "Payment not verified.", 400
    line_items = stripe.checkout.Session.list_line_items(session_id)
    customer_name = session.customer_details.name if session.customer_details and session.customer_details.name else "Unknown Customer"
    customer_email = session.customer_details.email if session.customer_details and session.customer_details.email else "No Email Provided"
    customer_address = (
        session.customer_details.address.line1
        if session.customer_details and session.customer_details.address and session.customer_details.address.line1
        else "No Address Provided"
    )
    customer_city = session.customer_details.address.city if session.customer_details and session.customer_details.address and session.customer_details.address.city else "N/A"
    customer_postal_code = session.customer_details.address.postal_code if session.customer_details and session.customer_details.address and session.customer_details.address.postal_code else "N/A"
    customer_country = session.customer_details.address.country if session.customer_details and session.customer_details.address and session.customer_details.address.country else "N/A"

    order_summary = ""
    for item in line_items.data:
        product_name = item.description
        quantity = item.quantity
        amount = item.amount_total / 100.0
        order_summary += f" - {product_name} (x{quantity}): £{amount:.2f}\n"

    email_subject = "New Order Received!"
    email_body = (
        f"{email_subject}\n\n"
        f"Order Details:\n"
        f"{order_summary}\n"
        f"Customer Information:\n"
        f" - Name: {customer_name}\n"
        f" - Email: {customer_email}\n"
        f" - Address: {customer_address}\n"
        f" - City: {customer_city}\n"
        f" - Postal Code: {customer_postal_code}\n"
        f" - Country: {customer_country}\n\n"
        f"Please process this order."
    )

    smtp_server = 'smtp.gmail.com'
    smtp_port = 465
    sender_email = 'james.robinson156.156@gmail.com'
    sender_password = 'avjv mwqg rorn jgvq'
    receiver_email = 'james.robinson156.156@gmail.com'

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = email_subject
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f'Failed to send email: {e}')

    return redirect("/?success=true", code=302)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_password = request.form.get('admin_password')
        if admin_password == 'R0b1ns0n06*':
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            flash('Incorrect admin password', 'error')

    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin():
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    products = Product.query.all()
    return render_template('admin_dashboard.html', products=products)

@app.route('/admin/product/new', methods=['GET', 'POST'])
def admin_new_product():
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image = request.form.get('image')
        price = float(request.form.get('price', 0.0))
        stock = int(request.form.get('stock', 0))

        new_product = Product(
            name=name,
            description=description,
            image=image,
            price=price,
            stock=stock
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_edit_product.html', product=None)


@app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.image = request.form.get('image')
        product.price = float(request.form.get('price', 0.0))
        product.stock = int(request.form.get('stock', 0))
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_edit_product.html', product=product)


@app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
def admin_delete_product(product_id):
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ################################## ADDING PRODUCTS ##################################
        # add_product(
        #     name="Test Product 1",
        #     description="A sample product.",
        #     image="imgs/product_imgs/test.png",
        #     price=19.99,
        #     stock=True
        # )
        ################################## ADDING PRODUCTS ##################################
    app.run(host='0.0.0.0', port=81)