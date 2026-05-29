"""AI Game Arcade - AI驱动的游戏创建与游玩平台"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from db import init_db, list_games, get_game, create_game, update_game, delete_game, increment_plays, toggle_like, get_user, update_user, get_user_games, get_user_stats, check_user_liked, get_or_create_user
from ai_generator import generate_game
from config import PORT, DEBUG, DEFAULT_USERNAME, CATEGORIES

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

CURRENT_USER_ID = 1


@app.route('/')
def index():
    return render_template('index.html')


# ===== Game APIs =====

@app.route('/api/games', methods=['GET'])
def api_list_games():
    sort = request.args.get('sort', 'trending')
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    games = list_games(sort=sort, category=category, search=search, limit=limit, offset=offset)

    game_ids = [g['id'] for g in games]
    liked_set = check_user_liked(CURRENT_USER_ID, game_ids)
    for g in games:
        g['liked'] = g['id'] in liked_set

    return jsonify({'games': games, 'total': len(games)})


@app.route('/api/games/<int:game_id>', methods=['GET'])
def api_get_game(game_id):
    game = get_game(game_id)
    if not game:
        return jsonify({'error': '游戏不存在'}), 404
    game['liked'] = game_id in check_user_liked(CURRENT_USER_ID, [game_id])
    return jsonify(game)


@app.route('/api/games/<int:game_id>/code', methods=['GET'])
def api_get_game_code(game_id):
    game = get_game(game_id)
    if not game:
        return jsonify({'error': '游戏不存在'}), 404
    return jsonify({'code': game['game_code']})


@app.route('/api/games', methods=['POST'])
def api_create_game():
    data = request.get_json()
    title = data.get('title', '').strip()
    prompt = data.get('prompt', '').strip()
    category = data.get('category', '休闲')
    game_code = data.get('game_code', '')

    if not prompt and not game_code:
        return jsonify({'error': '请提供游戏描述或游戏代码'}), 400

    if not game_code:
        game_code = generate_game(prompt, category)

    if not title:
        title = prompt[:20] if prompt else '未命名游戏'

    game_id = create_game(
        title=title,
        description=prompt[:100] if prompt else '',
        prompt=prompt,
        game_code=game_code,
        category=category,
        creator_id=CURRENT_USER_ID
    )

    return jsonify({'id': game_id, 'message': '游戏创建成功'})


@app.route('/api/games/<int:game_id>', methods=['PUT'])
def api_update_game(game_id):
    data = request.get_json()
    game = get_game(game_id)
    if not game:
        return jsonify({'error': '游戏不存在'}), 404
    if game['creator_id'] != CURRENT_USER_ID:
        return jsonify({'error': '无权限编辑'}), 403

    update_game(game_id, **{k: data[k] for k in ('title', 'description', 'game_code', 'category', 'is_public') if k in data})
    return jsonify({'message': '更新成功'})


@app.route('/api/games/<int:game_id>', methods=['DELETE'])
def api_delete_game(game_id):
    game = get_game(game_id)
    if not game:
        return jsonify({'error': '游戏不存在'}), 404
    if game['creator_id'] != CURRENT_USER_ID:
        return jsonify({'error': '无权限删除'}), 403

    delete_game(game_id)
    return jsonify({'message': '删除成功'})


@app.route('/api/games/<int:game_id>/play', methods=['POST'])
def api_play_game(game_id):
    increment_plays(game_id)
    return jsonify({'message': 'ok'})


@app.route('/api/games/<int:game_id>/like', methods=['POST'])
def api_like_game(game_id):
    liked = toggle_like(CURRENT_USER_ID, game_id)
    return jsonify({'liked': liked})


# ===== Generate API =====

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    category = data.get('category', '')

    if not prompt:
        return jsonify({'error': '请输入游戏描述'}), 400

    game_code = generate_game(prompt, category)
    return jsonify({'game_code': game_code})


# ===== User APIs =====

@app.route('/api/user', methods=['GET'])
def api_get_user():
    user = get_user(CURRENT_USER_ID)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    stats = get_user_stats(CURRENT_USER_ID)
    return jsonify({**user, 'stats': stats})


@app.route('/api/user', methods=['PUT'])
def api_update_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    update_user(CURRENT_USER_ID, username)
    return jsonify({'message': '更新成功'})


@app.route('/api/user/games', methods=['GET'])
def api_user_games():
    games = get_user_games(CURRENT_USER_ID)
    return jsonify({'games': games})


@app.route('/api/categories', methods=['GET'])
def api_categories():
    return jsonify({'categories': CATEGORIES})


if __name__ == '__main__':
    init_db()
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
