"""
项目扫描器 - 检测目录下的项目和软件
"""
import os
import json
import psutil
from pathlib import Path
from typing import List, Dict, Any


class ProjectScanner:
    """扫描目录中的项目"""

    # 项目标识文件
    PROJECT_MARKERS = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'main.py', 'app.py'],
        'node': ['package.json', 'node_modules'],
        'java': ['pom.xml', 'build.gradle', 'src/main/java'],
        'go': ['go.mod', 'main.go'],
        'rust': ['Cargo.toml'],
        'ruby': ['Gemfile'],
        'php': ['composer.json'],
        'git': ['.git'],
        'vscode': ['.vscode'],
        'skill': ['SKILL.md'],
        'generic': ['README.md', 'README.txt', 'LICENSE']
    }

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)

    def is_project_dir(self, path: Path) -> tuple[bool, str | None]:
        """判断是否是项目目录"""
        if not path.is_dir():
            return False, None

        # 跳过隐藏目录和系统目录
        if path.name.startswith('.') or path.name.startswith('__'):
            return False, None

        # 检查是否有项目标识文件
        for project_type, markers in self.PROJECT_MARKERS.items():
            for marker in markers:
                if (path / marker).exists():
                    return True, project_type

        # 检查是否有代码文件（至少3个）
        code_extensions = {'.py', '.js', '.ts', '.go', '.rs', '.java', '.c', '.cpp', '.h'}
        code_files = [
            f for f in path.iterdir()
            if f.is_file() and f.suffix in code_extensions
        ]
        if len(code_files) >= 3:
            return True, 'generic'

        return False, None

    def scan(self, max_depth: int = 2) -> List[Dict[str, Any]]:
        """扫描目录，返回项目列表"""
        projects = []

        for item in self.root_path.iterdir():
            if not item.is_dir():
                continue

            is_proj, proj_type = self.is_project_dir(item)
            if is_proj:
                projects.append(self._get_project_info(item, proj_type))

            # 递归扫描子目录（限制深度）
            elif max_depth > 1:
                try:
                    sub_scanner = ProjectScanner(str(item))
                    sub_projects = sub_scanner.scan(max_depth - 1)
                    projects.extend(sub_projects)
                except PermissionError:
                    continue

        return projects

    def _get_project_info(self, path: Path, proj_type: str) -> Dict[str, Any]:
        """获取项目详细信息"""
        info = {
            'name': path.name,
            'path': str(path.absolute()),
            'type': proj_type,
            'size': self._get_dir_size(path),
            'modified': os.path.getmtime(path),
        }

        # 尝试读取 README
        for readme_name in ['README.md', 'README.txt', 'readme.md']:
            readme_path = path / readme_name
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        info['description'] = f.read(500)  # 前500字符
                except:
                    pass
                break

        # 读取 package.json 获取更多信息
        if (path / 'package.json').exists():
            try:
                with open(path / 'package.json', 'r', encoding='utf-8') as f:
                    pkg = json.load(f)
                    info['package_name'] = pkg.get('name')
                    info['version'] = pkg.get('version')
                    info['description'] = pkg.get('description', info.get('description', ''))
            except:
                pass

        return info

    def _get_dir_size(self, path: Path) -> int:
        """获取目录大小（字节）"""
        try:
            total = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
            return total
        except:
            return 0


