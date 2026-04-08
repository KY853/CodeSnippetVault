"""
使用示例 - 演示如何使用 Vault 类
"""
from vault import Vault
from models.snippet import Snippet
from models.category import Category


def main():
    # 创建 Vault 实例
    vault = Vault("snippets.db")

    # 1. 添加分类（检查是否已存在）
    print("=" * 60)
    print("1. 添加分类")
    print("=" * 60)

    categories_to_add = [
        ("算法", "各种算法实现"),
        ("工具", "常用工具函数"),
    ]

    for name, desc in categories_to_add:
        if vault.add_category(Category(name, desc)):
            print(f"  ✅ 添加分类: {name}")
        else:
            print(f"  ⚠️ 分类已存在: {name}")

    print()

    # 2. 添加代码片段
    print("=" * 60)
    print("2. 添加代码片段")
    print("=" * 60)

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
    print(f"  ✅ 添加成功，ID: {id1}")

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
    print(f"  ✅ 添加成功，ID: {id2}")

    print()

    # 3. 搜索
    print("=" * 60)
    print("3. 搜索 '排序'")
    print("=" * 60)
    results = vault.search("排序")
    for r in results:
        print(f"  找到: {r['snippet'].title}")
        for m in r['matches']:
            print(f"    匹配: {m['context']}")

    print()

    # 4. 获取片段（会自动增加使用次数）
    print("=" * 60)
    print("4. 获取片段")
    print("=" * 60)
    s = vault.get_snippet(id1)
    print(f"  标题: {s.title}, 使用次数: {s.usage_count}")

    print()

    # 5. 智能推荐
    print("=" * 60)
    print("5. 智能推荐")
    print("=" * 60)
    recs = vault.recommend(limit=3)
    for rec in recs:
        print(f"  推荐: {rec.title} (使用{rec.usage_count}次)")

    print()

    # 6. 统计信息
    print("=" * 60)
    print("6. 统计信息")
    print("=" * 60)
    stats = vault.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print()

    # 7. 导出
    print("=" * 60)
    print("7. 导出到 JSON")
    print("=" * 60)
    vault.export_to_json("export.json")
    print("  ✅ 已导出到 export.json")

    print()

    # 8. 获取所有标签
    print("=" * 60)
    print("8. 所有标签")
    print("=" * 60)
    tags = vault.get_all_tags()
    for tag, count in tags:
        print(f"  #{tag}: {count}次")

    vault.close()
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()