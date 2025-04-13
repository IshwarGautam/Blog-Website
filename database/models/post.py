from datetime import datetime, timezone
from database.ext import db


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    featured_image = db.Column(db.String(255), nullable=True)
    images = db.relationship("PostImage", backref="post", cascade="all, delete-orphan")


class PostImage(db.Model):
    __tablename__ = "post_images"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    drive_image_id = db.Column(db.String(100), nullable=False)
