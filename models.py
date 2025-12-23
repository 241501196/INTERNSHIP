from pydantic import BaseModel

class Student(BaseModel):
    student_id: str
    name: str
    age: int
    email: str
    department: str
    gender: str