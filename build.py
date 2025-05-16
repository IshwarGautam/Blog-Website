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
    for filename in os.listdir(build_dir):
        if not filename.endswith(".html"):
            continue

        filepath = os.path.join(build_dir, filename)

        # Ignore known template files
        templates_file = {f for f in os.listdir("templates") if f.endswith(".html")}
        extra_files = {"verify-otp.html", "logout.html"}
        templates_file.update(extra_files)

        if filename in templates_file:
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Skip if already patched
        if 'fetch("/.netlify/functions/get_comments' in content:
            print(f"⚠️ Already patched: {filename}")
            continue

        slug = filename.replace(".html", "")

        comment_section = f"""
<h2>Leave a Comment</h2>

<form method="POST" class="p-3 bg-light rounded shadow">
  <input type="hidden" name="parent_id" value="" />

  <div class="form-group">
    <label>Your Name</label>
    <input type="text" name="name" class="form-control" required />
  </div>

  <div class="form-group">
    <label>Your Comment</label>
    <textarea name="content" class="form-control" rows="3" required></textarea>
  </div>

  <button type="submit" class="btn btn-primary">Post Comment</button>
</form>

<hr />

<h3>Comments</h3>
<div id="comments">
  <p>Loading comments...</p>
</div>

<script>
(function () {{
  const form = document.querySelector("form");
  const commentsContainer = document.getElementById("comments");
  if (!form || !commentsContainer) return;

  const slug = "{slug}";
  const submitBtn = form.querySelector("button[type='submit']");

  form.addEventListener("submit", function (e) {{
    e.preventDefault();
    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Posting...";

    const data = {{
      slug,
      name: form.name.value.trim(),
      content: form.content.value.trim(),
      parent_id: form.parent_id.value || null,
    }};

    if (!data.name || !data.content) {{
      alert("Please fill in your name and comment.");
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
      return;
    }}

    fetch("/.netlify/functions/submit_comment", {{
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
      }},
      body: JSON.stringify(data),
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
        alert("Error: " + err.message);
      }});
  }});

  function loadComments() {{
    fetch(`/.netlify/functions/get_comments?slug=${{encodeURIComponent(slug)}}`)
      .then(res => {{
        if (!res.ok) throw new Error("Failed to load comments");
        return res.json();
      }})
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
          div.className = "border";
          div.innerHTML = `<strong>${{escapeHtml(comment.name)}}</strong> - ${{new Date(comment.timestamp).toLocaleString()}}<br>${{escapeHtml(comment.content)}}`;
          if (comment.children.length) {{
            const childContainer = document.createElement("div");
            childContainer.style.marginLeft = "20px";
            comment.children.forEach(child => childContainer.appendChild(render(child)));
            div.appendChild(childContainer);
          }}
          return div;
        }};

        const topLevel = comments.filter(c => !c.parent_id);
        if (topLevel.length === 0) {{
          commentsContainer.innerHTML = "<p>No comments yet. Be the first to comment!</p>";
        }} else {{
          topLevel.forEach(top => {{
            commentsContainer.appendChild(render(top));
          }});
        }}
      }})
      .catch(err => {{
        commentsContainer.innerHTML = "<p>Failed to load comments.</p>";
        console.error(err);
      }});
  }}

  function escapeHtml(text) {{
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }}

  loadComments();
}})();
</script>
"""

        # Insert comment section before </body>
        if "</body>" in content:
            content = content.replace("</body>", comment_section + "\n</body>")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Patched {filename} with comment section.")
        else:
            print(f"⚠️ No </body> tag found in {filename}, skipping.")


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
