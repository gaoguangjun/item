// AI Game Arcade - Frontend

// ===== State =====
let currentSort = 'trending';
let currentCategory = '';
let currentUser = null;
let generatedCode = '';
let editingGameId = null;
let currentModalGame = null;

// ===== Init =====
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCategories();
    initGallery();
    initCreate();
    initProfile();
    initPlayerModal();
    initEditModal();
    loadUser();
    loadGames();
});

// ===== Tabs =====
function initTabs() {
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.getElementById('panel-' + btn.dataset.tab).classList.add('active');

            if (btn.dataset.tab === 'mygames') loadMyGames();
            if (btn.dataset.tab === 'profile') loadProfile();
        });
    });
}

// ===== Categories =====
function initCategories() {
    fetch('/api/categories').then(r => r.json()).then(data => {
        const cats = data.categories;
        ['game-category', 'edit-category', 'category-filter'].forEach(id => {
            const sel = document.getElementById(id);
            if (!sel) return;
            if (id === 'category-filter') {
                sel.innerHTML = '<option value="">全部分类</option>';
                cats.forEach(c => sel.innerHTML += `<option value="${c}">${c}</option>`);
            } else {
                sel.innerHTML = '';
                cats.forEach(c => sel.innerHTML += `<option value="${c}">${c}</option>`);
            }
        });
    });
}

// ===== Gallery =====
function initGallery() {
    document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSort = btn.dataset.sort;
            loadGames();
        });
    });
    document.getElementById('category-filter').addEventListener('change', e => {
        currentCategory = e.target.value;
        loadGames();
    });
    let searchTimer;
    document.getElementById('search-input').addEventListener('input', e => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => loadGames(), 300);
    });
}

async function loadGames() {
    const search = document.getElementById('search-input').value;
    const params = new URLSearchParams({sort: currentSort, category: currentCategory, search});
    const res = await fetch('/api/games?' + params);
    const data = await res.json();
    renderGameGrid(data.games, 'game-grid', 'gallery-empty', false);
}

function renderGameGrid(games, gridId, emptyId, showActions) {
    const grid = document.getElementById(gridId);
    const empty = document.getElementById(emptyId);
    if (!games.length) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';
    grid.innerHTML = games.map(g => `
        <div class="game-card" data-id="${g.id}">
            <div class="card-thumb" style="background:${gradientFromId(g.id)}">${g.title[0]}</div>
            <div class="card-body">
                <div class="card-title" title="${esc(g.title)}">${esc(g.title)}</div>
                <div class="card-meta">
                    <div class="card-meta-left">
                        <span class="card-stat">&#9654; ${formatNum(g.plays)}</span>
                        <span class="card-stat">&#9829; ${formatNum(g.likes)}</span>
                    </div>
                    <span class="card-creator">${esc(g.creator_name||'')}</span>
                </div>
                ${showActions ? `
                <div class="card-actions">
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();openEdit(${g.id})">编辑</button>
                    <button class="btn btn-danger btn-sm" onclick="event.stopPropagation();deleteGame(${g.id})">删除</button>
                </div>` : ''}
            </div>
        </div>
    `).join('');

    grid.querySelectorAll('.game-card').forEach(card => {
        card.addEventListener('click', () => openPlayer(parseInt(card.dataset.id)));
    });
}

// ===== Game Player Modal =====
function initPlayerModal() {
    document.getElementById('modal-close').addEventListener('click', closePlayer);
    document.getElementById('player-modal').addEventListener('click', e => {
        if (e.target.id === 'player-modal') closePlayer();
    });
    document.getElementById('modal-like-btn').addEventListener('click', async () => {
        if (!currentModalGame) return;
        const res = await fetch(`/api/games/${currentModalGame.id}/like`, {method: 'POST'});
        const data = await res.json();
        document.getElementById('modal-like-btn').textContent = data.liked ? '已赞' : '点赞';
        document.getElementById('modal-like-btn').style.background = data.liked ? 'var(--success)' : '';
        loadGames();
    });
    document.getElementById('modal-share-btn').addEventListener('click', () => {
        const url = window.location.origin + '/play/' + (currentModalGame ? currentModalGame.id : '');
        navigator.clipboard.writeText(url).then(() => showToast('链接已复制'));
    });
}

async function openPlayer(gameId) {
    const res = await fetch(`/api/games/${gameId}`);
    const game = await res.json();
    if (!game.id) return;
    currentModalGame = game;

    document.getElementById('modal-game-title').textContent = game.title;
    document.getElementById('modal-game-creator').textContent = 'by ' + (game.creator_name || '');
    document.getElementById('modal-plays').textContent = game.plays + ' 次游玩';
    document.getElementById('modal-likes').textContent = game.likes + ' 赞';
    document.getElementById('modal-like-btn').textContent = game.liked ? '已赞' : '点赞';
    document.getElementById('modal-like-btn').style.background = game.liked ? 'var(--success)' : '';

    const iframe = document.getElementById('game-iframe');
    const blob = new Blob([game.game_code], {type: 'text/html'});
    iframe.src = URL.createObjectURL(blob);

    document.getElementById('player-modal').style.display = 'flex';
    fetch(`/api/games/${gameId}/play`, {method: 'POST'});
}

function closePlayer() {
    document.getElementById('player-modal').style.display = 'none';
    document.getElementById('game-iframe').src = '';
    currentModalGame = null;
}

