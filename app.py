from flask import Flask, request, jsonify, send_from_directory, g
import sqlite3
import random
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')

ADMINS = {'Sashabozar', 'flaros01'}

DATABASE = '/tmp/easy_gift.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT,
            stars INTEGER DEFAULT 100,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_url TEXT NOT NULL,
            stars_required INTEGER NOT NULL,
            rarity TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gift_id INTEGER NOT NULL,
            is_sold BOOLEAN DEFAULT 0,
            opened_at TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_url TEXT NOT NULL,
            stars_required INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS case_gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            gift_id INTEGER NOT NULL,
            probability REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Подарки (20 шт + Flor1s)
GIFTS_DATA = [
    {"name": "Loot Bag", "image_url": "https://nft.fragment.com/gift/lootbag-10736.medium.jpg", "stars_required": 10, "rarity": "Обычный"},
    {"name": "Toy Bear", "image_url": "https://nft.fragment.com/gift/toybear-12019.medium.jpg", "stars_required": 50, "rarity": "Обычный"},
    {"name": "Perfume Bottle", "image_url": "https://nft.fragment.com/gift/perfumebottle-1620.medium.jpg", "stars_required": 100, "rarity": "Необычный"},
    {"name": "Easter Egg", "image_url": "https://nft.fragment.com/gift/easteregg-103928.medium.jpg", "stars_required": 300, "rarity": "Необычный"},
    {"name": "Kissed Frog", "image_url": "https://nft.fragment.com/gift/kissedfrog-6355.medium.jpg", "stars_required": 500, "rarity": "Редкий"},
    {"name": "Diamond Ring", "image_url": "https://nft.fragment.com/gift/diamondring-6789.medium.jpg", "stars_required": 1000, "rarity": "Редкий"},
    {"name": "Snoop Dogg", "image_url": "https://nft.fragment.com/gift/snoopdogg-55555.medium.jpg", "stars_required": 5000, "rarity": "Эпический"},
    {"name": "Diamond Ring 2", "image_url": "https://nft.fragment.com/gift/diamondring-27070.medium.jpg", "stars_required": 10000, "rarity": "Эпический"},
    {"name": "Star Notepad", "image_url": "https://nft.fragment.com/gift/starnotepad-25037.medium.jpg", "stars_required": 20000, "rarity": "Легендарный"},
    {"name": "Heart Locket", "image_url": "https://nft.fragment.com/gift/heartlocket-269.medium.jpg", "stars_required": 50000, "rarity": "Легендарный"},
    {"name": "Heart Locket 2", "image_url": "https://nft.fragment.com/gift/heartlocket-875.medium.jpg", "stars_required": 100, "rarity": "Необычный"},
    {"name": "Vintage Cigar", "image_url": "https://nft.fragment.com/gift/vintagecigar-15623.medium.jpg", "stars_required": 300, "rarity": "Редкий"},
    {"name": "Cupid Charm", "image_url": "https://nft.fragment.com/gift/cupidcharm-5387.medium.jpg", "stars_required": 800, "rarity": "Редкий"},
    {"name": "Joyful Bundle", "image_url": "https://nft.fragment.com/gift/joyfulbundle-6940.medium.jpg", "stars_required": 2500, "rarity": "Эпический"},
    {"name": "Signet Ring", "image_url": "https://nft.fragment.com/gift/signetring-4633.medium.jpg", "stars_required": 6000, "rarity": "Легендарный"},
    {"name": "Loot Bag 2", "image_url": "https://nft.fragment.com/gift/lootbag-11217.medium.jpg", "stars_required": 15000, "rarity": "Легендарный"},
    {"name": "Ion Gem", "image_url": "https://nft.fragment.com/gift/iongem-555.medium.jpg", "stars_required": 30000, "rarity": "Мифический"},
    {"name": "Sharp Tongue", "image_url": "https://nft.fragment.com/gift/sharptongue-4346.medium.jpg", "stars_required": 70000, "rarity": "Мифический"},
    {"name": "Scared Cat", "image_url": "https://nft.fragment.com/gift/scaredcat-18166.medium.jpg", "stars_required": 120000, "rarity": "Уникальный"},
    {"name": "Precious Peach", "image_url": "https://nft.fragment.com/gift/preciouspeach-2161.medium.jpg", "stars_required": 200000, "rarity": "Уникальный"},
    {"name": "Flor1s", "image_url": "https://avatars.mds.yandex.net/i?id=4f57e6c6c46272adfbc815617d088115ce35afb3-3900893-images-thumbs&n=13", "stars_required": 1000000000, "rarity": "Божественный"},
]

