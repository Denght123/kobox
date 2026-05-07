# Kobox 项目阶段记录

记录时间：2026-04-21  
项目路径：`G:\codex_projects\kobox`

---

## 1. 项目定位

Kobox 是一个面向动漫用户的追番收藏展示网站。核心目标不是社区、评分或评论，而是：

- 快速搜索动漫并添加到个人展柜。
- 自动获取动漫名称、封面和基础信息。
- 按“已追番 / 在追 / 想看”等状态整理收藏。
- 建立个人公开主页，用封面墙形式展示个人动漫收藏。
- 支持“我の最爱”排行榜。
- 支持二维码和链接分享个人主页。
- 支持多语言切换。
- 支持个人资料、头像、页面背景图设置。

当前技术栈：

- 前端：Vue 3 + TypeScript + Vite + Pinia + Vue Query
- 后端：FastAPI + SQLAlchemy + Alembic
- 本地验收数据库：SQLite
- 目标生产数据库：PostgreSQL，最终推荐先部署在阿里云 ECS 本机

---

## 2. 当前功能完成情况

目前核心功能已经基本完成，达到可进入部署准备阶段的状态。

已完成：

- 用户注册
- 用户登录
- 退出登录确认弹窗
- 忘记密码基础流程
- 用户资料保存
- 头像上传
- 页面背景图片上传
- 恢复默认背景
- 展柜页面
- 搜索动漫
- 搜索联想
- 添加追番 / 在追 / 想看
- 删除收藏
- 收藏数据和当前用户数据库绑定
- 我の最爱排行榜
- 排行榜最多 10 个
- 排行榜添加、删除、排序
- 公开分享主页
- 分享二维码
- 公开主页只读访问
- 公开主页展示对方背景图
- 公开主页展示“Ta的最爱”
- “我也要建立展柜”跳转到本站登录页
- 多语言切换
- 动漫名称随语言切换
- 美化提示框和确认框
- 注册人数统计接口
- 本地验收启动脚本

---

## 3. 最近修复和关键决策

### 3.1 分享页权限边界

之前公开分享链接中点击“我也要建立展柜”时，如果浏览器已有登录态，会被路由守卫带到 `/showcase`。这容易造成“进入别人展柜并可操作别人数据”的误解。

已经修复为：

- 公开页 CTA 跳转到 `/auth?publicEntry=1`
- 路由守卫遇到 `publicEntry=1` 时不自动跳转到 `/showcase`
- 公开页始终是只读展示
- 用户只能操作自己账号绑定的数据

涉及：

- `frontend/src/router/index.ts`
- `frontend/src/pages/PublicProfilePage.vue`
- `frontend/src/components/layout/AppTopNav.vue`

### 3.2 公开主页背景图

之前公开主页背景图读取的是当前登录用户背景，而不是被访问用户背景。

已修复为：

- `FloatingBackdrop` 支持传入 `backgroundImageUrl`
- 公开主页从 `/api/public/users/:username` 获取对方 `background_image_url`
- 分享链接打开后背景始终跟随对方账号

### 3.3 背景图片显示

用户不希望背景图灰蒙蒙，所以已经去掉自定义背景图遮罩层。当前背景图使用原图显示，保留内容卡片自身的透明透视效果。

涉及：

- `frontend/src/components/layout/FloatingBackdrop.vue`

### 3.4 退出登录确认

已经接入统一美化确认框：

- 点击“退出登录”后先弹确认框
- 点击“确认退出”才真正清理登录态并回到登录页
- 点击取消则不退出

涉及：

- `frontend/src/components/layout/AppTopNav.vue`

### 3.5 注册人数统计

新增后台统计接口：

```text
GET /api/admin/stats
```

使用 `ADMIN_STATS_TOKEN` 保护。

本地查看：

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8001/api/admin/stats `
  -Headers @{ "X-Admin-Token" = "local-dev-admin-stats-token" }
```

统计内容包括：

- 总注册人数
- 活跃用户数
- 今日新增注册人数
- 近 7 天新增
- 近 30 天新增
- 近 30 天每日注册趋势
- 总收藏数
- 已建立展柜用户数
- 总排行榜条目数
- 已设置排行榜用户数

新增表：

```text
analytics_events
```

当前 Alembic 版本：

```text
20260420_0007 (head)
```

说明文档：

