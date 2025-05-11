from database.ext import db
from database.models.post import Post
from database.models.comment import Comment
from flask import request, redirect, url_for, render_template, Blueprint


comment_bp = Blueprint("comment", __name__)


@comment_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def comment(post_id):
    post = Post.query.get_or_404(post_id)

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
            return redirect(url_for("comment", post_id=post_id))

    comments = (
        Comment.query.filter_by(post_id=post.id, parent_id=None)
        .order_by(Comment.timestamp.desc())
        .all()
    )
    return render_template("comment.html", post=post, comments=comments)
