"""
Vault 核心类 - 实现所有接口
"""
import re
import json
import sqlite3
import math
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict

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
    # 智能推荐（多维度混合算法 + 可解释性）
    # ============================================

    def _compute_tfidf_tag_weights(self) -> Dict[str, float]:
        """
        计算标签的 TF-IDF 权重
        返回 Dict[tag, idf_weight]
        """
        all_rows = self.db.execute_query("SELECT tags FROM snippets WHERE tags != ''")
        total_docs = len(all_rows) or 1
        
        # 每个标签出现在多少文档中
        doc_freq: Dict[str, int] = defaultdict(int)
        for row in all_rows:
            tags = set(t.strip() for t in row[0].split(',') if t.strip())
            for tag in tags:
                doc_freq[tag] += 1
        
        # IDF = log(N / df) 平滑处理避免除零
        idf: Dict[str, float] = {}
        for tag, df in doc_freq.items():
            idf[tag] = math.log((total_docs + 1) / (df + 1)) + 1
        return idf

    def _compute_tag_similarity(
        self, 
        snippet_tags: List[str],
        target_tags: set,
        idf_weights: Dict[str, float],
    ) -> float:
        """
        计算带 IDF 权重的标签相似度（Jaccard 加权变体）
        
        weighted_jaccard = sum(idf(common)) / sum(idf(union))
        """
        if not target_tags or not snippet_tags:
            return 0.0
        
        tag_set = set(snippet_tags)
        common = tag_set & target_tags
        union = tag_set | target_tags
        
        if not union:
            return 0.0
        
        num = sum(idf_weights.get(t, 1.0) for t in common)
        den = sum(idf_weights.get(t, 1.0) for t in union)
        return num / den if den > 0 else 0.0

    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """
        简单文本相似度：基于标题关键词重叠（无 embedding）
        提取标题中的中文词 + 英文单词
        """
        def tokenize(s: str) -> set:
            s = s.lower()
            # 提取中文和英文 token
            chinese = set(c for c in s if '\u4e00' <= c <= '\u9fff')
            # 英文单词按空格/标点切分
            english = set(re.findall(r'[a-z0-9_]+', s))
            return chinese | english
        
        tokens1 = tokenize(text1)
        tokens2 = tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0
        
        common = tokens1 & tokens2
        union = tokens1 | tokens2
        return len(common) / len(union) if union else 0.0

    def _compute_recency(self, updated_at: Optional[str]) -> float:
        """
        时效性分数：越近更新时间越高
        按天衰减，30天后趋近于0
        """
        if not updated_at:
            return 0.0
        try:
            dt = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            delta_days = (now - dt).days
            # 30天半衰期
            return math.exp(-delta_days / 30)
        except ValueError:
            return 0.0

    def recommend(
        self, 
        limit: int = 5, 
        based_on: int = None,
        include_scores: bool = False,
    ) -> List[Any]:
        """
        多维度混合智能推荐算法。
        
        特征维度：
        1. 标签语义匹配（TF-IDF 加权 Jaccard）       — 40%
        2. 标题文本相似度（基于关键词重叠）          — 10%
        3. 分类接近度（同一分类 + 同语言 + 额外分）— 15%
        4. 使用热度（对数归一化使用频率）            — 20%
        5. 时效性（30天指数衰减）                    — 10%
        6. 多样性惩罚（同类别不超过 50%）             — 5%
        
        Args:
            limit: 返回数量
            based_on: 基于某个片段推荐，None 则基于全局热门标签
            include_scores: 返回详细评分信息
        
        Returns:
            List[Snippet] or List[Dict]（当 include_scores=True）
        """
        all_snippets = self.get_all_snippets(limit=1000)
        if not all_snippets:
            return []

        # ── 1. 计算全局 IDF 权重 ──
        idf_weights = self._compute_tfidf_tag_weights()

        # ── 2. 确定目标特征 ──
        target_tags: set = set()
        target_title: str = ""
        target_category: str = ""
        target_language: str = ""

        if based_on:
            rows = self.db.execute_query(
                "SELECT tags, title, category, language FROM snippets WHERE id = ?",
                (based_on,)
            )
            if rows:
                tags_str = rows[0][0]
                target_tags = set(
                    t.strip() for t in tags_str.split(",") if t.strip()
                ) if tags_str else set()
                target_title = rows[0][1]
                target_category = rows[0][2]
                target_language = rows[0][3]

        # 如果没有 based_on 或 based_on 无标签，用全局热门标签
        if not target_tags:
            top_tags = self.get_all_tags()[:5]
            target_tags = {tag for tag, _ in top_tags}

        # ── 3. 计算全局特征统计数据（用于归一化） ──
        max_usage = max((s.usage_count for s in all_snippets), default=1)
        max_usage = max(max_usage, 1)

        # ── 4. 对每个片段评分 ──
        scored: List[Tuple[float, Snippet, Dict[str, float]]] = []
        category_count: Dict[str, int] = defaultdict(int)

        for snippet in all_snippets:
            if based_on and snippet.id == based_on:
                continue

            # 维度①：标签语义匹配（40%）
            tag_score = self._compute_tag_similarity(
                snippet.tags, target_tags, idf_weights
            )

            # 维度②：标题文本相似度（10%）
            title_score = self._compute_text_similarity(
                snippet.title, target_title or snippet.title
            ) if target_title else 0.0

            # 维度③：分类+语言接近度（15%）
            category_boost = 0.0
            if target_category and snippet.category == target_category:
                category_boost = 0.08
            if target_language and snippet.language == target_language:
                category_boost += 0.07
            cat_lang_score = category_boost

            # 维度④：使用热度（20%）— 对数归一化更平滑
            usage_norm = math.log(1 + snippet.usage_count) / math.log(1 + max_usage)
            usage_norm = max(0.0, min(usage_norm, 1.0))

            # 维度⑤：时效性（10%）
            recency_score = self._compute_recency(snippet.updated_at)

            # ── 综合得分：可配置权重 ──
            score = (
                0.40 * tag_score +
                0.10 * title_score +
                0.15 * cat_lang_score +
                0.20 * usage_norm +
                0.10 * recency_score
            )

            detail = {
                "tag_match": round(tag_score, 4),
                "title_similarity": round(title_score, 4),
                "cat_lang_match": round(cat_lang_score, 4),
                "usage_heat": round(usage_norm, 4),
                "recency": round(recency_score, 4),
            }

            if score > 0:
                scored.append((score, snippet, detail))
                category_count[snippet.category] += 1

        # ── 5. 多样性重排序 ──
        scored.sort(key=lambda x: x[0], reverse=True)

        final: List[Any] = []
        final_cats: Dict[str, int] = defaultdict(int)
        limit_left = limit

        for score, snippet, detail in scored:
            if len(final) >= limit:
                break

            # 多样性惩罚：同类不超过 50%
            cat = snippet.category
            max_of_cat = max(limit // 2, 1)
            if final_cats[cat] >= max_of_cat:
                # 如果同类超额，检查后面是否还有不同类的可以替代
                continue

            final_cats[cat] += 1
            if include_scores:
                final.append({
                    "snippet": snippet,
                    "score": round(score, 4),
                    "details": detail,
                    "reasons": self._generate_reasons(detail, snippet, target_tags),
                })
            else:
                final.append(snippet)

        return final

    def _generate_reasons(
        self,
        detail: Dict[str, float],
        snippet: Snippet,
        target_tags: set,
    ) -> List[str]:
        """根据评分细节生成可读的推荐理由"""
        reasons = []
        
        # 标签匹配
        common_tags = set(snippet.tags) & target_tags
        if common_tags:
            tags_str = "、".join(sorted(common_tags))
            reasons.append(f"\u6807\u7b7e\u5339\u914d\uff1a\u201c{tags_str}\u201d")
        
        # 分类匹配
        if detail.get("cat_lang_match", 0) > 0:
            reasons.append(f"同分类/语言")
        
        # 热门度
        if snippet.usage_count >= 3:
            reasons.append(f"热度高（使用 {snippet.usage_count} 次）")
        
        # 时效性
        if detail.get("recency", 0) > 0.5:
            reasons.append("最近更新")
        
        return reasons[:3]  # 最多3条理由

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
    # Markdown / HTML 导出（带语法高亮）
    # ============================================

    def export_to_markdown(self, filepath: str, snippets: List[Snippet] = None) -> bool:
        """导出为带语法高亮标注的 Markdown"""
        if snippets is None:
            snippets = self.get_all_snippets(limit=10000)
        if not snippets:
            return False

        lines = [
            "# 代码片段集 (Code Snippet Vault)",
            "",
            f"导出时间: {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"共 {len(snippets)} 条片段",
            "",
            "---",
            "",
        ]

        for s in snippets:
            tags_str = ", ".join(s.tags) if s.tags else "无"
            lines.append(f"## {s.title}")
            lines.append("")
            lines.append(f"- **语言**: {s.language}  |  **分类**: {s.category}  |  **标签**: {tags_str}  |  **使用**: {s.usage_count} 次")
            lines.append("")
            lines.append(f"```{s.language}")
            lines.append(s.code)
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception:
            return False

    def export_to_html(self, filepath: str, snippets: List[Snippet] = None) -> bool:
        """导出为带 highlight.js 语法高亮的独立 HTML"""
        if snippets is None:
            snippets = self.get_all_snippets(limit=10000)
        if not snippets:
            return False

        snippet_html = []
        for s in snippets:
            code_escaped = s.code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            tags_html = " ".join(f'<span class="tag">{t}</span>' for t in s.tags) if s.tags else ""
            snippet_html.append(f"""
    <div class="snippet">
        <h2>{s.title}</h2>
        <div class="meta">
            <span class="lang">{s.language}</span>
            <span class="cat">{s.category}</span>
            {tags_html}
            <span class="usage">使用 {s.usage_count} 次</span>
        </div>
        <pre><code class="language-{s.language}">{code_escaped}</code></pre>
    </div>""")

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>代码片段集 - Code Snippet Vault</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; padding: 40px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #58a6ff; margin-bottom: 8px; }}
        .subtitle {{ color: #8b949e; margin-bottom: 30px; }}
        .snippet {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 24px; padding: 20px; }}
        .snippet h2 {{ color: #58a6ff; font-size: 1.2rem; margin: 0 0 10px 0; }}
        .meta {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 12px; display: flex; gap: 12px; flex-wrap: wrap; }}
        .tag {{ display: inline-block; padding: 2px 8px; background: rgba(88,166,255,.15); color: #58a6ff; border-radius: 20px; font-size: 0.75rem; }}
        pre {{ margin: 0; border-radius: 6px; overflow-x: auto; }}
        code {{ font-family: 'SF Mono', 'JetBrains Mono', monospace; font-size: 0.85rem; }}
    </style>
</head>
<body>
<div class="container">
    <h1>代码片段集</h1>
    <div class="subtitle">导出时间: {datetime.now():%Y-%m-%d %H:%M:%S} | 共 {len(snippets)} 条片段</div>
    {''.join(snippet_html)}
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>hljs.highlightAll();</script>
</body>
</html>"""

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            return True
        except Exception:
            return False

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