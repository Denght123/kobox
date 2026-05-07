# Supabase 数据库接入说明

## 目标

本项目当前把 Supabase 只作为一个托管 PostgreSQL 数据库来使用。

目前**没有**使用这些 Supabase 能力：

- Supabase Auth
- Supabase Storage
- Supabase Realtime
- Supabase JS Client Key

所以在数据库接入这件事上，你**不需要**这些参数：

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

你现在真正需要的，只有 PostgreSQL 连接串，以及应用本身常规的环境变量。

## 为了支持 Supabase，我做了哪些代码调整

后端已经补上了对 Supabase 的直接支持：

1. 新增 PostgreSQL 驱动：`psycopg[binary]==3.3.3`
2. Supabase 提供的 `postgres://` 或 `postgresql://` 连接串，会自动归一化成 SQLAlchemy 可直接使用的 `postgresql+psycopg://`
3. 如果你使用的是 Supabase 的事务池化端口 `:6543`，后端会自动：
   - 使用 `NullPool`
   - 关闭 psycopg 的 prepared statements

相关文件：

- [config.py](/g:/codex_projects/kobox/backend/app/core/config.py)
- [session.py](/g:/codex_projects/kobox/backend/app/db/session.py)
- [requirements.txt](/g:/codex_projects/kobox/backend/requirements.txt)

## 这个项目应该选 Supabase 的哪种连接方式

### 推荐选择

对于当前 Kobox 项目，优先推荐：

- **Session Pooler（5432 端口）**

适合场景：

- 你在本地 Windows 环境开发
- 你的网络主要是 IPv4
- 后端是一个常驻运行的 FastAPI 服务
- 你想要更稳妥、少踩坑的默认方案

### Direct Connection（5432 端口）

适合场景：

- 你的部署环境支持 IPv6
- 后端运行在稳定的云主机 / 长驻容器中

### Transaction Pooler（6543 端口）

只建议在这些情况下使用：

- 你的后端运行在 serverless / 短生命周期环境
- 你明确知道自己要用 Supavisor 的事务池化

对当前这个 FastAPI 项目来说，**Session Pooler 是最稳妥的默认选项**。

## 这些参数去 Supabase 后台哪里拿

在 Supabase 控制台中：

1. 打开你的项目
2. 点击 `Connect`
3. 选择你要使用的连接方式：
   - Direct connection
   - Session pooler
   - Transaction pooler
4. 复制连接串，或者抄下原始参数

你会用到这些值：

- `project_ref`
- `db_password`
- `host`
- `port`
- `database_name`
- `user`

常见情况：

- `database_name` 一般是 `postgres`
- `user`：
  - Direct connection 通常是 `postgres`
  - Pooler 模式通常是 `postgres.<project-ref>`

如果你忘了数据库密码，可以在 Supabase 项目设置里重置，然后同步更新 `.env`。

## 应用里需要配置哪些参数

### 后端 `.env`

必填：

- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ALLOW_ORIGINS`

生产环境建议：

- `SEED_ON_STARTUP=false`
- `AUTO_CREATE_TABLES=false`

### 前端 `.env`

必填：

- `VITE_API_BASE_URL`

建议：

- `VITE_USE_MOCK=false`

## DATABASE_URL 示例

### 1. Supabase Session Pooler

这是最推荐的方案。

```env
DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

### 2. Supabase Direct Connection

只在你的后端部署环境支持 IPv6 时推荐使用。

```env
DATABASE_URL=postgresql+psycopg://postgres:<db-password>@db.<project-ref>.supabase.co:5432/postgres
```

### 3. Supabase Transaction Pooler

仅适合 serverless / 短连接场景。

```env
DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

如果你直接把 Supabase 提供的原始 `postgres://...` 连接串粘贴进来，后端现在也会自动归一化处理。

## Kobox 推荐环境变量示例

### backend/.env

```env
APP_NAME=Kobox API
APP_ENV=production
APP_DEBUG=false
DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres
SECRET_KEY=<your-random-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
SEED_ON_STARTUP=false
AUTO_CREATE_TABLES=false
CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*
CORS_ALLOW_CREDENTIALS=true
UPLOADS_DIR=uploads
UPLOADS_URL_PREFIX=/uploads
UPLOAD_MAX_BYTES=5242880
UPLOAD_ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/webp,image/gif
ANILIST_API_URL=https://graphql.anilist.co
ANILIST_TIMEOUT_SECONDS=8
```

