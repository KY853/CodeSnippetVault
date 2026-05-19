"""
交互式命令行界面 - 代码片段管理器 CLI
覆盖基本得分项第7条：选择与循环实现交互式命令行界面
"""
import os
import sys
import shutil
from datetime import datetime

from vault import Vault
from models.snippet import Snippet
from models.category import Category


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    """打印带样式的标题"""
    width = shutil.get_terminal_size().columns
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    print()


def print_menu(options: list):
    """打印菜单选项"""
    for i, (key, desc) in enumerate(options, 1):
        print(f"  {i}. {desc}")
    print()


def get_choice(options: list) -> str:
    """从选项列表中选择"""
    while True:
        try:
            choice = input("\n  请输入选项编号: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
            print("  ❌ 无效选项，请重新输入")
        except ValueError:
            print("  ❌ 请输入数字")


def input_non_empty(prompt: str) -> str:
    """获取非空输入"""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  内容不能为空，请重新输入")


def print_snippet(snippet: Snippet, index: int = None):
    """打印单个片段（格式化输出）"""
    prefix = f"[{index}] " if index else ""
    print(f"\n  {prefix}{'─' * 50}")
    print(f"  📄 {snippet.title}")
    print(f"  🏷️  语言: {snippet.language}  |  分类: {snippet.category}")
    print(f"  🔖 标签: {', '.join(snippet.tags) if snippet.tags else '无'}")
    print(f"  👁️  使用次数: {snippet.usage_count}")
    print(f"  🕐 创建: {snippet.created_at}  |  更新: {snippet.updated_at}")
    print(f"  {'─' * 54}")
    # 打印代码（缩进对齐）
    for line in snippet.code.split('\n'):
        print(f"  {line}")
    print(f"  {'─' * 54}")


def show_snippet_detail(vault: Vault):
    """查看片段详情"""
    snippet_id = input("  请输入片段ID: ").strip()
    if not snippet_id.isdigit():
        print("  ❌ 无效的ID")
        return

    snippet = vault.get_snippet(int(snippet_id))
    if not snippet:
        print("  ❌ 片段不存在")
        return

    clear_screen()
    print_header("片段详情")
    print_snippet(snippet)

    input("\n  按 Enter 返回...")


def list_snippets(vault: Vault):
    """列出所有片段"""
    clear_screen()
    print_header("我的代码片段")

    snippets = vault.get_all_snippets(limit=100)
    if not snippets:
        print("  📭 还没有代码片段，快去添加吧！")
        input("\n  按 Enter 返回...")
        return

    for i, s in enumerate(snippets, 1):
        print(f"  [{s.id:3d}] {s.title}")
        print(f"       {s.language:10s} | {s.category:10s} | 标签: {', '.join(s.tags[:3]) if s.tags else '无'}")
        print()

    total = len(snippets)
    print(f"  📊 共 {total} 条片段")
    choice = input("\n  输入ID查看详情，或直接按Enter返回: ").strip()
    if choice.isdigit():
        snippet = vault.get_snippet(int(choice))
        if snippet:
            clear_screen()
            print_header("片段详情")
            print_snippet(snippet)
            input("\n  按 Enter 返回...")


def add_snippet(vault: Vault):
    """添加代码片段"""
    clear_screen()
    print_header("添加代码片段")

    title = input_non_empty("  标题: ")
    print("  代码 (输入完成后，在新行输入 --- 结束): ")

    code_lines = []
    while True:
        line = input()
        if line.strip() == "---":
            break
        code_lines.append(line)
    code = "\n".join(code_lines)

    if not code.strip():
        print("  ❌ 代码不能为空")
        input("  按 Enter 返回...")
        return

    language = input("  语言 (默认 text): ").strip() or "text"

    tags_str = input("  标签 (逗号分隔): ").strip()
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

    # 显示可用分类
    categories = vault.get_all_categories()
    print("\n  可用分类:")
    for i, c in enumerate(categories, 1):
        print(f"    {i}. {c.name}")
    cat_choice = input("  选择分类编号 或 输入分类名 (默认: 默认): ").strip()
    if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories):
        category = categories[int(cat_choice) - 1].name
    elif cat_choice and cat_choice not in [c.name for c in categories]:
        # 新分类，自动创建
        vault.add_category(Category(cat_choice))
        category = cat_choice
        print(f"  ✅ 已自动创建分类 '{category}'")
    elif cat_choice:
        category = cat_choice
    else:
        category = "默认"

    try:
        snippet = Snippet(title=title, code=code, language=language, tags=tags, category=category)
        snippet_id = vault.add_snippet(snippet)
        print(f"\n  ✅ 添加成功！ID: {snippet_id}")
    except ValueError as e:
        print(f"\n  ❌ 添加失败: {e}")
    except Exception as e:
        print(f"\n  ❌ 添加失败: {e}")

    input("\n  按 Enter 返回...")


