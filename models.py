from pydantic import BaseModel

class Student(BaseModel):
 
    name: str
    age: int
    dob: str
    email: str
    department: str
    year: int
