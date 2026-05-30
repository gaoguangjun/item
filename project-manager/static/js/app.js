// 应用状态
let projects = [];
let software = [];
let sysProcesses = [];
let currentTab = 'projects';

// DOM 元素
const projectsList = document.getElementById('projects-list');
const softwareList = document.getElementById('software-list');
const sysprocList = document.getElementById('sysproc-list');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSearch();
    initRefresh();
    initModal();
    initEventDelegation();
    loadAllData();

    // 定期刷新运行状态
    setInterval(refreshStatus, 5000);
});

// 初始化事件委托
function initEventDelegation() {
    // 项目列表的点击事件
    projectsList.addEventListener('click', (e) => {
        const card = e.target.closest('.item-card');
        if (!card) return;

        const path = card.dataset.path;
        if (!path) return;

        if (e.target.closest('.btn-start')) {
            e.stopPropagation();
            startProject(path);
        } else if (e.target.closest('.btn-stop')) {
            e.stopPropagation();
            stopProject(path);
        } else if (e.target.closest('.btn-restart')) {
            e.stopPropagation();
            restartProject(path);
        } else if (e.target.closest('.btn-detail')) {
            e.stopPropagation();
            showProjectDetail(path);
        } else {
            // 点击卡片其他区域显示详情
            showProjectDetail(path);
        }
    });

    // 系统进程列表的点击事件
    sysprocList.addEventListener('click', (e) => {
        const card = e.target.closest('.sysproc-card');
        if (!card) return;

        const pid = parseInt(card.dataset.pid);
        if (e.target.closest('.btn-kill-proc')) {
            e.stopPropagation();
            killProcess(pid);
        }
    });
}

// 初始化标签页
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;

    // 更新标签按钮
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    // 更新面板
    document.querySelectorAll('.panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `${tab}-panel`);
    });

    // 如果切换到系统进程标签页，刷新进程列表
    if (tab === 'sysprocesses') {
        loadSysProcesses();
    }
    if (tab === 'services') {
        loadServices();
    }
}

// 初始化搜索
function initSearch() {
    const projectSearch = document.getElementById('project-search');
    const typeFilter = document.getElementById('type-filter');
    const softwareSearch = document.getElementById('software-search');
    const sysprocSearch = document.getElementById('sysproc-search');
    const sysprocTypeFilter = document.getElementById('sysproc-type-filter');

    projectSearch.addEventListener('input', () => renderProjects());
    typeFilter.addEventListener('change', () => renderProjects());
    softwareSearch.addEventListener('input', () => renderSoftware());
    sysprocSearch.addEventListener('input', () => renderSysProcesses());
    sysprocTypeFilter.addEventListener('change', () => renderSysProcesses());
}

// 初始化刷新按钮
function initRefresh() {
    document.getElementById('refresh-btn').addEventListener('click', loadAllData);
}

// 初始化弹窗
function initModal() {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.querySelector('.close-btn').addEventListener('click', closeModal);
}

// 加载所有数据
async function loadAllData() {
    showLoading();

    try {
        const response = await fetch('/api/scan');
        const data = await response.json();

        projects = data.projects || [];
        software = data.software || [];

        document.getElementById('scan-dir').textContent =
            `扫描目录: ${projects.length} 个项目, ${software.length} 个软件`;

        renderProjects();
        renderSoftware();
        loadSysProcesses();
    } catch (error) {
        console.error('加载失败:', error);
        showError('加载失败，请刷新重试');
    }
}

// 刷新运行状态
async function refreshStatus() {
    try {
        const response = await fetch('/api/scan');
        const data = await response.json();

        // 更新项目的运行状态
        const updatedProjects = data.projects || [];
        const runningMap = {};
        updatedProjects.forEach(p => {
            runningMap[p.path] = p.running;
        });

        projects.forEach(p => {
            if (runningMap[p.path] !== undefined) {
                p.running = runningMap[p.path];
            }
        });

        renderProjects();
        if (currentTab === 'sysprocesses') {
            loadSysProcesses();
        }
    } catch (error) {
        console.error('状态刷新失败:', error);
    }
}

