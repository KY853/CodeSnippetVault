"""
Flask Web 服务器 - 代码片段管理器后端 API
"""
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import os
import json
import tempfile
from datetime import datetime

from vault import Vault
from models.snippet import Snippet
from models.category import Category

app = Flask(__name__)
CORS(app)

# 初始化 Vault
vault = Vault("snippets.db")

# HTML 模板（从上面的文件读取）
HTML_TEMPLATE = open('templates/index.html', 'r', encoding='utf-8').read() if os.path.exists(
    'templates/index.html') else None


@app.route('/')
def index():
    """主页"""
    if HTML_TEMPLATE:
        return render_template_string(HTML_TEMPLATE)
    return open('index.html', 'r', encoding='utf-8').read()


# ============================================
# API 路由 - CRUD
# ============================================

@app.route('/api/snippets', methods=['GET'])
def get_snippets():
    """获取片段列表"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort_by = request.args.get('sort_by', 'updated_at')

    snippets = vault.get_all_snippets(sort_by=sort_by, limit=limit, offset=offset)
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in snippets]
    })


@app.route('/api/snippets/<int:snippet_id>', methods=['GET'])
def get_snippet(snippet_id):
    """获取单个片段"""
    snippet = vault.get_snippet(snippet_id)
    if not snippet:
        return jsonify({'success': False, 'error': '片段不存在'}), 404

    return jsonify({
        'success': True,
        'data': snippet.to_dict()
    })


@app.route('/api/snippets', methods=['POST'])
def add_snippet():
    """添加片段"""
    data = request.json

    try:
        snippet = Snippet(
            title=data['title'],
            code=data['code'],
            language=data.get('language', 'text'),
            tags=data.get('tags', []),
            category=data.get('category', '默认')
        )
        snippet_id = vault.add_snippet(snippet)
        return jsonify({'success': True, 'id': snippet_id})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/snippets/<int:snippet_id>', methods=['PUT'])
def update_snippet(snippet_id):
    """更新片段"""
    data = request.json
    success = vault.update_snippet(snippet_id, **data)

    if not success:
        return jsonify({'success': False, 'error': '更新失败'}), 404

    return jsonify({'success': True})


@app.route('/api/snippets/<int:snippet_id>', methods=['DELETE'])
def delete_snippet(snippet_id):
    """删除片段"""
    success = vault.delete_snippet(snippet_id)

    if not success:
        return jsonify({'success': False, 'error': '删除失败'}), 404

    return jsonify({'success': True})


# ============================================
# API 路由 - 搜索
# ============================================

@app.route('/api/search')
def search():
    """全文搜索"""
    keyword = request.args.get('keyword', '')
    field = request.args.get('field', 'all')

    if not keyword:
        return jsonify({'success': True, 'data': []})

    results = vault.search(keyword, field)

    # 序列化结果（包含匹配信息）
    serialized = []
    for r in results:
        serialized.append({
            'snippet': r['snippet'].to_dict(),
            'matches': r['matches']
        })

    return jsonify({'success': True, 'data': serialized})


# ============================================
# API 路由 - 分类
# ============================================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    categories = vault.get_all_categories()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in categories]
    })


@app.route('/api/categories', methods=['POST'])
def add_category():
    """添加分类"""
    data = request.json
    category = Category(data['name'], data.get('description', ''))
    success = vault.add_category(category)

    if not success:
        return jsonify({'success': False, 'error': '分类已存在'}), 400

    return jsonify({'success': True})


@app.route('/api/categories/<path:name>', methods=['DELETE'])
def delete_category(name):
    """删除分类"""
    try:
        success = vault.delete_category(name)
        if not success:
            return jsonify({'success': False, 'error': '分类不存在'}), 404
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/categories/<path:old_name>/rename', methods=['PUT'])
def rename_category(old_name):
    """重命名分类"""
    data = request.json
    new_name = data.get('new_name')

    if not new_name:
        return jsonify({'success': False, 'error': '新分类名不能为空'}), 400

    try:
        success = vault.rename_category(old_name, new_name)
        if not success:
            return jsonify({'success': False, 'error': '重命名失败（分类名可能已存在）'}), 400
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================
# API 路由 - 标签
# ============================================

@app.route('/api/tags')
def get_tags():
    """获取所有标签"""
    tags = vault.get_all_tags()
    return jsonify({
        'success': True,
        'data': tags
    })


@app.route('/api/snippets/<int:snippet_id>/tags', methods=['POST'])
def add_tag(snippet_id):
    """添加标签"""
    data = request.json
    tag = data.get('tag')

    if not tag:
        return jsonify({'success': False, 'error': '标签不能为空'}), 400

    success = vault.add_tag_to_snippet(snippet_id, tag)
    return jsonify({'success': success})


@app.route('/api/snippets/<int:snippet_id>/tags/<tag>', methods=['DELETE'])
def remove_tag(snippet_id, tag):
    """移除标签"""
    success = vault.remove_tag_from_snippet(snippet_id, tag)
    return jsonify({'success': success})


# ============================================
# API 路由 - 推荐
# ============================================

@app.route('/api/recommend')
def recommend():
    """智能推荐"""
    limit = request.args.get('limit', 10, type=int)
    based_on = request.args.get('based_on', type=int)

    recommendations = vault.recommend(limit=limit, based_on=based_on)
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in recommendations]
    })


# ============================================
# API 路由 - 导入导出
# ============================================

@app.route('/api/export')
def export_snippets():
    """导出片段到JSON"""
    fd, temp_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)

    success = vault.export_to_json(temp_path)

    if not success:
        return jsonify({'success': False, 'error': '导出失败'}), 500

    return send_file(
        temp_path,
        as_attachment=True,
        download_name=f'snippets_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        mimetype='application/json'
    )


@app.route('/api/import', methods=['POST'])
def import_snippets():
    """导入JSON文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择文件'}), 400

    merge = request.form.get('merge', 'true').lower() == 'true'

    # 保存临时文件
    fd, temp_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    file.save(temp_path)

    try:
        count = vault.import_from_json(temp_path, merge=merge)
        os.unlink(temp_path)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        os.unlink(temp_path)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export-sample', methods=['POST'])
