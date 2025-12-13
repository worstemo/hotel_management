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

# 导入操作系统接口模块，用于设置环境变量
import os

# 从Django核心ASGI模块导入应用获取函数
from django.core.asgi import get_asgi_application

# 设置Django配置模块的环境变量
# 指向项目的settings.py文件
# 如果环境变量中没有设置DJANGO_SETTINGS_MODULE，则使用默认值
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_management.settings")

# 获取ASGI应用实例
# 该应用实例用于ASGI服务器调用
application = get_asgi_application()
