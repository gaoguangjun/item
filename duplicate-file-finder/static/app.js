// 重复文件检查工具 - 前端逻辑

let currentScanId = null;
let scanResults = null;
let progressInterval = null;
let browseState = {
    currentPath: '',
    selectedPath: ''
};
let filesListState = {
    currentPage: 0,
    pageSize: 50,
    totalFiles: 0,
    currentSort: 'size-desc',
    currentFilter: null,  // null = all files, or file extension
    currentTitle: ''
};

// DOM 元素
const elements = {
    directory: document.getElementById('directory'),
    maxFiles: document.getElementById('maxFiles'),
    browseBtn: document.getElementById('browseBtn'),
    scanBtn: document.getElementById('scanBtn'),
    stopBtn: document.getElementById('stopBtn'),
    progressSection: document.getElementById('progressSection'),
    progressBar: document.getElementById('progressBar'),
    progressText: document.getElementById('progressText'),
    statsSection: document.getElementById('statsSection'),
    duplicatesSection: document.getElementById('duplicatesSection'),
    totalFiles: document.getElementById('totalFiles'),
    totalFolders: document.getElementById('totalFolders'),
    totalSize: document.getElementById('totalSize'),
    duplicateGroups: document.getElementById('duplicateGroups'),
    recoverableSpace: document.getElementById('recoverableSpace'),
    fileTypeList: document.getElementById('fileTypeList'),
    duplicatesList: document.getElementById('duplicatesList'),
    selectAllBtn: document.getElementById('selectAllBtn'),
    deselectAllBtn: document.getElementById('deselectAllBtn'),
    selectSmartBtn: document.getElementById('selectSmartBtn'),
    deleteSelectedBtn: document.getElementById('deleteSelectedBtn'),
    viewRecycleBinBtn: document.getElementById('viewRecycleBinBtn'),
    exportBtn: document.getElementById('exportBtn'),
    toast: document.getElementById('toast'),
    // 对话框元素
    browseDialog: document.getElementById('browseDialog'),
    closeDialogBtn: document.getElementById('closeDialogBtn'),
    drivesList: document.getElementById('drivesList'),
    drivesContainer: document.getElementById('drivesContainer'),
    directoriesList: document.getElementById('directoriesList'),
    directoriesContainer: document.getElementById('directoriesContainer'),
    currentPath: document.getElementById('currentPath'),
    browseLoading: document.getElementById('browseLoading'),
    selectDirBtn: document.getElementById('selectDirBtn'),
    backToDrivesBtn: document.getElementById('backToDrivesBtn'),
    // 文件列表对话框元素
    filesDialog: document.getElementById('filesDialog'),
    filesDialogTitle: document.getElementById('filesDialogTitle'),
    closeFilesDialogBtn: document.getElementById('closeFilesDialogBtn'),
    closeFilesBtn: document.getElementById('closeFilesBtn'),
    filesTotalCount: document.getElementById('filesTotalCount'),
    filesSortSelect: document.getElementById('filesSortSelect'),
    filesSearchInput: document.getElementById('filesSearchInput'),
    filesListContainer: document.getElementById('filesListContainer'),
    filesPrevBtn: document.getElementById('filesPrevBtn'),
    filesNextBtn: document.getElementById('filesNextBtn'),
    filesPageInfo: document.getElementById('filesPageInfo'),
    // 删除进度对话框元素
    deleteProgressDialog: document.getElementById('deleteProgressDialog'),
    deleteProgressBar: document.getElementById('deleteProgressBar'),
    deleteProgressText: document.getElementById('deleteProgressText'),
    deleteTotal: document.getElementById('deleteTotal'),
    deleteSuccess: document.getElementById('deleteSuccess'),
    deleteFailed: document.getElementById('deleteFailed'),
    closeDeleteProgressBtn: document.getElementById('closeDeleteProgressBtn'),
    // 回收站对话框元素
    recycleBinDialog: document.getElementById('recycleBinDialog'),
    closeRecycleBinDialogBtn: document.getElementById('closeRecycleBinDialogBtn'),
    closeRecycleBinBtn: document.getElementById('closeRecycleBinBtn'),
    recycleBinCount: document.getElementById('recycleBinCount'),
    recycleBinSize: document.getElementById('recycleBinSize'),
    recycleFilesList: document.getElementById('recycleFilesList'),
    recycleLoading: document.getElementById('recycleLoading'),
    recycleEmpty: document.getElementById('recycleEmpty'),
    refreshRecycleBinBtn: document.getElementById('refreshRecycleBinBtn'),
    emptyRecycleBinConfirmBtn: document.getElementById('emptyRecycleBinConfirmBtn')
};

