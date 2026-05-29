"""
项目管理器 Web 应用
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
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


if __name__ == '__main__':
    print(f"项目管理器启动中...")
    print(f"扫描目录: {ROOT_PATH}")
    print(f"访问地址: http://localhost:5000")

    app.run(debug=False, host='0.0.0.0', port=5000)
