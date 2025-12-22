from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import bcrypt

app = FastAPI()

SECRET_KEY = "MY_SECRET_KEY_2025"
ALGORITHM = "HS256"
security = HTTPBearer()

client = MongoClient("mongodb+srv://shakthi:abcde@cluster0.a6ouuwr.mongodb.net/?retryWrites=true&w=majority")
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
    name: str
    age: int
    dob: str
    email: str
    department: str
    year: int


def create_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")


@app.post("/signup")
def signup(data: UserSignup):
    if users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pass = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())

    users.insert_one({
        "name": data.name,
        "email": data.email,
        "password": hashed_pass
    })

    return {"message": "User created"}


@app.post("/login")
def login(data: UserLogin):
    user = users.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=400, detail="Email not found")

    if not bcrypt.checkpw(data.password.encode(), user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_token({"email": user["email"]})

    return {"access_token": token, "token_type": "bearer"}


@app.post("/students")
def add_student(student: Student, user=Depends(verify_token)):
    result = students.insert_one(student.dict())
    return {"message": "Student added", "id": str(result.inserted_id)}


@app.get("/students")
def get_students(user=Depends(verify_token)):
    result = []
    for s in students.find():
        s["_id"] = str(s["_id"])
        result.append(s)
    return result


@app.put("/students/{student_id}")
def update_student(student_id: str, student: Student, user=Depends(verify_token)):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ID format")

    result = students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": student.dict()}
    )

    if result.modified_count == 1:
        return {"message": "Student fully updated"}

    raise HTTPException(status_code=404, detail="Student not found")


@app.patch("/students/{student_id}")
def patch_student(student_id: str, student: dict, user=Depends(verify_token)):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ID format")

    result = students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": student}
    )

    if result.modified_count == 1:
        return {"message": "Student partially updated"}

    raise HTTPException(status_code=404, detail="Student not found")


@app.delete("/students/{student_id}")
def delete_student(student_id: str, user=Depends(verify_token)):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ID format")

    result = students.delete_one({"_id": ObjectId(student_id)})

    if result.deleted_count == 1:
        return {"message": "Student deleted"}

    raise HTTPException(status_code=404, detail="Student not found")
