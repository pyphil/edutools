from django.forms import ModelForm
from .models import Upload, UploadLaufband


class UploadForm(ModelForm):
    class Meta:
        model = Upload
        fields = (
            'name',
            'file',
        )


class UploadLaufbandForm(ModelForm):
    class Meta:
        model = UploadLaufband
        fields = (
            'name',
            'text_nz',
            'text_mz',
        )