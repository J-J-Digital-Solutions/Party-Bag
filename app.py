from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from sqlalchemy.sql.expression import func
import stripe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database/users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'ht7r884932t7cr84392tbrc743829tbrv473829btrcv743829bycr478329cnbyr78xm8u'

stripe.api_key = "sk_test_51PuEkj03NN6R2KGdl6yihdeFRc0df3BXF2CHdBbTNQO5eGkqvn5rlp065zP1SXNsGTsYFOnmlg7zEob4fgD3ooZT00hBYbaaVa"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    name = db.Column(db.String(50))
    age = db.Column(db.Boolean)
    admin = db.Column(db.Boolean)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(300))
    image = db.Column(db.String(100))
    price = db.Column(db.Float)
    stock = db.Column(db.Boolean)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    order_description = db.Column(db.String(300))
    order_date = db.Column(db.DateTime, default=datetime.now)
    total_price = db.Column(db.Float)


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

        # Retrieve product details from the database
        product = Product.query.get_or_404(product_id)

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': product.name,
                        'description': product.description,
                    },
                    'unit_amount': int(product.price * 100),  # Convert to pence
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url='http://192.168.0.14:81/success?session_id={CHECKOUT_SESSION_ID}', ################################## CHANGE THIS URL ##################################
            cancel_url='http://192.168.0.14:81/cancel', ################################## CHANGE THIS URL ##################################
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
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"Payment for session {session['id']} was successful.")
        # Perform post-payment actions (e.g., fulfill order)

    return 'Success', 200


@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    if not session_id:
        return "Invalid session.", 400

    session = stripe.checkout.Session.retrieve(session_id)

    if session and session.payment_status == 'paid':
        return "Payment successful! Thank you for your order."
    else:
        return "Payment not verified.", 400


@app.route('/cancel')
def cancel():
    return "Payment canceled. You can try again or contact support."


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