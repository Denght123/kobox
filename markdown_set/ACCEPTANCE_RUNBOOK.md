# Kobox 本地验收运行方案

## 目标

本方案用于进入稳定验收阶段：前端、后端、数据库全部在本机可控运行，避免 Supabase 直连不稳定导致页面无法调试。

## 当前验收方案

- 前端：Vite，固定运行在 `http://127.0.0.1:5173/`
- 后端：FastAPI，固定运行在 `http://127.0.0.1:8001/`
- 数据库：本地 SQLite，路径为 `backend/kobox.db`
- 上传文件：本地静态目录，路径为 `backend/uploads`

## 一键启动

在项目根目录执行：

```powershell
.\scripts\start_acceptance.ps1
```

脚本会自动完成：

- 停止占用 `5173` 和 `8001` 的旧调试进程
- 将后端临时切换到本地 SQLite 验收数据库
- 执行 Alembic 数据库迁移
- 启动后端和前端
- 检查后端 `/health/ready`
- 检查前端首页可访问

## 日志位置

- 后端日志：`.tmp/run/backend-8001.log`
- 前端日志：`.tmp/run/frontend-5173.log`

## Demo 账号

```text
账号：demo@kobox.local
密码：Demo1234!
```

## Supabase 上线切换说明

当前 Supabase 直连曾出现远端断开连接，验收阶段先使用本地 SQLite 保证功能稳定。正式上线时再将 `backend/.env` 的 `DATABASE_URL` 切回 Supabase PostgreSQL，并建议优先使用 Supabase Transaction Pooler 连接串。

上线前仍需执行：

```powershell
python backend\scripts\run_release_checks.py
```
