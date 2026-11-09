import os
#from altair import Order
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, Integer
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker



# Part 1 : load DATABASE_URL from the .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")




# Part 2 : Create the engine (connection to PostgreSQL)
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    version = conn.execute(text("SELECT version()")).scalar()
    print(f"Connected to {version.split(',')[0]}")



# Part 3 : Create SessionLocal and Base
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()

#Base Creating
class Base(DeclarativeBase):
    pass

#Part 4 : Create the Student_db table

class student_db(Base):
    __tablename__ = "student_records"
    id      = Column(String, primary_key=True)
    name    = Column(String(50), nullable=False)
    age     = Column(Integer, nullable=False)
    course  = Column(String(50), nullable=False)
    marks   = Column(Integer, nullable=False)
    email   = Column(String, unique=True, nullable=False) 


# bind=engine -> every session travels to this road
Base.metadata.create_all(bind=engine)
print("Table ready...")




#part 5: Pydantic schemas for input (StudentCreate, StudentUpdate)


from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator
from fastapi import HTTPException, Query

class StudentCreate(BaseModel):
    id       : str = Field(..., examples= ["S001"])
    name     : str = Field(..., min_length=2, max_length=50)
    age      : int = Field(..., gt=0, le=100)
    email    : EmailStr 
    course   : str = Field(..., max_length=50)
    marks    : int = Field(..., ge=0, le=100)

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        if not value.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters and spaces")
        return value.title() 

class StudentUpdate(BaseModel): #Pydantic Model
    name    : str | None = Field(None, min_length=2, max_length=50)
    age     : int | None = Field(None, gt=0, le=100)
    course  : str | None = Field(None, max_length=50)
    marks   : int | None = Field(None, ge=0, le=100)
    email   : EmailStr | None = None


    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        if value is not None:
            if not value.replace(" ", "").isalpha():
                raise ValueError("Name must contain only letters and spaces")
            return value.title()
        return value


# Part 6 : Pydantic schemas for output (StudentResponse, StudentPage, Message)
class StudentResponse(StudentCreate):
    model_config = ConfigDict(from_attributes = True)


    @computed_field
    @property

    def grade(self) ->str:
        if self.marks >=90:
            return "A+"
        elif self.marks >=80:
            return "A"
        elif self.marks >=70:
            return "B"
        elif self.marks >=60:
            return "C"
        else:
            return "F"



# Part 7 : get_db() - one session per request

#opens a session, gives it to the endpoint, always closed it, replaces load_data/save_data
def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# Part 8 : Create the FastAPI app

from fastapi import FastAPI, Path, Depends
app = FastAPI()


#part 9 : GET one student

@app.get("/student/{student_id}", response_model=StudentResponse, tags=["GET ROUTE"])
def get_student(
    student_id : str = Path(..., description="The Id of the student"),
    db : Session = Depends(get_db)

):
    student = db.get(student_db, student_id)
    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student with the Id '{student_id}' not found"
                        )
    return student



# Part 10 : POST - create a student
from sqlalchemy.exc import IntegrityError


@app.post('/CreateStudent', response_model= StudentResponse, status_code=201, tags=["POST ROUTE"])
def create_student(student : StudentCreate, 
                   db : Session = Depends(get_db)):
    if db.get(student_db, student.id):
        raise HTTPException(status_code= 400,
                             detail= f"Student with th Id, '{student.id}' already exists")
    new_student = student_db(**student.model_dump())
    db.add(new_student)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail=f"Email '{student.email}' is already used by another student")

    db.refresh(new_student)
    return new_student


# Part 11 : PUT : - update a student
"""
@app.put('/UpdateStudent/{student_id}')

def update_student(student : StudentUpdate,
                   student_id : str = Path(..., description="The Id of the student"),
                   db : Session = Depends(get_db)
                   ):
    student = db.get(student_db, student_id)
    if student is None:
        raise HTTPException(
            status_code=404, detail=f"Student with the Id '{student_id}' does not exists.. "
        )

    changes = update_student.model_dump(exclude_unset=True)

    for key, value in changes.items():
        setattr(student, key, value)

    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"Email '{student.email}' is already used by another student"
        )

    db.refresh(student)
    return student
"""


@app.put('/UpdateStudent/{student_id}', response_model=StudentResponse, tags=["PUT ROUTE"])
def update_student(
    student_update: StudentUpdate,
    student_id: str = Path(..., description="The Id of the student"),
    db: Session = Depends(get_db)
):
    student = db.get(student_db, student_id)
    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student with the Id '{student_id}' does not exist"
        )

    changes = student_update.model_dump(exclude_unset=True)

    for key, value in changes.items():
        setattr(student, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email is already used by another student"
        )

    db.refresh(student)
    return student



# Part 12 : DELETE : remove a student

@app.delete("/DeleteStudent/{student_id}",tags=["DELETE ROUTE"])

def DeleteStudent(
    student_id : str = Path(..., description="The Id of the Student"),
    db : Session = Depends(get_db)
):
    student = db.get(student_db, student_id)
    if student is None:
        raise HTTPException(
            status_code=404,
            detail = f"Student with the Id '{student_id}' not found")

    db.delete(student)
    db.commit()
    return {"message" : f"Student '{student_id}' is deleted Successfully"}





 #Part 13: GET all students (filter + sort + paginate)
from fastapi import FastAPI, Path, Depends, Query
from sqlalchemy import func

class StudentPage(BaseModel):
    page: int
    limit: int
    total_students: int
    students: list[StudentResponse]


SORT_FIELDS = ["marks", "age", "name"]
SORT_ORDER = ["asc", "desc"]

@app.get("/students", response_model=StudentPage, tags=["GET ROUTE"])
def get_all(
    course: str | None = Query(None, description="Show only students in this course", examples=["Python"]),
    sort_by: str | None = Query(None, description="Sort by marks, age or name"),
    order: str = Query("asc", description="asc or desc", examples=["desc"]),
    page: int = Query(1, ge=1, description="Which page you want (start from 1)"),
    limit: int = Query(2, ge=1, le=100, description="How many students on one page (1 to 100)"),
    db: Session = Depends(get_db),
):
    if sort_by is not None and sort_by not in SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by '{sort_by}', choose from {SORT_FIELDS}"
        )
    if order not in SORT_ORDER:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order '{order}', choose from {SORT_ORDER}"
        )

    query = db.query(student_db)  # SELECT * FROM student_records

    if course:  # WHERE lower(course) = 'python'
        query = query.filter(func.lower(student_db.course) == course.lower())

    total_students = query.count()  # filter ke baad, pagination se pehle

    if sort_by:
        column = getattr(student_db, sort_by)
        query = query.order_by(column.desc() if order == "desc" else column.asc())
    else:
        query = query.order_by(student_db.id)

    # Pagination: OFFSET + LIMIT
    offset = (page - 1) * limit
    students = query.offset(offset).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total_students": total_students,
        "students": students,
    }