// 加载系统进程
async function loadSysProcesses() {
    try {
        const response = await fetch('/api/running-processes');
        sysProcesses = await response.json();
        renderSysProcesses();
    } catch (error) {
        console.error('加载进程失败:', error);
    }
}

// 显示加载状态
function showLoading() {
    projectsList.innerHTML = '<div class="loading">加载中...</div>';
    softwareList.innerHTML = '<div class="loading">加载中...</div>';
    sysprocList.innerHTML = '<div class="loading">加载中...</div>';
}

// 显示错误
function showError(message) {
    projectsList.innerHTML = `<div class="empty-state"><span class="icon">⚠️</span>${message}</div>`;
}

// 显示提示消息
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 格式化文件大小
function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// JSON 安全字符串转义
function jsonEscape(str) {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

// HTML 转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 渲染项目列表
function renderProjects() {
    const searchTerm = document.getElementById('project-search').value.toLowerCase();
    const typeFilter = document.getElementById('type-filter').value;

    const filtered = projects.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(searchTerm);
        const matchesType = !typeFilter || p.type === typeFilter;
        return matchesSearch && matchesType;
    });

    if (filtered.length === 0) {
        projectsList.innerHTML = `
            <div class="empty-state">
                <span class="icon">📁</span>
                <p>未找到匹配的项目</p>
            </div>
        `;
        return;
    }

    projectsList.innerHTML = filtered.map(project => `
        <div class="item-card ${project.running ? 'running' : ''}" data-path="${jsonEscape(project.path)}">
            <div class="item-header">
                <span class="item-name">${escapeHtml(project.name)}</span>
                <span class="status-badge ${project.running ? 'running' : 'stopped'}">
                    <span class="status-dot ${project.running ? 'animated' : ''}"></span>
                    ${project.running ? '运行中' : '已停止'}
                </span>
            </div>
            <div class="item-path">${escapeHtml(project.path)}</div>
            <div class="item-meta">
                <span>📦 <span class="item-type ${project.type}">${project.type}</span></span>
                <span>📊 ${formatSize(project.size)}</span>
            </div>
            ${project.description ? `<div class="item-desc">${escapeHtml(project.description)}</div>` : ''}
            <div class="item-controls">
                ${project.running
                    ? `<button class="btn btn-warning btn-restart">
                        <span class="icon">↻</span> 重启
                       </button>
                       <button class="btn btn-danger btn-stop">
                        <span class="icon">⏹</span> 停止
                       </button>`
                    : `<button class="btn btn-success btn-start">
                        <span class="icon">▶</span> 启动
                       </button>`
                }
                <button class="btn btn-primary btn-detail">
                    <span class="icon">ℹ</span> 详情
                </button>
            </div>
        </div>
    `).join('');
}