# Кейсы
CASES_DATA = [
    {"name": "smert1x", "image_url": "https://i.pinimg.com/videos/thumbnails/originals/d3/58/17/d358171152ca94f3b94d45f275fe685f.0000000.jpg", "stars_required": 50},
    {"name": "Саша барзеников", "image_url": "https://i.ytimg.com/vi/9UnhcIpY5xw/maxresdefault.jpg", "stars_required": 150},
    {"name": "FISCH", "image_url": "https://abancommercials.com/uploadStream/14056.jpg", "stars_required": 1000},
    {"name": "jailbrikor", "image_url": "https://sun1-88.userapi.com/s/v1/ig2/qMd3SNuZgqB2t17Af0GeF1wsH_MgGsPuFLv5qtJIt5TA7RgGEffRu1kHBV4ptB7_MLSroxdWDBUtewtd_XQ9Xjoy.jpg?size=1800x1800&quality=95&crop=0,0,1800,1800&ava=1", "stars_required": 50000},
]

# Распределение подарков по кейсам
CASE_GIFTS_MAP = {
    1: [1, 2, 3, 4, 5, 6, 11, 12],          # smert1x: 10–1000
    2: [3, 4, 5, 6, 7, 8, 11, 12, 13, 14],  # Саша: 100–20000
    3: [5, 6, 7, 8, 9, 10, 13, 14, 15, 16], # FISCH: 100–100000
    4: [7, 8, 9, 10, 15, 16, 17, 18, 19, 20] # jailbrikor: 10000–500000
}

def assign_probabilities(gift_ids):
    gifts = [g for g in GIFTS_DATA if g['id'] in gift_ids]
    total = sum(1 / (g['stars_required'] or 1) for g in gifts)
    return [(g['id'], (1 / (g['stars_required'] or 1)) / total) for g in gifts]

def populate_db():
    conn = get_db_connection()
    # Подарки
    for i, g in enumerate(GIFTS_DATA, 1):
        g['id'] = i
        conn.execute('INSERT OR IGNORE INTO gifts (id, name, image_url, stars_required, rarity) VALUES (?, ?, ?, ?, ?)',
                     (i, g['name'], g['image_url'], g['stars_required'], g['rarity']))
    # Кейсы
    for i, c in enumerate(CASES_DATA, 1):
        conn.execute('INSERT OR IGNORE INTO cases (id, name, image_url, stars_required) VALUES (?, ?, ?, ?)',
                     (i, c['name'], c['image_url'], c['stars_required']))
    # Награды
    for case_id, gift_ids in CASE_GIFTS_MAP.items():
        probs = assign_probabilities(gift_ids)
        for gift_id, prob in probs:
            conn.execute('INSERT OR IGNORE INTO case_gifts (case_id, gift_id, probability) VALUES (?, ?, ?)',
                         (case_id, gift_id, prob))
    conn.commit()
    conn.close()

@app.before_request
def setup_once():
    if not hasattr(g, 'initialized'):
        init_db()
        populate_db()
        g.initialized = True

# --- API ---
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/user', methods=['POST'])
def get_user():
    data = request.json
    telegram_id = data.get('telegram_id')
    username = data.get('username', 'unknown')
    if not telegram_id:
        return jsonify({'error': 'telegram_id required'}), 400
    is_admin = 1 if username in ADMINS else 0
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (telegram_id, username, is_admin) VALUES (?, ?, ?)',
                     (telegram_id, username, is_admin))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    else:
        conn.execute('UPDATE users SET username = ?, is_admin = ? WHERE telegram_id = ?',
                     (username, is_admin, telegram_id))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    conn.close()
    return jsonify({
        'id': user['id'],
        'telegram_id': user['telegram_id'],
        'username': user['username'],
        'stars': user['stars'],
        'is_admin': bool(user['is_admin'])
    })

@app.route('/api/cases', methods=['GET'])
def get_cases():
    conn = get_db_connection()
    cases = conn.execute('SELECT * FROM cases').fetchall()
    conn.close()
    return jsonify([dict(c) for c in cases])

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    conn = get_db_connection()
    gifts = conn.execute('''
        SELECT g.*, ug.id as user_gift_id, ug.is_sold
        FROM user_gifts ug
        JOIN gifts g ON ug.gift_id = g.id
        WHERE ug.user_id = ? AND ug.is_sold = 0
    ''', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(g) for g in gifts])

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db_connection()
    users = conn.execute('''
        SELECT username, stars
        FROM users
        WHERE username IS NOT NULL
        ORDER BY stars DESC
        LIMIT 10
    ''').fetchall()
    conn.close()
    return jsonify([{'username': u['username'] or 'Игрок', 'stars': u['stars']} for u in users])

