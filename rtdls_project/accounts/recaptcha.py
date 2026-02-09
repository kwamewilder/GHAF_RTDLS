import json
from typing import Tuple
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


GENERIC_ERROR = 'Unable to verify reCAPTCHA. Please try again.'


def verify_recaptcha_token(*, token: str, remote_ip: str | None = None) -> Tuple[bool, str]:
    secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', '').strip()
    verify_url = getattr(settings, 'RECAPTCHA_VERIFY_URL', 'https://www.google.com/recaptcha/api/siteverify')
    timeout = int(getattr(settings, 'RECAPTCHA_TIMEOUT_SECONDS', 5))

    if not secret:
        return False, 'reCAPTCHA secret key is not configured.'

    payload = {'secret': secret, 'response': token}
    if remote_ip:
        payload['remoteip'] = remote_ip

    request_data = urlencode(payload).encode('utf-8')
    request = Request(
        verify_url,
        data=request_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (URLError, TimeoutError, ValueError):
        return False, GENERIC_ERROR

    if data.get('success'):
        return True, ''

    error_codes = data.get('error-codes', [])
    if 'timeout-or-duplicate' in error_codes:
        return False, 'reCAPTCHA expired. Please retry the challenge.'
    if 'missing-input-response' in error_codes:
        return False, 'Please complete the reCAPTCHA challenge.'
    if 'invalid-input-response' in error_codes:
        return False, 'Invalid reCAPTCHA response. Please retry.'

    return False, GENERIC_ERROR
