from buchungstool_settings.models import Setting


def add_institution(request):
    try:
        obj = Setting.objects.get(name='settings')
        return {
            'institution_name': obj.institution,
            'institution_logo': obj.logo,
            }
    except Setting.DoesNotExist:
        return {
            'institution_name': "",
            'institution_logo': "",
            }


def get_logout_url(request):
    try:
        settings = Setting.objects.filter(name='settings').first()
        access_token = settings.access_token
    except AttributeError:
        LOGOUT_REDIRECT_URL = "/"
    else:
        if access_token == "":
            LOGOUT_REDIRECT_URL = "/"
        else:
            LOGOUT_REDIRECT_URL = "/?access=" + access_token
    
    return {
        'LOGOUT_REDIRECT_URL': LOGOUT_REDIRECT_URL
    }
