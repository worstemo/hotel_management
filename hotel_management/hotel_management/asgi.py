"""
ASGI配置文件

ASGI (Asynchronous Server Gateway Interface) 是Python Web应用的异步服务器网关接口
支持WebSocket、HTTP/2等异步协议，是WSGI的异步版本

用途：
1. 生产环境下使用Daphne、Uvicorn等ASGI服务器部署
2. 支持实时功能，如WebSocket通信
3. 提供更高的并发性能

更多信息请参考:
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_management.settings")

application = get_asgi_application()
