
from flask import Flask, request, render_template, make_response, redirect, url_for, flash, get_flashed_messages, session, abort
import json
import os
from dotenv import load_dotenv
from hashlib import sha256
import psycopg
from user_repo import UserRepository

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")
# !!!НЕЛЬЗЯ ХРАНИТЬ ПУБЛИЧНО!!!
# python -c 'import secrets; print(secrets.token_hex())'
# uv pip install python-dotenv
# from dotenv import load_dotenv
# import os
# load_dotenv()
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

#conn = psycopg.connect("postgresql://user:password@host:port/database_name")

DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL is not None, "DATABASE_URL is not set"
conn = psycopg.connect(DATABASE_URL)

repo = UserRepository(conn)
app.logger.setLevel("DEBUG")

def validate_user(user):
    errors = {}
    if not user["name"]:
        errors["name"] = "Can't be blank"
    if len(user["nickname"]) <= 4:
        errors["nickname"] = "Nickname must be greater than 4 characters"
    if user["password"] != user["passwordConfirmation"]:
        errors["passwordConfirmation"] = "Wrong password"
    if not user["city"]:
        errors["city"] = "Choose the city"
    return errors


@app.get('/')
def users_index():
    users = repo.list_all()
    messages = get_flashed_messages(with_categories=True)
    return render_template('users/index.html', users=users, messages=messages)

@app.get("/users/new")
def users_new():
    user = {
        "name": "",
        "nickname": "",
        "email": "",
        "password": "",
        "city": ""
    }
    errors = {}
    messages = get_flashed_messages(with_categories=True)
    app.logger.debug("отправляем пустую форму")
    return render_template("users/new.html", user=user, errors=errors, messages=messages)

@app.post("/users")
def users_post():
    app.logger.debug("извлекаем данные из формы")
    user = request.form.to_dict()
    app.logger.debug("валидируем данные")
    errors = validate_user(user)
    if errors:
        app.logger.info("данные некорректны, ожидаем повторный ввод")
        flash("Invalid data", "error")
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            "users/new.html",
            user=user,
            errors=errors,
            messages=messages
        ), 422
    user.pop("passwordConfirmation", None)
    app.logger.info("сохраняем нового пользователя")
    repo.save(user)
    flash("User saved!", "success")
    app.logger.debug("делаем редирект на список пользователей")
    return redirect(url_for('users_index'), code=302)

@app.get("/users/search")
def search_user():
    term = request.args.get("nickname", default='')
    id = request.args.get('id', type=int)
    if term and not id:
        app.logger.debug("поиск по терму")
        users = repo.find_by_term(term)
        if len(users) < 1:
            app.logger.debug("совпадений не найдено")
            flash("User not found!", "error")
            messages = get_flashed_messages(with_categories=True)
            return render_template('users/search.html', messages=messages)
        return render_template('users/index.html', users=users)
    elif id and not term:
        app.logger.debug("поиск по id")
        user = repo.find(id)
        if not user:
            app.logger.debug("совпадений не найдено")
            flash("User not found!", "error")
            messages = get_flashed_messages(with_categories=True)
            return render_template('users/search.html', messages=messages)
        users = [user]
        return render_template('users/index.html', users=users)
    else:
        if id and term:
            flash("Please choose one search option", "error")
        messages = get_flashed_messages(with_categories=True)
        return render_template('users/search.html', messages=messages)

@app.get("/users/<int:id>")
def show_user(id):
    user = repo.find(id)
    app.logger.debug("просмотр информации о пользователе")
    if not user:
        return "User not found!", 404
    return render_template("users/show.html", user=user)

@app.route("/users/delete/<int:id>", methods=["POST"])
def user_delete(id):
    app.logger.debug("удаление пользователя")
    repo.delete(id)
    flash("User has been deleted", "success")
    return redirect(url_for('users_index'))

@app.get("/users/<int:id>/edit")
def edit_form(id):
    user = repo.find(id)
    errors = {}
    return render_template('users/new.html', user=user, errors=errors)


