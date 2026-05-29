"""SQLite database helper for AI Game Arcade."""

import sqlite3
import os
from config import DB_PATH, DEFAULT_USERNAME


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        avatar_color TEXT DEFAULT '#6366f1',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        prompt TEXT DEFAULT '',
        game_code TEXT NOT NULL,
        category TEXT DEFAULT '休闲',
        creator_id INTEGER NOT NULL DEFAULT 1,
        plays INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        is_public INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, game_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (game_id) REFERENCES games(id)
    )''')

    # Seed default user
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO users (username) VALUES (?)', (DEFAULT_USERNAME,))

    # Seed demo games if empty
    c.execute('SELECT COUNT(*) FROM games')
    if c.fetchone()[0] == 0:
        _seed_demo_games(c)

    conn.commit()
    conn.close()


def _seed_demo_games(c):
    """Insert 4 built-in demo games."""
    from demo_games import DEMO_GAMES
    for game in DEMO_GAMES:
        c.execute(
            'INSERT INTO games (title, description, prompt, game_code, category, plays, likes) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (game['title'], game['description'], game['prompt'], game['code'], game['category'], game.get('plays', 0), game.get('likes', 0))
        )


def get_or_create_user(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    if user:
        conn.close()
        return dict(user)
    c.execute('INSERT INTO users (username) VALUES (?)', (username,))
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return {'id': user_id, 'username': username, 'avatar_color': '#6366f1'}


def get_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user(user_id, username):
    conn = get_conn()
    conn.execute('UPDATE users SET username = ? WHERE id = ?', (username, user_id))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as total_games, COALESCE(SUM(plays), 0) as total_plays, COALESCE(SUM(likes), 0) as total_likes FROM games WHERE creator_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {'total_games': 0, 'total_plays': 0, 'total_likes': 0}


def create_game(title, description, prompt, game_code, category, creator_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO games (title, description, prompt, game_code, category, creator_id) VALUES (?, ?, ?, ?, ?, ?)',
        (title, description, prompt, game_code, category, creator_id)
    )
    conn.commit()
    game_id = c.lastrowid
    conn.close()
    return game_id


def get_game(game_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT g.*, u.username as creator_name
        FROM games g JOIN users u ON g.creator_id = u.id
        WHERE g.id = ?
    ''', (game_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_game(game_id, **kwargs):
    conn = get_conn()
    sets = []
    vals = []
    for k in ('title', 'description', 'game_code', 'category', 'is_public'):
        if k in kwargs:
            sets.append(f'{k} = ?')
            vals.append(kwargs[k])
    if sets:
        vals.append(game_id)
        conn.execute(f"UPDATE games SET {', '.join(sets)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", vals)
        conn.commit()
    conn.close()


def delete_game(game_id):
    conn = get_conn()
    conn.execute('DELETE FROM likes WHERE game_id = ?', (game_id,))
    conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
    conn.commit()
    conn.close()


def list_games(sort='trending', category='', search='', limit=20, offset=0):
    conn = get_conn()
    c = conn.cursor()

    where = 'WHERE g.is_public = 1'
    params = []

    if category:
        where += ' AND g.category = ?'
        params.append(category)
    if search:
        where += ' AND (g.title LIKE ? OR g.description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    if sort == 'popular':
        order = 'ORDER BY g.likes DESC, g.plays DESC'
    elif sort == 'newest':
        order = 'ORDER BY g.created_at DESC'
    else:  # trending
        order = 'ORDER BY (g.plays * 0.3 + g.likes * 0.7) DESC, g.created_at DESC'

    c.execute(f'''
        SELECT g.id, g.title, g.description, g.category, g.creator_id,
               g.plays, g.likes, g.created_at, u.username as creator_name
        FROM games g JOIN users u ON g.creator_id = u.id
        {where} {order}
        LIMIT ? OFFSET ?
    ''', params + [limit, offset])

    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def increment_plays(game_id):
    conn = get_conn()
    conn.execute('UPDATE games SET plays = plays + 1 WHERE id = ?', (game_id,))
    conn.commit()
    conn.close()


def toggle_like(user_id, game_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id FROM likes WHERE user_id = ? AND game_id = ?', (user_id, game_id))
    existing = c.fetchone()
    if existing:
        conn.execute('DELETE FROM likes WHERE user_id = ? AND game_id = ?', (user_id, game_id))
        conn.execute('UPDATE games SET likes = likes - 1 WHERE id = ?', (game_id,))
        conn.commit()
        conn.close()
        return False
    else:
        conn.execute('INSERT INTO likes (user_id, game_id) VALUES (?, ?)', (user_id, game_id))
        conn.execute('UPDATE games SET likes = likes + 1 WHERE id = ?', (game_id,))
        conn.commit()
        conn.close()
        return True


def get_user_games(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT g.*, u.username as creator_name
        FROM games g JOIN users u ON g.creator_id = u.id
        WHERE g.creator_id = ?
        ORDER BY g.created_at DESC
    ''', (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def check_user_liked(user_id, game_ids):
    if not game_ids:
        return set()
    conn = get_conn()
    c = conn.cursor()
    placeholders = ','.join('?' * len(game_ids))
    c.execute(f'SELECT game_id FROM likes WHERE user_id = ? AND game_id IN ({placeholders})', [user_id] + game_ids)
    liked = {r['game_id'] for r in c.fetchall()}
    conn.close()
    return liked