// ===== Create Game =====
function initCreate() {
    document.getElementById('generate-btn').addEventListener('click', generateGame);
    document.getElementById('regenerate-btn').addEventListener('click', generateGame);
    document.getElementById('save-game-btn').addEventListener('click', saveGame);
}

async function generateGame() {
    const prompt = document.getElementById('game-prompt').value.trim();
    if (!prompt) { showToast('请输入游戏描述'); return; }

    const category = document.getElementById('game-category').value;
    document.getElementById('generate-loading').style.display = 'block';
    document.getElementById('preview-card').style.display = 'none';

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt, category})
        });
        const data = await res.json();
        generatedCode = data.game_code;

        const iframe = document.getElementById('preview-iframe');
        const blob = new Blob([generatedCode], {type: 'text/html'});
        iframe.src = URL.createObjectURL(blob);

        document.getElementById('preview-card').style.display = 'block';
    } catch (e) {
        showToast('生成失败，请重试');
    }
    document.getElementById('generate-loading').style.display = 'none';
}

async function saveGame() {
    const title = document.getElementById('game-title').value.trim();
    const prompt = document.getElementById('game-prompt').value.trim();
    const category = document.getElementById('game-category').value;

    const res = await fetch('/api/games', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, prompt, category, game_code: generatedCode})
    });
    const data = await res.json();
    if (data.id) {
        showToast('游戏保存成功！');
        document.getElementById('preview-card').style.display = 'none';
        document.getElementById('game-prompt').value = '';
        document.getElementById('game-title').value = '';
        generatedCode = '';
        loadGames();
    } else {
        showToast(data.error || '保存失败');
    }
}

// ===== My Games =====
async function loadMyGames() {
    const res = await fetch('/api/user/games');
    const data = await res.json();
    renderGameGrid(data.games, 'mygames-grid', 'mygames-empty', true);
}

async function deleteGame(id) {
    if (!confirm('确定删除这个游戏？')) return;
    await fetch(`/api/games/${id}`, {method: 'DELETE'});
    showToast('已删除');
    loadMyGames();
    loadGames();
}

// ===== Edit Modal =====
function initEditModal() {
    document.getElementById('edit-modal-close').addEventListener('click', () => {
        document.getElementById('edit-modal').style.display = 'none';
    });
    document.getElementById('edit-modal').addEventListener('click', e => {
        if (e.target.id === 'edit-modal') document.getElementById('edit-modal').style.display = 'none';
    });
    document.getElementById('edit-save-btn').addEventListener('click', async () => {
        if (!editingGameId) return;
        const res = await fetch(`/api/games/${editingGameId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                title: document.getElementById('edit-title').value,
                description: document.getElementById('edit-desc').value,
                category: document.getElementById('edit-category').value,
                is_public: document.getElementById('edit-public').checked ? 1 : 0
            })
        });
        const data = await res.json();
        showToast('已更新');
        document.getElementById('edit-modal').style.display = 'none';
        loadMyGames();
        loadGames();
    });
}

async function openEdit(gameId) {
    const res = await fetch(`/api/games/${gameId}`);
    const game = await res.json();
    editingGameId = gameId;
    document.getElementById('edit-title').value = game.title;
    document.getElementById('edit-desc').value = game.description || '';
    document.getElementById('edit-category').value = game.category;
    document.getElementById('edit-public').checked = game.is_public;
    document.getElementById('edit-modal').style.display = 'flex';
}

// ===== Profile =====
function initProfile() {
    document.getElementById('edit-name-btn').addEventListener('click', () => {
        document.getElementById('edit-name-row').style.display = 'flex';
        document.getElementById('edit-name-btn').style.display = 'none';
        document.getElementById('edit-name-input').value = currentUser.username;
    });
    document.getElementById('cancel-name-btn').addEventListener('click', () => {
        document.getElementById('edit-name-row').style.display = 'none';
        document.getElementById('edit-name-btn').style.display = 'inline-block';
    });
    document.getElementById('save-name-btn').addEventListener('click', async () => {
        const name = document.getElementById('edit-name-input').value.trim();
        if (!name) return;
        await fetch('/api/user', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: name})
        });
        currentUser.username = name;
        document.getElementById('edit-name-row').style.display = 'none';
        document.getElementById('edit-name-btn').style.display = 'inline-block';
        loadProfile();
        showToast('已更新');
    });
}

async function loadUser() {
    const res = await fetch('/api/user');
    currentUser = await res.json();
    loadProfile();
}

function loadProfile() {
    if (!currentUser) return;
    document.getElementById('profile-name').textContent = currentUser.username;
    document.getElementById('profile-avatar').textContent = currentUser.username[0];
    const s = currentUser.stats || {};
    document.getElementById('stat-games').textContent = s.total_games || 0;
    document.getElementById('stat-likes').textContent = s.total_likes || 0;
    document.getElementById('stat-plays').textContent = s.total_plays || 0;
}

// ===== Utils =====
function gradientFromId(id) {
    const hues = [(id*47)%360, (id*83+120)%360];
    return `linear-gradient(135deg, hsl(${hues[0]},60%,35%), hsl(${hues[1]},60%,30%))`;
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}

function formatNum(n) {
    if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n/1000).toFixed(1) + 'K';
    return n;
}

function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}
