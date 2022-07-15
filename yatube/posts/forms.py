from django import forms

from .models import Post, Group


class PostForm(forms.ModelForm):
    group = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   empty_label='---------',
                                   required=False
                                   )

    class Meta:
        model = Post
        fields = ("text", "group")
