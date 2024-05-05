import os

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User, Room, Roomadm
from .karatube import recover_email
from . import db

auth = Blueprint("auth", __name__)


@auth.route("/login")
def login():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login_post():
    # login code goes here
    userid = request.form.get("userid")
    password = request.form.get("password")
    remember = True if request.form.get("remember") else False

    user = User.query.filter_by(id=userid).first()
    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash("Please check your login details and try again.")
        flash("alert-danger")
        return redirect(
            url_for("auth.login")
        )  # if the user doesn't exist or password is wrong, reload the page

    room = Room.query.filter_by(roomid=user.roomid).first()
    # check if the room actually exists
    # take the room-supplied password, hash it, and compare it to the hashed password in the database
    # if the above check passes, then we know the user has the right credentials
    if not room:
        if user.admin != "X":
            flash("User not assigned to room.")
            flash("alert-danger")
            return redirect(
                url_for("auth.login")
            )  # if the user doesn't exist or password is wrong, reload the page

    if user.admin == "X":
        user.roomadm = "X"
    else:
        roomadm = Roomadm.query.filter_by(roomid=room.roomid, userid=user.id).first
        try:
            if roomadm.roomid == user.roomid:
                user.roomadm = "X"
            else:
                user.roomadm = ""
        except:
            user.roomadm = ""

    login_user(user, remember=remember)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("main.profile"))


@auth.route("/signup")
def signup():

    return render_template("signup.html")


@auth.route("/signup", methods=["POST"])
def signup_post():
    # code to validate and add user to database goes here

    userid = request.form.get("userid")
    password = request.form.get("password")
    repass = request.form.get("repass")
    name = request.form.get("name")
    email = request.form.get("email")
    mobile = request.form.get("mobile")
    roomid = request.form.get("roomid")
    roompass = request.form.get("roompass")

    if password != repass:
        flash("Password don't match")
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    room = Room.query.filter_by(roomid=roomid).first()

    if not room or not check_password_hash(room.password, roompass):
        flash("Wrong room or room password")
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    if "@" not in email:
        flash("Enter valid E-mail")
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    user = User.query.filter_by(
        email=email
    ).first()  # if this returns a user, then the email already exists in database

    if (
        user
    ):  # if a user is found, we want to redirect back to signup page so user can try again
        flash("E-mail already registred")
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    user = None

    user = User.query.filter_by(
        id=userid
    ).first()  # if this returns a user, then the email already exists in database

    if (
        user
    ):  # if a user is found, we want to redirect back to signup page so user can try again
        flash("User already exists")
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(
        id=userid,
        name=name,
        roomid=roomid,
        password=generate_password_hash(password, method="pbkdf2:sha256"),
        roomadm="",
        email=email,
        mobile=mobile,
        admin="",
    )

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    message = "User " + str(userid) + " created, please login"

    flash(message)
    flash("alert-success")

    return redirect(url_for("auth.login"))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@auth.route("/recoverlogin")
def recoverlogin():

    return render_template("recoverlogin.html")

@auth.route("/recoverlogin", methods=["POST"])
def recoverlogin_post():

    email = request.form.get("email")
    
    if "@" not in email:
        flash("Enter valid E-mail")
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    user = User.query.filter_by(
        email=email
    ).first()  # if this returns a user, then the email already exists in database

    if ( not user ):  # if a user is found, we want to redirect back to signup page so user can try again
        flash("E-mail not exist in database.")
        flash("alert-danger")
    else:
        password = os.urandom(5).hex()
        if recover_email(user, password):
            user.password = generate_password_hash(password, method="pbkdf2:sha256")
            db.session.commit()
            flash("Recorver E-mail as sended")
            flash("alert-success")
        else:     
            flash("Fails to send recover email. Contact administrator")
            flash("alert-danger")

    return redirect(url_for("auth.login"))