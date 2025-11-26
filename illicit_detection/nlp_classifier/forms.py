from django import forms

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
