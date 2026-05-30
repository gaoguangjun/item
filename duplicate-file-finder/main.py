from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import threading
import os
import platform
from pathlib import Path
from scanner import FileScanner, ScanResult, DuplicateGroup

app = FastAPI(title="重复文件检查工具")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局扫描器实例
scanners = {}
scanner_lock = threading.Lock()


class ScanRequest(BaseModel):
    directory: str
    max_files: Optional[int] = None


class DeleteRequest(BaseModel):
    scan_id: str
    files: List[str]


class ScanStatusResponse(BaseModel):
    status: str  # scanning, completed, error
    progress: dict
    stats: Optional[dict] = None


def progress_callback(scan_id: str):
    """创建进度回调函数"""
    def callback(progress):
        with scanner_lock:
            if scan_id in scanners:
                scanners[scan_id]["progress"] = progress
    return callback


def run_scan(scan_id: str, directory: str, max_files: Optional[int] = None):
    """后台运行扫描任务"""
    try:
        scanner = FileScanner(directory)
        scanner.set_callback(progress_callback(scan_id))

        with scanner_lock:
            scanners[scan_id]["scanner"] = scanner
            scanners[scan_id]["status"] = "scanning"
            scanners[scan_id]["should_stop"] = False

        # 扫描目录
        if not scanner.scan_directory(max_files, stop_check=lambda: check_stop(scan_id)):
            # 被停止
            with scanner_lock:
                scanners[scan_id]["status"] = "stopped"
            return

        # 检查是否被停止
        if check_stop(scan_id):
            with scanner_lock:
                scanners[scan_id]["status"] = "stopped"
            return

        # 查找重复文件
        scanner.find_duplicates(stop_check=lambda: check_stop(scan_id))

        with scanner_lock:
            if not scanners[scan_id].get("should_stop"):
                scanners[scan_id]["status"] = "completed"

    except Exception as e:
        with scanner_lock:
            scanners[scan_id]["status"] = "error"
            scanners[scan_id]["error"] = str(e)


def check_stop(scan_id: str) -> bool:
    """检查是否应该停止扫描"""
    with scanner_lock:
        return scanners.get(scan_id, {}).get("should_stop", False)


@app.get("/")
async def index():
    """返回主页面"""
    return FileResponse("static/index.html")


@app.post("/api/scan/start")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """开始扫描指定目录"""
    import uuid
    scan_id = str(uuid.uuid4())[:8]

    # 验证目录
    directory = Path(request.directory).resolve()
    if not directory.exists():
        raise HTTPException(status_code=400, detail="目录不存在")

    with scanner_lock:
        scanners[scan_id] = {
            "scanner": None,
            "status": "starting",
            "progress": {"current": 0, "total": 0, "stage": "初始化..."},
            "directory": str(directory)
        }

    # 在后台运行扫描
    background_tasks.add_task(run_scan, scan_id, str(directory), request.max_files)

    return {"scan_id": scan_id, "status": "started"}


@app.get("/api/scan/status/{scan_id}")
async def get_scan_status(scan_id: str):
    """获取扫描状态"""
    with scanner_lock:
        if scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[scan_id]
        response = {
            "status": scan_data["status"],
            "progress": scan_data.get("progress", {}),
            "directory": scan_data.get("directory", "")
        }

        # 如果已完成，添加统计信息
        if scan_data["status"] == "completed" and scan_data.get("scanner"):
            scanner = scan_data["scanner"]
            result = scanner.result
            response["stats"] = {
                "total_files": result.total_files,
                "total_folders": result.total_folders,
                "total_size": result.total_size,
                "total_size_formatted": scanner._format_size(result.total_size),
                "duplicate_groups": len(result.duplicate_groups),
                "file_type_stats": result.file_type_stats,
                "largest_files": result.largest_files[:10]
            }

        if scan_data["status"] == "error":
            response["error"] = scan_data.get("error", "未知错误")

        return response


@app.get("/api/scan/results/{scan_id}")
async def get_scan_results(scan_id: str):
    """获取扫描结果（重复文件列表）"""
    with scanner_lock:
        if scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[scan_id]

        if scan_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="扫描未完成")

        scanner = scan_data["scanner"]
        result = scanner.result

        # 格式化重复文件组
        duplicate_groups = []
        for group in result.duplicate_groups:
            files_info = []
            for f in group.files:
                files_info.append({
                    "path": f.path,
                    "rel_path": f.rel_path,
                    "size": f.size
                })

            duplicate_groups.append({
                "group_id": group.group_id,
                "size": group.size,
                "size_formatted": scanner._format_size(group.size),
                "recoverable": scanner._format_size(group.size * (len(group.files) - 1)),
                "md5_hash": group.md5_hash,
                "files": files_info
            })

        return {
            "scan_id": scan_id,
            "stats": {
                "total_files": result.total_files,
                "total_size": result.total_size,
                "total_size_formatted": scanner._format_size(result.total_size),
                "duplicate_groups": len(duplicate_groups)
            },
            "duplicate_groups": duplicate_groups
        }


