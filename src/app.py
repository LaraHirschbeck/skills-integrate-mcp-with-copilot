"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends, Cookie, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
import json
import hashlib
import secrets
from pathlib import Path
from typing import Optional

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Load users from JSON file
def load_users():
    with open(os.path.join(current_dir, "users.json"), "r") as f:
        return json.load(f)

# Active sessions store
active_sessions = {}

# Authentication dependency
async def get_current_user(session: Optional[str] = Cookie(None)):
    if not session or session not in active_sessions:
        return None
    return active_sessions[session]

# Hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    for teacher in users["teachers"]:
        if teacher["username"] == form_data.username and teacher["password_hash"] == hash_password(form_data.password):
            session = secrets.token_urlsafe(32)
            active_sessions[session] = teacher
            response = JSONResponse(content={"message": "Login successful", "name": teacher["name"]})
            response.set_cookie(key="session", value=session)
            return response
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/auth/logout")
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    response.delete_cookie(key="session")
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return None
    return {"username": current_user["username"], "name": current_user["name"]}


# Update the activity endpoints to require authentication for modifications
@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, current_user: dict = Depends(get_current_user)):
    """Sign up a student for an activity"""
    # Require teacher authentication
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    
    # Check if user exists in teachers list
    teacher = next((t for t in users["teachers"] if t["username"] == form_data.username), None)
    if not teacher or hash_password(form_data.password) != teacher["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_token = secrets.token_urlsafe()
    active_sessions[session_token] = {"username": teacher["username"], "role": "teacher"}
    
    response = JSONResponse({"message": "Login successful", "username": teacher["username"]})
    response.set_cookie(key="session", value=session_token)
    return response

@app.post("/api/logout")
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    # Clear session cookie
    response.delete_cookie("session")
    return {"message": "Logout successful"}

# Modify the registration endpoint to require teacher authentication
@app.post("/api/activities/{activity_name}/register")
async def register_student(
    activity_name: str,
    student_email: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=401,
            detail="Only teachers can register students for activities"
        )
    
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    activity = activities[activity_name]
    if student_email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student already registered for this activity"
        )
        
    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")
        
    activity["participants"].append(student_email)
    return {"message": f"Student {student_email} registered for {activity_name}"}

# Modify the unregister endpoint to require teacher authentication
@app.post("/api/activities/{activity_name}/unregister")
async def unregister_student(
    activity_name: str,
    student_email: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user or current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=401,
            detail="Only teachers can unregister students from activities"
        )

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    activity = activities[activity_name]
    if student_email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student not registered for this activity"
        )
        
    activity["participants"].remove(student_email)
    return {"message": f"Student {student_email} unregistered from {activity_name}"}