// 渲染系统进程列表
function renderSysProcesses() {
    const searchTerm = document.getElementById('sysproc-search').value.toLowerCase();
    const typeFilter = document.getElementById('sysproc-type-filter').value;

    const filtered = sysProcesses.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(searchTerm) ||
                             p.cmdline.toLowerCase().includes(searchTerm) ||
                             p.cwd.toLowerCase().includes(searchTerm);
        const matchesType = !typeFilter || p.type === typeFilter;
        return matchesSearch && matchesType;
    });

    if (filtered.length === 0) {
        sysprocList.innerHTML = `
            <div class="empty-state">
                <span class="icon">⚡</span>
                <p>未找到运行中的开发进程</p>
            </div>
        `;
        return;
    }

    sysprocList.innerHTML = filtered.map(proc => `
        <div class="sysproc-card ${proc.managed ? 'managed' : ''}" data-pid="${proc.pid}">
            <div class="sysproc-header">
                <span class="sysproc-icon">${proc.icon || '⚙️'}</span>
                <div class="sysproc-main">
                    <div class="sysproc-name">
                        ${escapeHtml(proc.name)}
                        ${proc.managed ? '<span class="managed-badge">已管理</span>' : ''}
                    </div>
                    <div class="sysproc-type">${escapeHtml(proc.type)}</div>
                </div>
            </div>
            <div class="sysproc-details">
                <div class="sysproc-detail-item">
                    <span class="label">PID:</span>
                    <span class="value">${proc.pid}</span>
                </div>
                <div class="sysproc-detail-item">
                    <span class="label">内存:</span>
                    <span class="value">${formatSize(proc.memory_mb * 1024 * 1024)}</span>
                </div>
                <div class="sysproc-detail-item">
                    <span class="label">CPU:</span>
                    <span class="value">${proc.cpu_percent.toFixed(1)}%</span>
                </div>
                ${proc.ports.length > 0 ? `
                    <div class="sysproc-detail-item">
                        <span class="label">端口:</span>
                        <span class="value">${proc.ports.map(p => `<a href="http://localhost:${p}" target="_blank" class="port-link">${p}</a>`).join(', ')}</span>
                    </div>
                ` : ''}
            </div>
            <div class="sysproc-cmd">${escapeHtml(proc.cmdline)}</div>
            <div class="sysproc-cwd">${escapeHtml(proc.cwd)}</div>
            <div class="sysproc-actions">
                ${!proc.managed ? `
                    <button class="btn btn-danger btn-kill-proc">
                        <span class="icon">⏹</span> 结束进程
                    </button>
                ` : `
                    <span class="managed-info">由项目管理器管理</span>
                `}
            </div>
        </div>
    `).join('');
}

// 渲染软件列表
function renderSoftware() {
    const searchTerm = document.getElementById('software-search').value.toLowerCase();

    const filtered = software.filter(s => {
        return s.name.toLowerCase().includes(searchTerm) ||
               (s.publisher && s.publisher.toLowerCase().includes(searchTerm));
    });

    if (filtered.length === 0) {
        softwareList.innerHTML = `
            <div class="empty-state">
                <span class="icon">💻</span>
                <p>未找到匹配的软件</p>
            </div>
        `;
        return;
    }

    softwareList.innerHTML = filtered.map(sw => `
        <div class="item-card">
            <div class="item-header">
                <span class="item-name">${escapeHtml(sw.name)}</span>
            </div>
            <div class="item-meta">
                <span>📌 ${sw.publisher || '未知'}</span>
                <span>🏷️ ${sw.version || '未知版本'}</span>
            </div>
            ${sw.install_location ? `<div class="item-path">${escapeHtml(sw.install_location)}</div>` : ''}
        </div>
    `).join('');
}