@app.post("/api/scan/delete")
@app.post("/api/scan/delete")
async def delete_files(request: DeleteRequest):
    """删除选中的重复文件（后台任务）"""
    import uuid

    with scanner_lock:
        if request.scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[request.scan_id]
        if scan_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="扫描未完成")

    # 创建删除任务 ID
    delete_id = str(uuid.uuid4())[:8]

    with scanner_lock:
        # 初始化删除任务状态
        scan_data[f"delete_{delete_id}"] = {
            "status": "deleting",
            "total": len(request.files),
            "current": 0,
            "success": 0,
            "failed": 0
        }

    # 在后台执行删除
    import asyncio
    asyncio.create_task(delete_files_bg(request.scan_id, delete_id, request.files))

    return {
        "delete_id": delete_id,
        "status": "started",
        "total": len(request.files)
    }


async def delete_files_bg(scan_id: str, delete_id: str, files: List[str]):
    """后台执行删除文件任务"""
    def update_progress(current: int, success: int, failed: int):
        with scanner_lock:
            if scan_id in scanners:
                scanners[scan_id][f"delete_{delete_id}"] = {
                    "status": "deleting",
                    "total": len(files),
                    "current": current,
                    "success": success,
                    "failed": failed
                }

    scanner = None
    with scanner_lock:
        if scan_id in scanners:
            scanner = scanners[scan_id]["scanner"]

    if not scanner:
        return

    success_count = 0
    failed_list = []

    for i, filepath in enumerate(files):
        try:
            path = Path(filepath)
            if path.exists() and path.is_file():
                path.unlink()
                success_count += 1
            else:
                failed_list.append(filepath)
        except Exception as e:
            failed_list.append(f"{filepath} ({str(e)})")

        # 每删除 10 个文件或最后一个文件时更新进度
        if (i + 1) % 10 == 0 or i == len(files) - 1:
            update_progress(i + 1, success_count, len(failed_list))

    # 更新最终状态
    with scanner_lock:
        if scan_id in scanners:
            scanners[scan_id][f"delete_{delete_id}"] = {
                "status": "completed",
                "total": len(files),
                "current": len(files),
                "success": success_count,
                "failed": failed_list
            }


@app.get("/api/scan/delete/status/{scan_id}/{delete_id}")
async def get_delete_status(scan_id: str, delete_id: str):
    """获取删除任务状态"""
    with scanner_lock:
        if scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[scan_id]
        key = f"delete_{delete_id}"

        if key not in scan_data:
            raise HTTPException(status_code=404, detail="删除任务不存在")

        return scan_data[key]


