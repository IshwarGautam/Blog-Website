from flask_frozen import Freezer
from app import create_app


class CustomFreezer(Freezer):
    def urlpath_to_filepath(self, urlpath):
        filepath = super().urlpath_to_filepath(urlpath)
        if "." not in filepath:
            filepath += ".html"
        return filepath


app = create_app()
freezer = CustomFreezer(app)

if __name__ == "__main__":
    freezer.freeze()