// 工具函数
function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

function formatNumber(num) {
    return num.toLocaleString('zh-CN');
}

function showToast(message, type = 'info') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type} show`;
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

// ==================== 目录浏览功能 ====================

async function openBrowseDialog() {
    elements.browseDialog.classList.remove('hidden');
    elements.drivesList.classList.add('hidden');
    elements.directoriesList.classList.add('hidden');
    elements.browseLoading.classList.remove('hidden');
    elements.backToDrivesBtn.classList.add('hidden');

    try {
        // 加载驱动器列表
        const response = await fetch('/api/filesystem/drives');
        const data = await response.json();

        elements.browseLoading.classList.add('hidden');
        elements.drivesList.classList.remove('hidden');

        displayDrives(data.drives);

    } catch (error) {
        elements.browseLoading.classList.add('hidden');
        showToast('加载驱动器失败: ' + error.message, 'error');
    }
}

function displayDrives(drives) {
    elements.drivesContainer.innerHTML = '';

    if (!drives || drives.length === 0) {
        elements.drivesContainer.innerHTML = '<p class="text-muted">未找到可用驱动器</p>';
        return;
    }

    drives.forEach(drive => {
        const item = document.createElement('div');
        item.className = 'drive-item';
        item.innerHTML = `
            <div class="drive-name">${drive.name}</div>
            <div class="drive-info">${drive.total_formatted} · 可用 ${drive.free_formatted}</div>
        `;
        item.addEventListener('click', () => loadDirectory(drive.path));
        elements.drivesContainer.appendChild(item);
    });
}

async function loadDirectory(path) {
    elements.browseLoading.classList.remove('hidden');
    elements.drivesList.classList.add('hidden');
    elements.directoriesList.classList.add('hidden');

    try {
        const response = await fetch(`/api/filesystem/directories?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        elements.browseLoading.classList.add('hidden');
        elements.directoriesList.classList.remove('hidden');
        elements.backToDrivesBtn.classList.remove('hidden');

        browseState.currentPath = data.current_path;
        displayDirectories(data.directories);

    } catch (error) {
        elements.browseLoading.classList.add('hidden');
        showToast('加载目录失败: ' + error.message, 'error');
    }
}

function displayDirectories(directories) {
    elements.currentPath.textContent = browseState.currentPath;
    elements.directoriesContainer.innerHTML = '';

    if (!directories || directories.length === 0) {
        elements.directoriesContainer.innerHTML = '<p class="text-muted">此目录为空</p>';
        return;
    }

    directories.forEach(dir => {
        const item = document.createElement('div');
        item.className = 'directory-item' + (dir.is_parent ? ' is-parent' : '');
        item.innerHTML = `
            <svg class="directory-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
            </svg>
            <span class="directory-name">${dir.name}</span>
        `;
        item.addEventListener('click', () => loadDirectory(dir.path));
        elements.directoriesContainer.appendChild(item);
    });
}

function closeBrowseDialog() {
    elements.browseDialog.classList.add('hidden');
}

function selectCurrentDirectory() {
    if (browseState.currentPath) {
        elements.directory.value = browseState.currentPath;
        browseState.selectedPath = browseState.currentPath;
        closeBrowseDialog();
    }
}

