from .ext import db
from app import create_app
from .models.user import User
from .models.post import Post, PostImage
from werkzeug.security import generate_password_hash


app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()

    # Check if the admin user already exists
    if not User.query.filter_by(username="ishwargautam").first():
        admin_user = User(
            username="ishwargautam",
            password=generate_password_hash("test1234"),
            is_admin=True,
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