- `markdown_set/ADMIN_STATS_WORKTHROUGH.md`

---

## 4. 当前本地运行方式

已经新增本地验收启动脚本：

```text
scripts/start_acceptance.ps1
```

启动方式：

```powershell
cd G:\codex_projects\kobox
.\scripts\start_acceptance.ps1
```

启动后：

```text
前端：http://127.0.0.1:5173/
后端：http://127.0.0.1:8001/
健康检查：http://127.0.0.1:8001/health/ready
```

本地 Demo 账号：

```text
账号：demo@kobox.local
密码：Demo1234!
```

日志位置：

```text
G:\codex_projects\kobox\.tmp\run\backend-8001.log
G:\codex_projects\kobox\.tmp\run\frontend-5173.log
```

说明文档：

- `markdown_set/ACCEPTANCE_RUNBOOK.md`

---

## 5. 已有测试和检查

已多次执行并通过：

```powershell
python backend\scripts\run_release_checks.py
```

该脚本包括：

- 后端 Python 编译检查
- 后端 smoke test
- PRD 核心流程 smoke test
- 前端生产构建

生产环境检查脚本：

```powershell
cd backend
python scripts\check_production_readiness.py
```

它会检查：

- 是否生产环境
- 是否关闭 debug
- 是否使用 PostgreSQL
- 是否关闭自动建表和 seed
- 是否配置 SMTP
- 是否配置正式域名
- 是否配置强 `SECRET_KEY`
- 是否配置 `ADMIN_STATS_TOKEN`
- 数据库是否可连接

---

## 6. 当前部署方案的最新决策

用户反馈：

- Vercel 对中国用户访问不稳定，可能超时。
- Render 不适合，且可能不免费。
- 用户已有一台阿里云 ECS。
- 希望部署方案简单、国内访问更快。

根据截图确认 ECS 信息：

```text
云厂商：阿里云 ECS
地域：西南 1（成都）
系统：Ubuntu 24.04 64位
规格：2 vCPU / 2 GB 内存
公网 IP：47.109.180.204
带宽：100 Mbps 峰值
状态：运行中
```

最终推荐方案：

```text
阿里云 ECS 成都
+ 宝塔面板
+ Nginx
+ PostgreSQL 本机数据库
+ FastAPI 后端
+ Vue 前端静态文件
+ 本机 uploads 图片目录
+ QQ 邮箱 SMTP
```

不推荐当前阶段使用：

- Vercel
- Render
- Supabase
- Docker 全家桶
- 阿里云 RDS
- 阿里云 OSS

原因：

- 当前第一版目标是快速上线和中国用户可访问。
- 2 核 2G ECS 足够跑第一版轻量服务。
- 本机 PostgreSQL 比跨境 Supabase 连接更稳。
- 宝塔面板对新手更友好。

---

## 7. 推荐生产架构

第一版推荐单域名部署，减少配置复杂度：

```text
https://你的域名.com
```

路径规划：

```text
/                 → 前端 Vue dist
/api              → FastAPI 后端 127.0.0.1:8001
/uploads          → 后端上传文件目录
/u/:username      → 公开分享主页
/api/admin/stats  → 后台统计接口
```

服务器内部结构：

```text
ECS 47.109.180.204
├── Nginx
│   ├── /                 → frontend/dist
│   ├── /api              → 127.0.0.1:8001
│   └── /uploads          → backend/uploads
├── FastAPI
│   └── 127.0.0.1:8001
├── PostgreSQL
│   └── 127.0.0.1:5432
└── uploads
    └── 用户头像 / 用户背景图
```

公网只开放：

```text
80
443
22
宝塔面板端口，建议只允许自己的 IP
```

不要开放：

```text
5173
8001
5432
```

---

## 8. 域名和备案方案

用户目前：

- 没有域名
- 不知道去哪里购买
- 可以 root 登录 ECS
- 愿意使用宝塔面板

建议：

1. 在阿里云购买域名。
2. 完成域名实名认证。
3. 因为 ECS 是中国大陆成都地域，正式域名上线需要 ICP 备案。
4. 备案期间可以先用公网 IP 部署测试版。
5. 备案完成后再绑定正式域名。

购买域名入口：

```text
https://wanwang.aliyun.com/domain/
```

备案入口：

```text
https://beian.aliyun.com/
```

建议域名后缀优先级：

```text
.com > .cn > .cc > .net
```

