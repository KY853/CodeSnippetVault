"""
分类数据模型
"""


class Category:
    """分类类"""

    def __init__(self, name: str, description: str = ""):
        self.name: str = name
        self.description: str = description
        self.snippet_count: int = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "snippet_count": self.snippet_count
        }

    def __repr__(self) -> str:
        return f"<Category name={self.name} count={self.snippet_count}>"