from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

client = MongoClient(
    "mongodb+srv://shakthi:abcde@cluster0.a6ouuwr.mongodb.net/?appName=Cluster0"
)

db = client["backend_db"]

students_collection = db["students"]

