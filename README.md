# FreeAPI Directory

免费 API 资源导航网站，搭载 AI 智能搜索。基于 FastAPI + Ollama Qwen3.5 0.8b。

## 功能

- 6 大分类，62 个精选免费 API（天气、新闻、AI、金融、社交、开发工具）
- AI 智能搜索：自然语言提问，Qwen3.5 展示完整思考过程并匹配相关 API
- 混合搜索引擎：SQLite FTS5 处理英文，中文 2-gram 关键词 + 概念映射
- 暗色/亮色主题切换，偏好保存在本地
- API 收藏功能（localStorage 持久化）
- 请求示例一键复制
- 支持公网访问（ngrok 隧道或直连 IP）

## 技术栈

| 层面 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.138 |
| 模板 | Jinja2（直接使用 Environment） |
| CSS | Tailwind CSS CDN |
| 数据库 | SQLite + SQLAlchemy 2.0 (async) + FTS5 全文搜索 |
| AI | Ollama + Qwen3.5 0.8b（本地推理） |

## 快速开始

### 环境要求

- Python 3.10+
- Ollama 已安装并运行
- Qwen3.5 0.8b 模型：`ollama pull qwen3.5:0.8b`

### 安装运行

```bash
git clone <仓库地址>
cd all_api

pip install -r requirements.txt
python seed.py          # 初始化数据库
python run.py           # 启动服务，默认端口 9000
```

浏览器打开 http://localhost:9000

### 公网访问

```bash
python run.py --public
```

启动后自动创建 localhost.run 隧道，生成 `https://xxx.lhr.life` 公网 URL。
无需注册账号，免费使用。将 URL 分享给任何人即可访问。

## 项目结构

```
all_api/
├── main.py              # FastAPI 路由
├── models.py            # 数据模型（Category, ApiEntry）
├── database.py          # 异步 SQLite + FTS5
├── seed.py              # 62 个 API 种子数据
├── ollama_service.py    # AI 服务 + 混合搜索引擎
├── run.py               # 一键启动（支持 --public 公网隧道）
├── requirements.txt
├── templates/
│   ├── base.html        # 暗/亮主题布局
│   ├── index.html       # 首页分类网格
│   ├── category.html    # 分类 API 列表
│   ├── detail.html      # API 详情 + 复制 + 收藏
│   ├── search.html      # AI 搜索 + 思考过程展示
│   └── 404.html
└── static/
```

## AI 搜索流程

```
用户输入 → 关键词提取
            ├─ 中文：2-gram 分词 + 概念映射（计算机→开发工具/AI 分类）
            ├─ 英文：SQLite FTS5 + BM25 排序
            └─ 分类权重加速

搜索结果 → Ollama Qwen3.5 0.8b
            ├─ 思考过程：展示完整推理链
            └─ AI 回答：结构化推荐结果
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页 |
| GET | `/category/{slug}` | 分类列表 |
| GET | `/api/{id}` | API 详情 |
| GET | `/search` | AI 搜索页面 |
| POST | `/api/ask` | AI 问答 JSON 接口 |
| GET | `/api/categories` | 分类列表 JSON |

## License

MIT
