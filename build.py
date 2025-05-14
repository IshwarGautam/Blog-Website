from flask_frozen import Freezer
from app import create_app
from database.models.post import Post


class CustomFreezer(Freezer):
    def urlpath_to_filepath(self, urlpath):
        filepath = super().urlpath_to_filepath(urlpath)
        if "." not in filepath:
            filepath += ".html"
        return filepath


app = create_app()
freezer = CustomFreezer(app)


@freezer.register_generator
def index():
    total_posts = Post.query.count()
    per_page = 10
    total_pages = (total_posts + per_page - 1) // per_page
    for page in range(1, total_pages + 1):
        yield ("post.index", {"page": page})


if __name__ == "__main__":
    freezer.freeze()