function backToDrives() {
    elements.directoriesList.classList.add('hidden');
    elements.backToDrivesBtn.classList.add('hidden');
    elements.drivesList.classList.remove('hidden');
}

// ==================== 扫描控制功能 ====================

async function startScan() {
    const directory = elements.directory.value.trim();
    if (!directory) {
        showToast('请先选择要扫描的目录', 'error');
        return;
    }

    elements.scanBtn.classList.add('hidden');
    elements.stopBtn.classList.remove('hidden');
    elements.progressSection.classList.remove('hidden');
    elements.statsSection.classList.add('hidden');
    elements.duplicatesSection.classList.add('hidden');
    elements.duplicatesList.innerHTML = '';

    try {
        const response = await fetch('/api/scan/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                directory: directory,
                max_files: elements.maxFiles.value ? parseInt(elements.maxFiles.value) : null
            })
        });

        const data = await response.json();
        currentScanId = data.scan_id;

        pollProgress();

    } catch (error) {
        showToast('启动扫描失败: ' + error.message, 'error');
        resetScanButtons();
    }
}

async function stopScan() {
    if (!currentScanId) return;

    try {
        const response = await fetch(`/api/scan/stop/${currentScanId}`, {
            method: 'POST'
        });

        if (response.ok) {
            showToast('正在停止扫描...', 'info');
        }

    } catch (error) {
        showToast('停止扫描失败: ' + error.message, 'error');
    }
}

function pollProgress() {
    if (progressInterval) clearInterval(progressInterval);

    progressInterval = setInterval(async () => {
        if (!currentScanId) return;

        try {
            const response = await fetch(`/api/scan/status/${currentScanId}`);
            const data = await response.json();

            updateProgress(data);

            if (data.status === 'completed') {
                clearInterval(progressInterval);
                await loadResults();
                resetScanButtons();
                showToast('扫描完成！', 'success');
            } else if (data.status === 'stopped') {
                clearInterval(progressInterval);
                elements.progressText.textContent = '扫描已停止';
                resetScanButtons();
                showToast('扫描已停止', 'info');
            } else if (data.status === 'error') {
                clearInterval(progressInterval);
                showToast('扫描出错: ' + (data.error || '未知错误'), 'error');
                resetScanButtons();
            }

        } catch (error) {
            console.error('获取状态失败:', error);
        }
    }, 500);
}

function updateProgress(data) {
    const progress = data.progress || {};
    const current = progress.current || 0;
    const total = progress.total || 100;
    const stage = progress.stage || '处理中...';

    const percent = total > 0 ? Math.min(100, (current / total) * 100) : 0;
    elements.progressBar.style.width = `${percent}%`;
    elements.progressText.textContent = `${stage} ${Math.floor(percent)}%`;
}

async function loadResults() {
    if (!currentScanId) return;

    try {
        const response = await fetch(`/api/scan/results/${currentScanId}`);
        scanResults = await response.json();

        displayStats(scanResults.stats);
        displayDuplicates(scanResults.duplicate_groups);

    } catch (error) {
        showToast('加载结果失败: ' + error.message, 'error');
    }
}

