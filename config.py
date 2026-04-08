"""
配置文件
"""
import os

# 数据库配置
DB_PATH = os.path.join(os.path.dirname(__file__), "snippets.db")

# 默认分类
DEFAULT_CATEGORIES = [
    ("默认", "未分类的代码片段"),
    ("工作", "工作相关代码"),
    ("学习", "学习笔记代码"),
    ("个人", "个人项目代码"),
]

# 支持的语言列表
SUPPORTED_LANGUAGES = [
    "python", "java", "javascript", "html", "css", "sql",
    "c", "cpp", "go", "rust", "ruby", "php", "json", "yaml",
    "markdown", "text"
]