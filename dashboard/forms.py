from django import forms
from .models import Document
from django.contrib.auth.models import User

class DocumentForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'id': 'tags-field',
            'class': 'form-control',
        })
    )

    class Meta:
        model = Document
        fields = ['title', 'content', 'file', 'visibility', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document Title'}),
            'content': forms.Textarea(attrs={'id': 'quill-editor'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'visibility': forms.Select(attrs={'id': 'visibility-select', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bootstrap style for all fields except content (handled by Quill)
        for field_name in ['title', 'file', 'visibility']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

        # Disable tags unless "tagged" is selected
        if self.data.get('visibility') != 'tagged':
            self.fields['tags'].disabled = True
