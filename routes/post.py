import re
from database.ext import db
from bs4 import BeautifulSoup
from database.models.comment import Comment
from utils.slug import generate_unique_slug
from database.models.post import Post, PostImage
from flask_login import login_required, current_user
from flask import (
    flash,
    request,
    url_for,
    redirect,
    Blueprint,
    current_app,
    render_template,
)
from utils.helper import (
    extract_base64_images,
    upload_image_to_google_drive,
    delete_image_from_google_drive,
)


post_bp = Blueprint("post", __name__)


def get_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return post


def generate_excerpt(html, word_limit=30):
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(separator=" ")
    words = text.split()
    excerpt = " ".join(words[:word_limit]) + "..."

    return excerpt


def get_featured_image(html):
    soup = BeautifulSoup(html, "html.parser")

    img_tag = soup.find("img", selected=True)
    if not img_tag:
        img_tag = soup.find("img")

    if img_tag and img_tag.get("src"):
        featured_image = img_tag["src"]
    else:
        featured_image = url_for("static", filename="images/blank.png")
    return featured_image


@post_bp.route("/")
@post_bp.route("/page/<int:page>.html")
def index(page=1):
    query = Post.query.order_by(Post.id.desc())

    posts = db.paginate(query, page=page, per_page=9, error_out=False)

    for post in posts.items:
        post.excerpt = generate_excerpt(post.content)

    return render_template("index.html", posts=posts)


@post_bp.route("/<slug>.html")
def post(slug):
    post = get_post(slug)

    comments = (
        Comment.query.filter_by(post_id=post.id, parent_id=None)
        .order_by(Comment.timestamp.desc())
        .all()
    )

    for comment in comments:
        comment.replies = (
            Comment.query.filter_by(parent_id=comment.id)
            .order_by(Comment.timestamp.asc())
            .all()
        )

    return render_template("post.html", post=post, comments=comments)


@post_bp.route("/create.html", methods=["GET", "POST"])
@login_required
def create():
    if not current_user.is_admin:
        flash("Access denied! Admins only.")
        return redirect(url_for("post.index"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        if not title:
            flash("Title is required!")
        else:
            images = extract_base64_images(content)
            uploaded_images = []
            for image_data in images:
                file_url = upload_image_to_google_drive(
                    image_data["base64"],
                    image_data["format"],
                    current_app.drive_service,
                    current_app.folder_id,
                    image_data["filename"],
                )
                content = content.replace(image_data["base64"], file_url)
                drive_image_id = file_url.split("id=")[-1].split("&")[0]
                uploaded_images.append(drive_image_id)

            slug = generate_unique_slug(title)
            featured_image = get_featured_image(content)

            post = Post(
                title=title, slug=slug, content=content, featured_image=featured_image
            )
            db.session.add(post)
            db.session.commit()

            for img_id in uploaded_images:
                db.session.add(PostImage(post_id=post.id, drive_image_id=img_id))
            db.session.commit()

            return redirect(url_for("post.index"))
    return render_template("create.html")


@post_bp.route("/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit(slug):
    if not current_user.is_admin:
        flash("Access denied! Admins only.")
        return redirect(url_for("post.index"))

    post = get_post(slug)
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        if not title:
            flash("Title is required!")
            return render_template("edit.html", post=post)

        existing_ids = {img.drive_image_id for img in post.images}
        new_uploaded_ids = []

        images = extract_base64_images(content)
        for image_data in images:
            file_url = upload_image_to_google_drive(
                image_data["base64"],
                image_data["format"],
                current_app.drive_service,
                current_app.folder_id,
                image_data["filename"],
            )
            content = content.replace(image_data["base64"], file_url)
            drive_id_match = re.search(r"id=([\w-]+)&", file_url)
            if drive_id_match:
                new_uploaded_ids.append(drive_id_match.group(1))

        current_ids_in_content = set(re.findall(r"id=([\w-]+)&", content))
        removed_ids = existing_ids - current_ids_in_content

        for image_id in removed_ids:
            delete_image_from_google_drive(current_app.drive_service, image_id)
            PostImage.query.filter_by(post_id=post.id, drive_image_id=image_id).delete()

        new_ids_to_insert = set(new_uploaded_ids) - existing_ids
        for img_id in new_ids_to_insert:
            db.session.add(PostImage(post_id=post.id, drive_image_id=img_id))

        new_slug = generate_unique_slug(title, post_id=post.id)
        featured_image = get_featured_image(content)

        post.title = title
        post.content = content
        post.slug = new_slug
        post.featured_image = featured_image

        db.session.commit()

        flash("Post updated successfully!")
        return redirect(url_for("post.index"))

    return render_template("edit.html", post=post)


@post_bp.route("/<slug>/delete", methods=["POST"])
@login_required
def delete(slug):
    post = get_post(slug)
    for image in post.images:
        delete_image_from_google_drive(current_app.drive_service, image.drive_image_id)

    db.session.delete(post)
    db.session.commit()
    flash(f'"{post.title}" was successfully deleted!')
    return redirect(url_for("post.index"))
