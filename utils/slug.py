import re
from unicodedata import normalize
from database.models.post import Post


def slugify(text):
    text = normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def generate_unique_slug(title, post_id=None):
    base_slug = slugify(title)
    slug = base_slug
    count = 1

    while True:
        existing = Post.query.filter_by(slug=slug).first()
        if not existing or (post_id is not None and existing.id == post_id):
            break
        count += 1
        slug = f"{base_slug}-{count}"

    return slug
