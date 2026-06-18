# POE2 暗金价格监控系统

一个用于监控 Path of Exile 2 暗金物品价格的 Web 应用系统。

## 功能特性

- 📊 **价格监控**: 实时追踪暗金物品的市场价格
- 🌐 **Web 界面**: 提供直观的 Web 管理界面
- 💾 **数据持久化**: 使用 SQLite 存储价格历史记录
- 🔍 **搜索功能**: 快速搜索特定物品
- 📈 **价格历史**: 查看物品的历史价格走势

## 目录结构

```
server/
├── start_server.py          # 服务器启动入口
├── init_db.py              # 数据库初始化脚本
├── requirements.txt         # Python 依赖
├── backend/
│   ├── api.py              # Flask REST API
│   └── db.py               # 数据库操作模块
├── web/
│   ├── templates/
│   │   └── index.html      # Web 界面模板
│   └── static/
│       └── favicon.ico     # 网站图标
└── data/
    ├── items.json          # 物品配置数据
    └── items.db            # SQLite 数据库
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/breezysc/poe2highitem.git
cd poe2highitem
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库（首次运行必需）

```bash
python init_db.py
```

### 4. 启动服务器

```bash
python start_server.py
```

### 5. 访问界面

打开浏览器访问: `http://localhost:8000`

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/items` | GET | 获取所有物品列表 |
| `/api/items` | POST | 添加新物品 |
| `/api/items/<id>` | GET | 获取单个物品信息 |
| `/api/items/<id>` | PUT | 更新物品信息 |
| `/api/items/<id>` | DELETE | 删除物品 |
| `/api/update` | POST | 更新物品价格 |
| `/api/latest` | GET | 获取最新价格 |
| `/api/history/<id>` | GET | 获取价格历史 |

## 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite
- **前端**: HTML + JavaScript
- **跨域**: Flask-CORS

## 许可证

MIT License
