from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import init_db  # assuming you have an init_db function to initialize the DB
from app.api import dataset  # assuming you have dataset routes

app = FastAPI()

# Define allowed origins (you can specify specific domains or use '*' for all domains)
origins = [
    "http://localhost:5173",  # frontend on localhost
    "https://myfrontend.com",  # production frontend domain
]

# Add CORS middleware to FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,  # Allows cookies and credentials
    allow_methods=["*"],     # Allows all HTTP methods
    allow_headers=["*"],     # Allows all headers
)

@app.on_event("startup")
async def on_startup():
    await init_db()  # Initialize the database

# Include your dataset routes or other routers here
app.include_router(dataset.router, prefix="/datasets", tags=["Datasets"])
