from django import forms
from django.core import validators
from .models import AutoSuggestModel

class AutoSuggestModelForm(forms.ModelForm):

    class Meta:
        model = AutoSuggestModel
        fields = '__all__'

