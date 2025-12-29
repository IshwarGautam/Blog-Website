import os


class Config:
    TINY_MCE_API_KEY = os.getenv("TINY_MCE_API_KEY")
    ENVIRONMENT = os.getenv("ENVIRONMENT")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Increase max upload size to 16MB (for images embedded in posts)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Supabase/PostgreSQL database connection
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = "aws-0-ap-south-1.pooler.supabase.com"
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    PROJECT_ID = os.getenv("PROJECT_ID")

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}.{PROJECT_ID}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Contact Form
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
