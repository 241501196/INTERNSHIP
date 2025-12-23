from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt

app = FastAPI()

SECRET_KEY = "MY_SECRET_KEY_2025"
ALGORITHM = "HS256"
security = HTTPBearer()

client = MongoClient(
    "mongodb+srv://shakthi:abcde@cluster0.a6ouuwr.mongodb.net/?retryWrites=true&w=majority"
)
db = client["backend"]

users = db["users"]
students = db["students"]

class UserSignup(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Student(BaseModel):
    student_id: str
    name: str
    age: int
    email: str
    department: str
    gender: str


def create_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")


@app.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(data: UserSignup):
    if users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pass = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())

    users.insert_one({
        "name": data.name,
        "email": data.email,
        "password": hashed_pass
    })

    return {"message": "User created successfully"}


@app.post("/login", status_code=status.HTTP_201_CREATED)
def login(data: UserLogin):
    user = users.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=400, detail="Email not found")

    if not bcrypt.checkpw(data.password.encode(), user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_token({"email": user["email"]})
    return {"access_token": token, "token_type": "bearer"}



@app.post("/students", status_code=status.HTTP_201_CREATED)
def add_student(student: Student, user=Depends(verify_token)):
    if students.find_one({"student_id": student.student_id}):
        raise HTTPException(status_code=400, detail="Student ID already exists")

    students.insert_one(student.dict())
    return {"message": "Student added successfully"}


@app.get("/students")
def get_students(user=Depends(verify_token)):
    return list(students.find({}, {"_id": 0}))


@app.get("/students/{student_id}")
def get_student(student_id: str, user=Depends(verify_token)):
    student = students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.put("/students/{student_id}")
def update_student(student_id: str, student: Student, user=Depends(verify_token)):
    result = students.update_one(
        {"student_id": student_id},
        {"$set": student.dict()}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    updated_student = students.find_one(
        {"student_id": student_id},
        {"_id": 0}
    )

    return {
        "message": "Student updated successfully",
        "student": updated_student
    }


@app.delete("/students/{student_id}")
def delete_student(student_id: str, user=Depends(verify_token)):
    result = students.delete_one({"student_id": student_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    return {"message": "Student deleted successfully"}