// 启动项目
async function startProject(path) {
    try {
        showToast('正在启动项目...', 'success');
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const result = await response.json();

        if (result.success) {
            showToast(`项目已启动 (PID: ${result.pid})`, 'success');
            if (result.port) {
                showToast(`访问地址: http://localhost:${result.port}`, 'success');
            }
            await refreshStatus();
        } else {
            showToast(`启动失败: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('启动失败:', error);
        showToast('启动失败', 'error');
    }
}

// 停止项目
async function stopProject(path) {
    if (!confirm('确定要停止此项目吗？')) return;

    try {
        const response = await fetch('/api/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const result = await response.json();

        if (result.success) {
            showToast('项目已停止', 'success');
            await refreshStatus();
        } else {
            showToast(`停止失败: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('停止失败:', error);
        showToast('停止失败', 'error');
    }
}

// 重启项目
async function restartProject(path) {
    try {
        showToast('正在重启项目...', 'success');
        const response = await fetch('/api/restart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const result = await response.json();

        if (result.success) {
            showToast(`项目已重启 (PID: ${result.pid})`, 'success');
            if (result.port) {
                showToast(`访问地址: http://localhost:${result.port}`, 'success');
            }
            await refreshStatus();
        } else {
            showToast(`重启失败: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('重启失败:', error);
        showToast('重启失败', 'error');
    }
}

// 结束进程
async function killProcess(pid) {
    if (!confirm(`确定要结束进程 ${pid} 吗？`)) return;

    try {
        const response = await fetch('/api/kill-process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pid })
        });
        const result = await response.json();

        if (result.success) {
            showToast('进程已结束', 'success');
            await loadSysProcesses();
        } else {
            showToast(`结束失败: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('结束进程失败:', error);
        showToast('结束进程失败', 'error');
    }
}

// 显示项目详情
async function showProjectDetail(path) {
    try {
        const response = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        if (!response.ok) throw new Error('获取详情失败');

        const info = await response.json();

        modalTitle.textContent = info.name;
        modalBody.innerHTML = `
            <div class="detail-status ${info.running ? 'running' : 'stopped'}">
                <div class="detail-status-info">
                    <span class="status-badge ${info.running ? 'running' : 'stopped'}">
                        <span class="status-dot ${info.running ? 'animated' : ''}"></span>
                        ${info.running ? '运行中' : '已停止'}
                    </span>
                    ${info.process_info ? `
                        <span style="color: var(--text-muted); font-size: 14px;">
                            PID: ${info.process_info.pid}
                            ${info.process_info.port ? ` | 端口: ${info.process_info.port}` : ''}
                            ${info.process_info.memory_mb ? ` | 内存: ${info.process_info.memory_mb.toFixed(1)} MB` : ''}
                        </span>
                    ` : ''}
                </div>
            </div>

            <div class="detail-info">
                <div class="detail-item">
                    <div class="detail-label">类型</div>
                    <div class="detail-value"><span class="item-type ${info.type}">${info.type}</span></div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">大小</div>
                    <div class="detail-value">${formatSize(info.size)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">路径</div>
                    <div class="detail-value">${escapeHtml(info.path)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">版本</div>
                    <div class="detail-value">${info.version || '未知'}</div>
                </div>
            </div>

            ${info.description ? `
                <div class="detail-item" style="grid-column: 1 / -1;">
                    <div class="detail-label">描述</div>
                    <div class="detail-value">${escapeHtml(info.description)}</div>
                </div>
            ` : ''}

            <div class="detail-actions">
                ${info.running
                    ? `<button class="btn btn-warning" id="modal-restart">
                        <span class="icon">↻</span> 重启
                       </button>
                       <button class="btn btn-danger" id="modal-stop">
                        <span class="icon">⏹</span> 停止
                       </button>`
                    : `<button class="btn btn-success" id="modal-start">
                        <span class="icon">▶</span> 启动
                       </button>`
                }
                <button class="btn btn-primary" id="modal-open">
                    <span class="icon">📂</span> 打开文件夹
                </button>
                <button class="btn btn-primary" id="modal-copy">
                    <span class="icon">📋</span> 复制路径
                </button>
            </div>

            ${info.process_info && info.process_info.command ? `
                <div class="detail-item" style="grid-column: 1 / -1; margin-top: 15px;">
                    <div class="detail-label">启动命令</div>
                    <div class="detail-value" style="font-family: monospace; background: var(--bg); padding: 10px; border-radius: 6px;">
                        ${escapeHtml(info.process_info.command)}
                    </div>
                </div>
            ` : ''}

            ${info.tree && info.tree.length > 0 ? `
                <div class="file-tree">
                    <h3>文件结构</h3>
                    <div class="file-tree-list">
                        ${info.tree.slice(0, 50).map(item => `
                            <div class="file-tree-item ${item.is_dir ? 'dir' : 'file'}">
                                <span>${item.is_dir ? '📁' : '📄'}</span>
                                <span>${escapeHtml(item.name)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;

        // 绑定弹窗内按钮事件
        const modalPath = info.path;
        document.getElementById('modal-open')?.addEventListener('click', () => openPath(modalPath));
        document.getElementById('modal-copy')?.addEventListener('click', () => copyPath(modalPath));
        document.getElementById('modal-start')?.addEventListener('click', () => { closeModal(); startProject(modalPath); });
        document.getElementById('modal-stop')?.addEventListener('click', () => { closeModal(); stopProject(modalPath); });
        document.getElementById('modal-restart')?.addEventListener('click', () => { closeModal(); restartProject(modalPath); });

        modal.classList.add('active');
    } catch (error) {
        console.error('获取详情失败:', error);
        showToast('获取项目详情失败', 'error');
    }
}

// 打开路径
async function openPath(path) {
    try {
        await fetch('/api/open', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        closeModal();
    } catch (error) {
        console.error('打开失败:', error);
        showToast('打开文件夹失败', 'error');
    }
}

// 复制路径
function copyPath(path) {
    navigator.clipboard.writeText(path).then(() => {
        showToast('路径已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}

// 关闭弹窗
function closeModal() {
    modal.classList.remove('active');
}

// 格式化数字
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// 格式化日期
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
}

// 格式化日期时间
function formatDateTime(isoStr) {
    const date = new Date(isoStr);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) {
        return '刚刚';
    } else if (diff < 3600000) {
        return `${Math.floor(diff / 60000)} 分钟前`;
    } else if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)} 小时前`;
    } else {
        return date.toLocaleString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// ========== Dashboard 功能 ==========

async function loadDashboard() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('stat-total').textContent = stats.total_projects || 0;
        document.getElementById('stat-running').textContent = stats.running_projects || 0;
        document.getElementById('stat-stopped').textContent = stats.stopped_projects || 0;
        document.getElementById('stat-size').textContent = formatSize(stats.total_size || 0);

        // 渲染项目类型分布
        renderTypeDistribution(stats.project_types || {});

        // 加载最近访问
        loadRecentProjects();
    } catch (error) {
        console.error('加载仪表板失败:', error);
    }
}

function renderTypeDistribution(types) {
    const container = document.getElementById('type-distribution');
    const total = Object.values(types).reduce((a, b) => a + b, 0);

    if (total === 0) {
        container.innerHTML = '<div class="empty-state"><span class="icon">📊</span><p>暂无项目数据</p></div>';
        return;
    }

    const colors = {
        python: '#3b82f6',
        node: '#22c55e',
        java: '#f97316',
        go: '#06b6d4',
        rust: '#ef4444',
        git: '#f59e0b',
        generic: '#6b7280'
    };

    container.innerHTML = Object.entries(types)
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => {
            const percent = (count / total * 100).toFixed(1);
            const color = colors[type] || '#888';
            return `
                <div class="type-item">
                    <span class="type-label">${type}</span>
                    <div class="type-bar">
                        <div class="type-fill" style="width: ${percent}%; background: ${color};"></div>
                    </div>
                    <span class="type-count">${count}</span>
                </div>
            `;
        }).join('');
}

async function loadRecentProjects() {
    try {
        const response = await fetch('/api/recent');
        const recent = await response.json();

        const container = document.getElementById('recent-projects');

        if (!recent || recent.length === 0) {
            container.innerHTML = '<div class="empty-state"><span class="icon">🕐</span><p>暂无最近访问记录</p></div>';
            return;
        }

        container.innerHTML = recent.map(r => `
            <div class="item-card" data-path="${jsonEscape(r.path)}">
                <div class="item-header">
                    <span class="item-name">${escapeHtml(r.name)}</span>
                </div>
                <div class="item-path">${escapeHtml(r.path)}</div>
                <div class="item-meta">
                    <span>🕐 ${formatDateTime(r.visited_at)}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载最近访问失败:', error);
    }
}

// 批量启动所有项目
async function batchStartAll() {
    if (!confirm('确定要启动所有项目吗？')) return;

    const paths = projects.filter(p => !p.running).map(p => p.path);
    if (paths.length === 0) {
        showToast('没有需要启动的项目', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/batch/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths })
        });
        const result = await response.json();

        showToast(`已启动 ${result.started} 个项目，失败 ${result.failed} 个`, result.success ? 'success' : 'error');
        await loadAllData();
    } catch (error) {
        showToast('批量启动失败', 'error');
    }
}

// 批量停止所有项目
async function batchStopAll() {
    if (!confirm('确定要停止所有运行中的项目吗？')) return;

    const paths = projects.filter(p => p.running).map(p => p.path);
    if (paths.length === 0) {
        showToast('没有运行中的项目', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/batch/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths })
        });
        const result = await response.json();

        showToast(`已停止 ${result.stopped} 个项目，失败 ${result.failed} 个`, result.success ? 'success' : 'error');
        await loadAllData();
    } catch (error) {
        showToast('批量停止失败', 'error');
    }
}

// ========== 收藏功能 ==========

async function loadFavorites() {
    try {
        const response = await fetch('/api/favorites');
        const favorites = await response.json();

        const container = document.getElementById('favorites-list');

        if (!favorites || favorites.length === 0) {
            container.innerHTML = '<div class="empty-state"><span class="icon">⭐</span><p>暂无收藏项目<br>点击项目详情中的收藏按钮添加</p></div>';
            return;
        }

        container.innerHTML = favorites.map(f => `
            <div class="item-card" data-path="${jsonEscape(f.path)}">
                <div class="item-header">
                    <span class="item-name">${escapeHtml(f.name)}</span>
                    <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="removeFavorite('${jsonEscape(f.path)}')">取消收藏</button>
                </div>
                <div class="item-path">${escapeHtml(f.path)}</div>
                <div class="item-meta">
                    <span>⭐ 收藏于 ${formatDateTime(f.added_at)}</span>
                </div>
                <div class="item-controls">
                    <button class="btn btn-primary btn-detail" onclick="showProjectDetail('${jsonEscape(f.path)}')">
                        <span class="icon">ℹ</span> 详情
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载收藏失败:', error);
    }
}

async function addFavorite(path, name) {
    try {
        const response = await fetch('/api/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, name })
        });
        const result = await response.json();

        if (result.success) {
            showToast('已添加到收藏', 'success');
        } else {
            showToast(result.error || '添加失败', 'error');
        }
    } catch (error) {
        showToast('添加收藏失败', 'error');
    }
}

async function removeFavorite(path) {
    try {
        const response = await fetch('/api/favorites', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const result = await response.json();

        if (result.success) {
            showToast('已取消收藏', 'success');
            loadFavorites();
        }
    } catch (error) {
        showToast('取消收藏失败', 'error');
    }
}

// ========== 设置功能 ==========

async function loadSettings() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        document.getElementById('setting-root-path').value = config.root_path || '';
        document.getElementById('setting-refresh-interval').value = (config.refresh_interval || 5000) / 1000;
        document.getElementById('setting-theme').value = config.theme || 'dark';
    } catch (error) {
        console.error('加载设置失败:', error);
    }
}

async function saveRootPath() {
    const path = document.getElementById('setting-root-path').value.trim();
    if (!path) {
        showToast('请输入有效的路径', 'error');
        return;
    }

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ root_path: path })
        });
        const result = await response.json();

        if (result.success) {
            showToast('扫描目录已更新，请刷新页面', 'success');
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        showToast('保存失败', 'error');
    }
}

async function saveRefreshInterval() {
    const interval = parseInt(document.getElementById('setting-refresh-interval').value);
    if (interval < 1 || interval > 60) {
        showToast('请输入1-60之间的数值', 'error');
        return;
    }

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_interval: interval * 1000 })
        });
        const result = await response.json();

        if (result.success) {
            showToast('刷新间隔已更新', 'success');
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        showToast('保存失败', 'error');
    }
}

