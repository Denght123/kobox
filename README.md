# Kobox

Kobox 是一个基于 Vue 3 + FastAPI 的动漫收藏与展示网站，核心体验围绕「搜索加入收藏、整理状态、展示主页、分享给别人」展开。
当前已有备案并上线网站：https://kobox.top/

## 项目状态

当前仓库已经具备可本地运行的完整前后端：

- 登录、注册、刷新令牌与忘记密码接口
- 个人资料、头像上传、本地静态资源访问
- 动漫搜索与详情同步，支持 AniList、Bangumi、Jikan、Kitsu 数据源配置
- 收藏状态管理与喜欢榜管理
- 公开个人主页、公开收藏展示、分享二维码
- 多语言基础支持：简体中文、繁體中文、English、日本語、한국어
- 生产基础能力：CORS、Trusted Hosts、安全响应头、基础限流、健康检查、Alembic 迁移、发布前检查脚本

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Vue I18n、TanStack Vue Query
- 后端：FastAPI、SQLAlchemy 2.x、Alembic、Pydantic、JWT、psycopg 3
- 数据库：本地默认 SQLite，生产建议 PostgreSQL / Supabase

## 目录结构

```text
kobox/
├─ frontend/          Vue 3 前端应用
├─ backend/           FastAPI 后端服务
├─ markdown_set/      PRD、技术设计、上线手册与验收文档
├─ UI_DESIGNED/       早期视觉参考稿
├─ scripts/           本地辅助脚本
└─ uploads/           本地上传资源目录，默认不提交
```

## 本地启动

### 1. 启动后端

```powershell
cd G:\codex_projects\kobox\backend
python -m pip install -r requirements.txt
```

如果没有 `backend/.env`，先创建一个最小开发配置：

```env
APP_ENV=development
APP_DEBUG=true
DATABASE_URL=sqlite:///./kobox.db
SECRET_KEY=replace_this_with_a_long_random_secret
SEED_ON_STARTUP=true
AUTO_CREATE_TABLES=true
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
TRUSTED_HOSTS=localhost,127.0.0.1,testserver
PUBLIC_SITE_URL=http://127.0.0.1:5173
PASSWORD_RESET_URL=http://127.0.0.1:5173/auth
```

然后执行迁移并启动 API：

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

- API 地址：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health/ready`

### 2. 启动前端

```powershell
cd G:\codex_projects\kobox\frontend
npm install
```

如果没有 `frontend/.env`，创建：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_PUBLIC_SITE_URL=http://127.0.0.1:5173
VITE_USE_MOCK=false
```

启动开发服务：

```powershell
npm run dev
```

前端地址：`http://127.0.0.1:5173`

## Demo 账号

开发环境默认 `SEED_ON_STARTUP=true` 时会写入演示数据：

- 邮箱：`demo@kobox.local`
- 密码：`Demo1234!`

## 常用命令

前端构建：

```powershell
cd G:\codex_projects\kobox\frontend
npm run build
```

后端 smoke test：

```powershell
cd G:\codex_projects\kobox\backend
alembic upgrade head
python tests\smoke_api.py
```

完整发布前检查：

```powershell
cd G:\codex_projects\kobox
python backend\scripts\run_release_checks.py
```

## 生产部署要点

生产环境建议使用 PostgreSQL / Supabase，并关闭启动时建表与种子数据：

```env
APP_ENV=production
APP_DEBUG=false
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=<至少 32 位的随机密钥，建议 64 位以上>
SEED_ON_STARTUP=false
AUTO_CREATE_TABLES=false
CORS_ALLOW_ORIGINS=https://www.your-domain.com,https://your-domain.com
TRUSTED_HOSTS=api.your-domain.com,your-backend-host.example.com
PUBLIC_SITE_URL=https://www.your-domain.com
PASSWORD_RESET_URL=https://www.your-domain.com/auth
SMTP_HOST=<smtp-host>
SMTP_USERNAME=<smtp-username>
SMTP_PASSWORD=<smtp-password-or-app-password>
SMTP_FROM_EMAIL=<no-reply@your-domain.com>
```

配置完成后，在后端目录运行生产校验：

```powershell
cd G:\codex_projects\kobox\backend
python scripts\check_production_readiness.py
```

更完整的上线步骤见 [markdown_set/PRODUCTION_WORKTHROUGH.md](markdown_set/PRODUCTION_WORKTHROUGH.md)。

## API 概览

- `GET /health/live`、`GET /health/ready`：服务健康检查
- `/api/auth/*`：登录、注册、令牌与密码重置
- `/api/me/*`：当前用户资料、头像与私有数据
- `/api/anime/*`：动漫搜索、详情与同步
- `/api/me/collections/*`：收藏状态管理
- `/api/me/favorites/*`：喜欢榜管理
- `/api/public/*`：公开主页与公开展示数据
- `/api/admin/*`：管理统计接口，需要配置 `ADMIN_STATS_TOKEN`

## 备注

- 本地数据库文件、上传目录、前端构建产物和依赖目录都不应提交。
- 头像默认上传到后端本地 `uploads` 目录；生产环境需要保证该目录可持久化，或后续替换为对象存储。
- 前端是 SPA，部署静态站点时需要把未知路由 fallback 到 `index.html`，否则 `/u/<username>` 这类公开主页刷新会 404。
