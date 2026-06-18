import sqlite3
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'data' / 'items.db'
ITEMS_JSON_PATH = BASE_DIR / 'data' / 'items.json'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 新结构：items 表使用 (id, region) 复合主键
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id TEXT,
            name TEXT,
            condition TEXT,
            url TEXT,
            enabled INTEGER,
            remark TEXT,
            target_value TEXT,
            region TEXT DEFAULT "global",
            PRIMARY KEY (id, region)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT,
            p1 TEXT,
            p2 TEXT,
            p3 TEXT,
            update_time DATETIME,
            region TEXT DEFAULT "global"
        )
    ''')

    try:
        cursor.execute('ALTER TABLE prices ADD COLUMN region TEXT DEFAULT "global"')
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def load_items_from_json():
    if not ITEMS_JSON_PATH.exists():
        return []
    with open(ITEMS_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def sync_items_to_db():
    items = load_items_from_json()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 先清空旧数据（避免残留旧结构）
    cursor.execute('DELETE FROM items')

    # 每条记录对应一行数据，自带 region
    for item in items:
        region = item.get('region', 'global')
        cursor.execute('''
            INSERT OR REPLACE INTO items (id, name, condition, url, enabled, remark, target_value, region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['id'],
            item.get('name', ''),
            item.get('condition', ''),
            item.get('url', ''),
            1 if item.get('enabled', True) else 0,
            item.get('remark', ''),
            item.get('target_value', ''),
            region
        ))

    conn.commit()
    conn.close()
    return items


def get_all_items(region=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if region:
        cursor.execute('SELECT * FROM items WHERE region = ?', (region,))
    else:
        cursor.execute('SELECT * FROM items')
    rows = cursor.fetchall()

    items = []
    for row in rows:
        items.append({
            'id': row['id'],
            'name': row['name'],
            'condition': row['condition'],
            'url': row['url'],
            'enabled': bool(row['enabled']),
            'remark': row['remark'],
            'target_value': row['target_value'] if row['target_value'] else '',
            'region': row['region'] if row['region'] else 'global'
        })

    conn.close()
    return items


def save_price(item_id, p1, p2, p3, condition=None, region='global'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if condition is not None and condition.strip():
        cursor.execute('''
            UPDATE items
            SET condition = ?
            WHERE id = ? AND region = ?
        ''', (condition, item_id, region))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO prices (item_id, p1, p2, p3, update_time, region)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (item_id, p1, p2, p3, now, region))

    conn.commit()
    conn.close()


def get_latest_prices(region=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if region:
        cursor.execute('''
            SELECT i.*, p.p1, p.p2, p.p3, p.update_time
            FROM items i
            LEFT JOIN (
                SELECT item_id, region, MAX(id) as max_id
                FROM prices
                WHERE region = ?
                GROUP BY item_id, region
            ) latest ON i.id = latest.item_id AND i.region = latest.region
            LEFT JOIN prices p ON latest.max_id = p.id
            WHERE i.region = ?
        ''', (region, region))
    else:
        cursor.execute('''
            SELECT i.*, p.p1, p.p2, p.p3, p.update_time
            FROM items i
            LEFT JOIN (
                SELECT item_id, region, MAX(id) as max_id
                FROM prices
                GROUP BY item_id, region
            ) latest ON i.id = latest.item_id AND i.region = latest.region
            LEFT JOIN prices p ON latest.max_id = p.id
        ''')

    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'],
            'name': row['name'],
            'condition': row['condition'],
            'url': row['url'],
            'enabled': bool(row['enabled']),
            'remark': row['remark'],
            'target_value': row['target_value'] if row['target_value'] else '',
            'region': row['region'] if row['region'] else 'global',
            'p1': row['p1'],
            'p2': row['p2'],
            'p3': row['p3'],
            'update_time': row['update_time']
        })

    conn.close()
    return result


def search_items(keyword, region=None):
    items = get_latest_prices(region)
    if not keyword:
        return items
    keyword = keyword.lower()
    return [item for item in items if keyword in item['name'].lower()]


def get_price_history(item_id, limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p1, p2, p3, update_time
        FROM prices
        WHERE item_id = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (item_id, limit))

    rows = cursor.fetchall()

    history = []
    for row in rows:
        history.append({
            'p1': row['p1'],
            'p2': row['p2'],
            'p3': row['p3'],
            'update_time': row['update_time']
        })

    conn.close()
    return history


def update_target_value(item_id, target_value, region='global'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE items
        SET target_value = ?
        WHERE id = ? AND region = ?
    ''', (target_value, item_id, region))

    conn.commit()
    conn.close()

    # 同时更新 items.json 文件
    items = load_items_from_json()
    for item in items:
        if item['id'] == item_id:
            item['target_value'] = target_value
            break

    with open(ITEMS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_item(item_data):
    items = load_items_from_json()

    # 生成新的 ID
    if items:
        max_id = max(int(item['id']) for item in items)
        new_id = str(max_id + 1).zfill(3)
    else:
        new_id = '001'

    target_region = item_data.get('region', 'global')

    new_item = {
        'id': new_id,
        'name': item_data.get('name', ''),
        'condition': item_data.get('condition', ''),
        'url': item_data.get('url', ''),
        'region': target_region,
        'enabled': item_data.get('enabled', True),
        'remark': item_data.get('remark', ''),
        'target_value': item_data.get('target_value', '')
    }
    items.append(new_item)

    # 保存到 JSON
    with open(ITEMS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # 同步到数据库
    sync_items_to_db()

    return new_item


def update_item(item_id, item_data):
    items = load_items_from_json()
    found = False
    target_region = item_data.get('region', 'global')

    for item in items:
        if item['id'] == item_id:
            if 'name' in item_data:
                item['name'] = item_data['name']
            if 'condition' in item_data:
                item['condition'] = item_data['condition']
            if 'enabled' in item_data:
                item['enabled'] = item_data['enabled']
            if 'remark' in item_data:
                item['remark'] = item_data['remark']
            if 'target_value' in item_data:
                item['target_value'] = item_data['target_value']
            if 'url' in item_data:
                item['url'] = item_data['url']
            if 'region' in item_data:
                item['region'] = item_data['region']
            found = True
            break

    if not found:
        return None

    # 保存到 JSON
    with open(ITEMS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # 同步到数据库
    sync_items_to_db()

    for item in items:
        if item['id'] == item_id:
            return item
    return None


def delete_item(item_id, region=None):
    items = load_items_from_json()

    # 简单删除：按 id 删除整条记录
    items = [item for item in items if item['id'] != item_id]

    # 保存到 JSON
    with open(ITEMS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # 从数据库删除
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if region:
        cursor.execute('DELETE FROM items WHERE id = ? AND region = ?', (item_id, region))
        cursor.execute('DELETE FROM prices WHERE item_id = ? AND region = ?', (item_id, region))
    else:
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        cursor.execute('DELETE FROM prices WHERE item_id = ?', (item_id,))
    conn.commit()
    conn.close()

    return True


def get_item_by_id(item_id):
    items = load_items_from_json()
    for item in items:
        if item['id'] == item_id:
            return item
    return None
