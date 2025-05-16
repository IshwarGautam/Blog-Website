import os
import shutil
from app import create_app
from flask_frozen import Freezer
from database.models.post import Post


def delete_comment_folders(destination):
    for root, dirs, files in os.walk(destination):
        if "comment.html" in files:
            print(f"Removing folder: {root}")
            shutil.rmtree(root)


class CustomFreezer(Freezer):
    def urlpath_to_filepath(self, urlpath):
        filepath = super().urlpath_to_filepath(urlpath)
        if "." not in filepath:
            filepath += ".html"
        return filepath


def patch_contact_form_for_emailjs(build_dir):
    contact_path = os.path.join(build_dir, "contact.html")
    if not os.path.exists(contact_path):
        print("No contact.html found to patch.")
        return

    with open(contact_path, "r", encoding="utf-8") as f:
        content = f.read()

    js_script = """
    <script type="text/javascript">
    (function() {
        const form = document.querySelector("form");
        const submitBtn = form.querySelector("button[type='submit']");

        form.addEventListener("submit", function(e) {
            e.preventDefault();

            submitBtn.disabled = true;
            const originalBtnText = submitBtn.textContent;
            submitBtn.textContent = "Sending...";

            fetch("/.netlify/functions/get_emailjs_keys")
                .then(res => res.json())
                .then(keys => {
                    const formData = new FormData(form);
                    const sentAt = new Date().toLocaleString();

                    const params = {
                        name: formData.get("name"),
                        reply_to: formData.get("email"),
                        message: formData.get("message"),
                        time: sentAt,
                        subject: "Contact Form Submission [IG Tech Team]"
                    };

                    return fetch("https://api.emailjs.com/api/v1.0/email/send", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            service_id: keys.service_id,
                            template_id: keys.template_id,
                            user_id: keys.public_key,
                            template_params: params
                        })
                    });
                })
                .then(response => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;

                    if (response.ok) {
                        alert("Message sent successfully!");
                        form.reset();
                    } else {
                        return response.text().then(text => {
                            alert("Email failed: " + text);
                        });
                    }
                })
                .catch(error => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                    alert("Error sending email: " + error);
                });
        });
    })();
    </script>
    """

    if "</form>" in content:
        content = content.replace("</form>", "</form>" + js_script)
        with open(contact_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Patched contact.html with EmailJS fetch script.")


def patch_post_pages_for_comments(build_dir):
    for root, _, files in os.walk(build_dir):
        for file in files:
            if not file.endswith(".html"):
                continue

            file_path = os.path.join(root, file)
            slug = os.path.splitext(file)[0]

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Skip if there's no comment form
            if 'action="/' not in content or "comment.html" not in content:
                continue

            # Replace placeholder comment section with a dynamic container
            if "<p>No comments yet. Be the first to comment!</p>" in content:
                content = content.replace(
                    "<p>No comments yet. Be the first to comment!</p>",
                    '<div id="comments">Loading comments...</div>',
                )

            # JS to be injected with dynamic slug
            js_script = f"""
<script>
(function() {{
  const form = document.querySelector("form[action*='comment.html']");
  const commentsContainer = document.getElementById("comments");
  if (!form || !commentsContainer) return;

  const submitBtn = form.querySelector("button[type='submit']");
  form.addEventListener("submit", function(e) {{
    e.preventDefault();
    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Posting...";

    const formData = new FormData(form);
    formData.append("slug", "{slug}");

    fetch("/.netlify/functions/submit_comment", {{
      method: "POST",
      body: formData
    }})
    .then(res => {{
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
      if (res.ok) {{
        alert("Comment submitted!");
        form.reset();
        loadComments();
      }} else {{
        return res.text().then(text => alert("Failed: " + text));
      }}
    }})
    .catch(err => {{
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
      alert("Error: " + err);
    }});
  }});

  function loadComments() {{
    fetch("/.netlify/functions/get_comments?slug={slug}")
      .then(res => res.json())
      .then(comments => {{
        commentsContainer.innerHTML = "";
        const map = {{}};
        comments.forEach(c => {{
          c.children = [];
          map[c.id] = c;
        }});
        comments.forEach(c => {{
          if (c.parent_id && map[c.parent_id]) {{
            map[c.parent_id].children.push(c);
          }}
        }});

        const render = (comment) => {{
          const div = document.createElement("div");
          div.className = "border p-2 mb-2 rounded";
          div.innerHTML = `<strong>${{comment.name}}</strong> - ${{new Date(comment.timestamp).toLocaleString()}}<br>${{comment.content}}`;
          if (comment.children.length) {{
            const childContainer = document.createElement("div");
            childContainer.style.marginLeft = "20px";
            comment.children.forEach(child => childContainer.appendChild(render(child)));
            div.appendChild(childContainer);
          }}
          return div;
        }};

        comments.filter(c => !c.parent_id).forEach(top => {{
          commentsContainer.appendChild(render(top));
        }});
      }});
  }}

  loadComments();
}})();
</script>
"""

            # Inject the script before </body>
            if "</body>" in content:
                content = content.replace("</body>", js_script + "\n</body>")

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"✅ Patched {file_path} with dynamic comment system")


def build_static_site(destination, base_url):
    app = create_app()
    app.config["FREEZER_DESTINATION"] = destination
    app.config["FREEZER_BASE_URL"] = base_url

    freezer = Freezer(app)

    @freezer.register_generator
    def index():
        total_posts = Post.query.count()
        per_page = 10
        total_pages = (total_posts + per_page - 1) // per_page
        for page in range(1, total_pages + 1):
            yield ("post.index", {"page": page})

    freezer.freeze()
    delete_comment_folders(destination)

    if destination == "docs":
        cname_path = os.path.join(destination, "CNAME")
        with open(cname_path, "w") as f:
            f.write("www.ishwargautam1.com.np")

    replace_image_paths(destination)
    patch_contact_form_for_emailjs(destination)
    patch_post_pages_for_comments(destination)


def replace_image_paths(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                updated_content = content.replace(
                    "/static/Images/blank.png", "/static/images/blank.png"
                )
                if content != updated_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                    print(f"Updated image path in: {file_path}")


if __name__ == "__main__":
    # Build for development
    build_static_site(destination="build", base_url="/build/")

    # Build for production
    build_static_site(destination="docs", base_url="/")