def delete_snippet(vault: Vault):
    """删除片段"""
    snippet_id = input("  请输入要删除的片段ID: ").strip()
    if not snippet_id.isdigit():
        print("  ❌ 无效的ID")
        return

    snippet = vault.get_snippet(int(snippet_id))
    if not snippet:
        print("  ❌ 片段不存在")
        return

    clear_screen()
    print_header("确认删除")
    print_snippet(snippet)

    confirm = input("\n  确认删除？(yes/no): ").strip().lower()
    if confirm in ("yes", "y"):
        vault.delete_snippet(int(snippet_id))
        print("  ✅ 删除成功")
    else:
        print("  已取消")

    input("  按 Enter 返回...")


def update_snippet(vault: Vault):
    """更新片段"""
    snippet_id = input("  请输入要编辑的片段ID: ").strip()
    if not snippet_id.isdigit():
        print("  ❌ 无效的ID")
        return

    snippet = vault.get_snippet(int(snippet_id))
    if not snippet:
        print("  ❌ 片段不存在")
        return

    clear_screen()
    print_header("编辑片段")
    print_snippet(snippet)
    print("\n  直接按 Enter 保持原值不变")

    title = input(f"  标题 [{snippet.title}]: ").strip()
    code = input(f"  代码 (输入 --- 编辑，或直接Enter保持不变): ").strip()
    if code == "---":
        print("  输入新代码，--- 结束:")
        code_lines = []
        while True:
            line = input()
            if line.strip() == "---":
                break
            code_lines.append(line)
        code = "\n".join(code_lines)
    else:
        code = ""

    language = input(f"  语言 [{snippet.language}]: ").strip()
    tags_str = input(f"  标签 [{', '.join(snippet.tags)}]: ").strip()
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None
    category = input(f"  分类 [{snippet.category}]: ").strip()

    updates = {}
    if title:
        updates["title"] = title
    if code:
        updates["code"] = code
    if language:
        updates["language"] = language
    if tags is not None:
        updates["tags"] = tags
    if category:
        updates["category"] = category

    if not updates:
        print("  未做任何修改")
    else:
        vault.update_snippet(int(snippet_id), **updates)
        print("  ✅ 更新成功")

    input("  按 Enter 返回...")


def search_snippets(vault: Vault):
    """搜索片段"""
    clear_screen()
    print_header("全文搜索")

    keyword = input("  关键词 (支持正则表达式): ").strip()
    if not keyword:
        return

    print("\n  搜索范围:")
    print("    1. 全部")
    print("    2. 标题")
    print("    3. 代码")
    print("    4. 标签")
    field_map = {"1": "all", "2": "title", "3": "code", "4": "tags"}
    field_choice = input("  请选择 (默认 1): ").strip() or "1"
    field = field_map.get(field_choice, "all")

    results = vault.search(keyword, field)

    if not results:
        print(f"\n  📭 未找到匹配 '{keyword}' 的结果")
        input("  按 Enter 返回...")
        return

    print(f"\n  🔍 找到 {len(results)} 条匹配结果:\n")

    for i, r in enumerate(results, 1):
        s = r["snippet"]
        match_summary = ", ".join(
            f"{m['field']}: ...{m['context']}..."
            for m in r['matches'][:3]
        )
        print(f"  [{s.id:3d}] {s.title}")
        print(f"       {s.language:10s} | 匹配: {match_summary}")
        print()

    choice = input("  输入ID查看详情，或直接按Enter返回: ").strip()
    if choice.isdigit():
        snippet = vault.get_snippet(int(choice))
        if snippet:
            clear_screen()
            print_header("片段详情")
            print_snippet(snippet)
            input("\n  按 Enter 返回...")


