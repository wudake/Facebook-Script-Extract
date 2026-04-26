# Video Script Extractor - Team Edition

Facebook 视频音频转文字工具 —— **前后端分离团队版**。

支持通过 Web 界面提交 Facebook 视频链接，自动下载、提取音频、语音识别，输出 TXT / SRT / VTT / JSON 格式。

## 架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│   React     │     │   Redis     │
│  (80端口)   │     │   前端      │     │  任务队列   │
└──────┬──────┘     └─────────────┘     └──────┬──────┘
       │                                         │
       │  /api/* 反向代理                        │
       │  /ws/*  WebSocket                       │
       ▼                                         │
┌─────────────┐     ┌─────────────┐             │
│   FastAPI   │◀────│   Celery    │─────────────┘
│   后端 API  │     │   Worker    │
└─────────────┘     └─────────────┘
```

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 API_KEY 和 OPENAI_API_KEY（如使用 API 模式）

# 2. 启动全部服务
docker-compose up -d

# 3. 访问
# 前端: http://localhost
# API 文档: http://localhost:8000/docs
```

### 方式二：本地开发

**后端**
```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Redis（需要本地安装 Redis）
redis-server

# 启动 FastAPI
cd api && uvicorn main:app --reload --port 8000

# 启动 Celery Worker（另开终端）
celery -A api.celery_app worker --loglevel=info
```

**前端**
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 项目结构

```
.
├── api/                  # FastAPI 后端
│   ├── main.py           # 应用入口
│   ├── celery_app.py     # Celery 配置
│   ├── core/             # 配置
│   ├── models/           # 数据模型
│   ├── routers/          # API 路由
│   │   ├── health.py
│   │   ├── tasks.py      # 任务 CRUD
│   │   └── ws.py         # WebSocket 实时进度
│   └── tasks/
│       └── worker.py     # Celery 任务处理
├── frontend/             # React + Vite 前端
│   ├── src/
│   │   ├── api/client.ts # API 客户端
│   │   ├── pages/        # 页面组件
│   │   └── hooks/        # 自定义 Hooks
│   ├── Dockerfile
│   └── nginx.conf
├── src/                  # 核心转写模块（前后端共享）
│   ├── downloader.py     # 视频下载 (yt-dlp)
│   ├── audio_extractor.py# 音频提取 (ffmpeg)
│   ├── transcriber.py    # OpenAI Whisper API
│   ├── local_transcriber.py # 本地 faster-whisper
│   └── formatter.py      # 输出格式化
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tasks` | 创建转写任务 |
| GET | `/tasks` | 任务列表 |
| GET | `/tasks/{id}` | 任务详情 |
| GET | `/tasks/{id}/result` | 获取结果数据 |
| GET | `/tasks/{id}/download` | 下载结果文件 |
| WS | `/ws/tasks` | WebSocket 实时进度 |

所有接口需要在 Header 中携带 `X-API-Key`。

## 团队使用说明

1. **共享 API Key**：团队成员使用相同的 `API_KEY` 访问服务
2. **任务隔离**：每个任务有独立 ID，结果保存在 `output/` 目录
3. **并发处理**：Celery Worker 支持多任务并行，可通过 `docker-compose.yml` 调整 `concurrency`
4. **GPU 加速**：Worker 服务已配置 NVIDIA GPU 支持（需主机安装 NVIDIA Docker Runtime）

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_KEY` | `dev-api-key-change-me` | 团队共享的 API 认证 Key |
| `OPENAI_API_KEY` | - | OpenAI API Key（使用 API 模式时必填） |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `TEMP_DIR` | `./temp` | 临时文件目录 |
| `OUTPUT_DIR` | `./output` | 结果输出目录 |

## License

MIT
