from django.contrib import admin
from .models import UploadKey, Upload, UploadLaufband

# Register your models here.
admin.site.register(UploadKey)
admin.site.register(Upload)
admin.site.register(UploadLaufband)