"""
代码片段数据模型
"""
from datetime import datetime
from typing import List, Optional, Dict


class Snippet:
    """代码片段类"""

    def __init__(self, title: str, code: str, language: str,
                 tags: List[str] = None, category: str = "默认"):
        self.id: Optional[int] = None
        self.title: str = title
        self.code: str = code
        self.language: str = language.lower()
        self.tags: List[str] = tags if tags else []
        self.category: str = category
        self.usage_count: int = 0
        self.created_at: Optional[str] = None
        self.updated_at: Optional[str] = None

    def to_dict(self, as_list: bool = True) -> Dict:
        """转换为字典格式"""
        tags_value = self.tags if as_list else (",".join(self.tags) if self.tags else "")
        return {
            "id": self.id,
            "title": self.title,
            "code": self.code,
            "language": self.language,
            "tags": tags_value,
            "category": self.category,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Snippet':
        """从字典创建实例"""
        tags = data.get("tags", "")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        snippet = Snippet(
            title=data["title"],
            code=data["code"],
            language=data["language"],
            tags=tags,
            category=data.get("category", "默认")
        )
        snippet.id = data.get("id")
        snippet.usage_count = data.get("usage_count", 0)
        snippet.created_at = data.get("created_at")
        snippet.updated_at = data.get("updated_at")
        return snippet

    def __repr__(self) -> str:
        return f"<Snippet id={self.id} title={self.title}>"