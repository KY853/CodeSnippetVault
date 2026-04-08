"""
使用示例 - 演示如何使用 Vault 类
"""
from vault import Vault
from models.snippet import Snippet
from models.category import Category


def main():
    # 创建 Vault 实例
    vault = Vault("test.db")

    # 1. 添加分类
    vault.add_category(Category("算法", "各种算法实现"))
    vault.add_category(Category("工具", "常用工具函数"))

    # 2. 添加代码片段
    snippet1 = Snippet(
        title="快速排序",
        code="""def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = [x for x in arr[1:] if x <= pivot]
    right = [x for x in arr[1:] if x > pivot]
    return quicksort(left) + [pivot] + quicksort(right)""",
        language="python",
        tags=["排序", "算法", "面试"],
        category="算法"
    )
    id1 = vault.add_snippet(snippet1)
    print(f"添加成功，ID: {id1}")

    snippet2 = Snippet(
        title="读取文件",
        code="""def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()""",
        language="python",
        tags=["文件", "IO", "工具"],
        category="工具"
    )
    id2 = vault.add_snippet(snippet2)
    print(f"添加成功，ID: {id2}")

    # 3. 搜索
    print("\n--- 搜索 '排序' ---")
    results = vault.search("排序")
    for r in results:
        print(f"找到: {r['snippet'].title}")
        for m in r['matches']:
            print(f"  匹配: {m['context']}")

    # 4. 获取片段（会自动增加使用次数）
    print("\n--- 获取片段 ---")
    s = vault.get_snippet(id1)
    print(f"标题: {s.title}, 使用次数: {s.usage_count}")

    # 5. 智能推荐
    print("\n--- 智能推荐 ---")
    recs = vault.recommend(limit=3)
    for rec in recs:
        print(f"推荐: {rec.title} (使用{rec.usage_count}次)")

    # 6. 统计信息
    print("\n--- 统计信息 ---")
    stats = vault.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # 7. 导出
    vault.export_to_json("export.json")
    print("\n已导出到 export.json")

    # 8. 获取所有标签
    print("\n--- 所有标签 ---")
    tags = vault.get_all_tags()
    for tag, count in tags:
        print(f"{tag}: {count}次")

    vault.close()


if __name__ == "__main__":
    main()