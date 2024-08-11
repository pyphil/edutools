from django.contrib import admin
from django.urls import path, include
from mkr import views
# from .settings import MEDIA_URL, MEDIA_ROOT
# from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('edutools_home.urls')),
    path('wlan-codes/', include('WLANCodesWebApp.urls')),
    path('wlan-codes/codeimport/', include('codeimport.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('booking/', include('buchungstool.urls')),
    path('userlist/', include('userlist.urls')),
    path('booking/devices/', include('devicelist.urls')),
    path('booking/settings/', include('buchungstool_settings.urls')),
    path('mkr/', include('mkr.urls')),
    path('qrcode_generator/', include('qrcode_generator.urls')),
    path('library_manager/', include('library_manager.urls')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('logo/<filename>', views.get_logo, name='get_logo'),
]

# urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