async function saveTheme() {
    const theme = document.getElementById('setting-theme').value;

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme })
        });
        const result = await response.json();

        if (result.success) {
            showToast('主题已更新，请刷新页面', 'success');
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        showToast('保存失败', 'error');
    }
}

async function resetConfig() {
    if (!confirm('确定要重置所有设置吗？这将清除所有配置。')) return;

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                root_path: ROOT_PATH,
                refresh_interval: 5000,
                theme: 'dark',
                favorites: [],
                recent_projects: []
            })
        });
        const result = await response.json();

        if (result.success) {
            showToast('配置已重置，请刷新页面', 'success');
        } else {
            showToast('重置失败', 'error');
        }
    } catch (error) {
        showToast('重置失败', 'error');
    }
}

// ========== 扩展事件初始化 ==========

// 在现有的 initEventDelegation 函数中添加批量操作按钮的事件
document.getElementById('batch-start-all')?.addEventListener('click', batchStartAll);
document.getElementById('batch-stop-all')?.addEventListener('click', batchStopAll);
document.getElementById('batch-refresh')?.addEventListener('click', loadAllData);

// 设置按钮事件
document.getElementById('save-root-path')?.addEventListener('click', saveRootPath);
document.getElementById('save-refresh-interval')?.addEventListener('click', saveRefreshInterval);
document.getElementById('save-theme')?.addEventListener('click', saveTheme);
document.getElementById('reset-config')?.addEventListener('click', resetConfig);

