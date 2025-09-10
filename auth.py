from flask import Flask, render_template, request, redirect, session, jsonify, Blueprint
from flask_session import Session
from datetime import datetime
import pytz
from sql import *  # Used for database connection and management
from SarvAuth import *  # Used for user authentication functions

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if session.get("name"):
        return redirect("/")
    if request.method == "GET":
        return render_template("/auth/login.html")
    else:
        username = request.form.get("username").strip().lower()
        password = request.form.get("password").strip()

        password = hash(password)

        db = SQL("sqlite:///users.db")
        users = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        if len(users) == 0:
            return render_template("/auth/login.html", error="Invalid username or password")
            
        user = users[0]
        if user["password"] == password:
            session["name"] = username
            return redirect("/")

        return render_template("/auth/login.html", error="Invalid username or password")
    
@auth_blueprint.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")
