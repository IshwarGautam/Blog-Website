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

        # Ignore template and static files
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
        <style>
        .comment-container {{
            margin-left: 20px;
            margin-bottom: 1rem;
            padding: 1rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #fafafa;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .comment-header {{
            font-weight: 600;
            font-size: 0.95rem;
            color: #333;
            margin-bottom: 0.3rem;
        }}

        .comment-timestamp {{
            font-weight: 400;
            font-size: 0.8rem;
            color: #777;
            margin-left: 0.5rem;
        }}

        .comment-content {{
            margin-bottom: 0.8rem;
            white-space: pre-wrap;
        }}

        .reply-link {{
            font-size: 0.85rem;
            color: #1877f2;
            cursor: pointer;
            user-select: none;
        }}

        .reply-link:hover {{
            text-decoration: underline;
        }}

        .reply-form {{
            margin-top: 0.8rem;
            display: none;
        }}

        .reply-form input,
        .reply-form textarea {{
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }}

        .reply-form button {{
            font-size: 0.85rem;
        }}

        /* Nested replies indent */
        .nested-replies {{
            margin-left: 30px;
            margin-top: 1rem;
        }}

        .comments-wrapper {{
            margin: 20px auto;
            padding: 15px 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            font-family: Arial, sans-serif;
        }}

        .comments-wrapper h4 {{
            margin-bottom: 15px;
            color: #333;
            font-weight: 600;
            font-size: 1.5rem;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }}
        </style>

      <div class="comments-wrapper">
        <h4>Comments</h4>
        <div class="comment-container">
            <p>Loading comments...</p>
        </div>
        </div>

        <script>
        (function () {{
          const form = document.querySelector("form");
          const commentsContainer = document.querySelector(".comment-container");
          if (!form || !commentsContainer) return;

          const slug = "{slug}";
          const submitBtn = form.querySelector("button[type='submit']");

          form.addEventListener("submit", function (e) {{
            e.preventDefault();
            const data = {{
              slug,
              name: form.name.value.trim(),
              content: form.content.value.trim(),
              parent_id: form.parent_id.value || null,
            }};

            if (!data.name || !data.content) {{
              alert("Please fill in your name and comment.");
              return;
            }}

            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = "Posting...";

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
                  const wrapper = document.createElement("div");
                  wrapper.className = "comment-container";

                  const header = document.createElement("div");
                  header.className = "comment-header";
                  header.innerHTML = `<strong>${{escapeHtml(comment.name)}}</strong><span class="comment-timestamp"> - ${{new Date(comment.timestamp).toLocaleString()}}</span>`;
                  wrapper.appendChild(header);

                  const content = document.createElement("div");
                  content.className = "comment-content";
                  content.textContent = comment.content;
                  wrapper.appendChild(content);

                  const replyLink = document.createElement("span");
                  replyLink.className = "reply-link";
                  replyLink.textContent = "Reply";
                  replyLink.onclick = () => toggleReplyForm(`reply-form-${{comment.id}}`);
                  wrapper.appendChild(replyLink);

                  const replyForm = document.createElement("form");
                  replyForm.method = "POST";
                  replyForm.className = "reply-form";
                  replyForm.id = `reply-form-${{comment.id}}`;
                  replyForm.innerHTML = `
                    <input type="hidden" name="parent_id" value="${{comment.id}}" />
                    <input type="text" name="name" placeholder="Your Name" class="form-control form-control-sm" required />
                    <textarea name="content" placeholder="Write a reply..." class="form-control form-control-sm" rows="2" required></textarea>
                    <button type="submit" class="btn btn-sm btn-primary">Post Reply</button>
                  `;
                  replyForm.addEventListener("submit", function (e) {{
                    e.preventDefault();
                    const replyData = {{
                      slug,
                      name: replyForm.name.value.trim(),
                      content: replyForm.content.value.trim(),
                      parent_id: comment.id,
                    }};

                    if (!replyData.name || !replyData.content) {{
                      alert("Please fill in your name and reply.");
                      return;
                    }}

                    const replyBtn = replyForm.querySelector("button");
                    const originalText = replyBtn.textContent;
                    replyBtn.disabled = true;
                    replyBtn.textContent = "Posting...";

                    fetch("/.netlify/functions/submit_comment", {{
                      method: "POST",
                      headers: {{
                        "Content-Type": "application/json",
                      }},
                      body: JSON.stringify(replyData),
                    }})
                      .then(res => {{
                        replyBtn.disabled = false;
                        replyBtn.textContent = originalText;
                        if (res.ok) {{
                          alert("Reply submitted!");
                          replyForm.reset();
                          replyForm.style.display = "none";
                          loadComments();
                        }} else {{
                          return res.text().then(text => alert("Failed: " + text));
                        }}
                      }})
                      .catch(err => {{
                        replyBtn.disabled = false;
                        replyBtn.textContent = originalText;
                        alert("Error: " + err.message);
                      }});
                  }});
                  wrapper.appendChild(replyForm);

                  if (comment.children.length) {{
                    const nested = document.createElement("div");
                    nested.className = "nested-replies";
                    comment.children.forEach(child => nested.appendChild(render(child)));
                    wrapper.appendChild(nested);
                  }}

                  return wrapper;
                }};

                const topLevel = comments.filter(c => !c.parent_id);
                if (topLevel.length === 0) {{
                  commentsContainer.innerHTML = "<p>No comments yet. Be the first to comment!</p>";
                }} else {{
                  topLevel.forEach(c => commentsContainer.appendChild(render(c)));
                }}
              }})
              .catch(err => {{
                commentsContainer.innerHTML = "<p>Failed to load comments.</p>";
                console.error(err);
              }});
          }}

          function toggleReplyForm(id) {{
            const form = document.getElementById(id);
            if (form) {{
              const isHidden = window.getComputedStyle(form).display === "none";
              form.style.display = isHidden ? "block" : "none";
            }}
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

        if "<!-- Post Footer -->" in content:
            content = content.replace(
                "<!-- Post Footer -->", comment_section + "\n<!-- Post Footer -->"
            )
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
