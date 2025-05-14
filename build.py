import os
from app import create_app
from flask_frozen import Freezer
from database.models.post import Post


class CustomFreezer(Freezer):
    def urlpath_to_filepath(self, urlpath):
        filepath = super().urlpath_to_filepath(urlpath)
        if "." not in filepath:
            filepath += ".html"
        return filepath


def build_static_site(destination, base_url):
    app = create_app()
    app.config["FREEZER_DESTINATION"] = destination
    app.config["FREEZER_BASE_URL"] = base_url
    freezer = CustomFreezer(app)

    @freezer.register_generator
    def index():
        total_posts = Post.query.count()
        per_page = 10
        total_pages = (total_posts + per_page - 1) // per_page
        for page in range(1, total_pages + 1):
            yield ("post.index", {"page": page})

    freezer.freeze()

    if destination == "docs":
        cname_path = os.path.join(destination, "CNAME")
        with open(cname_path, "w") as f:
            f.write("www.ishwargautam1.com.np")

    replace_image_paths(destination)


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
