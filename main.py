from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import jwt
from passlib.context import CryptContext

app = FastAPI()

# ------------------- CONFIG -------------------

SECRET_KEY = "supersecretkey1234567890"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ------------------- DB -------------------

def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect("tasks.db")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        date TEXT,
        start_time TEXT,
        end_time TEXT,
        completed INTEGER DEFAULT 0,
        user_email TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ------------------- MODELS -------------------

class UserCreate(BaseModel):
    email: str
    password: str


class TaskCreate(BaseModel):
    title: str
    description: str
    date: str
    start_time: str
    end_time: str


class TaskUpdate(BaseModel):
    title: str
    description: str
    date: str
    start_time: str
    end_time: str


# ------------------- AUTH -------------------

def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: str = Header(..., alias="Authorization")):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


# ------------------- ROUTES -------------------

@app.post("/register")
def register(user: UserCreate, db=Depends(get_db)):
    hashed = get_password_hash(user.password)

    try:
        db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (user.email, hashed)
        )
        db.commit()
    except:
        raise HTTPException(status_code=400, detail="User already exists")

    return {"message": "User created"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = sqlite3.connect("tasks.db")
    db.row_factory = sqlite3.Row

    user = db.execute(
        "SELECT * FROM users WHERE email=?",
        (form_data.username,)
    ).fetchone()

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": user["email"]})

    return {"access_token": token}


# ------------------- TASKS -------------------

@app.get("/tasks")
def get_tasks(user=Depends(get_current_user), db=Depends(get_db)):
    tasks = db.execute(
        "SELECT * FROM tasks WHERE user_email=?",
        (user,)
    ).fetchall()

    return [dict(t) for t in tasks]


@app.post("/tasks")
def create_task(task: TaskCreate, user=Depends(get_current_user), db=Depends(get_db)):
    db.execute(
        "INSERT INTO tasks (title, description, date, start_time, end_time, user_email) VALUES (?, ?, ?, ?, ?, ?)",
        (task.title, task.description, task.date, task.start_time, task.end_time, user)
    )
    db.commit()

    return {"message": "Task created"}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, user=Depends(get_current_user), db=Depends(get_db)):
    db.execute(
        "UPDATE tasks SET title=?, description=?, date=?, start_time=?, end_time=? WHERE id=? AND user_email=?",
        (task.title, task.description, task.date, task.start_time, task.end_time, task_id, user)
    )
    db.commit()

    return {"message": "Task updated"}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    db.execute(
        "DELETE FROM tasks WHERE id=? AND user_email=?",
        (task_id, user)
    )
    db.commit()

    return {"message": "Task deleted"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")
