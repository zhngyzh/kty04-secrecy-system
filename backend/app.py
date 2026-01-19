"""
KTY04 群签名管理系统 - Flask 后端主应用
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import groups, members, signatures
from utils.database import init_db
from utils.key_manager import KeyManager

app = Flask(__name__, 
            template_folder='../frontend',
            static_folder='../frontend')
CORS(app)

# 获取前端目录的绝对路径
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

# 初始化数据库
init_db()

# 初始化密钥管理器
key_manager = KeyManager()

# 注册蓝图
app.register_blueprint(groups.bp)
app.register_blueprint(members.bp)
app.register_blueprint(signatures.bp)

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'KTY04 管理系统运行正常'
    })

# 添加静态文件路由（确保 CSS 和 JS 文件能被正确加载）
@app.route('/css/<path:filename>')
def css_files(filename):
    """提供 CSS 文件"""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'css'), filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    """提供 JS 文件"""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'js'), filename)

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs('data/groups', exist_ok=True)
    os.makedirs('data/members', exist_ok=True)
    os.makedirs('data/signatures', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
