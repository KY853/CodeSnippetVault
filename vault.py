"""
Vault 核心类 - 实现所有接口
"""
import re
import json
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import Counter

from database.db_manager import DatabaseManager
from models.snippet import Snippet
from models.category import Category
from config import SUPPORTED_LANGUAGES


class Vault:
    """代码片段仓库主类"""

    def __init__(self, db_path: str = "snippets.db"):
        self.db = DatabaseManager(db_path)

    def close(self):
        """关闭数据库连接"""
        pass  # SQLite 连接自动管理，无需显式关闭

    # ============================================
    # CRUD 操作
    # ============================================

    def add_snippet(self, snippet: Snippet) -> int:
        """
        添加代码片段
        返回: 新插入片段的ID
        """
        # 验证分类是否存在
        if not self._category_exists(snippet.category):
            raise ValueError(f"分类 '{snippet.category}' 不存在")

        tags_str = ",".join(snippet.tags) if snippet.tags else ""

        query = """
            INSERT INTO snippets (title, code, language, tags, category)
            VALUES (?, ?, ?, ?, ?)
        """
        snippet_id = self.db.execute_update(
            query,
            (snippet.title, snippet.code, snippet.language, tags_str, snippet.category)
        )
        return snippet_id

    def delete_snippet(self, snippet_id: int) -> bool:
        """
        删除代码片段
        返回: 是否删除成功
        """
        query = "DELETE FROM snippets WHERE id = ?"
        rows = self.db.execute_update(query, (snippet_id,))
        return rows > 0

    def update_snippet(self, snippet_id: int, **kwargs) -> bool:
        """
        更新片段字段
        可更新字段: title, code, language, tags, category
        """
        allowed_fields = {"title", "code", "language", "tags", "category"}
        updates = []
        values = []

        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                if field == "tags" and isinstance(value, list):
                    value = ",".join(value)
                values.append(value)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(snippet_id)

        query = f"UPDATE snippets SET {', '.join(updates)} WHERE id = ?"
        rows = self.db.execute_update(query, tuple(values))
        return rows > 0

    def get_snippet(self, snippet_id: int) -> Optional[Snippet]:
        """
        根据ID获取片段，同时 usage_count += 1
        """
        # 增加使用次数
        self.db.execute_update(
            "UPDATE snippets SET usage_count = usage_count + 1 WHERE id = ?",
            (snippet_id,)
        )

        # 获取片段
        query = "SELECT * FROM snippets WHERE id = ?"
        result = self.db.execute_query(query, (snippet_id,))

        if not result:
            return None

        return self._row_to_snippet(result[0])

    def get_all_snippets(self, sort_by: str = "updated_at",
                         limit: int = 100, offset: int = 0) -> List[Snippet]:
        """
        获取片段列表
        sort_by: created_at / updated_at / usage_count / title
        """
        allowed_sort = {"created_at", "updated_at", "usage_count", "title"}
        if sort_by not in allowed_sort:
            sort_by = "updated_at"

        query = f"""
            SELECT * FROM snippets 
            ORDER BY {sort_by} DESC 
            LIMIT ? OFFSET ?
        """
        results = self.db.execute_query(query, (limit, offset))
        return [self._row_to_snippet(row) for row in results]

    # ============================================
    # 搜索功能
    # ============================================

    def search(self, keyword: str, field: str = "all") -> List[Dict]:
        """
        全文搜索：按匹配相似度排序
        
        搜索策略：
        1. 完整关键词匹配（标题/标签精确包含关键词）→ 最高分
        2. 中文单字匹配（标题/标签包含搜索词中的每一个中文字）→ 中分
        3. 中文任意单字匹配（标题/标签包含搜索词中的至少一个中文字）→ 低分
        
        最终按匹配字数从多到少排序。
        """
        if field not in ["all", "title", "code", "tags"]:
            field = "all"

        # 提取关键词中的中文字（"快排" → ['快','排']）
        chinese_chars = [c for c in keyword if '\u4e00' <= c <= '\u9fff']
        search_title = field in ["all", "title"]
        search_tags = field in ["all", "tags"]
        search_code = field in ["all", "code"]

        snippets = self.get_all_snippets(limit=1000)
        results = []

        for snippet in snippets:
            # 计算标题匹配
            title_matched_chars = []
            if search_title and chinese_chars:
                title_matched_chars = [c for c in chinese_chars if c in snippet.title]

            # 计算标签匹配
            all_tag_text = "".join(snippet.tags)
            tag_matched_chars = []
            if search_tags and chinese_chars:
                tag_matched_chars = [c for c in chinese_chars if c in all_tag_text]

            # 计算代码匹配次数（仅精确关键词）
            code_match_count = 0
            if search_code:
                code_match_count = snippet.code.lower().count(keyword.lower())

            # 去重合并匹配到的中文字
            all_matched = list(dict.fromkeys(title_matched_chars + tag_matched_chars))
            matched_count = len(all_matched)
            total_chars = len(chinese_chars)

            # 没有任何匹配 → 跳过
            if matched_count == 0 and code_match_count == 0:
                continue

            # 构建 matches 信息
            matches = []
            if title_matched_chars:
                matches.append({
                    "field": "title",
                    "matched_chars": title_matched_chars,
                    "match_type": "exact" if matched_count == total_chars else "fuzzy",
                })
            if tag_matched_chars:
                matches.append({
                    "field": "tags",
                    "matched_chars": tag_matched_chars,
                    "match_type": "exact" if matched_count == total_chars else "fuzzy",
                })
            if code_match_count > 0:
                matches.append({
                    "field": "code",
                    "match_type": "exact",
                })

            # 计算分数 = 匹配字数 * 权重
            score = matched_count * 100 + code_match_count * 30

            results.append({
                "snippet": snippet,
                "matches": matches,
                "score": score,
                "matched_chars": all_matched,
                "total_chars": total_chars
            })

        # 按匹配字数从多到少排序，再按分数
        results.sort(key=lambda r: (len(r["matched_chars"]), r["score"]), reverse=True)

        return results

    def get_snippets_by_category(self, category: str) -> List[Snippet]:
        """获取指定分类下的所有片段"""
        query = "SELECT * FROM snippets WHERE category = ? ORDER BY updated_at DESC"
        results = self.db.execute_query(query, (category,))
        return [self._row_to_snippet(row) for row in results]

    def get_snippets_by_tag(self, tag: str) -> List[Snippet]:
        """获取包含指定标签的所有片段"""
        query = "SELECT * FROM snippets WHERE tags LIKE ? ORDER BY updated_at DESC"
        results = self.db.execute_query(query, (f"%{tag}%",))
        return [self._row_to_snippet(row) for row in results]

    def get_snippets_by_ids(self, ids: List[int]) -> List[Snippet]:
        """根据ID列表批量获取片段"""
        if not ids:
            return []
        placeholders = ",".join(["?"] * len(ids))
        query = f"SELECT * FROM snippets WHERE id IN ({placeholders}) ORDER BY updated_at DESC"
        results = self.db.execute_query(query, tuple(ids))
        return [self._row_to_snippet(row) for row in results]

    # ============================================
    # 分类管理
    # ============================================

    def add_category(self, category: Category) -> bool:
        """添加新分类"""
        try:
            query = "INSERT INTO categories (name, description) VALUES (?, ?)"
            self.db.execute_update(query, (category.name, category.description))
            return True
        except sqlite3.IntegrityError:
            return False  # 分类已存在，返回 False

    def delete_category(self, category_name: str) -> bool:
        """删除分类，该分类下的片段移动到'默认'分类"""
        if category_name == "默认":
            raise ValueError("不能删除默认分类")

        # 将片段移到默认分类
        self.db.execute_update(
            "UPDATE snippets SET category = '默认' WHERE category = ?",
            (category_name,)
        )

        # 删除分类
        query = "DELETE FROM categories WHERE name = ?"
        rows = self.db.execute_update(query, (category_name,))
        return rows > 0

    def get_all_categories(self) -> List[Category]:
        """获取所有分类（含片段数量）"""
        query = """
            SELECT c.name, c.description, COUNT(s.id) as snippet_count
            FROM categories c
            LEFT JOIN snippets s ON c.name = s.category
            GROUP BY c.name
            ORDER BY snippet_count DESC
        """
        results = self.db.execute_query(query)
        categories = []
        for row in results:
            cat = Category(row[0], row[1])
            cat.snippet_count = row[2]
            categories.append(cat)
        return categories

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """重命名分类"""
        if old_name == "默认":
            raise ValueError("不能重命名默认分类")

        # 检查新分类名是否已存在
        if self._category_exists(new_name):
            return False

        # 更新分类名
        self.db.execute_update(
            "UPDATE categories SET name = ? WHERE name = ?",
            (new_name, old_name)
        )

        # 更新片段中的分类名
        self.db.execute_update(
            "UPDATE snippets SET category = ? WHERE category = ?",
            (new_name, old_name)
        )

        return True

    # ============================================
    # 标签管理
    # ============================================

    def get_all_tags(self) -> List[Tuple[str, int]]:
        """获取所有标签及使用频率，按频率降序"""
        query = "SELECT tags FROM snippets WHERE tags != ''"
        results = self.db.execute_query(query)

        tag_counter = Counter()
        for row in results:
            tags = row[0].split(",") if row[0] else []
            for tag in tags:
                tag_counter[tag.strip()] += 1

        return sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)

    def add_tag_to_snippet(self, snippet_id: int, tag: str) -> bool:
        """为片段添加标签"""
        snippet = self.get_snippet(snippet_id)
        if not snippet:
            return False

        if tag not in snippet.tags:
            snippet.tags.append(tag)
            return self.update_snippet(snippet_id, tags=snippet.tags)
        return True

    def remove_tag_from_snippet(self, snippet_id: int, tag: str) -> bool:
        """移除片段的某个标签"""
        snippet = self.get_snippet(snippet_id)
        if not snippet:
            return False

        if tag in snippet.tags:
            snippet.tags.remove(tag)
            return self.update_snippet(snippet_id, tags=snippet.tags)
        return True

    # ============================================
    # 智能推荐（加分项★1）
    # ============================================

    def recommend(self, limit: int = 5, based_on: int = None) -> List[Snippet]:
        """
        基于标签和使用频率的智能推荐
        """
        all_snippets = self.get_all_snippets(limit=1000)

        if not all_snippets:
            return []

        # 获取目标标签
        target_tags = set()
        if based_on:
            base = self.get_snippet(based_on)
            if base:
                target_tags = set(base.tags)

        # 如果没有based_on或找不到，使用全局高频标签
        if not target_tags:
            top_tags = self.get_all_tags()[:3]
            target_tags = {tag for tag, _ in top_tags}

        # 计算每个片段的推荐分数
        scored = []
        for snippet in all_snippets:
            if based_on and snippet.id == based_on:
                continue

            tag_overlap = len(set(snippet.tags) & target_tags)
            score = tag_overlap * 10 + snippet.usage_count

            if score > 0:
                scored.append((score, snippet))

        # 按分数排序
        scored.sort(key=lambda x: x[0], reverse=True)

        return [snippet for _, snippet in scored[:limit]]

    # ============================================
    # 文件导入导出
    # ============================================

    def export_to_json(self, filepath: str, snippet_ids: List[int] = None) -> bool:
        """导出片段到JSON文件"""
        if snippet_ids:
            snippets = [self.get_snippet(sid) for sid in snippet_ids if self.get_snippet(sid)]
        else:
            snippets = self.get_all_snippets(limit=10000)

        data = {
            "version": "1.0",
            "export_time": datetime.now().isoformat(),
            "snippets": [s.to_dict(as_list=False) for s in snippets]
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def import_from_json(self, filepath: str, merge: bool = True) -> int:
        """从JSON文件导入片段"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return 0

        if not merge:
            # 清空现有数据
            self.db.execute_update("DELETE FROM snippets")

        count = 0
        for snippet_data in data.get("snippets", []):
            # 检查是否重复（相同title和code）
            if merge and self._is_duplicate(snippet_data["title"], snippet_data["code"]):
                continue

            snippet = Snippet.from_dict(snippet_data)
            self.add_snippet(snippet)
            count += 1

        return count

    # ============================================
    # 统计功能
    # ============================================

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = self.db.execute_query("SELECT COUNT(*) FROM snippets")[0][0]

        # 最常用语言
        lang_result = self.db.execute_query(
            "SELECT language, COUNT(*) as cnt FROM snippets GROUP BY language ORDER BY cnt DESC LIMIT 1"
        )
        most_used_lang = lang_result[0][0] if lang_result else "None"

        # 最热门片段（前5）
        popular_rows = self.db.execute_query(
            "SELECT id, title, usage_count FROM snippets ORDER BY usage_count DESC LIMIT 5"
        )
        most_popular = [
            {"id": r[0], "title": r[1], "usage_count": r[2]}
            for r in popular_rows
        ] if popular_rows else []

        # 分类统计
        categories = self.get_all_categories()

        # 标签统计
        tags = self.get_all_tags()

        return {
            "total_snippets": total,
            "total_categories": len(categories),
            "total_tags": len(tags),
            "most_used_language": most_used_lang,
            "most_popular_snippets": most_popular
        }

    # ============================================
    # 私有辅助方法
    # ============================================

    def _row_to_snippet(self, row: tuple) -> Snippet:
        """将数据库行转换为Snippet对象"""
        tags = [t.strip() for t in row[4].split(",") if t.strip()] if row[4] else []

        snippet = Snippet(
            title=row[1],
            code=row[2],
            language=row[3],
            tags=tags,
            category=row[5]
        )
        snippet.id = row[0]
        snippet.usage_count = row[6]
        snippet.created_at = row[7]
        snippet.updated_at = row[8]
        return snippet

    def _category_exists(self, name: str) -> bool:
        """检查分类是否存在"""
        result = self.db.execute_query(
            "SELECT 1 FROM categories WHERE name = ?", (name,)
        )
        return len(result) > 0

    def _is_duplicate(self, title: str, code: str) -> bool:
        """检查是否重复"""
        result = self.db.execute_query(
            "SELECT 1 FROM snippets WHERE title = ? AND code = ?",
            (title, code)
        )
        return len(result) > 0

    def _get_context(self, text: str, start: int, end: int, max_len: int = 50) -> str:
        """获取匹配位置的上下文"""
        context_start = max(0, start - 20)
        context_end = min(len(text), end + 20)

        prefix = "..." if context_start > 0 else ""
        suffix = "..." if context_end < len(text) else ""

        return f"{prefix}{text[context_start:context_end]}{suffix}"