function displayStats(stats) {
    elements.statsSection.classList.remove('hidden');

    elements.totalFiles.textContent = formatNumber(stats.total_files || 0);
    elements.totalFolders.textContent = formatNumber(stats.total_folders || 0);
    elements.totalSize.textContent = formatSize(stats.total_size || 0);
    elements.duplicateGroups.textContent = formatNumber(stats.duplicate_groups || 0);

    // 使统计卡片可点击
    elements.totalFiles.parentElement.classList.add('clickable');
    elements.totalFolders.parentElement.classList.add('clickable');
    elements.totalSize.parentElement.classList.add('clickable');
    elements.duplicateGroups.parentElement.classList.add('clickable');
    elements.recoverableSpace.parentElement.classList.add('clickable');

    // 绑定点击事件
    elements.totalFiles.parentElement.onclick = () => showFilesList('所有文件');
    elements.totalSize.parentElement.onclick = () => showFilesList('所有文件（按大小）');
    elements.duplicateGroups.parentElement.onclick = () => {
        elements.duplicatesSection.scrollIntoView({ behavior: 'smooth' });
    };

    if (stats.file_type_stats) {
        elements.fileTypeList.innerHTML = '';
        Object.entries(stats.file_type_stats).slice(0, 15).forEach(([ext, count]) => {
            const tag = document.createElement('span');
            tag.className = 'file-type-tag';
            tag.style.cursor = 'pointer';
            tag.innerHTML = `${ext || '(无)'}: <span>${formatNumber(count)}</span>`;
            tag.addEventListener('click', () => showFilesList(`${ext || '(无)'} 文件`, ext));
            elements.fileTypeList.appendChild(tag);
        });
    }
}

function displayDuplicates(groups) {
    elements.duplicatesSection.classList.remove('hidden');

    if (!groups || groups.length === 0) {
        elements.duplicatesList.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p>未发现重复文件！</p>
            </div>
        `;
        elements.recoverableSpace.textContent = '0 B';
        return;
    }

    elements.duplicatesList.innerHTML = '';
    let totalRecoverable = 0;

    groups.forEach((group, index) => {
        totalRecoverable += group.size * (group.files.length - 1);
        const groupEl = createGroupElement(group, index);
        elements.duplicatesList.appendChild(groupEl);
    });

    elements.recoverableSpace.textContent = formatSize(totalRecoverable);
}

function createGroupElement(group, index) {
    const container = document.createElement('div');
    container.className = 'duplicate-group';
    container.dataset.groupId = group.group_id;

    const header = document.createElement('div');
    header.className = 'group-header';
    header.innerHTML = `
        <div class="group-info">
            <span>重复组 #${index + 1}</span>
            <span class="group-size">${group.size_formatted}</span>
            <span class="group-recoverable">可释放: ${group.recoverable}</span>
            <span>${group.files.length} 个文件</span>
        </div>
        <span class="group-toggle">▼</span>
    `;

    const filesContainer = document.createElement('div');
    filesContainer.className = 'group-files';

    group.files.forEach((file, fileIndex) => {
        const fileEl = document.createElement('div');
        fileEl.className = 'file-item' + (fileIndex === 0 ? ' original' : '');
        fileEl.innerHTML = `
            <input type="checkbox" class="file-checkbox" data-path="${file.path}">
            <span class="file-path">${file.rel_path}</span>
            <span class="file-badge ${fileIndex === 0 ? 'original' : 'duplicate'}">
                ${fileIndex === 0 ? '原始' : '重复'}
            </span>
        `;
        filesContainer.appendChild(fileEl);
    });

    header.addEventListener('click', () => {
        filesContainer.classList.toggle('expanded');
        header.querySelector('.group-toggle').classList.toggle('expanded');
    });

    container.appendChild(header);
    container.appendChild(filesContainer);

    return container;
}

// ==================== 批量操作 ====================

function selectAll() {
    document.querySelectorAll('.file-checkbox').forEach(cb => {
        if (!cb.closest('.file-item').classList.contains('original')) {
            cb.checked = true;
        }
    });
}

function deselectAll() {
    document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = false);
}

function selectSmart() {
    document.querySelectorAll('.file-checkbox').forEach(cb => {
        const path = cb.dataset.path;
        const isMarked = /\(\d\)|\.copy| - 副本|\[1\]/i.test(path);
        if (isMarked) {
            cb.checked = true;
        }
    });
    showToast('已智能选择标记的重复文件', 'success');
}

async function deleteSelected() {
    const selected = [];
    document.querySelectorAll('.file-checkbox:checked').forEach(cb => {
        selected.push(cb.dataset.path);
    });

    if (selected.length === 0) {
        showToast('请先选择要删除的文件', 'error');
        return;
    }

    const confirmed = confirm(`确定要删除 ${selected.length} 个文件吗？此操作不可撤销！`);
    if (!confirmed) return;

    // 显示删除进度对话框
    showDeleteProgress(selected.length);

    try {
        const response = await fetch('/api/scan/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scan_id: currentScanId,
                files: selected
            })
        });

        const result = await response.json();

        // 轮询删除进度
        pollDeleteProgress(currentScanId, result.delete_id, selected.length);

    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
        closeDeleteProgress();
    }
}

function showDeleteProgress(total) {
    elements.deleteProgressDialog.classList.remove('hidden');
    elements.deleteProgressBar.style.width = '0%';
    elements.deleteProgressText.textContent = '准备删除...';
    elements.deleteTotal.textContent = formatNumber(total);
    elements.deleteSuccess.textContent = '0';
    elements.deleteFailed.textContent = '0';
    elements.closeDeleteProgressBtn.classList.add('hidden');
}

function pollDeleteProgress(scanId, deleteId, total) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/scan/delete/status/${scanId}/${deleteId}`);
            const data = await response.json();

            // 更新进度
            const percent = data.total > 0 ? (data.current / data.total) * 100 : 0;
            elements.deleteProgressBar.style.width = `${percent}%`;
            elements.deleteProgressText.textContent = `正在删除... ${Math.floor(percent)}%`;
            elements.deleteSuccess.textContent = formatNumber(data.success);
            elements.deleteFailed.textContent = formatNumber(data.failed ? data.failed.length : 0);

            if (data.status === 'completed') {
                clearInterval(interval);

                // 删除完成
                elements.deleteProgressBar.style.width = '100%';
                elements.deleteProgressText.textContent = '删除完成！';

                // 显示关闭按钮
                elements.closeDeleteProgressBtn.classList.remove('hidden');

                // 显示结果消息
                if (data.success > 0) {
                    showToast(`成功删除 ${data.success} 个文件`, 'success');
                }

                // 重新加载结果
                await loadResults();
            }

        } catch (error) {
            clearInterval(interval);
            console.error('获取删除进度失败:', error);
        }
    }, 200);
}