def manage_categories(vault: Vault):
    """分类管理"""
    while True:
        clear_screen()
        print_header("分类管理")

        categories = vault.get_all_categories()
        print("  当前分类:\n")
        for i, c in enumerate(categories, 1):
            bar = "█" * min(c.snippet_count, 30) if c.snippet_count else ""
            print(f"  {i:2d}. {c.name:15s} ({c.snippet_count} 个片段) {bar}")

        print()
        print("  1. 创建分类")
        print("  2. 重命名分类")
        print("  3. 删除分类")
        print("  4. 返回主菜单")

        choice = input("\n  请选择: ").strip()
        if choice == "1":
            name = input_non_empty("  分类名: ")
            desc = input("  描述 (可选): ").strip()
            if vault.add_category(Category(name, desc)):
                print(f"  ✅ 分类 '{name}' 创建成功")
            else:
                print(f"  ❌ 分类 '{name}' 已存在")
            input("  按 Enter 继续...")

        elif choice == "2":
            old_name = input_non_empty("  原分类名: ")
            if not vault._category_exists(old_name):
                print("  ❌ 分类不存在")
                input("  按 Enter 继续...")
                continue
            new_name = input_non_empty("  新分类名: ")
            try:
                if vault.rename_category(old_name, new_name):
                    print(f"  ✅ 已重命名为 '{new_name}'")
                else:
                    print(f"  ❌ 重命名失败（分类名可能已存在）")
            except ValueError as e:
                print(f"  ❌ {e}")
            input("  按 Enter 继续...")

        elif choice == "3":
            name = input_non_empty("  要删除的分类名: ")
            try:
                if vault.delete_category(name):
                    print(f"  ✅ 已删除分类 '{name}'，其中的片段已移至'默认'")
                else:
                    print("  ❌ 分类不存在")
            except ValueError as e:
                print(f"  ❌ {e}")
            input("  按 Enter 继续...")

        elif choice == "4":
            break


def manage_tags(vault: Vault):
    """标签管理"""
    clear_screen()
    print_header("标签管理")

    tags = vault.get_all_tags()
    if not tags:
        print("  📭 暂无标签")
    else:
        print("  标签使用频率:\n")
        max_count = max(c for _, c in tags)
        for tag, count in tags:
            bar_len = int(count / max_count * 20) if max_count else 0
            bar = "█" * bar_len
            print(f"  {tag:20s} {count:3d} 次 {bar}")

    input("\n  按 Enter 返回...")


