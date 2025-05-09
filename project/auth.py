import os
import uuid
import requests

from flask_wtf import FlaskForm, RecaptchaField
from flask import Blueprint, current_app, render_template, redirect, url_for, request, flash, session
from flask_babel import gettext as _
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User, Room, Roomadm
from .karatube import recover_email
from . import db

auth = Blueprint("auth", __name__)

class RecoverLoginForm(FlaskForm):
    recaptcha = RecaptchaField()

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
    if not user:
        user = User.query.filter_by(email=userid).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash(_("Please check your login details and try again."))
        flash("alert-danger")
        return redirect(
            url_for("auth.login")
        )  # if the user doesn't exist or password is wrong, reload the page

    #room = Room.query.filter_by(roomid=user.roomid).first()
    # check if the room actually exists
    # take the room-supplied password, hash it, and compare it to the hashed password in the database
    # if the above check passes, then we know the user has the right credentials
    #if not room:
    #    if user.admin != "X":
    #        flash(_("User not assigned to room."))
    #        flash("alert-danger")
    #        return redirect(
    #            url_for("auth.login")
    #        )  # if the user doesn't exist or password is wrong, reload the page
            
    if user.admin == "X":
        user.roomadm = "X"
    else:
        #roomadm = Roomadm.query.filter_by(roomid=room.roomid, userid=user.id).first()
        roomadm = Roomadm.query.filter_by(roomid=user.roomid, userid=user.id).first()
        try:
            if roomadm.roomid == user.roomid:
                user.roomadm = "X"
            else:
                user.roomadm = ""
        except:
            user.roomadm = ""

    if user.roomadm == "":        
        user.roomid = ""
    
    login_user(user, remember=remember)
    db.session.add(user)
    db.session.commit()
    
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

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
    language = request.form.get("lang_selection")

    if password != repass:
        flash(_("Password dont match"))
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    room = Room.query.filter_by(roomid=roomid).first()

    if not room or room.password != roompass:
        flash(_("Wrong room or room password"))
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    if "@" not in email:
        flash(_("Enter valid E-mail"))
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    user = User.query.filter_by(
        email=email
    ).first()  # if this returns a user, then the email already exists in database

    if (
        user
    ):  # if a user is found, we want to redirect back to signup page so user can try again
        flash(_("E-mail already registred"))
        flash("alert-danger")
        return redirect(url_for("auth.signup"))

    user = None

    user = User.query.filter_by(
        id=userid
    ).first()  # if this returns a user, then the email already exists in database

    if (
        user
    ):  # if a user is found, we want to redirect back to signup page so user can try again
        flash(_("User already exists"))
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
        language=language,
    )

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    message = _("User") + " " + str(userid) + "  " + _("created, please login")

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
    
    form = RecoverLoginForm()
    return render_template("recoverlogin.html", form=form)


@auth.route("/recoverlogin", methods=["POST"])
def recoverlogin_post():

    form = RecoverLoginForm()
    recaptcha_response = request.form.get('g-recaptcha-response')
    secret_key = current_app.config['RECAPTCHA_PRIVATE_KEY']

    # Verify the reCAPTCHA response with Google's API
    recaptcha_verify_url = "https://www.google.com/recaptcha/api/siteverify"
    response = requests.post(recaptcha_verify_url, data={
        'secret': secret_key,
        'response': recaptcha_response
    })
    result = response.json()

    if not result.get('success') or result.get('score', 0) < 0.5:
        flash(_("Failed reCAPTCHA verification. Please try again."))
        flash("alert-danger")
        return redirect(url_for("auth.recoverlogin"))

    # Proceed with the rest of the recoverlogin logic
    email = request.form.get("email")

    if "@" not in email:
        flash(_("Enter valid E-mail"))
        flash("alert-danger")
        return redirect(url_for("auth.recoverlogin"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash(_("E-mail not exist in database."))
        flash("alert-danger")
    else:
        password = os.urandom(5).hex()
        if recover_email(user, password):
            user.password = generate_password_hash(password, method="pbkdf2:sha256")
            db.session.commit()
            flash(_("Recover E-mail has been sent"))
            flash("alert-success")
        else:
            flash(_("Failed to send recover email. Contact administrator"))
            flash("alert-danger")

    return redirect(url_for("auth.login"))