function closeDeleteProgress() {
    elements.deleteProgressDialog.classList.add('hidden');
}

async function openRecycleBinDialog() {
    elements.recycleBinDialog.classList.remove('hidden');
    elements.recycleLoading.classList.remove('hidden');
    elements.recycleFilesList.innerHTML = '';
    elements.recycleEmpty.classList.add('hidden');

    await loadRecycleBinContents();
}

async function loadRecycleBinContents() {
    elements.recycleLoading.classList.remove('hidden');
    elements.recycleFilesList.innerHTML = '';
    elements.recycleEmpty.classList.add('hidden');

    try {
        const response = await fetch('/api/system/recycle-bin');
        const data = await response.json();

        elements.recycleLoading.classList.add('hidden');

        // 更新统计
        elements.recycleBinCount.textContent = formatNumber(data.total || 0);
        elements.recycleBinSize.textContent = data.total_size_formatted || '0 B';

        if (data.total === 0) {
            elements.recycleEmpty.classList.remove('hidden');
            return;
        }

        // 显示文件列表
        displayRecycleBinFiles(data.files || []);

    } catch (error) {
        elements.recycleLoading.classList.add('hidden');
        showToast('加载回收站失败: ' + error.message, 'error');
    }
}

function displayRecycleBinFiles(files) {
    if (!files || files.length === 0) {
        elements.recycleFilesList.innerHTML = '';
        elements.recycleEmpty.classList.remove('hidden');
        return;
    }

    let html = `
        <div class="files-list">
            <div class="files-list-header">
                <span>文件名</span>
                <span style="text-align:right">大小</span>
                <span style="text-align:center">类型</span>
            </div>
    `;

    files.forEach(file => {
        const ext = (file.extension || file.name.split('.').pop()).toUpperCase().slice(0, 4) || '(无)';
        html += `
            <div class="recycle-file-item">
                <span class="file-list-name" title="${file.name}">${file.name}</span>
                <span class="file-list-size">${file.size_formatted}</span>
                <span class="file-list-type">${ext}</span>
            </div>
        `;
    });

    html += '</div>';

    if (files.length >= 100) {
        html += `<p style="text-align:center;color:#999;padding:10px;">显示前 100 个文件，共 ${formatNumber(files.length)} 个</p>`;
    }

    elements.recycleFilesList.innerHTML = html;
}

