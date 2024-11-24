from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database/users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'ht7r884932t7cr84392tbrc743829tbrv473829btrcv743829bycr478329cnbyr78xm8u'

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
    return render_template("product.html", product=product)


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        add_product(
            name="Test Product 1",
            description="A sample product.",
            image="imgs/product_imgs/test.png",
            price=19.99,
            stock=True
        )
    app.run(host='0.0.0.0', port=81)