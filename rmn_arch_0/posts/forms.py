from django import forms

from dal.autocomplete import ModelSelect2

from .models import Post, Comment, Report


class StrictNewlineCharField(forms.CharField):
    """
    Strips \r from the value to be compatible with all broswer newline characters
    """
    widget = forms.Textarea
    def to_python(self, value):
        return super().to_python(value).replace('\r', '')


class PostForm(forms.ModelForm):
    """
    Form to create posts
    """
    images = forms.ImageField(widget=forms.FileInput(attrs={'multiple': True}))

    class Meta:
        model = Post
        fields = ['images', 'description', 'anonymous']
        field_classes = {'description': StrictNewlineCharField}


class CommentForm(forms.ModelForm):
    """
    Form to create comments
    """
    class Meta:
        model = Comment
        fields = ['description']
        field_classes = {'description': StrictNewlineCharField}


class ReportForm(forms.ModelForm):
    """
    Form to create reports
    """
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {'reason': forms.RadioSelect()}
        field_classes = {'description': StrictNewlineCharField}
