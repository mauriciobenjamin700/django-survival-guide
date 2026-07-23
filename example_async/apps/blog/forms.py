"""Forms for the async blog.

Forms themselves are sync (validation is CPU work). In the async views we call
``form.is_valid()`` normally and then persist with the async ORM (``acreate``).
"""

from django import forms

from apps.blog.models import Comment


class CommentForm(forms.ModelForm):
    """Public form used by readers to submit a comment on a post."""

    class Meta:
        model = Comment
        fields = ["author_name", "email", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4}),
        }
