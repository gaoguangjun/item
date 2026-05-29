// 全局状态
const state = {
    mode: 'file',
    files: [],
    folder: null,
    folderFiles: [],
    results: [],
    downloadedFiles: new Set()
};

// 支持的视频格式
const VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpeg', '.mpg'];

// DOM 元素
const elements = {
    modeTabs: document.querySelectorAll('.mode-tab'),
    fileSelectSection: document.getElementById('fileSelectSection'),
    folderSelectSection: document.getElementById('folderSelectSection'),
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('videoFiles'),
    fileList: document.getElementById('fileList'),
    folderSelector: document.getElementById('folderSelector'),
    folderInput: document.getElementById('folderInput'),
    folderInfo: document.getElementById('folderInfo'),
    folderPath: document.getElementById('folderPath'),
    folderStats: document.getElementById('folderStats'),
    folderFileList: document.getElementById('folderFileList'),
    form: document.getElementById('extractForm'),
    submitBtn: document.getElementById('submitBtn'),
    formatOptions: document.querySelectorAll('.format-option'),
    resultsSection: document.getElementById('resultsSection'),
    resultsSummary: document.getElementById('resultsSummary'),
    resultsList: document.getElementById('resultsList'),
    batchDownloadBtn: document.getElementById('batchDownloadBtn'),
    newExtractionBtn: document.getElementById('newExtractionBtn')
};

// 文件大小格式化
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 检查是否为视频文件
function isVideoFile(filename) {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return VIDEO_EXTENSIONS.includes(ext);
}

// 渲染文件列表
function renderFileList() {
    if (state.files.length === 0) {
        elements.fileList.innerHTML = '';
        return;
    }

    elements.fileList.innerHTML = state.files.map((file, index) => `
        <div class="file-item">
            <div class="file-item-info">
                <span class="file-icon">🎬</span>
                <div>
                    <div class="file-name" title="${file.name}">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <button type="button" class="file-remove" data-index="${index}" title="移除">✕</button>
        </div>
    `).join('');

    document.querySelectorAll('.file-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.target.dataset.index);
            state.files.splice(index, 1);
            renderFileList();
        });
    });
}

// 渲染文件夹文件列表
function renderFolderFileList() {
    if (state.folderFiles.length === 0) {
        elements.folderFileList.innerHTML = '';
        return;
    }

    elements.folderFileList.innerHTML = `
        <div style="margin-top: 15px; font-size: 13px; color: var(--text-secondary);">
            已识别 <span class="highlight">${state.folderFiles.length}</span> 个视频文件：
        </div>
        ${state.folderFiles.map((file) => `
            <div class="file-item">
                <div class="file-item-info">
                    <span class="file-icon">🎬</span>
                    <div>
                        <div class="file-name" title="${file.webkitRelativePath || file.name}">${file.name}</div>
                        <div class="file-size">${formatFileSize(file.size)}</div>
                    </div>
                </div>
            </div>
        `).join('')}
    `;
}

// 处理文件选择
function handleFiles(newFiles) {
    for (const file of newFiles) {
        if (isVideoFile(file.name)) {
            if (!state.files.some(f => f.name === file.name && f.size === file.size)) {
                state.files.push(file);
            }
        }
    }
    renderFileList();
}

// 处理文件夹选择
function handleFolderSelect(files) {
    const videoFiles = [];

    for (const file of files) {
        if (isVideoFile(file.name)) {
            videoFiles.push(file);
        }
    }

    state.folderFiles = videoFiles;

    if (files.length > 0) {
        const firstFile = files[0];
        const path = firstFile.webkitRelativePath || firstFile.name;
        const folderName = path.split('/')[0];
        state.folder = folderName;
    }

    renderFolderFileList();

    if (videoFiles.length > 0) {
        elements.folderPath.textContent = `📁 ${state.folder}`;
        elements.folderStats.innerHTML = `找到 <span class="highlight">${videoFiles.length}</span> 个视频文件`;
        elements.folderInfo.style.display = 'block';
    } else {
        elements.folderInfo.style.display = 'none';
        alert('所选文件夹中没有找到支持的视频文件');
    }
}

// 模式切换
elements.modeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const mode = tab.dataset.mode;
        state.mode = mode;

        elements.modeTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        if (mode === 'file') {
            elements.fileSelectSection.style.display = 'block';
            elements.folderSelectSection.style.display = 'none';
        } else {
            elements.fileSelectSection.style.display = 'none';
            elements.folderSelectSection.style.display = 'block';
        }
    });
});

// 拖放事件
elements.dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropzone.classList.add('dragover');
});

elements.dropzone.addEventListener('dragleave', () => {
    elements.dropzone.classList.remove('dragover');
});

elements.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropzone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

// 点击选择文件
elements.dropzone.addEventListener('click', () => {
    elements.fileInput.click();
});

elements.fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
    elements.fileInput.value = '';
});

// 点击选择文件夹
elements.folderSelector.addEventListener('click', () => {
    elements.folderInput.click();
});

