import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Supabase/PostgreSQL database connection
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = "aws-0-ap-south-1.pooler.supabase.com"
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    PROJECT_ID = os.getenv("PROJECT_ID")

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}.{PROJECT_ID}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
