# Kobox 正式上线操作手册

这份文件记录上线前还需要你手动填写的参数，以及部署时应该执行的自动检查。代码侧已经内置生产配置校验、限流、安全响应头、数据库就绪检查和发布检查脚本。

## 一、你需要手动填写的配置

### 后端 `backend/.env`

从 `backend/.env.production.example` 复制为 `backend/.env`，并填写：

```env
APP_ENV=production
APP_DEBUG=false
DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres
SECRET_KEY=<生成一个至少 32 位，推荐 64 位以上的随机密钥>
SEED_ON_STARTUP=false
AUTO_CREATE_TABLES=false
CORS_ALLOW_ORIGINS=https://www.your-domain.com,https://your-domain.com
TRUSTED_HOSTS=api.your-domain.com,your-backend-host.example.com
PUBLIC_SITE_URL=https://www.your-domain.com
PASSWORD_RESET_URL=https://www.your-domain.com/auth
SMTP_HOST=<你的 SMTP 服务地址>
SMTP_USERNAME=<SMTP 用户名>
SMTP_PASSWORD=<SMTP 密码或应用专用密码>
SMTP_FROM_EMAIL=<no-reply@your-domain.com>
```

`SECRET_KEY` 可以用下面的命令生成：

```powershell
cd G:\codex_projects\kobox\backend
python scripts\generate_secret_key.py
```

必须替换的值：

- `DATABASE_URL`：Supabase 的 PostgreSQL 连接串，推荐使用 Session Pooler 的 `5432` 端口。
- `SECRET_KEY`：不能使用示例值，建议用密码管理器或 `openssl rand -hex 32` 生成。
- `CORS_ALLOW_ORIGINS`：你的正式前端域名。
- `TRUSTED_HOSTS`：你的正式后端域名或部署平台分配的后端 host。
- `PUBLIC_SITE_URL`：用户二维码和公开主页使用的正式前端域名。
- `PASSWORD_RESET_URL`：找回密码邮件里的前端地址。
- `SMTP_*`：正式邮件服务，用于忘记密码。

### 前端 `frontend/.env.production`

从 `frontend/.env.production.example` 复制为 `frontend/.env.production`，并填写：

```env
VITE_API_BASE_URL=https://api.your-domain.com
VITE_PUBLIC_SITE_URL=https://www.your-domain.com
VITE_USE_MOCK=false
```

必须替换的值：

- `VITE_API_BASE_URL`：正式后端 API 域名。
- `VITE_PUBLIC_SITE_URL`：正式前端域名，二维码分享链接会使用它。

## 二、数据库上线流程

1. 在 Supabase 创建正式项目。
2. 将 `DATABASE_URL` 配到后端生产环境。
3. 在后端目录执行迁移：

```powershell
cd G:\codex_projects\kobox\backend
alembic upgrade head
alembic current
```

期望版本：

```text
20260416_0006 (head)
```

生产环境必须保持：

```env
AUTO_CREATE_TABLES=false
SEED_ON_STARTUP=false
```

## 三、上线前自动检查

在本地或 CI 中执行：

```powershell
cd G:\codex_projects\kobox
python backend\scripts\run_release_checks.py
```

它会自动运行：

- 后端 Python 编译检查。
- 后端 smoke 测试。
- PRD 核心流程 smoke 测试。
- 前端生产构建。

生产环境变量填完后，再执行：

```powershell
cd G:\codex_projects\kobox\backend
python scripts\check_production_readiness.py
```

它会检查：

- 生产环境是否关闭 debug。
- 是否使用强 `SECRET_KEY`。
- 是否使用 PostgreSQL/Supabase，而不是 SQLite。
- 是否关闭 `AUTO_CREATE_TABLES` 和 `SEED_ON_STARTUP`。
- CORS、Trusted Hosts、密码重置 URL、公开站点 URL 是否仍是本地地址。
- SMTP 是否配置。
- 数据库是否能 `select 1`。

## 四、部署建议

### 后端

推荐命令：

```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

生产平台上建议：

- 使用 HTTPS 反向代理。
- 设置健康检查路径为 `/health/ready`。
- 对 `/api/auth/*` 和 `/api/anime/search*` 保留平台侧限流。
- 确保 `uploads` 目录可持久化，或后续迁移到对象存储。

### 前端

构建：

```powershell
cd frontend
npm ci
npm run build
```

部署 `frontend/dist` 到静态托管平台，并设置 SPA fallback 到 `index.html`，否则 `/u/<用户>` 这类公开主页刷新时会 404。

## 五、当前代码已具备的上线保护

- JWT 鉴权保护 `/api/me/*` 私有接口。
- 用户展柜和榜单按 `user_id` 查询，不能操作别人的数据。
- 公开主页只有浏览接口，写操作只存在登录态 `/api/me/*`。
- 公开主页关闭后返回 404。
- 公开榜单关闭后返回空列表。
- 用户收藏和榜单有数据库唯一约束，避免重复数据。
- 后端已内置基础限流。
- 后端已内置安全响应头。
- 后端已内置 `/health/live` 和 `/health/ready`。
- 二维码分享链接使用 `public_slug` 和正式 `VITE_PUBLIC_SITE_URL`。

## 六、上线后仍建议观察的指标

- 登录耗时。
- `/api/me/dashboard` 首次和缓存命中耗时。
- `/api/anime/search` 与 `/api/anime/search/suggestions` 冷启动耗时。
- Supabase 连接池使用率和慢查询。
- SMTP 发送成功率。
- 429 限流次数。
- 5xx 错误率。
