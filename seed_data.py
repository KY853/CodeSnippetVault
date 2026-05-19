"""
批量添加示例代码片段到数据库
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from vault import Vault
from models.snippet import Snippet
from models.category import Category

v = Vault("snippets.db")

# 确保分类存在
for cat_name, desc in [
    ("Python", "Python 相关代码"),
    ("JavaScript", "JavaScript 相关代码"),
    ("前端", "HTML/CSS/React 等"),
    ("后端", "后端服务相关"),
    ("算法", "算法与数据结构"),
    ("工具", "常用工具函数"),
]:
    try:
        v.add_category(Category(cat_name, desc))
    except Exception:
        pass  # 已存在

snippets = [
    # === 算法 ===
    Snippet(
        title="二分查找",
        code='''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

arr = [1, 3, 5, 7, 9, 11]
print(binary_search(arr, 7))  # 输出: 3''',
        language="python",
        tags=["算法", "二分", "搜索"],
        category="算法",
    ),
    Snippet(
        title="快速排序",
        code='''def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

print(quick_sort([3, 6, 8, 10, 1, 2, 1]))''',
        language="python",
        tags=["算法", "排序"],
        category="算法",
    ),
    # === Python ===
    Snippet(
        title="列表去重（保留顺序）",
        code='''def unique_ordered(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

print(unique_ordered([3, 1, 2, 1, 3, 4]))  # [3, 1, 2, 4]''',
        language="python",
        tags=["Python", "列表", "去重", "工具"],
        category="Python",
    ),
    Snippet(
        title="斐波那契数列生成器",
        code='''def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print(list(fibonacci(10)))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]''',
        language="python",
        tags=["算法", "Python", "生成器"],
        category="算法",
    ),
    Snippet(
        title="装饰器 - 计时器",
        code='''import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} 耗时: {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_sum(n):
    return sum(range(n))

slow_sum(10_000_000)''',
        language="python",
        tags=["Python", "装饰器", "性能"],
        category="Python",
    ),
    Snippet(
        title="单例模式（元类实现）",
        code='''class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=SingletonMeta):
    def __init__(self):
        self.settings = {}

a = Config()
b = Config()
print(a is b)  # True''',
        language="python",
        tags=["Python", "设计模式", "单例"],
        category="Python",
    ),
    Snippet(
        title="Flask 请求参数校验",
        code='''from functools import wraps
from flask import request, jsonify

def validate_params(*required):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            missing = [p for p in required if p not in data]
            if missing:
                return jsonify({"error": f"缺少参数: {', '.join(missing)}"}), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator''',
        language="python",
        tags=["Flask", "后端", "校验"],
        category="后端",
    ),
    # === JavaScript ===
    Snippet(
        title="防抖函数",
        code='''function debounce(fn, delay = 300) {
    let timer = null;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// input.addEventListener("input", debounce(handleSearch, 500));''',
        language="javascript",
        tags=["JavaScript", "防抖", "性能"],
        category="JavaScript",
    ),
    Snippet(
        title="节流函数",
        code='''function throttle(fn, interval = 300) {
    let last = 0;
    return function (...args) {
        const now = Date.now();
        if (now - last >= interval) {
            last = now;
            fn.apply(this, args);
        }
    };
}

// window.addEventListener("scroll", throttle(handleScroll, 200));''',
        language="javascript",
        tags=["JavaScript", "节流", "性能"],
        category="JavaScript",
    ),
    Snippet(
        title="深拷贝对象（防循环引用）",
        code='''function deepClone(obj, map = new WeakMap()) {
    if (obj === null || typeof obj !== "object") return obj;
    if (map.has(obj)) return map.get(obj);

    const clone = Array.isArray(obj) ? [] : {};
    map.set(obj, clone);

    for (const key of Object.keys(obj)) {
        clone[key] = deepClone(obj[key], map);
    }
    return clone;
}

const obj = { a: 1, b: { c: 2 } };
const cloned = deepClone(obj);
console.log(cloned.b === obj.b); // false''',
        language="javascript",
        tags=["JavaScript", "工具", "深拷贝"],
        category="JavaScript",
    ),
    # === 前端 ===
    Snippet(
        title="CSS 居中方案汇总",
        code='''/* Flexbox（推荐） */
.container {
    display: flex;
    justify-content: center;
    align-items: center;
}

/* Grid */
.container {
    display: grid;
    place-items: center;
}

/* 绝对定位 + transform */
.parent { position: relative; }
.child {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
}''',
        language="css",
        tags=["CSS", "居中", "布局"],
        category="前端",
    ),
    Snippet(
        title="React 带历史记录的状态 Hook",
        code='''import { useState, useCallback } from "react";

function useHistoryState(initialValue) {
    const [state, setState] = useState(initialValue);
    const [history, setHistory] = useState([initialValue]);

    const set = useCallback((newValue) => {
        setState(newValue);
        setHistory(prev => [...prev, newValue]);
    }, []);

    const undo = useCallback(() => {
        if (history.length > 1) {
            const h = [...history];
            h.pop();
            setState(h[h.length - 1]);
            setHistory(h);
        }
    }, [history]);

    return [state, set, undo, history];
}''',
        language="javascript",
        tags=["React", "Hook", "状态管理"],
        category="前端",
    ),
    Snippet(
        title="带超时的 fetch 封装",
        code='''async function request(url, options = {}) {
    const { timeout = 5000, ...fetchOptions } = options;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
        const res = await fetch(url, {
            ...fetchOptions, signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } finally {
        clearTimeout(timer);
    }
}''',
        language="javascript",
        tags=["前端", "HTTP", "工具"],
        category="前端",
    ),
    # === 后端 ===
    Snippet(
        title="Dockerfile 最佳实践",
        code='''FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]''',
        language="text",
        tags=["Docker", "后端", "部署"],
        category="后端",
    ),
    Snippet(
        title="SQLAlchemy 通用分页",
        code='''def paginate(query, page=1, per_page=20):
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }''',
        language="python",
        tags=["SQLAlchemy", "后端", "分页"],
        category="后端",
    ),
    # === 工具 ===
    Snippet(
        title="JSON 文件读写工具类",
        code='''import json, os

class JsonFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self._data = self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            return {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()''',
        language="python",
        tags=["工具", "JSON", "文件"],
        category="工具",
    ),
    Snippet(
        title="Git 常用命令速查",
        code='''# 分支操作
git branch feature-x          # 创建分支
git checkout feature-x        # 切换分支
git checkout -b feature-x     # 创建并切换

# 暂存
git stash                     # 暂存当前修改
git stash pop                 # 恢复暂存

# 撤销
git reset --soft HEAD~1       # 撤销上次 commit，保留修改
git reset --hard HEAD~1       # 完全撤销上次 commit

# 日志
git log --oneline --graph     # 图形化日志

# 合并
git merge feature-x           # 合并分支
git rebase main               # 变基''',
        language="text",
        tags=["Git", "工具", "速查"],
        category="工具",
    ),
]

count = 0
for s in snippets:
    try:
        v.add_snippet(s)
        count += 1
        print(f"  [{count}] {s.title}")
    except Exception as e:
        print(f"  x {s.title}: {e}")

print(f"\n共添加 {count} 条示例片段")
