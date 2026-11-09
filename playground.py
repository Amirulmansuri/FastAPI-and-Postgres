"""
Python will interect with PostgreSQL directly without any FASTAPI routes or endpoints
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, Integer
from sqlalchemy.orm import DeclarativeBase, sessionmaker


#step-1 : Get the URL from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)

#Step-2 : Engine = the road to the DATABASE
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    version = conn.execute(text("SELECT version()")).scalar()
    print(f"Connected to {version.split(",")[0]}")


"""
DeclarativeBase is the Parent class from SQLALchemy that turn a normal python class into a database table

Declartive : You declare(describe) what a table looks like
Base       : It's the Parent class everything else built on top of this.
"""
"""class Base(DeclarativeBase):
    pass

class student_db(Base):
    __tablename__ = "student_records"
    id      = Column(String, primary_key=True)
    name    = Column(String(50), nullable=False)
    age     = Column(Integer, nullable=False)
    course  = Column(String(50), nullable=False)
    marks   = Column(Integer, nullable=False)
    email   = Column(String, unique=True, nullable=False)  """


#bind=engine -> every session travels to this road
"""Base.metadata.create_all(bind=engine)
print("Table ready...")"""

#Step 4: Session = One Visit, Open, do work, commit, close
"""SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()

if db.get(student_db, "S003") is None:
    db.add(student_db(id="S003",
                     name="Aarav Sharma",
                     age=25,
                     course = "Python",
                     marks=80,
                     email="Ara3@example.com"))
    db.commit()

"""
#Read it Back
"""for i in db.query(student_db).all():
    print(i.id, i.name, i.age, i.marks, i.course, i.email)
"""

#Update name in S003 Aarav to Anish
"""aarav = db.get(student_db, "S003")
aarav.name = "Anish Mansuri"
db.commit()
"""

class Base(DeclarativeBase):
    pass

class student_db(Base):
    __tablename__ = "student_records"
    id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    course = Column(String(50), nullable=False)
    marks = Column(Integer, nullable=False)
    email = Column(String, unique=True, nullable=False)


#bind = engine -> Attach to: Create the table inside THIS database
Base.metadata.create_all(bind=engine)


#Step 4 : Creating Session
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()