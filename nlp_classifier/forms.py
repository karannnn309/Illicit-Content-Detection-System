from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, AdminReview

# ========================================
# AUTHENTICATION FORMS
# ========================================
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    organization = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Organization (Optional)'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class AdminReviewForm(forms.ModelForm):
    class Meta:
        model = AdminReview
        fields = ['decision', 'comments']
        widgets = {
            'decision': forms.Select(attrs={
                'class': 'form-control'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add your comments here...'
            })
        }


# ========================================
# CLASSIFICATION FORMS
# ========================================
class TextInputForm(forms.Form):
    text = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}))
    url = forms.URLField(required=False)

class ImageInputForm(forms.Form):
    image = forms.ImageField(required=False)
    image_url = forms.URLField(required=False)
    video = forms.FileField(required=False)
    video_url= forms.URLField(required=False)


class AudioInputForm(forms.Form):
    audio = forms.FileField(required=False, label="Upload Audio (wav/mp3)")