@app.route('/api/open_case', methods=['POST'])
def open_case():
    data = request.json
    user_id = data.get('user_id')
    case_id = data.get('case_id')
    if not user_id or not case_id:
        return jsonify({'error': 'user_id and case_id required'}), 400
    conn = get_db_connection()
    user = conn.execute('SELECT stars FROM users WHERE id = ?', (user_id,)).fetchone()
    case = conn.execute('SELECT stars_required FROM cases WHERE id = ?', (case_id,)).fetchone()
    if not user or not case:
        return jsonify({'error': 'User or case not found'}), 404
    if user['stars'] < case['stars_required']:
        return jsonify({'error': 'Not enough stars'}), 400
    rewards = conn.execute('SELECT gift_id, probability FROM case_gifts WHERE case_id = ?', (case_id,)).fetchall()
    rand = random.random()
    cum = 0.0
    selected = rewards[0]['gift_id']
    for r in rewards:
        cum += r['probability']
        if rand <= cum:
            selected = r['gift_id']
            break
    conn.execute('UPDATE users SET stars = stars - ? WHERE id = ?', (case['stars_required'], user_id))
    conn.execute('INSERT INTO user_gifts (user_id, gift_id, opened_at) VALUES (?, ?, ?)',
                 (user_id, selected, datetime.now()))
    gift = conn.execute('SELECT * FROM gifts WHERE id = ?', (selected,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'gift': dict(gift)})

@app.route('/api/sell_gift', methods=['POST'])
def sell_gift():
    data = request.json
    user_gift_id = data.get('user_gift_id')
    if not user_gift_id:
        return jsonify({'error': 'user_gift_id required'}), 400
    conn = get_db_connection()
    gift = conn.execute('''
        SELECT g.stars_required, ug.user_id
        FROM user_gifts ug
        JOIN gifts g ON ug.gift_id = g.id
        WHERE ug.id = ? AND ug.is_sold = 0
    ''', (user_gift_id,)).fetchone()
    if not gift:
        return jsonify({'error': 'Gift not found or already sold'}), 404
    refund = int(gift['stars_required'] * 0.7)  # 70% возврат
    conn.execute('UPDATE user_gifts SET is_sold = 1 WHERE id = ?', (user_gift_id,))
    conn.execute('UPDATE users SET stars = stars + ? WHERE id = ?', (refund, gift['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'refund': refund})

@app.route('/api/upgrade', methods=['POST'])
def upgrade_gift():
    data = request.json
    user_id = data.get('user_id')
    gift_ids = data.get('gift_ids', [])
    if len(gift_ids) != 5:
        return jsonify({'error': 'Need exactly 5 gifts'}), 400
    conn = get_db_connection()
    # Проверяем, что все подарки принадлежат пользователю, не проданы и одинаковые
    placeholders = ','.join('?' * len(gift_ids))
    rows = conn.execute(f'''
        SELECT id, gift_id FROM user_gifts
        WHERE id IN ({placeholders}) AND user_id = ? AND is_sold = 0
    ''', (*gift_ids, user_id)).fetchall()
    if len(rows) != 5:
        return jsonify({'error': 'Invalid gifts'}), 400
    gift_ids_set = set(r['gift_id'] for r in rows)
    if len(gift_ids_set) != 1:
        return jsonify({'error': 'All gifts must be the same'}), 400
    # Удаляем старые подарки
    for r in rows:
        conn.execute('UPDATE user_gifts SET is_sold = 1 WHERE id = ?', (r['id'],))
    # Выдаём Flor1s (id=21)
    conn.execute('INSERT INTO user_gifts (user_id, gift_id, opened_at) VALUES (?, ?, ?)',
                 (user_id, 21, datetime.now()))
    flor = conn.execute('SELECT * FROM gifts WHERE id = 21').fetchone()
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'gift': dict(flor)})

# Админка
@app.route('/api/admin/give-stars', methods=['POST'])
def give_stars():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount', 0)
    if not user_id or amount <= 0:
        return jsonify({'error': 'Invalid input'}), 400
    conn = get_db_connection()
    admin = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    if not admin or not admin['is_admin']:
        return jsonify({'error': 'Access denied'}), 403
    conn.execute('UPDATE users SET stars = stars + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/give-all-gifts', methods=['POST'])
def give_all_gifts():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    conn = get_db_connection()
    admin = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    if not admin or not admin['is_admin']:
        return jsonify({'error': 'Access denied'}), 403
    gifts = conn.execute('SELECT id FROM gifts WHERE id != 21').fetchall()  # без Flor1s
    for g in gifts:
        conn.execute('INSERT INTO user_gifts (user_id, gift_id, opened_at) VALUES (?, ?, ?)',
                     (user_id, g['id'], datetime.now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'count': len(gifts)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