### frontend/.env

```env
VITE_API_BASE_URL=https://your-backend-domain.com
VITE_USE_MOCK=false
```

## 如何一步步配置 Supabase

### 1. 创建项目

在 Supabase 后台：

1. 创建一个新项目
2. 选择离你的后端更近的区域
3. 设置一个强密码作为数据库密码
4. 等数据库初始化完成

### 2. 选择连接方式

对于 Kobox：

- 本地开发 / IPv4 环境：选 **Session Pooler**
- 支持 IPv6 的长驻后端：选 **Direct Connection**

### 3. 填写后端 `.env`

创建 `backend/.env`，至少填写：

- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ALLOW_ORIGINS`
- `SEED_ON_STARTUP=false`
- `AUTO_CREATE_TABLES=false`

### 4. 安装依赖

```powershell
cd g:\codex_projects\kobox\backend
python -m pip install -r requirements.txt
```

### 5. 执行迁移

```powershell
cd g:\codex_projects\kobox\backend
alembic upgrade head
```

这一步会在你的 Supabase PostgreSQL 中创建 Kobox 所需的表。

### 6. 启动后端

```powershell
cd g:\codex_projects\kobox\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 7. 填写前端 `.env`

创建 `frontend/.env`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_USE_MOCK=false
```

如果你的后端已经部署到线上，就把它改成真实的后端域名。

### 8. 启动前端

```powershell
cd g:\codex_projects\kobox\frontend
npm install
npm run dev
```

## 数据库表设计

除非你后面主动改 schema 或 search path，否则所有表都会建在默认的 `public` schema 下。

### users

用途：  
存储账号身份和登录级别字段。

字段：

- `id` 主键
- `email` 唯一
- `username` 唯一
- `password_hash`
- `is_active`
- `role`
- `created_at`
- `updated_at`

### user_profiles

用途：  
存储用户公开资料和个性化设置。

字段：

- `id` 主键
- `user_id` 唯一外键 -> `users.id`
- `avatar_url`
- `display_name`
- `birthday`
- `bio`
- `public_slug` 唯一
- `is_public`
- `language`
- `show_dynamic_background`
- `show_public_rank`
- `created_at`
- `updated_at`

### refresh_tokens

用途：  
存储刷新令牌会话。

字段：

- `id` 主键
- `user_id` 外键 -> `users.id`
- `token_jti` 唯一
- `expires_at`
- `revoked_at`
- `created_at`

### anime

用途：  
存储动漫主数据和来源信息。

字段：

- `id` 主键
- `source_id` 唯一
- `cover_url`
- `source_cover_url`
- `local_cover_url`
- `cover_source`
- `year`
- `season`
- `status`
- `genres_json`
- `created_at`
- `updated_at`

### anime_translations

用途：  
存储不同语言下的标题和简介。

字段：

- `id` 主键
- `anime_id` 外键 -> `anime.id`
- `language_code`
- `title`
- `summary`

约束：

- `unique(anime_id, language_code)`

### user_collections

用途：  
存储用户收藏了哪些动漫，以及收藏状态。

字段：

- `id` 主键
- `user_id` 外键 -> `users.id`
- `anime_id` 外键 -> `anime.id`
- `collection_status`
- `added_at`
- `updated_at`

约束：

- `unique(user_id, anime_id)`

`collection_status` 枚举值：

- `completed`
- `watching`
- `plan_to_watch`
- `on_hold`
- `dropped`

### user_favorite_ranks

用途：  
存储每个用户的喜欢榜顺序。

字段：

- `id` 主键
- `user_id` 外键 -> `users.id`
- `anime_id` 外键 -> `anime.id`
- `rank_order`
- `created_at`
- `updated_at`

约束：

- `unique(user_id, anime_id)`
- `unique(user_id, rank_order)`

### password_reset_tokens

用途：  
存储“忘记密码”流程的一次性重置 token 哈希值。

字段：

- `id` 主键
- `user_id` 外键 -> `users.id`
- `token_hash`
- `expires_at`
- `used_at`
- `created_at`

约束：

- `unique(token_hash)`

## 关系总结

- `users` 1:1 `user_profiles`
- `users` 1:N `refresh_tokens`
- `users` 1:N `password_reset_tokens`
- `users` 1:N `user_collections`
- `users` 1:N `user_favorite_ranks`
- `anime` 1:N `anime_translations`
- `anime` 1:N `user_collections`
- `anime` 1:N `user_favorite_ranks`

## 迁移完成后如何验证

你可以在 Supabase 的 SQL Editor 里执行：

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```