class SoftwareScanner:
    """扫描系统中的已安装软件"""

    # 开发相关的进程名称
    DEV_PROCESSES = {
        'python': {
            'names': ['python.exe', 'python3.exe', 'pythonw.exe'],
            'type': 'Python',
            'icon': '🐍'
        },
        'node': {
            'names': ['node.exe'],
            'type': 'Node.js',
            'icon': '💚'
        },
        'npm': {
            'names': ['npm.cmd', 'npm.exe'],
            'type': 'NPM',
            'icon': '📦'
        },
        'java': {
            'names': ['java.exe', 'javaw.exe'],
            'type': 'Java',
            'icon': '☕'
        },
        'go': {
            'names': ['go.exe'],
            'type': 'Go',
            'icon': '🔵'
        },
        'dotnet': {
            'names': ['dotnet.exe'],
            'type': '.NET',
            'icon': '🟣'
        },
        'mvn': {
            'names': ['mvn.cmd', 'mvn.exe'],
            'type': 'Maven',
            'icon': '🔧'
        },
        'gradle': {
            'names': ['gradle.bat', 'gradle.exe'],
            'type': 'Gradle',
            'icon': '🐘'
        },
        'git': {
            'names': ['git.exe'],
            'type': 'Git',
            'icon': '📂'
        },
        'docker': {
            'names': ['docker.exe', 'dockerd.exe'],
            'type': 'Docker',
            'icon': '🐋'
        },
        'redis': {
            'names': ['redis-server.exe'],
            'type': 'Redis',
            'icon': '🔴'
        },
        'mysql': {
            'names': ['mysqld.exe'],
            'type': 'MySQL',
            'icon': '🗄️'
        },
        'nginx': {
            'names': ['nginx.exe'],
            'type': 'Nginx',
            'icon': '🔷'
        },
        'apache': {
            'names': ['httpd.exe'],
            'type': 'Apache',
            'icon': '🪶'
        },
    }

    def scan_running_processes(self) -> List[Dict[str, Any]]:
        """扫描系统中运行的开发相关进程"""
        running = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cwd']):
            try:
                proc_name = proc.info['name']
                proc_pid = proc.info['pid']

                # 匹配开发进程
                for proc_type, info in self.DEV_PROCESSES.items():
                    if proc_name in info['names']:
                        cmdline = proc.info['cmdline'] or []
                        cwd = proc.info['cwd'] or 'Unknown'

                        # 过滤掉项目管理器自己的进程
                        if 'project-manager' in str(cwd):
                            continue

                        # 获取进程详细信息
                        try:
                            mem_info = proc.memory_info()
                            cpu_percent = proc.cpu_percent()
                        except:
                            mem_info = None
                            cpu_percent = 0

                        # 尝试检测监听的端口
                        ports = self._get_process_ports(proc_pid)

                        running.append({
                            'pid': proc_pid,
                            'name': proc_name,
                            'type': info['type'],
                            'icon': info['icon'],
                            'cmdline': ' '.join(cmdline) if cmdline else '',
                            'cwd': str(cwd),
                            'memory_mb': mem_info.rss / 1024 / 1024 if mem_info else 0,
                            'cpu_percent': cpu_percent,
                            'create_time': proc.info['create_time'],
                            'ports': ports
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return running

    def _get_process_ports(self, pid: int) -> List[int]:
        """获取进程监听的端口"""
        ports = []
        try:
            proc = psutil.Process(pid)
            connections = proc.connections(kind='inet')
            for conn in connections:
                if conn.status == 'LISTEN' and conn.laddr:
                    ports.append(conn.laddr.port)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return ports

    def scan_windows(self) -> List[Dict[str, Any]]:
        """扫描 Windows 已安装软件"""
        software = []
        try:
            import winreg

            # 扫描已安装程序（32位和64位）
            reg_paths = [
                (r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', winreg.HKEY_LOCAL_MACHINE),
                (r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall', winreg.HKEY_LOCAL_MACHINE),
                (r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', winreg.HKEY_CURRENT_USER),
            ]

            seen = set()
            for sub_path, root in reg_paths:
                try:
                    key = winreg.OpenKey(root, sub_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            app_key = winreg.EnumKey(key, i)
                            app_path = f'{sub_path}\\{app_key}'
                            app_key_handle = winreg.OpenKey(root, app_path)

                            name = winreg.QueryValueEx(app_key_handle, 'DisplayName')[0]
                            if name and name not in seen:
                                seen.add(name)
                                software.append({
                                    'name': name,
                                    'version': winreg.QueryValueEx(app_key_handle, 'DisplayVersion')[0] if winreg.QueryValueEx(app_key_handle, 'DisplayVersion')[0] else 'Unknown',
                                    'publisher': winreg.QueryValueEx(app_key_handle, 'Publisher')[0] if winreg.QueryValueEx(app_key_handle, 'Publisher')[0] else 'Unknown',
                                    'install_location': winreg.QueryValueEx(app_key_handle, 'InstallLocation')[0] if winreg.QueryValueEx(app_key_handle, 'InstallLocation')[0] else '',
                                })
                            winreg.CloseKey(app_key_handle)
                        except:
                            continue
                    winreg.CloseKey(key)
                except:
                    continue
        except ImportError:
            pass
        return software

    def scan(self) -> List[Dict[str, Any]]:
        """根据平台扫描软件"""
        import platform
        system = platform.system()

        if system == 'Windows':
            return self.scan_windows()
        return []