可以尝试：

```text
kobox.cn
kobox.com
kobox.cc
mykobox.cn
koboxacg.cn
koboxbox.cn
```

备案网站名称建议：

```text
Kobox 动漫收藏展示
```

如果备案不允许英文，可用：

```text
小匣子动漫收藏展示
```

网站说明：

```text
用于用户整理、展示和分享个人动漫收藏内容。
```

---

## 9. 最新建议的上线步骤

### 阶段 1：现在即可做

先用 ECS 公网 IP 部署测试版：

```text
http://47.109.180.204
```

测试版路径：

```text
http://47.109.180.204          → 前端
http://47.109.180.204/api      → 后端
http://47.109.180.204/uploads  → 上传图片
```

需要做：

1. root 登录 ECS。
2. 安装宝塔面板。
3. 宝塔中安装 Nginx 和 PostgreSQL。
4. 上传或拉取项目代码。
5. 创建 PostgreSQL 数据库。
6. 配置后端 `.env`。
7. 执行 Alembic 迁移。
8. 构建前端 `npm run build`。
9. 配置 Nginx：
   - `/` 指向前端 `dist`
   - `/api` 反代到 `127.0.0.1:8001`
   - `/uploads` 指向上传目录
10. 用 IP 访问测试。

### 阶段 2：同时进行

购买域名并备案：

1. 阿里云购买域名。
2. 域名实名认证。
3. 提交 ICP 备案。
4. 等待备案通过。

### 阶段 3：备案完成后

切换正式域名：

1. DNS 添加 A 记录到 `47.109.180.204`
2. 宝塔绑定域名
3. 申请 SSL 证书
4. 后端 `.env` 改为正式域名：

```env
CORS_ALLOW_ORIGINS=https://你的域名.com
PUBLIC_SITE_URL=https://你的域名.com
PASSWORD_RESET_URL=https://你的域名.com/auth
TRUSTED_HOSTS=你的域名.com
```

5. 前端 `.env.production` 改为：

```env
VITE_API_BASE_URL=https://你的域名.com
VITE_PUBLIC_SITE_URL=https://你的域名.com
VITE_USE_MOCK=false
```

6. 重新构建前端并重启后端。

---

## 10. 接下来需要用户准备的信息

用户下一步需要确认或完成：

```text
1. 是否已经购买域名
2. 域名是什么
3. 是否已完成域名实名认证
4. 是否已开始 ICP 备案
5. 是否已经安装宝塔面板
6. 宝塔面板是否能打开
7. 是否愿意先用 IP 部署测试版
```

如果用户确认宝塔已安装成功，下一步可以继续生成：

```text
deploy/aliyun-ecs/
```

包含：

- 一键部署脚本
- systemd 服务文件
- Nginx IP 测试配置
- Nginx 域名正式配置
- PostgreSQL 初始化脚本
- 生产环境变量模板
- 数据库备份脚本
- 阿里云 ECS + 宝塔部署说明

---

## 11. 当前项目风险和后续优化

上线前必须注意：

- 生产环境不能继续用 SQLite。
- 生产环境必须配置 PostgreSQL。
- 生产环境必须配置强 `SECRET_KEY`。
- 生产环境必须配置 `ADMIN_STATS_TOKEN`。
- 忘记密码需要 SMTP。
- 大陆 ECS 正式域名上线需要 ICP 备案。
- 上传文件目前在本机 `uploads`，需要定期备份。
- PostgreSQL 本机部署也需要定期备份。

后续有用户后建议升级：

- PostgreSQL 迁移到阿里云 RDS PostgreSQL。
- uploads 迁移到阿里云 OSS。
- 接入 Sentry 做前后端错误监控。
- 接入阿里云日志服务。
- 做每日数据库自动备份。

---

## 12. 关键命令备忘

本地启动：

```powershell
cd G:\codex_projects\kobox
.\scripts\start_acceptance.ps1
```

本地完整测试：

```powershell
python backend\scripts\run_release_checks.py
```

查看本地统计：

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8001/api/admin/stats `
  -Headers @{ "X-Admin-Token" = "local-dev-admin-stats-token" }
```

查看本地前端：

```text
http://127.0.0.1:5173/
```

查看本地后端健康：

```text
http://127.0.0.1:8001/health/ready
```

生产数据库迁移期望：

```text
20260420_0007 (head)
```
