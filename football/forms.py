"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FOOTBALL/FORMS.py
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from django import forms

class DropDownForm(forms.Form):
    drop_down = forms.ChoiceField()

