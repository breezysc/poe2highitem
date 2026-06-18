"""
数据库初始化脚本
首次运行或需要重置数据库时执行
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from backend.db import init_db, sync_items_to_db, get_all_items

def main():
    print("=" * 50)
    print("POE2 暗金监控系统 - 数据库初始化")
    print("=" * 50)

    print("\n[1/3] 初始化数据库表...")
    init_db()
    print("      数据库表创建完成")

    print("\n[2/3] 同步物品数据...")
    items = sync_items_to_db()
    print(f"      已同步 {len(items)} 个物品到数据库")

    print("\n[3/3] 验证数据...")
    all_items = get_all_items()
    print(f"      数据库中共有 {len(all_items)} 个物品")

    print("\n" + "=" * 50)
    print("初始化完成！现在可以启动服务器：")
    print("  python start_server.py")
    print("=" * 50)

if __name__ == '__main__':
    main()
