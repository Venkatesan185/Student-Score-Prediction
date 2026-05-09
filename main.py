from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import os

FRONTEND_DIR = "frontend"
STATIC_DIR = os.path.abspath(FRONTEND_DIR)




from pydantic import BaseModel, Field



from typing import List, Optional
import pandas as pd
import joblib
import sqlite3
import os


app = FastAPI(title="Student Performance API", version="1.1.0")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Student(BaseModel):
    Hours_Studied: float = Field(..., ge=0, le=24)
    Attendance: float = Field(..., ge=0, le=100)
    Parental_Involvement: str = Field(..., min_length=1)
    Access_to_Resources: str = Field(..., min_length=1)
    Extracurricular_Activities: str = Field(..., min_length=1)
    Sleep_Hours: float = Field(..., ge=0, le=24)
    Previous_Scores: float = Field(..., ge=0, le=100)
    Motivation_Level: str = Field(..., min_length=1)
    Internet_Access: str = Field(..., min_length=1)
    Tutoring_Sessions: int = Field(..., ge=0)
    # Final_Exam_Score not needed for input


class StudentOut(Student):
    id: int
    Final_Exam_Score: Optional[float] = None

class PredictionInput(BaseModel):
    Hours_Studied: float = Field(..., ge=0, le=24)
    Attendance: float = Field(..., ge=0, le=100)
    Parental_Involvement: str = Field(..., min_length=1)
    Access_to_Resources: str = Field(..., min_length=1)
    Extracurricular_Activities: str = Field(..., min_length=1)
    Sleep_Hours: float = Field(..., ge=0, le=24)
    Previous_Scores: float = Field(..., ge=0, le=100)
    Motivation_Level: str = Field(..., min_length=1)
    Internet_Access: str = Field(..., min_length=1)
    Tutoring_Sessions: int = Field(..., ge=0)


class PredictionOut(BaseModel):
    predicted_score: float

# Global variables
MODEL_PATH = "student_model.pkl"
DB_PATH = "students.db"
model = None
students_df = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Hours_Studied REAL,
            Attendance REAL,
            Parental_Involvement TEXT,
            Access_to_Resources TEXT,
            Extracurricular_Activities TEXT,
            Sleep_Hours REAL,
            Previous_Scores REAL,
            Motivation_Level TEXT,
            Internet_Access TEXT,
            Tutoring_Sessions INTEGER,
            Final_Exam_Score REAL
        )
    """)
    conn.commit()
    conn.close()

def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    else:
        raise HTTPException(status_code=404, detail="Model not found")

def load_students():
    global students_df
    conn = sqlite3.connect(DB_PATH)
    students_df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()

@app.on_event("startup")
async def startup_event():
    # Ensure DB exists and model is loaded
    init_db()
    load_model()
    load_students()


# Load initial data from CSV
@app.post("/load_csv")
async def load_csv():
    if os.path.exists("student_dataset.csv"):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_csv("student_dataset.csv")
        df.to_sql("students", conn, if_exists="replace", index=False)
        conn.close()
        load_students()
        return {"message": f"Loaded {len(df)} students from CSV"}
    raise HTTPException(status_code=404, detail="student_dataset.csv not found")

# CRUD operations
@app.get("/students", response_model=List[StudentOut])
async def get_students(limit: int = 100, skip: int = 0):
    if students_df is None:
        raise HTTPException(status_code=500, detail="Students not loaded")
    return students_df[skip:skip+limit].to_dict('records')

@app.get("/students/{student_id}", response_model=StudentOut)
async def get_student(student_id: int):
    if students_df is None:
        raise HTTPException(status_code=500, detail="Students not loaded")
    student = students_df[students_df['id'] == student_id]
    if student.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    return student.iloc[0].to_dict()

@app.post("/students", response_model=StudentOut, status_code=201)
async def create_student(student: Student):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (Hours_Studied, Attendance, Parental_Involvement, 
        Access_to_Resources, Extracurricular_Activities, Sleep_Hours, 
        Previous_Scores, Motivation_Level, Internet_Access, Tutoring_Sessions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (student.Hours_Studied, student.Attendance, student.Parental_Involvement,
          student.Access_to_Resources, student.Extracurricular_Activities,
          student.Sleep_Hours, student.Previous_Scores, student.Motivation_Level,
          student.Internet_Access, student.Tutoring_Sessions))
    student_id = cursor.lastrowid
    conn.commit()
    conn.close()
    load_students()
    return await get_student(student_id)


@app.put("/students/{student_id}", response_model=StudentOut)
async def update_student(student_id: int, student: Student):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students SET Hours_Studied=?, Attendance=?, Parental_Involvement=?,
        Access_to_Resources=?, Extracurricular_Activities=?, Sleep_Hours=?,
        Previous_Scores=?, Motivation_Level=?, Internet_Access=?, Tutoring_Sessions=?
        WHERE id=?
    """, (student.Hours_Studied, student.Attendance, student.Parental_Involvement,
          student.Access_to_Resources, student.Extracurricular_Activities,
          student.Sleep_Hours, student.Previous_Scores, student.Motivation_Level,
          student.Internet_Access, student.Tutoring_Sessions, student_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    conn.commit()
    conn.close()
    load_students()
    return await get_student(student_id)


@app.delete("/students/{student_id}")
async def delete_student(student_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    conn.commit()
    conn.close()
    load_students()
    return {"message": "Student deleted"}

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}


# Prediction endpoint
@app.post("/predict", response_model=PredictionOut)
async def predict_score(input_data: PredictionInput):

    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Create DataFrame for prediction
    input_df = pd.DataFrame([input_data.dict()])
    prediction = model.predict(input_df)[0]
    return {"predicted_score": round(prediction, 2)}

# Static frontend
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def index():
    # Serve frontend UI
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