def export_sample():
    """导出示例数据"""
    sample_snippets = [
        Snippet(
            title="快速排序 Python 实现",
            code="""def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# 示例
print(quick_sort([3,6,8,10,1,2,1]))""",
            language="python",
            tags=["算法", "排序", "python"],
            category="学习"
        ),
        Snippet(
            title="Flask 路由示例",
            code="""from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello World!'})

if __name__ == '__main__':
    app.run(debug=True)""",
            language="python",
            tags=["flask", "api", "web"],
            category="工作"
        ),
        Snippet(
            title="JavaScript 数组去重",
            code="""// 多种数组去重方法
const arr = [1, 2, 2, 3, 4, 4, 5];

// 方法1: Set
const unique1 = [...new Set(arr)];

// 方法2: filter
const unique2 = arr.filter((item, index) => arr.indexOf(item) === index);

console.log(unique1); // [1,2,3,4,5]""",
            language="javascript",
            tags=["javascript", "数组", "工具"],
            category="学习"
        )
    ]

    for s in sample_snippets:
        vault.add_snippet(s)

    fd, temp_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    vault.export_to_json(temp_path)

    return send_file(
        temp_path,
        as_attachment=True,
        download_name='snippets_sample.json',
        mimetype='application/json'
    )


# ============================================
# API 路由 - 统计
# ============================================

@app.route('/api/statistics')
def get_statistics():
    """获取统计信息"""
    stats = vault.get_statistics()
    return jsonify({
        'success': True,
        'data': stats
    })


# ============================================
# 启动服务器
# ============================================

if __name__ == '__main__':
    # 确保模板目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # 保存 HTML 模板
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(open(__file__.replace('app.py', 'index.html'), 'r', encoding='utf-8').read() if os.path.exists(
            'index.html') else HTML_TEMPLATE or '')

    print("=" * 50)
    print("🚀 代码片段管理器已启动")
    print("📍 访问地址: http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)