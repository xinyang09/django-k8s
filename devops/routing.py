from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from django.urls import re_path
from devops.consumers import StreamConsumer
from devops.logs_consumers import StreamLogConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            # channels为3.0版本需要使用StreamConsumer.as_asgi 带参数，2.0版本不需要
            re_path(r'^workload/terminal/(?P<namespace>.*)/(?P<pod_name>.*)/(?P<container>.*)/', StreamConsumer.as_asgi()),
            re_path(r'^workload/pods_log/(?P<namespace>.*)/(?P<pod_name>.*)/(?P<container>.*)/', StreamLogConsumer.as_asgi()),
        ])
    ),
})
