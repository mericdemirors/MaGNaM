from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings


def verify_google_id_token(token):
    if settings.DISABLE_EXTERNAL_CALLS_FOR_TESTING:
        return
    try:
        payload = id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return payload
    except Exception:
        return None
