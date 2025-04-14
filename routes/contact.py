import os
from database.ext import mail
from flask_mail import Message
from flask import render_template, request, flash, redirect, url_for, Blueprint

contact_bp = Blueprint("contact", __name__)


@contact_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("Please fill in all fields", "danger")
            return redirect(url_for("contact.contact"))

        msg = Message(
            subject=f"Contact Form Submission - IG Tech Team",
            sender="no-matter-what-the-email-is@gmail.com",  # it will overwrite with the mail_username
            recipients=[os.getenv("MAIL_USERNAME")],
            body=f"Sender Name: {name}\nSender Email: {email}\n\nMessage:\n{message}",
            reply_to=email,
        )

        mail.send(msg)
        flash("Message sent successfully!", "success")
        return redirect(url_for("post.index"))

    return render_template("contact.html")
