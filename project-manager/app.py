"""
项目管理器 Web 应用
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
from scanner import ProjectScanner, SoftwareScanner
from process_manager import process_manager

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

# 配置扫描根目录
ROOT_PATH = r'C:\Users\yunxi\Desktop\item'

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / 'config.json'
STATS_FILE = Path(__file__).parent / 'stats.json'


def load_config():
    """加载配置"""
    default_config = {
        'root_path': ROOT_PATH,
        'refresh_interval': 5000,
        'theme': 'dark',
        'auto_scan': True,
        'favorites': [],
        'recent_projects': []
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
        except:
            pass
    return default_config


def save_config(config):
    """保存配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def get_root_path():
    """获取扫描根目录"""
    config = load_config()
    return config.get('root_path', ROOT_PATH)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/projects')
def get_projects():
    """获取项目列表"""
    scanner = ProjectScanner(ROOT_PATH)
    projects = scanner.scan(max_depth=2)

    # 排除 project-manager 自己
    current_path = str(Path(__file__).parent.absolute())
    projects = [p for p in projects if p['path'] != current_path]

    # 添加运行状态
    for project in projects:
        status = process_manager.get_status(project['path'])
        project['running'] = status.get('status') == 'running'
        project['managed'] = status.get('managed', False)

    return jsonify(projects)


@app.route('/api/software')
def get_software():
    """获取已安装软件列表"""
    scanner = SoftwareScanner()
    software = scanner.scan()
    return jsonify(software[:50])


@app.route('/api/scan')
def scan_all():
    """扫描所有内容"""
    scanner = ProjectScanner(ROOT_PATH)
    projects = scanner.scan(max_depth=2)

    # 排除 project-manager 自己
    current_path = str(Path(__file__).parent.absolute())
    projects = [p for p in projects if p['path'] != current_path]

    # 添加运行状态
    for project in projects:
        status = process_manager.get_status(project['path'])
        project['running'] = status.get('status') == 'running'
        project['managed'] = status.get('managed', False)

    software_scanner = SoftwareScanner()
    software = software_scanner.scan()

    return jsonify({
        'projects': projects,
        'software': software[:50]
    })


@app.route('/api/info', methods=['POST'])
def get_project_info():
    """获取项目详细信息"""
    data = request.json
    path = data.get('path')

    if not path or not os.path.exists(path):
        return jsonify({'error': 'Path not found'}), 404

    full_path = Path(path)
    scanner = ProjectScanner(ROOT_PATH)
    is_proj, proj_type = scanner.is_project_dir(full_path)

    if is_proj or full_path.is_dir():
        info = scanner._get_project_info(full_path, proj_type if is_proj else 'generic')

        # 获取目录结构
        try:
            tree = []
            for item in full_path.iterdir():
                try:
                    tree.append({
                        'name': item.name,
                        'is_dir': item.is_dir(),
                        'size': item.stat().st_size if item.is_file() else 0,
                    })
                except:
                    pass
            info['tree'] = sorted(tree[:100], key=lambda x: (not x['is_dir'], x['name']))
        except:
            info['tree'] = []

        # 获取运行状态
        status = process_manager.get_status(path)
        info['running'] = status.get('status') == 'running'
        info['managed'] = status.get('managed', False)
        if status.get('managed'):
            info['process_info'] = status

        return jsonify(info)

    return jsonify({'error': 'Not a valid path'}), 400


@app.route('/api/open', methods=['POST'])
def open_project():
    """打开项目目录"""
    data = request.json
    path = data.get('path')

    if path and os.path.exists(path):
        import subprocess
        import platform

        system = platform.system()
        if system == 'Windows':
            os.startfile(path)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', path])
        else:  # Linux
            subprocess.run(['xdg-open', path])

        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Path not found'}), 404


@app.route('/api/start', methods=['POST'])
def start_project():
    """启动项目"""
    data = request.json
    path = data.get('path')

    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': '项目路径不存在'})

    result = process_manager.start(path)
    return jsonify(result)


@app.route('/api/stop', methods=['POST'])
def stop_project():
    """停止项目"""
    data = request.json
    path = data.get('path')

    result = process_manager.stop(path)
    return jsonify(result)


@app.route('/api/restart', methods=['POST'])
def restart_project():
    """重启项目"""
    data = request.json
    path = data.get('path')

    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': '项目路径不存在'})

    result = process_manager.restart(path)
    return jsonify(result)


