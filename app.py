from flask import Flask, request, jsonify, send_from_directory, g
import sqlite3
import random
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')

# Админы (без @)
ADMINS = {'Sashabozar', 'Flaros'}

# Используем /tmp — единственное место для записи на Render
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
            opened_at TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_url TEXT NOT NULL,
            stars_required INTEGER NOT NULL,
            rarity TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS case_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            gift_id INTEGER NOT NULL,
            probability REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Данные
GIFTS_DATA = [
    {"name": "CryptoPunk #7804", "image_url": "https://placehold.co/200/ff0000/white?text=CryptoPunk", "stars_required": 20000, "rarity": "Легендарный"},
    {"name": "Bored Ape #8817", "image_url": "https://placehold.co/200/00ff00/white?text=Bored+Ape", "stars_required": 15000, "rarity": "Эпический"},
    {"name": "Azuki #9605", "image_url": "https://placehold.co/200/0000ff/white?text=Azuki", "stars_required": 10000, "rarity": "Редкий"},
]

CASES_DATA = [
    {"name": "Scary Case", "image_url": "https://placehold.co/200/ff5555/white?text=Scary", "stars_required": 10, "rarity": "Лимит"},
    {"name": "Devil Case", "image_url": "https://placehold.co/200/8b0000/white?text=Devil", "stars_required": 99, "rarity": "Лимит"},
]

REWARDS_DATA = [
    {"case_id": 1, "gift_id": 1, "probability": 0.001},
    {"case_id": 1, "gift_id": 2, "probability": 0.01},
    {"case_id": 1, "gift_id": 3, "probability": 0.989},
]

def populate_db():
    conn = get_db_connection()
    for g in GIFTS_DATA:
        conn.execute('INSERT OR IGNORE INTO gifts (name, image_url, stars_required, rarity) VALUES (?, ?, ?, ?)',
                     (g['name'], g['image_url'], g['stars_required'], g['rarity']))
    for c in CASES_DATA:
        conn.execute('INSERT OR IGNORE INTO cases (name, image_url, stars_required, rarity) VALUES (?, ?, ?, ?)',
                     (c['name'], c['image_url'], c['stars_required'], c['rarity']))
    for r in REWARDS_DATA:
        conn.execute('INSERT OR IGNORE INTO case_rewards (case_id, gift_id, probability) VALUES (?, ?, ?)',
                     (r['case_id'], r['gift_id'], r['probability']))
    conn.commit()
    conn.close()

# Инициализация при первом запросе (Flask 2.3+ совместимо)
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

    rewards = conn.execute('SELECT gift_id, probability FROM case_rewards WHERE case_id = ?', (case_id,)).fetchall()
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
    conn.commit()
    conn.close()
    # Возвращаем данные подарка для отображения
    return jsonify({
        'success': True,
        'gift': {
            'id': selected,
            'name': f'NFT #{selected}',
            'image_url': f'https://placehold.co/200?text=NFT+{selected}',
            'stars_required': 10000
        }
    })

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
    gifts = conn.execute('SELECT id FROM gifts').fetchall()
    for g in gifts:
        conn.execute('INSERT INTO user_gifts (user_id, gift_id, opened_at) VALUES (?, ?, ?)',
                     (user_id, g['id'], datetime.now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'count': len(gifts)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
