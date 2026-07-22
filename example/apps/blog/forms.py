"""Forms for the blog.

``ModelForm`` subclasses map a model to an HTML form, handling validation and
saving. Using them keeps the views thin: the form owns field definitions and
per-field validation, the view only decides what to do with a valid form.
"""

from django import forms

from apps.blog.models import Comment, Post


class PostForm(forms.ModelForm):
    """Create/update form for :class:`~apps.blog.models.Post`.

    Only author-editable fields are exposed; derived fields (slug,
    timestamps) are computed in ``Post.save`` and never trusted from input.
    """

    class Meta:
        model = Post
        fields = ["title", "body", "tags", "status"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 12}),
        }


class CommentForm(forms.ModelForm):
    """Public form used by readers to submit a comment on a post."""

    class Meta:
        model = Comment
        fields = ["author_name", "email", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4}),
        }