elements.folderInput.addEventListener('change', (e) => {
    handleFolderSelect(e.target.files);
    elements.folderInput.value = '';
});

// 格式选择
elements.formatOptions.forEach(option => {
    option.addEventListener('click', () => {
        elements.formatOptions.forEach(opt => opt.classList.remove('selected'));
        option.classList.add('selected');
        option.querySelector('input[type="radio"]').checked = true;
    });
});

// 表单提交
elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const filesToProcess = state.mode === 'folder' ? state.folderFiles : state.files;

    if (filesToProcess.length === 0) {
        alert(state.mode === 'folder' ? '请先选择包含视频的文件夹' : '请先选择视频文件');
        return;
    }

    const audioFormat = document.querySelector('input[name="audio_format"]:checked').value;

    const formData = new FormData();
    filesToProcess.forEach(file => {
        formData.append('videos', file);
    });
    formData.append('audio_format', audioFormat);

    elements.submitBtn.classList.add('loading');
    elements.submitBtn.disabled = true;

    try {
        const response = await fetch('/extract', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            displayResults(result);
        } else {
            alert('提取失败: ' + result.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        elements.submitBtn.classList.remove('loading');
        elements.submitBtn.disabled = false;
    }
});

// 显示结果
function displayResults(data) {
    state.results = data.results || [];
    state.downloadedFiles.clear();

    elements.form.style.display = 'none';
    elements.resultsSection.style.display = 'block';

    const summaryHtml = `成功: ${data.success_count} / ${data.total_files}`;
    elements.resultsSummary.textContent = summaryHtml;
    elements.resultsSummary.classList.toggle('has-errors', data.error_count > 0);

    if (data.results && data.results.length > 0) {
        elements.batchDownloadBtn.style.display = 'flex';
    } else {
        elements.batchDownloadBtn.style.display = 'none';
    }

    let resultsHtml = '';

    if (data.results && data.results.length > 0) {
        data.results.forEach(item => {
            resultsHtml += `
                <div class="result-item success">
                    <div class="result-info">
                        <div class="result-name">${item.original}</div>
                        <div class="result-meta">→ ${item.output} (${formatFileSize(item.size)})</div>
                    </div>
                    <button class="download-btn" data-id="${item.download_id}" data-name="${item.output}">
                        下载
                    </button>
                </div>
            `;
        });
    }

    if (data.errors && data.errors.length > 0) {
        data.errors.forEach(item => {
            resultsHtml += `
                <div class="result-item error">
                    <div class="result-info">
                        <div class="result-name">${item.file}</div>
                        <div class="result-error">${item.error}</div>
                    </div>
                </div>
            `;
        });
    }

    elements.resultsList.innerHTML = resultsHtml;

    document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const downloadId = e.target.dataset.id;
            const filename = e.target.dataset.name;
            downloadFile(downloadId, filename, e.target);
        });
    });
}

// 下载文件
async function downloadFile(fileId, filename, button) {
    const originalText = button.textContent;
    button.textContent = '下载中...';
    button.disabled = true;

    try {
        const response = await fetch(`/download/${fileId}/${filename}`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            button.textContent = '已完成';
            state.downloadedFiles.add(fileId);
        } else {
            button.textContent = '失败';
            setTimeout(() => {
                button.textContent = originalText;
                button.disabled = false;
            }, 2000);
        }
    } catch (error) {
        button.textContent = '失败';
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 2000);
    }
}

// 批量下载
async function batchDownloadAll() {
    if (state.results.length === 0) return;

    const btn = elements.batchDownloadBtn;
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> 打包中...';

    try {
        const fileIds = state.results.map(r => r.download_id);

        const response = await fetch('/batch-download-zip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_ids: fileIds })
        });

        if (response.ok) {
            btn.innerHTML = '<span class="btn-icon">⏳</span> 下载中...';

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            const disposition = response.headers.get('Content-Disposition');
            let filename = 'audio_files.zip';
            if (disposition && disposition.indexOf('filename=') !== -1) {
                filename = disposition.split('filename=')[1].replace(/"/g, '');
            }
            a.download = filename;

            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            fileIds.forEach(id => state.downloadedFiles.add(id));

            btn.innerHTML = '<span class="btn-icon">✅</span> 下载完成';
        } else {
            btn.innerHTML = '<span class="btn-icon">❌</span> 下载失败';
        }
    } catch (error) {
        btn.innerHTML = '<span class="btn-icon">❌</span> 下载失败';
        console.error('批量下载失败:', error);
    }

    setTimeout(() => {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
    }, 3000);
}

elements.batchDownloadBtn.addEventListener('click', batchDownloadAll);

// 继续提取
elements.newExtractionBtn.addEventListener('click', () => {
    if (state.downloadedFiles.size > 0) {
        fetch('/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_ids: Array.from(state.downloadedFiles) })
        }).catch(() => {});
    }

    state.files = [];
    state.folder = null;
    state.folderFiles = [];
    state.results = [];
    state.downloadedFiles.clear();

    renderFileList();
    elements.folderFileList.innerHTML = '';
    elements.folderInfo.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.form.style.display = 'block';
});