def export_menu(vault: Vault):
    """导出菜单"""
    while True:
        clear_screen()
        print_header("导入 / 导出")

        print("  1. 导出为 JSON")
        print("  2. 导出为 Markdown (带语法高亮)")
        print("  3. 导出为 HTML (带语法高亮)")
        print("  4. 从 JSON 导入")
        print("  5. 返回主菜单")

        choice = input("\n  请选择: ").strip()

        if choice == "1":
            filename = input("  导出文件名 (默认 snippets_export.json): ").strip()
            if not filename:
                filename = f"snippets_export_{datetime.now():%Y%m%d_%H%M%S}.json"
            if not filename.endswith(".json"):
                filename += ".json"
            if vault.export_to_json(filename):
                print(f"  ✅ 已导出到 {filename}")
            else:
                print("  ❌ 导出失败")
            input("  按 Enter 继续...")

        elif choice == "2":
            filename = input("  导出文件名 (默认 snippets_export.md): ").strip()
            if not filename:
                filename = f"snippets_export_{datetime.now():%Y%m%d_%H%M%S}.md"
            if not filename.endswith(".md"):
                filename += ".md"
            if export_to_markdown(vault, filename):
                print(f"  ✅ 已导出到 {filename}")
            else:
                print("  ❌ 导出失败")
            input("  按 Enter 继续...")

        elif choice == "3":
            filename = input("  导出文件名 (默认 snippets_export.html): ").strip()
            if not filename:
                filename = f"snippets_export_{datetime.now():%Y%m%d_%H%M%S}.html"
            if not filename.endswith(".html"):
                filename += ".html"
            if export_to_html(vault, filename):
                print(f"  ✅ 已导出到 {filename}")
            else:
                print("  ❌ 导出失败")
            input("  按 Enter 继续...")

        elif choice == "4":
            filename = input("  导入文件名: ").strip()
            if not filename or not os.path.exists(filename):
                print("  ❌ 文件不存在")
                input("  按 Enter 继续...")
                continue
            merge = input("  是否合并到现有数据？(Y/n): ").strip().lower()
            merge = merge not in ("n", "no")
            try:
                count = vault.import_from_json(filename, merge=merge)
                print(f"  ✅ 成功导入 {count} 条片段")
            except Exception as e:
                print(f"  ❌ 导入失败: {e}")
            input("  按 Enter 继续...")

        elif choice == "5":
            break


def export_to_markdown(vault: Vault, filepath: str) -> bool:
    """导出为带语法高亮标注的 Markdown"""
    snippets = vault.get_all_snippets(limit=10000)
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
        lines.append(f"## {s.title}")
        lines.append("")
        lines.append(f"- **语言**: {s.language}")
        lines.append(f"- **分类**: {s.category}")
        if s.tags:
            lines.append(f"- **标签**: {', '.join(s.tags)}")
        lines.append(f"- **使用次数**: {s.usage_count}")
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