你应该能看到这些业务表：

- `anime`
- `anime_translations`
- `refresh_tokens`
- `password_reset_tokens`
- `user_collections`
- `user_favorite_ranks`
- `user_profiles`
- `users`

再检查 Alembic 版本：

```sql
select * from alembic_version;
```

当前预期版本：

- `20260416_0006`

## 性能索引

当前已为展柜和喜欢榜的高频读取增加索引：

```sql
create index ix_user_collections_user_status_added
on user_collections (user_id, collection_status, added_at);

create index ix_user_collections_user_added
on user_collections (user_id, added_at);

create index ix_user_favorite_ranks_user_rank
on user_favorite_ranks (user_id, rank_order);
```

这些索引用于加速：

- “我的展柜”按用户读取收藏
- 展柜内按状态读取已追番 / 在追 / 想看
- 右侧“我の最爱”榜单按排名读取

## 忘记密码邮件参数

如果要让线上用户通过注册邮箱找回密码，需要在 `backend/.env` 配置 SMTP 参数：

```env
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
PASSWORD_RESET_URL=https://你的前端域名/auth
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=你的邮箱账号
SMTP_PASSWORD=你的邮箱授权码或 SMTP 密码
SMTP_FROM_EMAIL=你的发件邮箱
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

说明：

- `PASSWORD_RESET_URL` 必须指向前端登录页，系统会自动拼接 `?reset_token=...`。
- 开发环境未配置 SMTP 时，接口会返回一个测试用 `dev_reset_token`，方便本地验证流程。
- 生产环境未配置 SMTP 时，系统会拒绝发送，避免用户误以为邮件已发出。

## 注意事项

1. Supabase 的 direct connection 默认更偏向 IPv6，如果你的本机或服务器不支持 IPv6，请优先使用 Session Pooler。
2. 对这个 FastAPI 项目来说，除非是 serverless 场景，否则 Session Pooler 一般比 Transaction Pooler 更稳。
3. 当前项目的头像上传仍然使用本地磁盘，不是 Supabase Storage。
4. 当前项目登录认证仍然使用自己的 JWT 体系，不是 Supabase Auth。

## 官方参考

- Supabase: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase SQLAlchemy 指南: https://supabase.com/docs/guides/troubleshooting/using-sqlalchemy-with-supabase-FUqebT
- SQLAlchemy psycopg 方言: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg

## 相关源码

- [user.py](/g:/codex_projects/kobox/backend/app/models/user.py)
- [user_profile.py](/g:/codex_projects/kobox/backend/app/models/user_profile.py)
- [refresh_token.py](/g:/codex_projects/kobox/backend/app/models/refresh_token.py)
- [password_reset_token.py](/g:/codex_projects/kobox/backend/app/models/password_reset_token.py)
- [anime.py](/g:/codex_projects/kobox/backend/app/models/anime.py)
- [user_collection.py](/g:/codex_projects/kobox/backend/app/models/user_collection.py)
- [user_favorite_rank.py](/g:/codex_projects/kobox/backend/app/models/user_favorite_rank.py)
- [20260409_0001_initial.py](/g:/codex_projects/kobox/backend/alembic/versions/20260409_0001_initial.py)
- [20260409_0002_add_anime_genres_json.py](/g:/codex_projects/kobox/backend/alembic/versions/20260409_0002_add_anime_genres_json.py)
- [20260409_0003_add_anime_is_adult.py](/g:/codex_projects/kobox/backend/alembic/versions/20260409_0003_add_anime_is_adult.py)
- [20260414_0004_add_password_reset_tokens.py](/g:/codex_projects/kobox/backend/alembic/versions/20260414_0004_add_password_reset_tokens.py)
- [20260414_0005_add_collection_performance_indexes.py](/g:/codex_projects/kobox/backend/alembic/versions/20260414_0005_add_collection_performance_indexes.py)
- [20260416_0006_add_profile_background_image.py](/g:/codex_projects/kobox/backend/alembic/versions/20260416_0006_add_profile_background_image.py)
