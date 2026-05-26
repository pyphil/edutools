from django.contrib import admin
from django.urls import path, include
from mkr import views
from django.contrib.auth.views import LoginView
from django_ratelimit.decorators import ratelimit


# Ratelimit for the admin login view to prevent brute-force attacks
admin_login = admin.site.login

admin_login = ratelimit(
    key="ip",
    rate="10/m",
    method="POST",
    block=True,
)(admin_login)

admin_login = ratelimit(
    key="post:username",
    rate="3/m",
    method="POST",
    block=True,
)(admin_login)

admin.site.login = admin_login

# Ratelimit for the login view to prevent brute-force attacks
login_view = ratelimit(
    key='ip', 
    rate='60/m', 
    block=True,
)(
    ratelimit(
        key="post:username",
        rate="5/m",
        method='POST',
        block=True,
    )(LoginView.as_view(template_name='registration/login.html'))
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('edutools_home.urls')),
    path('wlan-codes/', include('WLANCodesWebApp.urls')),
    path('wlan-codes/codeimport/', include('codeimport.urls')),
    path(('accounts/login/'), login_view, name='login'),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('booking/', include('buchungstool.urls')),
    path('userlist/', include('userlist.urls')),
    path('booking/devices/', include('devicelist.urls')),
    path('booking/settings/', include('buchungstool_settings.urls')),
    path('mkr/', include('mkr.urls')),
    path('qrcode_generator/', include('qrcode_generator.urls')),
    path('library_manager/', include('library_manager.urls')),
    path('appointment/', include('appointment.urls')),
    path('activity/', include('activity.urls')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('logo/<filename>', views.get_logo, name='get_logo'),
    path('dsb/', include('dsb.urls')),
    path('upload/', include('upload.urls')),
]

# urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
