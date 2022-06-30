from django import forms
from django.forms import widgets
from django.urls import reverse

from dal.autocomplete import ModelSelect2

from .models import User, Profile, Settings, Relations


class SignupForm(forms.Form):
    """
    Sign up form for collecting additional information
    """
    name = forms.CharField(
        max_length=32, widget=forms.TextInput(attrs={'placeholder': 'Name'}))
    gender = forms.ChoiceField(
        choices=Profile.GENDERS, widget=forms.RadioSelect(), required=False)
    terms = forms.BooleanField()

    field_order = ['username', 'name', 'email', 'password1', 'password2', 'gender', 'terms']

    def signup(self, request, user):
        Profile.objects.create(
            user=user,
            name=self.cleaned_data['name'],
            gender=self.cleaned_data['gender'],
        )
        Settings.objects.create(user=user)
        Relations.objects.create(user=user)
        return
    
    def __init__(self, **kwargs):
        """
        Override init to push terms_and_conditions to after apps have loaded to avoid circular importation
        """
        super().__init__(**kwargs)
        self.fields['terms'].label = f'Agree to our <a href="{reverse("core:terms_and_conditions")}" target="_blank">Terms and Conditions</a>'
        return


class ProfileForm(forms.ModelForm):
    """
    Form to change user profile
    """
    class Meta:
        model = Profile
        exclude = ['user',]
        widgets = {
            'gender': forms.RadioSelect(),
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'image': forms.FileInput(),
            'location': ModelSelect2(url='users:city_autocomplete',
                attrs={
                    'style': 'width:100%',
                    'data-minimum-input-length': 3,
                    'data-placeholder': 'City',
                }),
        }
        labels = {
            'image': 'Profile Image',
        }


class EmailForm(forms.ModelForm):
    """
    Form to change user email
    """
    class Meta:
        model = User
        fields = ['email']


class SettingsForm(forms.ModelForm):
    """
    Form for user to change settings
    """
    class Meta:
        model = Settings
        exclude = ['user']
        widgets = {
            'rec_new_msg': forms.RadioSelect(),
        }
