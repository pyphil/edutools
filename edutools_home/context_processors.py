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


def get_legal_notice(request):
    try:
        obj = EdutoolsSetting.objects.get(name='settings')
        return {
            'legal_notice': obj.legal_notice,
            }
    except EdutoolsSetting.DoesNotExist:
        return {
            'legal_notice': '#',
            }


def get_privacy_policy(request):
    try:
        obj = EdutoolsSetting.objects.get(name='settings')
        return {
            'privacy_policy': obj.privacy_policy,
            }
    except EdutoolsSetting.DoesNotExist:
        return {
            'privacy_policy': '#',
            }
