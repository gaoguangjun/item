"""
进程管理器 - 管理项目的启动、停止、重启
"""
import subprocess
import psutil
import os
import time
import json
import re
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class ProcessManager:
    """管理项目进程"""

    def __init__(self, state_file: str = 'process_state.json'):
        self.state_file = Path(__file__).parent / state_file
        self.processes: Dict[str, Dict] = self._load_state()

    def _load_state(self) -> Dict:
        """加载进程状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_state(self):
        """保存进程状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.processes, f, ensure_ascii=False, indent=2)

    def _get_project_key(self, path: str) -> str:
        """获取项目唯一标识"""
        return str(Path(path).absolute())

    def _detect_project_type(self, path: str) -> str:
        """检测项目类型"""
        p = Path(path)

        # 检测 FastAPI 项目（main.py 中有 uvicorn）
        if (p / 'main.py').exists():
            try:
                content = (p / 'main.py').read_text(encoding='utf-8')
                if 'uvicorn' in content or 'FastAPI' in content:
                    return 'fastapi'
            except:
                pass

        # 检测 Flask 项目（app.py）
        if (p / 'app.py').exists():
            try:
                content = (p / 'app.py').read_text(encoding='utf-8')
                if 'Flask' in content:
                    return 'flask'
            except:
                pass
            return 'python'

        # 检测其他 Python 项目
        if (p / 'main.py').exists():
            return 'python'
        if (p / 'manage.py').exists():  # Django
            return 'django'
        if (p / 'requirements.txt').exists():
            return 'python'

        # 检测 Node.js 项目
        if (p / 'package.json').exists():
            pkg = p / 'package.json'
            try:
                with open(pkg, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    scripts = data.get('scripts', {})
                    if 'dev' in scripts or 'start' in scripts:
                        return 'node'
            except:
                pass
            return 'node'

        # 检测 Go 项目
        if (p / 'main.go').exists() or (p / 'go.mod').exists():
            return 'go'

        # 检测 Java 项目
        if (p / 'pom.xml').exists():
            return 'maven'
        if (p / 'build.gradle').exists():
            return 'gradle'

        return 'generic'

    def _get_start_command(self, path: str, proj_type: str) -> Optional[List[str]]:
        """获取项目启动命令"""
        p = Path(path)

        if proj_type == 'fastapi':
            # FastAPI 项目 - 直接运行 main.py（内部会启动 uvicorn）
            if (p / 'main.py').exists():
                return ['python', str(p / 'main.py')]
            return None

        elif proj_type == 'flask':
            # Flask 项目
            if (p / 'app.py').exists():
                return ['python', str(p / 'app.py')]
            return None

        elif proj_type == 'python':
            # 通用 Python 项目
            for entry in ['app.py', 'main.py', 'server.py']:
                if (p / entry).exists():
                    return ['python', str(p / entry)]
            return None

        elif proj_type == 'django':
            return ['python', str(p / 'manage.py'), 'runserver']

        elif proj_type == 'node':
            # 读取 package.json 获取启动脚本
            pkg_path = p / 'package.json'
            if pkg_path.exists():
                try:
                    with open(pkg_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        scripts = data.get('scripts', {})
                        if 'dev' in scripts:
                            return ['npm', 'run', 'dev']
                        if 'start' in scripts:
                            return ['npm', 'start']
                except:
                    pass
            return ['npm', 'start']

        elif proj_type == 'go':
            return ['go', 'run', str(p / 'main.go')]

        elif proj_type == 'maven':
            return ['mvn', 'spring-boot:run']

        elif proj_type == 'gradle':
            return ['gradle', 'bootRun']

        return None

    def start(self, path: str) -> Dict:
        """启动项目"""
        key = self._get_project_key(path)
        p = Path(path)

        if not p.exists():
            return {'success': False, 'error': '项目路径不存在'}

        # 检查是否已经在运行
        if key in self.processes and self.processes[key].get('status') == 'running':
            # 检查进程是否真的存在
            try:
                proc = psutil.Process(self.processes[key]['pid'])
                if proc.is_running():
                    return {'success': False, 'error': '项目已在运行中'}
            except:
                # 进程不存在，更新状态
                pass

        # 检测项目类型和启动命令
        proj_type = self._detect_project_type(path)
        command = self._get_start_command(path, proj_type)

        if not command:
            return {'success': False, 'error': f'无法识别如何启动此项目 (类型: {proj_type})'}

        try:
            # 打开日志文件
            log_file = self.state_file.parent / f'logs_{int(time.time())}.txt'

            # 启动进程（不使用 PIPE 避免阻塞）
            if os.name == 'nt':  # Windows
                # 使用 CREATE_NEW_CONSOLE 在新窗口启动
                process = subprocess.Popen(
                    command,
                    cwd=path,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                process = subprocess.Popen(
                    command,
                    cwd=path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            # 等待一小段时间检查进程是否启动成功
            time.sleep(0.5)

            # 检查进程是否还在运行
            try:
                proc = psutil.Process(process.pid)
                if not proc.is_running():
                    return {'success': False, 'error': '进程启动后立即退出（可能是缺少依赖或启动错误）'}
            except psutil.NoSuchProcess:
                return {'success': False, 'error': '进程启动失败'}

            # 保存进程信息
            self.processes[key] = {
                'path': path,
                'name': p.name,
                'pid': process.pid,
                'type': proj_type,
                'command': ' '.join(command),
                'status': 'running',
                'start_time': datetime.now().isoformat(),
                'port': self._detect_port(path, proj_type),
                'log_file': str(log_file)
            }
            self._save_state()

            return {
                'success': True,
                'pid': process.pid,
                'type': proj_type,
                'port': self.processes[key]['port'],
                'command': ' '.join(command)
            }

        except Exception as e:
            return {'success': False, 'error': f'启动失败: {str(e)}'}

    def _detect_port(self, path: str, proj_type: str) -> Optional[int]:
        """尝试检测项目运行的端口"""
        p = Path(path)

        # 检查常见的配置文件
        if proj_type == 'python':
            # 检查多个可能的入口文件
            for entry_file in ['app.py', 'main.py', 'server.py', 'manage.py']:
                entry_path = p / entry_file
                if entry_path.exists():
                    try:
                        content = entry_path.read_text(encoding='utf-8')
                        # 检测各种端口定义方式
                        patterns = [
                            r'app\.run\([^)]*port\s*=\s*(\d+)',
                            r'uvicorn\.run\([^)]*port\s*=\s*(\d+)',
                            r'port\s*=\s*(\d+)',
                            r'host=["\'][^"\']*["\'],\s*port\s*=\s*(\d+)',
                            r'port\s*=\s*(\d+),\s*host',
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, content)
                            if match:
                                return int(match.group(1))
                    except:
                        pass

        elif proj_type == 'node':
            # 检查 vite.config.js / next.config.js 等
            for config in ['vite.config.js', 'next.config.js', 'nuxt.config.js']:
                config_path = p / config
                if config_path.exists():
                    try:
                        content = config_path.read_text(encoding='utf-8')
                        match = re.search(r'port\s*:\s*(\d+)', content)
                        if match:
                            return int(match.group(1))
                    except:
                        pass

        # 默认端口
        defaults = {
            'python': 5000,
            'django': 8000,
            'fastapi': 8000,
            'node': 3000,
            'go': 8080,
            'maven': 8080,
        }
        return defaults.get(proj_type)

    def stop(self, path: str) -> Dict:
        """停止项目"""
        key = self._get_project_key(path)

        if key not in self.processes:
            return {'success': False, 'error': '项目未在管理中'}

        pid = self.processes[key]['pid']
        port = self.processes[key].get('port')

        killed_by_pid = False

        try:
            # 查找进程及其子进程
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            # Windows 上需要使用 kill 而不是 terminate
            # 因为 CREATE_NEW_PROCESS_GROUP 会创建新的进程组
            import os
            if os.name == 'nt':
                # Windows: 直接 kill 所有进程
                for child in children:
                    try:
                        child.kill()
                    except:
                        pass
                parent.kill()
            else:
                # Unix/Mac: 使用 terminate
                for child in children:
                    try:
                        child.terminate()
                    except:
                        pass
                parent.terminate()

            # 等待进程结束
            gone, alive = psutil.wait_procs([parent] + children, timeout=3)

            # 强制杀死仍然存活的进程
            for p in alive:
                try:
                    p.kill()
                except:
                    pass

            killed_by_pid = True

        except psutil.NoSuchProcess:
            # 进程可能已经不存在，继续检查端口
            pass
        except Exception as e:
            # PID 终止失败，尝试通过端口终止
            pass

        # 备用方法：如果有端口号，尝试通过端口终止
        killed_by_port = False
        if port and not killed_by_pid:
            killed_by_port = self._kill_by_port(port)

        # 更新状态
        if killed_by_pid or killed_by_port:
            self.processes[key]['status'] = 'stopped'
            self.processes[key]['stop_time'] = datetime.now().isoformat()
            self._save_state()

            method = 'PID' if killed_by_pid else '端口'
            return {'success': True, 'method': method, 'killed_by_port': killed_by_port}
        else:
            return {'success': False, 'error': '无法终止进程（PID 和端口方法都失败）'}

    def restart(self, path: str) -> Dict:
        """重启项目"""
        # 先停止
        self.stop(path)
        time.sleep(1)
        # 再启动
        return self.start(path)

    def get_status(self, path: str) -> Dict:
        """获取项目状态"""
        key = self._get_project_key(path)

        if key not in self.processes:
            return {
                'status': 'stopped',
                'managed': False
            }

        info = self.processes[key].copy()

        # 检查进程是否真的在运行
        try:
            proc = psutil.Process(info['pid'])
            if proc.is_running():
                info['status'] = 'running'
                info['cpu_percent'] = proc.cpu_percent()
                info['memory_mb'] = proc.memory_info().rss / 1024 / 1024
            else:
                info['status'] = 'stopped'
                self.processes[key]['status'] = 'stopped'
                self._save_state()
        except psutil.NoSuchProcess:
            info['status'] = 'stopped'
            self.processes[key]['status'] = 'stopped'
            self._save_state()

        info['managed'] = True
        return info

    def get_all_status(self) -> List[Dict]:
        """获取所有项目状态"""
        results = []
        for key, info in self.processes.items():
            status = self.get_status(info['path'])
            status['path'] = info['path']
            status['name'] = info['name']
            results.append(status)
        return results

    def _kill_by_port(self, port: int) -> bool:
        """通过端口杀死进程（备用方法）"""
        import os
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        proc = psutil.Process(conn.pid)
                        if os.name == 'nt':
                            proc.kill()
                        else:
                            proc.terminate()
                        return True
                    except:
                        pass
        except:
            pass
        return False

    def get_process_logs(self, path: str, lines: int = 50) -> List[str]:
        """获取进程输出（简单实现）"""
        # 这个功能需要更复杂的实现，比如重定向输出到文件
        return ['日志功能暂未实现']


# 全局实例
process_manager = ProcessManager()
