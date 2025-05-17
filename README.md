This is my blog post (made with Python and Flask).

To add comment through backend server

```html
<!-- comment.html [Reply Form] -->
<form method="POST" action="{{ url_for('comment.comment', slug=post.slug) }}" class="reply-form" id="reply-form-{{ comment.id }}">


<!-- post.html [Comment Section] -->
<form method="POST" action="{{ url_for('comment.comment', slug=post.slug) }}" class="p-3 bg-light rounded shadow">

<!-- post.html [Display Comments] -->
<h4>Comments</h4>

{% if comments %}
  {% for comment in comments %}
    {% include 'comment.html' %}
  {% endfor %}
{% else %}
  <p>No comments yet. Be the first to comment!</p>
{% endif %}
```
