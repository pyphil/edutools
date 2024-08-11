from .models import EdutoolsSetting


def get_login_hint(request):
    try:
        obj = EdutoolsSetting.objects.get(name='settings')
        return {
            'login_hint': obj.login_hint,
            }
    except EdutoolsSetting.DoesNotExist:
        return {
            'login_hint': '',
            }
