#!/usr/bin/env python
"""
Django项目的命令行管理工具入口文件

【这个文件是干什么的？】
这是Django项目的"遥控器"，用于执行各种管理命令

【常用命令示例】
  python manage.py runserver      # 启动开发服务器
  python manage.py makemigrations # 生成数据库迁移文件
  python manage.py migrate        # 执行数据库迁移
  python manage.py createsuperuser# 创建管理员账户
  python manage.py shell          # 进入Django交互式命令行

【第一行 #!/usr/bin/env python 是什么？】
Shebang（释伴）声明，告诉Linux/Mac系统用Python解释器运行此脚本
Windows系统会忽略这一行
"""

# ================================================================
# 导入模块
# ================================================================

# os模块：提供操作系统相关功能
# 这里用于设置环境变量
import os

# sys模块：提供Python解释器相关功能
# sys.argv 获取命令行参数，如 ['manage.py', 'runserver']
import sys


def main():
    """
    主函数 - 执行Django管理命令
    
    【执行流程】
    1. 设置环境变量，告诉Django使用哪个配置文件
    2. 导入Django的命令行执行器
    3. 执行用户输入的命令
    """
    
    # ----------------------------------------------------------
    # 第一步：设置Django配置文件的环境变量
    # ----------------------------------------------------------
    # os.environ 是一个字典，存储所有环境变量
    # setdefault() 的意思是：如果环境变量不存在，就设置它
    #
    # "DJANGO_SETTINGS_MODULE" 是Django约定的环境变量名
    # "hotel_management.settings" 指向 hotel_management/settings.py
    #
    # 为什么用 setdefault 而不是直接赋值？
    # 因为生产环境可能已经通过其他方式设置了这个变量
    # setdefault 不会覆盖已存在的值
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_management.settings")
    
    # ----------------------------------------------------------
    # 第二步：导入Django命令行执行器
    # ----------------------------------------------------------
    # 使用 try-except 捕获导入错误
    # 如果Django没有安装或环境有问题，会给出友好提示
    try:
        # 从Django核心模块导入命令行执行函数
        # execute_from_command_line 负责解析命令并执行
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 如果导入失败，抛出更友好的错误信息
        # 常见原因：
        #   1. Django没有安装（pip install django）
        #   2. 虚拟环境没有激活
        #   3. PYTHONPATH配置错误
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc  # from exc 保留原始异常信息，便于调试
    
    # ----------------------------------------------------------
    # 第三步：执行命令
    # ----------------------------------------------------------
    # sys.argv 是命令行参数列表
    # 例如运行 python manage.py runserver 8000
    # sys.argv = ['manage.py', 'runserver', '8000']
    #
    # execute_from_command_line 会：
    #   1. 解析 sys.argv 中的命令（如 runserver）
    #   2. 找到对应的命令处理类
    #   3. 执行命令
    execute_from_command_line(sys.argv)


# ================================================================
# Python入口点判断
# ================================================================
#
# 【__name__ 是什么？】
# __name__ 是Python的特殊变量，表示当前模块的名称
#   - 直接运行此文件时：__name__ = "__main__"
#   - 被其他文件导入时：__name__ = "manage"（模块名）
#
# 【为什么需要这个判断？】
# 确保只有直接运行此文件时才执行 main()
# 如果被其他文件 import，就不会自动执行
#
# 【这是Python的标准写法】
# 几乎所有Python程序的入口文件都会使用这个模式
#
if __name__ == "__main__":
    main()