@app.route('/api/status', methods=['POST'])
def get_project_status():
    """获取项目运行状态"""
    data = request.json
    path = data.get('path')

    status = process_manager.get_status(path)
    return jsonify(status)


@app.route('/api/processes')
def get_all_processes():
    """获取所有管理的进程"""
    processes = process_manager.get_all_status()
    return jsonify(processes)


@app.route('/api/running-processes')
def get_running_processes():
    """获取系统中运行的开发相关进程"""
    scanner = SoftwareScanner()
    running = scanner.scan_running_processes()

    # 标记哪些是由管理器启动的
    managed_paths = {p['path']: p for p in process_manager.get_all_status()}

    for proc in running:
        proc['managed'] = proc['cwd'] in managed_paths
        if proc['managed']:
            proc['managed_info'] = managed_paths[proc['cwd']]

    return jsonify(running)


@app.route('/api/kill-process', methods=['POST'])
def kill_process():
    """结束指定进程"""
    import psutil

    data = request.json
    pid = data.get('pid')

    if not pid:
        return jsonify({'success': False, 'error': 'PID 未提供'}), 400

    try:
        proc = psutil.Process(pid)
        proc.terminate()

        # 等待进程结束
        gone, alive = psutil.wait_procs([proc], timeout=3)

        # 强制杀死仍然存活的进程
        for p in alive:
            p.kill()

        return jsonify({'success': True})
    except psutil.NoSuchProcess:
        return jsonify({'success': False, 'error': '进程不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 新增 API 端点 ==========

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    config = load_config()
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        data = request.json
        config = load_config()
        config.update(data)
        if save_config(config):
            return jsonify({'success': True, 'config': config})
        return jsonify({'success': False, 'error': '保存配置失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    root_path = get_root_path()
    scanner = ProjectScanner(root_path)
    projects = scanner.scan(max_depth=2)
    processes = process_manager.get_all_status()

    stats = {
        'total_projects': len(projects),
        'running_projects': sum(1 for p in projects if process_manager.get_status(p['path']).get('status') == 'running'),
        'stopped_projects': sum(1 for p in projects if process_manager.get_status(p['path']).get('status') != 'running'),
        'managed_processes': len(processes),
        'project_types': {},
        'total_size': sum(p.get('size', 0) for p in projects)
    }

    # 统计项目类型
    for p in projects:
        ptype = p.get('type', 'unknown')
        stats['project_types'][ptype] = stats['project_types'].get(ptype, 0) + 1

    return jsonify(stats)


@app.route('/api/batch/start', methods=['POST'])
def batch_start():
    """批量启动项目"""
    data = request.json
    project_paths = data.get('paths', [])

    results = []
    for path in project_paths:
        if os.path.exists(path):
            result = process_manager.start(path)
            results.append({'path': path, 'result': result})
        else:
            results.append({'path': path, 'result': {'success': False, 'error': '路径不存在'}})

    return jsonify({
        'success': True,
        'results': results,
        'started': sum(1 for r in results if r['result'].get('success')),
        'failed': sum(1 for r in results if not r['result'].get('success'))
    })


@app.route('/api/batch/stop', methods=['POST'])
def batch_stop():
    """批量停止项目"""
    data = request.json
    project_paths = data.get('paths', [])

    results = []
    for path in project_paths:
        result = process_manager.stop(path)
        results.append({'path': path, 'result': result})

    return jsonify({
        'success': True,
        'results': results,
        'stopped': sum(1 for r in results if r['result'].get('success')),
        'failed': sum(1 for r in results if not r['result'].get('success'))
    })


@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """获取收藏的项目"""
    config = load_config()
    favorites = config.get('favorites', [])
    return jsonify(favorites)


@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    """添加收藏项目"""
    try:
        data = request.json
        path = data.get('path')
        name = data.get('name')

        if not path:
            return jsonify({'success': False, 'error': '路径不能为空'}), 400

        config = load_config()
        favorites = config.get('favorites', [])

        # 检查是否已收藏
        if any(f.get('path') == path for f in favorites):
            return jsonify({'success': False, 'error': '已收藏'}), 400

        favorites.append({
            'path': path,
            'name': name,
            'added_at': datetime.now().isoformat()
        })
        config['favorites'] = favorites
        save_config(config)

        return jsonify({'success': True, 'favorites': favorites})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/favorites', methods=['DELETE'])
def remove_favorite():
    """移除收藏项目"""
    try:
        data = request.json
        path = data.get('path')

        config = load_config()
        favorites = config.get('favorites', [])
        favorites = [f for f in favorites if f.get('path') != path]
        config['favorites'] = favorites
        save_config(config)

        return jsonify({'success': True, 'favorites': favorites})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recent', methods=['GET'])
def get_recent():
    """获取最近访问的项目"""
    config = load_config()
    recent = config.get('recent_projects', [])[:10]
    return jsonify(recent)


@app.route('/api/recent', methods=['POST'])
def add_recent():
    """添加最近访问"""
    try:
        data = request.json
        path = data.get('path')
        name = data.get('name')

        if not path:
            return jsonify({'success': False}), 400

        config = load_config()
        recent = config.get('recent_projects', [])

        # 移除已存在的，然后添加到前面
        recent = [r for r in recent if r.get('path') != path]
        recent.insert(0, {
            'path': path,
            'name': name,
            'visited_at': datetime.now().isoformat()
        })

        # 只保留最近20个
        config['recent_projects'] = recent[:20]
        save_config(config)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search', methods=['GET'])
def search_projects():
    """搜索项目"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])

    root_path = get_root_path()
    scanner = ProjectScanner(root_path)
    projects = scanner.scan(max_depth=2)

    results = []
    for p in projects:
        if query in p['name'].lower() or query in p['path'].lower():
            results.append(p)

    return jsonify(results[:20])


# ========== 服务注册表 ==========

BASE_DIR = Path(__file__).parent.parent

SERVICES = [
    {
        'id': 'ai-game-arcade',
        'name': 'AI 游戏乐园',
        'description': 'AI 驱动的游戏创建与游玩平台',
        'port': 5002,
        'path': str(BASE_DIR / 'ai-game-arcade'),
        'command': 'python app.py',
        'icon': '🎮',
        'color': '#6366f1',
        'url': 'http://localhost:5002',
    },
    {
        'id': 'sla-calculator',
        'name': 'SLA 计算器',
        'description': '服务等级协议计算工具',
        'port': 5001,
        'path': str(BASE_DIR / 'sla-calculator'),
        'command': 'python app.py',
        'icon': '📊',
        'color': '#22c55e',
        'url': 'http://localhost:5001',
    },
    {
        'id': 'duplicate-file-finder',
        'name': '重复文件查找器',
        'description': '扫描并清理重复文件',
        'port': 8000,
        'path': str(BASE_DIR / 'duplicate-file-finder'),
        'command': 'python main.py',
        'icon': '🔍',
        'color': '#f59e0b',
        'url': 'http://localhost:8000',
    },
    {
        'id': 'video-audio-extractor',
        'name': '视频音频提取器',
        'description': '从视频中提取音频',
        'port': 8001,
        'path': str(BASE_DIR / 'video-audio-extractor'),
        'command': 'python app.py',
        'icon': '🎬',
        'color': '#ef4444',
        'url': 'http://localhost:8001',
    },
]


@app.route('/api/services')
def get_services():
    """获取所有注册服务及其状态"""
    import socket
    result = []
    for svc in SERVICES:
        running = _check_port(svc['port'])
        result.append({**svc, 'running': running})
    return jsonify(result)


@app.route('/api/services/<service_id>/start', methods=['POST'])
def start_service(service_id):
    """启动指定服务"""
    svc = next((s for s in SERVICES if s['id'] == service_id), None)
    if not svc:
        return jsonify({'error': '服务不存在'}), 404

    if _check_port(svc['port']):
        return jsonify({'success': False, 'error': '服务已在运行中'})

    result = process_manager.start(svc['path'])
    return jsonify(result)


@app.route('/api/services/<service_id>/stop', methods=['POST'])
def stop_service(service_id):
    """停止指定服务"""
    svc = next((s for s in SERVICES if s['id'] == service_id), None)
    if not svc:
        return jsonify({'error': '服务不存在'}), 404

    result = process_manager.stop(svc['path'])
    return jsonify(result)


@app.route('/api/services/<service_id>/open', methods=['POST'])
def open_service(service_id):
    """在浏览器中打开服务"""
    import webbrowser
    svc = next((s for s in SERVICES if s['id'] == service_id), None)
    if not svc:
        return jsonify({'error': '服务不存在'}), 404

    webbrowser.open(svc['url'])
    return jsonify({'success': True})


def _check_port(port):
    """检查端口是否在监听"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False


if __name__ == '__main__':
    print(f"项目管理器启动中...")
    print(f"扫描目录: {ROOT_PATH}")
    print(f"访问地址: http://localhost:5000")

    app.run(debug=False, host='0.0.0.0', port=5000)
