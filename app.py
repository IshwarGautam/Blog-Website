import os
from flask import Flask
from dotenv import load_dotenv
from database.models.user import User
from database.ext import db, login_manager

# Load environment variables
load_dotenv()

from config import Config
from google.oauth2 import service_account
from googleapiclient.discovery import build


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_user_by_id(user_id)

    # Google Drive setup
    service_account_file = "credentials.json"
    scopes = ["https://www.googleapis.com/auth/drive.file"]
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes
    )
    drive_service = build("drive", "v3", credentials=credentials)

    # Attach drive service to app context
    app.drive_service = drive_service
    app.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.post import post_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(post_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