@app.post("/api/system/empty-recycle-bin")
async def empty_recycle_bin():
    """清空回收站"""
    import platform
    import subprocess

    system = platform.system()

    try:
        if system == "Windows":
            # Windows: 使用 PowerShell 清空回收站
            result = subprocess.run(
                ["powershell", "-Command", "Clear-RecycleBin -Force"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return {"success": True, "message": "回收站已清空"}
            else:
                return {"success": False, "message": f"清空失败: {result.stderr}"}

        elif system == "Darwin":  # macOS
            result = subprocess.run(
                ["rm", "-rf", "~/.Trash/*"],
                capture_output=True,
                text=True,
                timeout=60
            )
            return {"success": True, "message": "回收站已清空"}

        else:  # Linux
            # Linux 回收站位置可能不同，尝试常见位置
            trash_paths = [
                "~/.local/share/Trash/files/*",
                "~/.trash/*",
                "~/.Trash/*"
            ]
            for path in trash_paths:
                subprocess.run(["rm", "-rf", path], capture_output=True)
            return {"success": True, "message": "回收站已清空"}

    except Exception as e:
        return {"success": False, "message": f"清空失败: {str(e)}"}


@app.get("/api/system/recycle-bin")
async def get_recycle_bin_contents():
    """获取回收站文件列表"""
    import platform
    from pathlib import Path as FilePath
    import os
    import winreg

    system = platform.system()
    files = []
    total_size = 0

    try:
        if system == "Windows":
            # Windows: 使用 Shell.Application COM 对象获取回收站内容
            ps_script = """
            $shell = New-Object -ComObject Shell.Application
            $recycleBin = $shell.Namespace(0xA)  # 0xA = 回收站
            $items = $recycleBin.Items()
            $result = @()

            foreach ($item in $items) {
                $result += @{
                    Name = $item.Name
                    Path = $item.Path
                    Size = $item.Size
                    Extension = $item.GetExtension
                    Modified = $item.ModifyDate
                }
            }

            $result | ConvertTo-Json -Compress
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, list):
                        for item in data:
                            size = item.get("Size", 0)
                            if size is None:
                                size = 0
                            try:
                                size = int(size)
                            except:
                                size = 0

                            file_name = item.get("Name", "")
                            files.append({
                                "name": file_name,
                                "path": item.get("Path", ""),
                                "size": size,
                                "extension": item.get("Extension", "") or "",
                                "modified": item.get("Modified", "")
                            })
                            total_size += size
                except (json.JSONDecodeError, Exception) as e:
                    # 如果 COM 对象失败，尝试直接访问回收站文件夹
                    files, total_size = get_windows_recycle_bin_direct()

        elif system == "Darwin":  # macOS
            trash_path = FilePath("~/.Trash").expanduser()
            if trash_path.exists():
                for item in trash_path.iterdir():
                    if item.is_file():
                        try:
                            stat = item.stat()
                            files.append({
                                "name": item.name,
                                "path": str(item),
                                "size": stat.st_size,
                                "extension": item.suffix or "",
                                "modified": stat.st_mtime
                            })
                            total_size += stat.st_size
                        except:
                            pass

        else:  # Linux
            trash_paths = [
                FilePath("~/.local/share/Trash/files").expanduser(),
                FilePath("~/.trash").expanduser(),
                FilePath("~/.Trash").expanduser()
            ]
            for trash_path in trash_paths:
                if trash_path.exists():
                    for item in trash_path.iterdir():
                        if item.is_file():
                            try:
                                stat = item.stat()
                                files.append({
                                    "name": item.name,
                                    "path": str(item),
                                    "size": stat.st_size,
                                    "extension": item.suffix or "",
                                    "modified": stat.st_mtime
                                })
                                total_size += stat.st_size
                            except:
                                pass
                    break  # 找到一个就停止

        # 格式化大小
        for f in files:
            f["size_formatted"] = format_size(f["size"])

        return {
            "total": len(files),
            "total_size": total_size,
            "total_size_formatted": format_size(total_size),
            "files": files[:100]  # 最多返回100个
        }

    except Exception as e:
        return {
            "total": 0,
            "total_size": 0,
            "total_size_formatted": "0 B",
            "files": [],
            "error": str(e)
        }


def get_windows_recycle_bin_direct():
    """直接访问 Windows 回收站文件夹"""
    import os
    from pathlib import Path as FilePath

    files = []
    total_size = 0

    try:
        # 尝试访问用户的回收站文件夹
        # Windows 10/11 回收站路径
        recycle_base = FilePath("C:/$Recycle.Bin")

        if recycle_base.exists():
            for folder in recycle_base.iterdir():
                if folder.is_dir() and not folder.name.startswith('.'):
                    try:
                        for item in folder.iterdir():
                            if item.is_file():
                                try:
                                    stat = item.stat()
                                    files.append({
                                        "name": item.name,
                                        "path": str(item),
                                        "size": stat.st_size,
                                        "extension": item.suffix or "",
                                        "modified": stat.st_mtime
                                    })
                                    total_size += stat.st_size
                                except:
                                    pass
                    except:
                        continue
    except Exception as e:
        pass

    return files, total_size

@app.get("/api/scan/report/{scan_id}")
async def get_report(scan_id: str):
    """获取扫描报告（文本格式）"""
    with scanner_lock:
        if scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[scan_id]
        if scan_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="扫描未完成")

        scanner = scan_data["scanner"]

    return {
        "scan_id": scan_id,
        "report": scanner.get_report_text()
    }


@app.get("/api/scan/files/{scan_id}")
async def get_scan_files(scan_id: str, offset: int = 0, limit: int = 100, sort_by: str = "size", order: str = "desc"):
    """获取扫描到的文件列表（分页）"""
    with scanner_lock:
        if scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[scan_id]
        if scan_data["status"] not in ["completed", "stopped"]:
            raise HTTPException(status_code=400, detail="扫描未完成")

        scanner = scan_data["scanner"]
        files = scanner.result.all_files[:]

        # 排序
        if sort_by == "size":
            files.sort(key=lambda x: x.size, reverse=(order == "desc"))
        elif sort_by == "name":
            files.sort(key=lambda x: x.rel_path.lower(), reverse=(order == "desc"))
        elif sort_by == "type":
            files.sort(key=lambda x: Path(x.rel_path).suffix.lower(), reverse=(order == "desc"))

        # 分页
        total = len(files)
        files_page = files[offset:offset + limit]

        return {
            "scan_id": scan_id,
            "total": total,
            "offset": offset,
            "limit": limit,
            "files": [
                {
                    "path": f.path,
                    "rel_path": f.rel_path,
                    "size": f.size,
                    "size_formatted": scanner._format_size(f.size)
                }
                for f in files_page
            ]
        }


@app.get("/api/scan/files/by-type/{scan_id}")
async def get_files_by_type(scan_id: str, file_type: str = ""):
    """按文件类型获取文件列表"""
    with scanner_lock:
        if scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[scan_id]
        if scan_data["status"] not in ["completed", "stopped"]:
            raise HTTPException(status_code=400, detail="扫描未完成")

        scanner = scan_data["scanner"]

        # 筛选文件类型
        if file_type == "(无扩展名)":
            files = [f for f in scanner.result.all_files if not Path(f.rel_path).suffix]
        elif file_type:
            files = [f for f in scanner.result.all_files if Path(f.rel_path).suffix.lower() == file_type.lower()]
        else:
            files = scanner.result.all_files

        # 按大小排序
        files.sort(key=lambda x: x.size, reverse=True)

        return {
            "scan_id": scan_id,
            "file_type": file_type,
            "total": len(files),
            "files": [
                {
                    "path": f.path,
                    "rel_path": f.rel_path,
                    "size": f.size,
                    "size_formatted": scanner._format_size(f.size)
                }
                for f in files[:500]  # 最多返回500个
            ]
        }


@app.get("/api/scans")
async def list_scans():
    """列出所有扫描任务"""
    with scanner_lock:
        scan_list = []
        for scan_id, data in scanners.items():
            scan_list.append({
                "scan_id": scan_id,
                "status": data["status"],
                "directory": data.get("directory", ""),
                "progress": data.get("progress", {})
            })
        return {"scans": scan_list}


@app.post("/api/scan/stop/{scan_id}")
async def stop_scan(scan_id: str):
    """停止正在进行的扫描"""
    with scanner_lock:
        if scan_id not in scanners:
            raise HTTPException(status_code=404, detail="扫描任务不存在")

        scan_data = scanners[scan_id]
        if scan_data["status"] not in ["starting", "scanning"]:
            raise HTTPException(status_code=400, detail="只能停止正在扫描的任务")

        scan_data["should_stop"] = True

    return {"message": "正在停止扫描...", "scan_id": scan_id}


@app.get("/api/filesystem/drives")
async def get_drives():
    """获取可用的驱动器列表"""
    system = platform.system()

    if system == "Windows":
        # Windows: 获取所有驱动器
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                try:
                    total, used, free = os.disk_usage(path)
                    drives.append({
                        "path": path,
                        "name": f"本地磁盘 ({letter}:)",
                        "total": total,
                        "used": used,
                        "free": free,
                        "total_formatted": format_size(total),
                        "free_formatted": format_size(free)
                    })
                except:
                    drives.append({
                        "path": path,
                        "name": f"驱动器 ({letter}:)",
                        "total": 0,
                        "used": 0,
                        "free": 0,
                        "total_formatted": "未知",
                        "free_formatted": "未知"
                    })
        return {"drives": drives}

    else:
        # Linux/Mac: 根目录
        drives = [{
            "path": "/",
            "name": "根目录",
            "total": 0,
            "used": 0,
            "free": 0,
            "total_formatted": "/",
            "free_formatted": ""
        }]
        return {"drives": drives}


@app.get("/api/filesystem/directories")
async def get_directories(path: str = ""):
    """获取指定路径下的子目录列表"""
    try:
        if not path:
            # 默认返回用户主目录
            path = os.path.expanduser("~")

        dir_path = Path(path).resolve()

        if not dir_path.exists():
            raise HTTPException(status_code=404, detail="路径不存在")

        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail="不是目录")

        # 获取子目录和父目录
        directories = []

        # 添加父目录（如果有）
        if dir_path.parent != dir_path:
            directories.append({
                "name": "..",
                "path": str(dir_path.parent),
                "is_parent": True
            })

        # 获取子目录
        try:
            for item in sorted(dir_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        # 尝试获取目录信息
                        stat = item.stat()
                        directories.append({
                            "name": item.name,
                            "path": str(item),
                            "is_parent": False,
                            "modified": stat.st_mtime
                        })
                    except:
                        directories.append({
                            "name": item.name,
                            "path": str(item),
                            "is_parent": False,
                            "modified": 0
                        })
        except PermissionError:
            pass

        return {
            "current_path": str(dir_path),
            "directories": directories
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_size(bytes_size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"


# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