function closeRecycleBinDialog() {
    elements.recycleBinDialog.classList.add('hidden');
}

async function emptyRecycleBin() {
    const confirmed = confirm('确定要清空回收站吗？此操作不可撤销！');
    if (!confirmed) return;

    showToast('正在清空回收站...', 'info');

    try {
        const response = await fetch('/api/system/empty-recycle-bin', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showToast('回收站已清空', 'success');
            // 刷新回收站内容
            await loadRecycleBinContents();
        } else {
            showToast(result.message || '清空回收站失败', 'error');
        }

    } catch (error) {
        showToast('清空回收站失败: ' + error.message, 'error');
    }
}

async function exportReport() {
    if (!currentScanId) return;

    try {
        const response = await fetch(`/api/scan/report/${currentScanId}`);
        const data = await response.json();

        const blob = new Blob([data.report], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `重复文件报告_${new Date().toISOString().slice(0,10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);

        showToast('报告已导出', 'success');

    } catch (error) {
        showToast('导出失败: ' + error.message, 'error');
    }
}

function resetScanButtons() {
    elements.scanBtn.classList.remove('hidden');
    elements.stopBtn.classList.add('hidden');
    elements.scanBtn.disabled = false;
}

// ==================== 文件列表查看功能 ====================

function showFilesList(title, filter = null) {
    if (!currentScanId) {
        showToast('请先完成扫描', 'error');
        return;
    }

    filesListState.currentTitle = title;
    filesListState.currentFilter = filter;
    filesListState.currentPage = 0;

    elements.filesDialogTitle.textContent = title;
    elements.filesDialog.classList.remove('hidden');

    loadFilesPage();
}

async function loadFilesPage() {
    const offset = filesListState.currentPage * filesListState.pageSize;
    const [sort_by, order] = filesListState.currentSort.split('-');

    elements.filesListContainer.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>加载中...</p></div>';

    try {
        let url;
        if (filesListState.currentFilter) {
            // 按文件类型筛选
            url = `/api/scan/files/by-type/${currentScanId}?file_type=${encodeURIComponent(filesListState.currentFilter)}`;
        } else {
            // 获取所有文件
            url = `/api/scan/files/${currentScanId}?offset=${offset}&limit=${filesListState.pageSize}&sort_by=${sort_by}&order=${order}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        filesListState.totalFiles = data.total;
        elements.filesTotalCount.textContent = formatNumber(data.total);

        displayFilesList(data.files, data.total);

        // 更新分页信息
        updatePagination();

    } catch (error) {
        showToast('加载文件列表失败: ' + error.message, 'error');
        elements.filesListContainer.innerHTML = '<div class="files-empty">加载失败</div>';
    }
}

function displayFilesList(files, total) {
    if (!files || files.length === 0) {
        elements.filesListContainer.innerHTML = '<div class="files-empty">暂无文件</div>';
        return;
    }

    let html = `
        <div class="files-list">
            <div class="files-list-header">
                <span>文件名</span>
                <span style="text-align:right">大小</span>
                <span style="text-align:center">类型</span>
            </div>
    `;

    files.forEach(file => {
        const ext = file.rel_path.split('.').pop().toUpperCase().slice(0, 4) || '(无)';
        html += `
            <div class="file-list-item">
                <span class="file-list-name" title="${file.rel_path}">${file.rel_path}</span>
                <span class="file-list-size">${file.size_formatted}</span>
                <span class="file-list-type">${ext}</span>
            </div>
        `;
    });

    html += '</div>';
    elements.filesListContainer.innerHTML = html;
}

function updatePagination() {
    const totalPages = Math.ceil(filesListState.totalFiles / filesListState.pageSize);
    const currentPage = filesListState.currentPage + 1;

    elements.filesPageInfo.textContent = `第 ${currentPage} / ${totalPages || 1} 页`;
    elements.filesPrevBtn.disabled = filesListState.currentPage === 0;
    elements.filesNextBtn.disabled = filesListState.currentPage >= totalPages - 1;
}

function filesPrevPage() {
    if (filesListState.currentPage > 0) {
        filesListState.currentPage--;
        loadFilesPage();
    }
}

function filesNextPage() {
    const totalPages = Math.ceil(filesListState.totalFiles / filesListState.pageSize);
    if (filesListState.currentPage < totalPages - 1) {
        filesListState.currentPage++;
        loadFilesPage();
    }
}

function closeFilesDialog() {
    elements.filesDialog.classList.add('hidden');
}

function onFilesSortChange() {
    filesListState.currentSort = elements.filesSortSelect.value;
    filesListState.currentPage = 0;
    loadFilesPage();
}

// ==================== 事件绑定 ====================

// 扫描控制
elements.scanBtn.addEventListener('click', startScan);
elements.stopBtn.addEventListener('click', stopScan);

// 目录浏览
elements.browseBtn.addEventListener('click', openBrowseDialog);
elements.closeDialogBtn.addEventListener('click', closeBrowseDialog);
elements.selectDirBtn.addEventListener('click', selectCurrentDirectory);
elements.backToDrivesBtn.addEventListener('click', backToDrives);

// 点击对话框外部关闭
elements.browseDialog.addEventListener('click', (e) => {
    if (e.target === elements.browseDialog) {
        closeBrowseDialog();
    }
});

// 文件列表对话框
elements.closeFilesDialogBtn.addEventListener('click', closeFilesDialog);
elements.closeFilesBtn.addEventListener('click', closeFilesDialog);
elements.filesDialog.addEventListener('click', (e) => {
    if (e.target === elements.filesDialog) {
        closeFilesDialog();
    }
});
elements.filesPrevBtn.addEventListener('click', filesPrevPage);
elements.filesNextBtn.addEventListener('click', filesNextPage);
elements.filesSortSelect.addEventListener('change', onFilesSortChange);

// 批量操作
elements.selectAllBtn.addEventListener('click', selectAll);
elements.deselectAllBtn.addEventListener('click', deselectAll);
elements.selectSmartBtn.addEventListener('click', selectSmart);
elements.viewRecycleBinBtn.addEventListener('click', openRecycleBinDialog);
elements.deleteSelectedBtn.addEventListener('click', deleteSelected);
elements.exportBtn.addEventListener('click', exportReport);

// 删除进度对话框
elements.closeDeleteProgressBtn.addEventListener('click', closeDeleteProgress);

// 回收站对话框
elements.closeRecycleBinDialogBtn.addEventListener('click', closeRecycleBinDialog);
elements.closeRecycleBinBtn.addEventListener('click', closeRecycleBinDialog);
elements.recycleBinDialog.addEventListener('click', (e) => {
    if (e.target === elements.recycleBinDialog) {
        closeRecycleBinDialog();
    }
});
elements.refreshRecycleBinBtn.addEventListener('click', loadRecycleBinContents);
elements.emptyRecycleBinConfirmBtn.addEventListener('click', emptyRecycleBin);

// 页面加载时初始化
window.addEventListener('DOMContentLoaded', () => {
    // 如果有默认路径，自动填充
    const defaultDir = 'D:\\高云曦';
    elements.directory.value = defaultDir;
});
