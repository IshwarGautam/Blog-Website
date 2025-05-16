from database.ext import db
from database.models.post import Post
from database.models.comment import Comment
from flask import request, redirect, url_for, Blueprint, abort


comment_bp = Blueprint("comment", __name__)


@comment_bp.route("/<slug>/comment", methods=["POST"])
def comment(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()

    if request.method == "POST":
        name = request.form.get("name")
        content = request.form.get("content")
        parent_id = request.form.get("parent_id") or None

        if name and content:
            comment = Comment(
                name=name, content=content, post_id=post.id, parent_id=parent_id
            )
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for("post.post", slug=slug))

    abort(405)
