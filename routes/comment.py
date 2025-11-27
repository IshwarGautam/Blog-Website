
from flask import request, redirect, url_for, Blueprint, abort, jsonify
from database.ext import db
from database.models.post import Post
from database.models.comment import Comment

comment_bp = Blueprint("comment", __name__)

# AJAX endpoint to add a reply to a comment
@comment_bp.route('/notifications/reply', methods=['POST'])
def notifications_reply():
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')
    parent_id = data.get('parent_id')
    if not (name and content and parent_id):
        return {'success': False, 'error': 'Missing fields'}, 400
    parent = Comment.query.get(parent_id)
    if not parent:
        return {'success': False, 'error': 'Parent comment not found'}, 404
    comment = Comment(name=name, content=content, post_id=parent.post_id, parent_id=parent.id)
    db.session.add(comment)
    db.session.commit()
    return {'success': True}

# Notification API: List all comments as JSON for notification dropdown
@comment_bp.route('/notifications/comments')
def notifications_comments():
    def serialize_comment(comment):
        post = Post.query.get(comment.post_id)
        post_url = None
        if post and getattr(post, 'slug', None):
            post_url = url_for('post.post', slug=post.slug)  # This will generate /<slug>.html
        return {
            'id': comment.id,
            'name': comment.name,
            'content': comment.content,
            'timestamp': comment.timestamp.strftime('%Y-%m-%d %H:%M'),
            'post_title': post.title if post else 'Unknown',
            'post_id': comment.post_id,
            'post_url': post_url,
            'replies': [serialize_comment(reply) for reply in comment.replies.order_by(Comment.timestamp.asc()).all()]
        }
    # Only top-level comments
    comments = Comment.query.filter_by(parent_id=None).order_by(Comment.timestamp.desc()).all()
    result = [serialize_comment(c) for c in comments]
    return jsonify(result)


@comment_bp.route("/<slug>/comment.html", methods=["GET", "POST"])
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

    return "Comment endpoint - no content during freezing", 200
