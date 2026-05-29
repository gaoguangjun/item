import os
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set, Callable, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
import aiofiles


@dataclass
class FileEntry:
    path: str
    size: int
    rel_path: str  # 相对路径，便于展示


@dataclass
class DuplicateGroup:
    group_id: str
    size: int
    files: List[FileEntry]
    md5_hash: str = ""


@dataclass
class ScanResult:
    total_files: int = 0
    total_folders: int = 0
    total_size: int = 0
    file_type_stats: Dict[str, int] = field(default_factory=dict)
    largest_files: List[Tuple[str, int]] = field(default_factory=list)
    all_files: List[FileEntry] = field(default_factory=list)
    duplicate_groups: List[DuplicateGroup] = field(default_factory=list)
    scanned: bool = False


class FileScanner:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.result = ScanResult()
        self._scan_callback = None
        self._progress = {"current": 0, "total": 0, "stage": ""}

    def set_callback(self, callback):
        self._scan_callback = callback

    def _update_progress(self, current: int, total: int, stage: str):
        self._progress = {"current": current, "total": total, "stage": stage}
        if self._scan_callback:
            self._scan_callback(self._progress)

    def calculate_md5(self, filepath: Path, chunk_size: int = 8192) -> str:
        """计算文件的 MD5 哈希值"""
        md5 = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except (OSError, IOError) as e:
            return None

    async def calculate_md5_async(self, filepath: Path, chunk_size: int = 65536) -> str:
        """异步计算文件的 MD5 哈希值"""
        md5 = hashlib.md5()
        try:
            async with aiofiles.open(filepath, 'rb') as f:
                while chunk := await f.read(chunk_size):
                    md5.update(chunk)
            return md5.hexdigest()
        except (OSError, IOError):
            return None

    def scan_directory(self, max_files: int = None, stop_check: Optional[Callable[[], bool]] = None) -> ScanResult:
        """扫描目录，获取文件统计信息"""
        if not self.root_path.exists():
            raise ValueError(f"路径不存在: {self.root_path}")

        all_files = []
        size_by_type = defaultdict(int)
        size_list = []

        self._update_progress(0, 100, "扫描目录中...")

        # 遍历目录
        for root, dirs, files in os.walk(self.root_path):
            # 检查是否停止
            if stop_check and stop_check():
                return all_files

            self.result.total_folders += len(dirs)

            for filename in files:
                # 检查是否停止
                if stop_check and stop_check():
                    return all_files

                filepath = Path(root) / filename

                try:
                    size = filepath.stat().st_size
                    rel_path = str(filepath.relative_to(self.root_path))

                    all_files.append(FileEntry(
                        path=str(filepath),
                        size=size,
                        rel_path=rel_path
                    ))

                    self.result.total_files += 1
                    self.result.total_size += size

                    # 按文件类型统计
                    ext = filepath.suffix.lower() or "(无扩展名)"
                    size_by_type[ext] += 1

                    # 记录大文件
                    size_list.append((rel_path, size))

                except (OSError, IOError) as e:
                    continue

                if max_files and self.result.total_files >= max_files:
                    break

        self.result.file_type_stats = dict(sorted(
            size_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        # Top 20 大文件
        self.result.largest_files = sorted(
            size_list,
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # 保存所有文件列表
        self.result.all_files = all_files

        return all_files

    def find_duplicates(self, files: List[FileEntry] = None, stop_check: Optional[Callable[[], bool]] = None) -> List[DuplicateGroup]:
        """查找重复文件"""
        if files is None:
            files = []
            for root, dirs, filenames in os.walk(self.root_path):
                # 检查是否停止
                if stop_check and stop_check():
                    break
                for filename in filenames:
                    filepath = Path(root) / filename
                    try:
                        size = filepath.stat().st_size
                        rel_path = str(filepath.relative_to(self.root_path))
                        files.append(FileEntry(
                            path=str(filepath),
                            size=size,
                            rel_path=rel_path
                        ))
                    except (OSError, IOError):
                        continue

        # 按大小分组
        self._update_progress(0, len(files), "按大小分组...")
        size_groups = defaultdict(list)
        for i, f in enumerate(files):
            # 检查是否停止
            if stop_check and stop_check():
                break
            size_groups[f.size].append(f)
            if i % 100 == 0:
                self._update_progress(i, len(files), "按大小分组...")

        # 只处理有多个文件的相同大小组
        potential_duplicates = {s: fs for s, fs in size_groups.items() if len(fs) > 1}

        if not potential_duplicates:
            return []

        # 计算 MD5
        self._update_progress(0, len(potential_duplicates), "计算文件哈希值...")
        duplicate_groups = []
        processed = 0

        for size, file_list in potential_duplicates.items():
            # 检查是否停止
            if stop_check and stop_check():
                break

            md5_groups = defaultdict(list)

            for f in file_list:
                md5 = self.calculate_md5(Path(f.path))
                if md5:
                    md5_groups[md5].append(f)

            # 找出真正的重复（MD5 相同且文件数 > 1）
            for md5, dup_files in md5_groups.items():
                if len(dup_files) > 1:
                    # 按路径排序，路径短的作为"原始文件"
                    dup_files.sort(key=lambda x: (len(x.path), x.path))

                    duplicate_groups.append(DuplicateGroup(
                        group_id=f"{md5[:8]}_{size}",
                        size=size,
                        files=dup_files,
                        md5_hash=md5
                    ))

            processed += 1
            if processed % 10 == 0:
                self._update_progress(processed, len(potential_duplicates), "计算文件哈希值...")

        # 按可释放空间排序
        duplicate_groups.sort(key=lambda g: g.size * (len(g.files) - 1), reverse=True)

        self.result.duplicate_groups = duplicate_groups
        self.result.scanned = True
        self._update_progress(len(potential_duplicates), len(potential_duplicates), "扫描完成")

        return duplicate_groups

    def get_progress(self) -> dict:
        """获取当前进度"""
        return self._progress

    def delete_files(self, file_paths: List[str]) -> Tuple[int, List[str]]:
        """删除指定的文件，返回 (成功数, 失败列表)"""
        success = 0
        failed = []

        for filepath in file_paths:
            try:
                path = Path(filepath)
                if path.exists() and path.is_file():
                    path.unlink()
                    success += 1
                else:
                    failed.append(filepath)
            except Exception as e:
                failed.append(f"{filepath} ({str(e)})")

        return success, failed

    def get_report_text(self) -> str:
        """生成文本报告"""
        lines = [
            "=" * 60,
            "重复文件扫描报告",
            "=" * 60,
            f"扫描目录: {self.root_path}",
            f"扫描时间: {self._progress.get('timestamp', 'N/A')}",
            "",
            "【目录统计】",
            f"  总文件数: {self.result.total_files:,}",
            f"  总文件夹数: {self.result.total_folders:,}",
            f"  总大小: {self._format_size(self.result.total_size)}",
            "",
            "【文件类型统计】",
        ]

        for ext, count in list(self.result.file_type_stats.items())[:10]:
            lines.append(f"  {ext}: {count:,}")

        lines.extend([
            "",
            "【重复文件统计】",
            f"  重复组数: {len(self.result.duplicate_groups)}",
        ])

        total_duplicate_size = 0
        total_duplicate_count = 0
        for group in self.result.duplicate_groups:
            total_duplicate_size += group.size * (len(group.files) - 1)
            total_duplicate_count += len(group.files) - 1

        lines.extend([
            f"  重复文件数: {total_duplicate_count:,}",
            f"  可释放空间: {self._format_size(total_duplicate_size)}",
            "",
            "【重复文件详情】",
        ])

        for i, group in enumerate(self.result.duplicate_groups[:20], 1):
            lines.extend([
                f"",
                f"组 #{i} (MD5: {group.md5_hash[:8]}...)",
                f"  文件大小: {self._format_size(group.size)}",
                f"  可释放: {self._format_size(group.size * (len(group.files) - 1))}",
            ])
            for j, f in enumerate(group.files):
                marker = " [原始]" if j == 0 else ""
                lines.append(f"    {j+1}. {f.rel_path}{marker}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
