import sqlite3
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND
from backend.db import SessionLocal
from models.user import User
from models.secret import Secret
from passlib.context import CryptContext
from fastapi import FastAPI, Form, Request, HTTPException, Depends, Response, status, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from itsdangerous import URLSafeTimedSerializer
import secrets
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer
from jose import JWTError, jwt
import jwt
from typing import Optional
import random
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

app = FastAPI()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
templates = Jinja2Templates(directory='templates')

DATABASE_URL = "sqlite:///db.db"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

serializer = URLSafeTimedSerializer(SECRET_KEY)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
security = HTTPBearer()

engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_db_connection():
    conn = sqlite3.connect('db.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/secret", response_class=HTMLResponse)
async def secret_get(request: Request):
    return templates.TemplateResponse("secret.html", {"request": request})


@app.post("/secret")
async def secret_post(request: Request, content: str = Form(...)):
    try:
        secret_data = Secret(content=content, created_at=datetime.now())
        conn = sqlite3.connect('db.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO secret (content, created_at) VALUES (?, ?)
        ''', (secret_data.content, secret_data.created_at))
        conn.commit()
        conn.close()
        context = {"message": f"Секрет  записан!", "request": request}
        return templates.TemplateResponse("secret.html", context)
    except:
        conn.close()
        context = {"message": f"Что-то пошло не так... Попробуйте снова чуть позже", "request": request}
        return templates.TemplateResponse("secret.html", context)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=RedirectResponse)
async def login_post(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    if not form_data.username or not form_data.password:
        context = {"error_message": "Пожалуйста, заполните все поля.", "request": request}
        return templates.TemplateResponse("login.html", context)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (form_data.username,))
    h_password = cur.fetchone()
    if h_password is not None:
        stored_hashed_password = h_password[0]
        if pwd_context.verify(form_data.password, stored_hashed_password):
            conn.close()
            token_data = {"sub": form_data.username}
            access_token = create_access_token(data=token_data, expires_delta=timedelta(minutes=30))
            response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
            response.set_cookie(key="access_token", value=access_token, httponly=False)
            return response
    context = {"error_message": "Неправильное имя пользователя или пароль.", "request": request}
    return templates.TemplateResponse("login.html", context)


@app.get("/logout", response_class=RedirectResponse)
def logout(request: Request):
    response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
    response.delete_cookie('access_token')
    return response


@app.get("/registration", response_class=HTMLResponse)
async def registration(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})


@app.post("/registration")
def register_user(request: Request,
                  username: str = Form(...),
                  email: str = Form(...),
                  password: str = Form(...),
                  repeat_password: str = Form(...),
                  age: int = Form(...), ):
    if not all([username, email, password, repeat_password, age]):
        context = {"error_message": "Пожалуйста, заполните все поля.", "request": request}
        return templates.TemplateResponse("registration.html", context)
    if password != repeat_password:
        context = {"error_message": "Пароли не совпадают", "request": request}
        return templates.TemplateResponse("registration.html", context)
    if int(age) < 18:
        context = {"error_message": "Вы должны быть старше 18 лет!", "request": request}
        return templates.TemplateResponse("registration.html", context)
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM Users WHERE username = ?", (username,))
    existing_username = cursor.fetchone()
    if existing_username:
        context = {"error_message": "Такое имя пользователя уже существует.", "request": request}
        return templates.TemplateResponse("registration.html", context)
    cursor.execute("SELECT email FROM Users WHERE email = ?", (email,))
    existing_email = cursor.fetchone()
    if existing_email:
        context = {"error_message": "Этот адрес электронной почты уже используется.", "request": request}
        return templates.TemplateResponse("registration.html", context)
    hashed_password = pwd_context.hash(password)
    try:
        cursor.execute('''
            INSERT INTO users (username, password, email, age) VALUES (?, ?, ?, ?)
            ''', (username, hashed_password, email, age))
        conn.commit()
        conn.close()
        token_data = {"sub": username, "email": email}
        access_token = create_access_token(data=token_data, expires_delta=timedelta(minutes=30))
        response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
        context = {"error_message": "Произошла ошибка при регистрации. Попробуйте позже.", "request": request}
        return templates.TemplateResponse("registration.html", context)


@app.get("/protected", response_class=HTMLResponse)
def protected_route(request: Request):
    try:
        token = request.cookies['access_token']
    except KeyError:
        context = {"message": "Вы  должны Войти, чтоб читать секреты!", "request": request}
        return templates.TemplateResponse("home.html", context)
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Неверный токен или срок действия истёк.")
    return templates.TemplateResponse("protected.html", {"request": request})


@app.get("/get-random-secret")
def get_random_secret2():
    secrets = session.query(Secret).all()
    if not secrets:
        return {"content": "Нет секретов"}
    random_secret = random.choice(secrets)
    return {"content": random_secret.content}
