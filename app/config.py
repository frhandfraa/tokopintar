import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://user123:password123@localhost:5432/db_tokoonline'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
   
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'rahasia-super-aman')