def export_to_html(vault: Vault, filepath: str) -> bool:
    """导出为带 highlight.js 语法高亮的独立 HTML"""
    snippets = vault.get_all_snippets(limit=10000)
    if not snippets:
        return False

    snippet_html = []
    for s in snippets:
        tags_html = " ".join(f'<span class="tag">{t}</span>' for t in s.tags) if s.tags else ""
        snippet_html.append(f"""
    <div class="snippet">
        <div class="snippet-header">
            <h2>{s.title}</h2>
            <div class="meta">
                <span class="lang">{s.language}</span>
                <span class="cat">{s.category}</span>
                {tags_html}
                <span class="usage">使用: {s.usage_count} 次</span>
            </div>
        </div>
        <pre><code class="language-{s.language}">{s.code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</code></pre>
    </div>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码片段集 - Code Snippet Vault</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0d1117; color: #e6edf3; padding: 40px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #58a6ff; margin-bottom: 8px; }}
        .subtitle {{ color: #8b949e; margin-bottom: 30px; }}
        .snippet {{
            background: #161b22; border: 1px solid #30363d; border-radius: 8px;
            margin-bottom: 24px; overflow: hidden;
        }}
        .snippet-header {{
            padding: 16px 20px; border-bottom: 1px solid #30363d;
        }}
        .snippet-header h2 {{ font-size: 1.1rem; margin-bottom: 10px; }}
        .meta {{ display: flex; gap: 10px; flex-wrap: wrap; font-size: 0.8rem; }}
        .lang {{ color: #3fb950; }}
        .cat {{ color: #d29922; }}
        .tag {{ color: #58a6ff; }}
        .usage {{ color: #8b949e; }}
        pre {{ margin: 0; padding: 16px; overflow-x: auto; }}
        code {{ font-family: 'SF Mono', 'JetBrains Mono', monospace; font-size: 0.85rem; }}
        .footer {{ text-align: center; color: #8b949e; margin-top: 40px; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 代码片段集</h1>
        <p class="subtitle">导出于 {datetime.now():%Y-%m-%d %H:%M:%S} | 共 {len(snippets)} 条片段</p>
        {"".join(snippet_html)}
        <div class="footer">Generated by Code Snippet Vault</div>
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


def show_statistics(vault: Vault):
    """显示统计信息"""
    clear_screen()
    print_header("统计信息")

    stats = vault.get_statistics()
    print(f"  📊 代码片段总数:  {stats['total_snippets']}")
    print(f"  📁 分类总数:       {stats['total_categories']}")
    print(f"  🏷️  标签总数:      {stats['total_tags']}")
    print(f"  🔤 最常用语言:     {stats['most_used_language']}")
    if stats['most_popular_snippet']:
        p = stats['most_popular_snippet']
        print(f"  🔥 最热门片段:     [{p['id']}] {p['title']} (使用 {p['usage_count']} 次)")

    input("\n  按 Enter 返回...")


def recommend_snippets(vault: Vault):
    """智能推荐"""
    clear_screen()
    print_header("智能推荐")

    print("  推荐模式:")
    print("    1. 基于全局热门标签")
    print("    2. 基于某个已有片段")
    mode = input("  请选择 (默认 1): ").strip() or "1"

    if mode == "2":
        based_on = input("  输入参考片段ID: ").strip()
        if not based_on.isdigit():
            print("  ❌ 无效的ID")
            input("  按 Enter 返回...")
            return
        recommendations = vault.recommend(limit=10, based_on=int(based_on))
    else:
        recommendations = vault.recommend(limit=10)

    if not recommendations:
        print("  📭 暂无推荐结果（需要更多片段数据）")
        input("  按 Enter 返回...")
        return

    print(f"\n  ⭐ 为你推荐 ({len(recommendations)} 条):\n")
    for i, s in enumerate(recommendations, 1):
        print(f"  [{s.id:3d}] {s.title}")
        print(f"       {s.language:10s} | {s.category:10s} | 使用 {s.usage_count} 次")
        print()

    choice = input("  输入ID查看详情，或直接按Enter返回: ").strip()
    if choice.isdigit():
        snippet = vault.get_snippet(int(choice))
        if snippet:
            clear_screen()
            print_header("片段详情")
            print_snippet(snippet)
            input("\n  按 Enter 返回...")


def main():
    """主循环 - 交互式命令行界面"""
    vault = Vault("snippets.db")

    while True:
        clear_screen()
        print_header("🚀 Code Snippet Vault · 代码片段管理器")
        print(f"  当前数据库: snippets.db")
        print()

        main_menu = [
            ("list", "📋  浏览所有片段"),
            ("add", "➕  添加代码片段"),
            ("search", "🔍  全文搜索"),
            ("detail", "👁️  查看片段详情"),
            ("update", "✏️  编辑片段"),
            ("delete", "🗑️  删除片段"),
            ("category", "📁  分类管理"),
            ("tag", "🏷️  标签管理"),
            ("recommend", "⭐  智能推荐"),
            ("export", "📤  导入/导出"),
            ("stats", "📊  统计信息"),
            ("exit", "🚪  退出"),
        ]

        print_menu(main_menu)
        choice = get_choice(main_menu)

        actions = {
            "list": list_snippets,
            "add": add_snippet,
            "search": search_snippets,
            "detail": show_snippet_detail,
            "update": update_snippet,
            "delete": delete_snippet,
            "category": manage_categories,
            "tag": manage_tags,
            "recommend": recommend_snippets,
            "export": export_menu,
            "stats": show_statistics,
            "exit": lambda v: sys.exit(0),
        }

        action = actions.get(choice)
        if action:
            action(vault)


if __name__ == "__main__":
    main()
