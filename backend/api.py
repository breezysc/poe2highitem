from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from pathlib import Path
import sys
import json
import logging
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

from backend.db import (
    init_db,
    sync_items_to_db,
    get_all_items,
    save_price,
    get_latest_prices,
    search_items,
    get_price_history,
    update_target_value,
    add_item,
    update_item,
    delete_item,
    get_item_by_id
)

# 读取应用配置（版本号等）
def get_app_config():
    config_path = BASE_DIR / 'data' / 'app_config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {'version': '2.0'}

app = Flask(__name__,
            template_folder=str(BASE_DIR / 'web' / 'templates'),
            static_folder=str(BASE_DIR / 'web' / 'static'))
CORS(app)

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(LOG_DIR / 'app.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

@app.route('/')
def index():
    try:
        config = get_app_config()
        return render_template('index.html', version=config.get('version', '2.0'))
    except Exception as e:
        from flask import Response
        return Response(f'<h1>加载失败: {e}</h1>', status=500)

@app.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory(str(BASE_DIR / 'web' / 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/version')
def api_version():
    config = get_app_config()
    return jsonify(config)

@app.route('/api/items', methods=['GET'])
def api_items():
    try:
        sync_items_to_db()
        items = get_all_items()
        return jsonify(items)
    except Exception as e:
        logging.error(f'Error getting items: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/update', methods=['POST'])
def api_update():
    try:
        data = request.json
        item_id = data.get('item_id')
        p1 = data.get('p1')
        p2 = data.get('p2')
        p3 = data.get('p3')
        condition = data.get('condition')
        region = data.get('region', 'global')
        
        save_price(item_id, p1, p2, p3, condition, region)
        logging.info(f'Updated price for item {item_id} ({region}): {p1}, {p2}, {p3}')
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f'Error updating price: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest', methods=['GET'])
def api_latest():
    try:
        keyword = request.args.get('search', '')
        region = request.args.get('region', None)
        if keyword:
            items = search_items(keyword, region)
        else:
            items = get_latest_prices(region)
        return jsonify(items)
    except Exception as e:
        logging.error(f'Error getting latest prices: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<item_id>', methods=['GET'])
def api_history(item_id):
    try:
        limit = int(request.args.get('limit', 50))
        history = get_price_history(item_id, limit)
        return jsonify(history)
    except Exception as e:
        logging.error(f'Error getting history: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/log', methods=['POST'])
def api_log():
    try:
        data = request.json
        message = data.get('message', '')
        logging.info(message)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>/target-value', methods=['PUT'])
def api_update_target_value(item_id):
    try:
        data = request.json
        target_value = data.get('target_value', '')
        region = data.get('region', 'global')
        update_target_value(item_id, target_value, region)
        logging.info(f'Updated target_value for item {item_id} ({region}): {target_value}')
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f'Error updating target_value: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/items', methods=['POST'])
def api_add_item():
    try:
        data = request.json
        new_item = add_item(data)
        logging.info(f'Added new item: {new_item["name"]}')
        return jsonify(new_item)
    except Exception as e:
        logging.error(f'Error adding item: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['PUT'])
def api_update_item(item_id):
    try:
        data = request.json
        updated_item = update_item(item_id, data)
        if updated_item:
            logging.info(f'Updated item: {item_id}')
            return jsonify(updated_item)
        else:
            return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        logging.error(f'Error updating item: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['DELETE'])
def api_delete_item(item_id):
    try:
        data = request.json or {}
        region = data.get('region') if request.is_json else request.args.get('region')
        delete_item(item_id, region)
        logging.info(f'Deleted item: {item_id} ({region or "all"})')
        return jsonify({'status': 'success'})
    except Exception as e:
        logging.error(f'Error deleting item: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['GET'])
def api_get_item(item_id):
    try:
        item = get_item_by_id(item_id)
        if item:
            return jsonify(item)
        else:
            return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        logging.error(f'Error getting item: {e}')
        return jsonify({'error': str(e)}), 500

def main():
    init_db()
    sync_items_to_db()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=8000, debug=False)

if __name__ == '__main__':
    main()