// 更新 switchTab 函数以处理新标签页
const originalSwitchTab = switchTab;
switchTab = function(tab) {
    originalSwitchTab.call(this, tab);

    // 根据标签页加载相应数据
    switch(tab) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'favorites':
            loadFavorites();
            break;
        case 'settings':
            loadSettings();
            break;
        case 'sysprocesses':
            loadSysProcesses();
            break;
    }
};

// 页面加载时默认加载仪表板
window.addEventListener('load', () => {
    // 延迟加载，确保其他初始化完成
    setTimeout(() => {
        if (currentTab === 'dashboard') {
            loadDashboard();
        }
    }, 500);
});

// ========== Services Dashboard ==========

async function loadServices() {
    const grid = document.getElementById('services-grid');
    if (!grid) return;

    try {
        const res = await fetch('/api/services');
        const services = await res.json();

        grid.innerHTML = services.map(svc => `
            <div class="service-card" data-id="${svc.id}">
                <div class="svc-header">
                    <div class="svc-icon" style="background:${svc.color}">${svc.icon}</div>
                    <div class="svc-info">
                        <h3>${svc.name}</h3>
                        <p>${svc.description}</p>
                    </div>
                </div>
                <div class="svc-status">
                    <span class="dot ${svc.running ? 'running' : 'stopped'}"></span>
                    <span>${svc.running ? '运行中' : '已停止'}</span>
                    <span style="margin-left:auto;color:var(--text-muted)">端口 ${svc.port}</span>
                </div>
                <div class="svc-actions">
                    ${svc.running ? `
                        <button class="btn btn-primary" onclick="openService('${svc.id}')">打开</button>
                        <button class="btn btn-danger" onclick="stopService('${svc.id}')">停止</button>
                    ` : `
                        <button class="btn btn-primary" onclick="startService('${svc.id}')">启动</button>
                        <button class="btn btn-secondary" onclick="openFolder('${svc.path}')">目录</button>
                    `}
                </div>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = '<div class="loading">加载服务列表失败</div>';
    }
}

async function startService(id) {
    try {
        const res = await fetch(`/api/services/${id}/start`, {method: 'POST'});
        const data = await res.json();
        if (data.success) {
            showToast('服务启动中...');
            setTimeout(loadServices, 2000);
        } else {
            showToast(data.error || '启动失败');
        }
    } catch (e) {
        showToast('启动请求失败');
    }
}

async function stopService(id) {
    try {
        const res = await fetch(`/api/services/${id}/stop`, {method: 'POST'});
        const data = await res.json();
        if (data.success) {
            showToast('服务已停止');
            setTimeout(loadServices, 1000);
        } else {
            showToast(data.error || '停止失败');
        }
    } catch (e) {
        showToast('停止请求失败');
    }
}

async function openService(id) {
    try {
        await fetch(`/api/services/${id}/open`, {method: 'POST'});
    } catch (e) {}
}

function openFolder(path) {
    fetch('/api/open', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path})
    });
}

function showToast(msg) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#6366f1;color:#fff;padding:12px 24px;border-radius:10px;font-size:14px;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '1';
    setTimeout(() => toast.style.opacity = '0', 2500);
}
