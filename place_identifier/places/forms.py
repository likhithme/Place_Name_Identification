from django import forms

class SentenceForm(forms.Form):
    sentence = forms.CharField(label='Enter a sentence', max_length=200, widget=forms.TextInput(attrs={'placeholder': 'Enter a sentence containing place names'}))
