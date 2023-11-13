from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json
from datetime import datetime
from flask_mail import Message
from flask import request, render_template, url_for
import os
import cv2
import numpy as np
from PIL import Image
import random
import string
import pytesseract


local_server = True

with open("C:/Users/laksh/Desktop/flask_learning/templates/config.json", "r") as c:
    params = json.load(c)["params"]

# from sqlalchemy.orm import DeclarativeBase


app = Flask(__name__)


# Adding path to config
app.config["INITIAL_FILE_UPLOADS"] = params["uploads"]

if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]

else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]

app.config["SQLALCHEMY_MODIFICATIONS"] = True

app.secret_key = "super-secret-key"

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["user_email"],
    MAIL_PASSWORD=params["user_password"],
)

mail = Mail(app)


# class Base(DeclarativeBase):
#     pass


# db = SQLAlchemy(model_class=Base)

db = SQLAlchemy(app)

# db.init_app(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    phone_no = db.Column(db.String(13), nullable=False)
    message = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(30), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    subtitle = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(2000), nullable=False)
    img_file = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)


# Initialize the database
# db.create_all()


@app.route("/")
def home():
    if request.method == "GET":
        full_filename = "images/white_bg.jpg"
        return render_template("index.html", full_filename=full_filename, params=params)


@app.route("/index", methods=["GET", "POST"])
def index():
    # Execute if request is get
    if request.method == "GET":
        full_filename = "images/white_bg.jpg"
        return render_template("index.html", full_filename=full_filename, params=params)

    if request.method == "POST":
        image_upload = request.files["image_upload"]
        imagename = image_upload.filename
        image = Image.open(image_upload)

        # Converting image to array
        image_arr = np.array(image.convert("RGB"))
        # Converting image to grayscale
        gray_img_arr = cv2.cvtColor(image_arr, cv2.COLOR_BGR2GRAY)
        # Converting image back to rbg
        image = Image.fromarray(gray_img_arr)

        # Printing lowercase
        letters = string.ascii_lowercase
        # Generating unique image name for dynamic image display
        name = "".join(random.choice(letters) for i in range(10)) + ".png"
        full_filename = "uploads/" + name

        # Extracting text from image
        custom_config = r"-l eng --oem 3 --psm 6"
        text = pytesseract.image_to_string(image, config=custom_config)

        new_string = text

        img = Image.fromarray(image_arr, "RGB")
        img.save(os.path.join(params["UPLOADS"], name))
        # Returning template, filename, extracted text
        return render_template(
            "index.html", full_filename=full_filename, text=new_string, params=params
        )


# @app.route("/index")
# def home_index():
#     return render_template("index.html", params=params)


@app.route("/about")
def about():
    return render_template("about.html", params=params)


# @app.route("/about")
# def about():
#     variable = "lakshmanan"
#     return render_template("about.html", name=variable)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if ("user" in session) and (session["user"] == params["admin_name"]):
        posts = Posts.querry.all()
        return render_template("admin.html", params=params, posts=posts)

    if request.method == "POST":
        username = request.form.get("uname")
        userpass = request.form.get("upass")

        if username == params["admin_name"] and userpass == params["admin_password"]:
            # set the session variable
            session["user"] = username
            posts = Posts.query.all()
            return render_template("admin.html", params=params, posts=posts)

    else:
        return render_template("dashboard.html", params=params)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        phone = request.form.get("phone")

        entry = Contact(
            name=name, phone_no=phone, email=email, message=message, date=datetime.now()
        )

        db.session.add(entry)
        db.session.commit()
        msg = Message(
            "New message received from " + name,
            sender=email,
            recipients=[params["user_email"]],
            body=message + "\n" + phone,
        )
        mail.send(msg)

        return redirect(url_for("contact"))

    return render_template("contact.html", params=params)


@app.route("/post")
def post():
    posts = Posts.query.filter_by().all()
    return render_template("post.html", params=params, posts=posts)


@app.route("/post/<string:post_slug>", methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post1.html", params=params, post=post)


app.run(debug=True)
