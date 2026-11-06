from django.urls import re_path
from .consumers import *

websocket_urlpatterns = [
    re_path(r"ws/messages/(?P<profile_id>\d+)/$", MessageConsumer.as_asgi())
]
