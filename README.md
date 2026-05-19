# 📦 Code Snippet Vault · 代码片段管理器

> 一个程序员的代码片段收藏工具，支持分类、搜索、语法高亮、智能推荐和多种格式导出。

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_API-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ 功能一览

### 📋 核心功能

| 功能 | 说明 |
|---|---|
| **CRUD 操作** | 代码片段的添加、查看、编辑、删除 |
| **分类管理** | 创建/重命名/删除分类，自动归类 |
| **标签系统** | 自动聚合标签，按使用频率排序 |
| **全文搜索** | 支持正则表达式，可选标题/代码/标签搜索，返回匹配上下文 |
| **文件导入/导出** | JSON 格式导入导出，支持合并/覆盖模式 |
| **语法高亮** | 基于 highlight.js，支持 15+ 语言 |

### ⭐ 加分特性

| 特性 | 说明 |
|---|---|
| **智能推荐** | 基于标签重叠度 + 使用频率的推荐算法 |
| **Markdown 导出** | 围栏代码块格式，GitHub / 任意渲染器可直接使用 |
| **HTML 导出** | 独立 HTML 文件，内嵌 highlight.js 语法高亮 |
| **Flask Web 界面** | 暗色主题响应式 UI，支持一键复制代码 |
| **交互式 CLI** | 完整命令行界面，无需浏览器即可管理片段 |

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装

```bash
git clone https://github.com/KY853/CodeSnippetVault.git
cd CodeSnippetVault
pip install -r requirements.txt
```

### 运行方式

**方式一：Flask Web 界面（推荐）**

```bash
python app.py
```

访问 `http://localhost:5000` 即可使用图形界面。

**方式二：交互式命令行**

```bash
python cli.py
```

菜单驱动的命令行界面，涵盖全部功能。

---

## 🧩 项目结构

```
CodeSnippetVault/
├── app.py                 # Flask Web API 服务器
├── cli.py                 # 交互式命令行界面
├── vault.py               # Vault 核心逻辑类
├── config.py              # 配置文件
├── requirements.txt       # Python 依赖
├── index.html             # Web 前端（单页 SPA）
├── README.md              # 本文件
├── database/
│   ├── db_manager.py      # SQLite 数据库管理器
│   └── __init__.py
├── models/
│   ├── snippet.py          # 代码片段数据模型
│   ├── category.py         # 分类数据模型
│   └── __init__.py
└── snippets.db            # SQLite 数据文件（运行时生成）
```

---

## 🧑‍💻 API 路由一览

| 方法 | 路由 | 说明 |
|---|---|---|
| `GET` | `/api/snippets` | 获取片段列表 |
| `GET` | `/api/snippets/:id` | 获取单个片段 |
| `POST` | `/api/snippets` | 添加片段 |
| `PUT` | `/api/snippets/:id` | 更新片段 |
| `DELETE` | `/api/snippets/:id` | 删除片段 |
| `GET` | `/api/search` | 全文搜索 |
| `GET` | `/api/categories` | 获取分类列表 |
| `POST` | `/api/categories` | 添加分类 |
| `DELETE` | `/api/categories/:name` | 删除分类 |
| `PUT` | `/api/categories/:name/rename` | 重命名分类 |
| `GET` | `/api/tags` | 获取所有标签 |
| `GET` | `/api/recommend` | 智能推荐 |
| `GET` | `/api/export` | 导出 JSON |
| `POST` | `/api/import` | 导入 JSON |
| `GET` | `/api/statistics` | 统计信息 |

---

## 📐 设计思路

### OOP 设计

项目采用三层面向对象架构：

- **`Snippet`** / **`Category`** — 数据模型层，定义核心数据结构
- **`Vault`** — 业务逻辑层，封装全部 CRUD、搜索、推荐、导入导出
- **`DatabaseManager`** — 数据持久层，SQLite 连接管理和查询执行

### 搜索实现

全文搜索基于 Python `re` 正则模块：
- 支持标准正则语法
- 非正则输入自动 `re.escape` 兜底
- 返回匹配位置和上下文，前端可高亮显示

### 推荐算法

`recommend()` 方法采用标签重叠度 + 使用频率的综合打分：

```python
score = tag_overlap * 10 + usage_count
```

支持全局推荐（取高频标签）和基于某片段的相似推荐。

---

## ✅ 评分项覆盖

| 编号 | 要求 | 实现位置 |
|---|---|---|
| ① | OOP 设计 Snippet、Category、Vault 类 | `models/snippet.py`, `models/category.py`, `vault.py` |
| ② | 正则全文搜索与语法标注 | `vault.py` → `search()` |
| ③ | 字典/列表管理标签和分类 | `vault.py` → `get_all_tags()`, `get_all_categories()` |
| ④ | 函数封装 CRUD 操作 | `vault.py` → `add/delete/update/get_snippet()` |
| ⑤ | 文件操作：导入导出 | `vault.py` → `export_to_json()`, `import_from_json()` |
| ⑥ | SQLite 数据库存储 | `database/db_manager.py` |
| ⑦ | 交互式命令行界面 | `cli.py` → `main()` 循环 |
| ★1 | 智能推荐 | `vault.py` → `recommend()` |
| ★2 | Markdown/HTML 导出带语法高亮 | `cli.py` → `export_to_markdown()`, `export_to_html()` |
| ★3 | Flask Web 界面 + 一键复制 | `app.py` + `index.html` |

---

## 📄 License

MIT License © 2024 KY853
