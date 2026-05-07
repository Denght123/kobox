# 动漫收藏网站技术设计文档（TECH_DESIGN）

## 1. 文档目标

本文档用于明确动漫收藏网站在开发阶段的技术选型、系统结构、模块拆分与实现建议。

本阶段重点是：

- 保证你能基于现有技能快速开工
- 保证技术方案清晰、稳定、易维护
- 保证后续方便扩展
- **暂不考虑部署方案，等项目完成后再单独设计部署**

---

## 2. 项目背景与技术方向

该项目的产品定位为：

- 动漫收藏管理网站
- 个人动漫收藏柜主页
- 可分享的二次元展示空间

它不是：

- 社区论坛
- 评论网站
- 逐集追番记录工具
- 泛影视数据库

因此，技术设计的重点应围绕以下能力展开：

1. 用户登录注册
2. 用户资料管理
3. 动漫搜索与收藏
4. 收藏状态管理
5. 喜欢榜排序
6. 公开主页展示
7. 多语言支持
8. 高颜值前端展示能力

结合你的技能栈，推荐主方向为：

- 前端：Vue 3 生态
- 后端：FastAPI 生态

---

## 3. 技术选型总览

## 3.1 前端技术栈

推荐：

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Axios
- TanStack Query for Vue
- Element Plus 或 Naive UI
- vue-i18n

推荐结论：

**前端采用 Vue 3 + TypeScript + Vite，状态管理使用 Pinia，接口数据管理使用 Axios + TanStack Query，国际化使用 vue-i18n。**

---

## 3.2 后端技术栈

推荐：

- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- PostgreSQL

推荐结论：

**后端采用 FastAPI + SQLAlchemy 2.x + Pydantic + Alembic，数据库使用 PostgreSQL。**

---

## 3.3 本阶段不纳入技术设计范围

当前阶段暂不深入设计以下内容：

- 生产部署方案
- 容器化上线方案
- CDN/对象存储最终架构
- Redis 缓存与异步任务系统
- 搜索引擎拆分（如 Elasticsearch / Meilisearch）
- 微服务拆分

这些内容可以在项目开发接近完成后再补充。

---

## 4. 前端技术设计

## 4.1 Vue 3 + TypeScript

推荐原因：

- 你已具备 Vue 3 能力，学习成本最低
- Vue 3 Composition API 适合模块拆分和复用
- TypeScript 可以帮助约束接口类型和页面数据结构
- 后续前后端联调会更顺畅

适合场景：

- 收藏柜首页
- 搜索添加页
- 喜欢榜排序页
- 个人资料设置页
- 公开主页页

---

## 4.2 Vite

推荐原因：

- 启动和热更新速度快
- Vue 3 官方推荐方向
- 适合中小型前端项目快速开发
- 配置比传统打包工具更轻

建议：

- 直接使用 Vite 初始化 Vue 3 + TypeScript 项目
- 前端环境变量按 `.env.development`、`.env.production` 方式管理

---

## 4.3 Vue Router

推荐原因：

项目天然是一个多页面体验型网站，至少包含：

- 登录/注册页
- 首页/收藏柜页
- 搜索添加页
- 喜欢榜管理页
- 个人资料/设置页
- 公开主页页

因此必须使用前端路由管理页面切换。

建议路由结构：

```text
/auth
/home
/search
/favorite-rank
/settings
/u/:username
```

---

## 4.4 Pinia

推荐原因：

- 轻量
- 与 Vue 3 生态契合
- 写法现代
- 更适合 Composition API
- 足够支撑当前网站的全局状态管理

适合放在 Pinia 的状态：

- 登录态
- 当前用户信息
- 当前语言设置
- 应用级 UI 状态
- 收藏页的局部筛选条件

建议 Store：

- `useAuthStore`
- `useUserStore`
- `useAppStore`
- `useCollectionStore`

---

## 4.5 Axios + TanStack Query

推荐组合：

- Axios：处理 HTTP 请求封装
- TanStack Query：处理服务端状态缓存、请求状态、失效刷新

原因：

如果只依赖 Pinia 存接口数据，随着页面增多会变得混乱。  
TanStack Query 更适合处理：

- 首页收藏数据加载
- 搜索结果缓存
- 喜欢榜更新后的重新获取
- 公开主页访问缓存

建议：

- Axios 负责统一请求实例、拦截器、错误处理
- TanStack Query 负责 `useQuery` / `useMutation`

---

## 4.6 UI 组件库

推荐优先级：

### 方案 A：Element Plus
优点：

- 表单、弹窗、上传、抽屉、分页等组件齐全
- 文档成熟
- 上手快
- 开发效率高

适合：

- 登录注册表单
- 设置页表单
- 搜索页筛选和弹窗
- 喜欢榜管理页中的操作组件

### 方案 B：Naive UI
优点：

- 默认视觉更轻盈
- 更容易贴近你想要的清新、精致二次元风格

适合：

- 如果你愿意花一点时间做视觉统一和主题定制

推荐结论：

**如果你更重视开发效率，先选 Element Plus。**  
**如果你更重视整体默认颜值，可以选 Naive UI。**

---

## 4.7 前端国际化

推荐方案：

- 使用 `vue-i18n`
- 所有界面文案统一走语言包
- 默认语言为简体中文
- 预留繁体中文、英语、日语、韩语

建议目录：

```text
src/i18n/
  zh-CN.json
  zh-TW.json
  en.json
  ja.json
  ko.json
```

建议原则：

- 所有按钮、标题、导航、提示语，不直接写死在页面中
- 动漫基础信息多语言字段由后端返回
- 前端只负责 UI 文案国际化

---

## 4.8 前端目录结构建议

```text
src/
  api/
  assets/
  components/
  composables/
  layouts/
  pages/
  router/
  stores/
  types/
  utils/
  i18n/
```

建议说明：

- `api/`：接口请求封装
- `components/`：通用组件，如封面卡片、收藏分区、二维码模块
- `pages/`：页面级组件
- `stores/`：Pinia 状态
- `types/`：TS 类型定义
- `composables/`：可复用逻辑
- `utils/`：工具方法
- `layouts/`：基础页面布局

---

## 5. 后端技术设计

## 5.1 FastAPI

推荐原因：

- 你已具备 FastAPI 技能
- 开发 REST API 非常高效
- 类型提示友好
- 自动生成 Swagger 文档
- 非常适合前后端分离项目

适合本项目的原因：

- 当前项目核心是中后台风格 API
- 页面虽然偏展示，但本质依旧是标准的用户、收藏、搜索、公开主页 API

---

## 5.2 Pydantic

推荐原因：

- 用于定义请求体、响应体、数据校验
- 和 FastAPI 深度整合
- 可以清晰表达接口的数据结构
- 方便前后端联调时对齐字段

建议：

- 所有输入输出都定义 schema
- 不要直接返回 ORM 模型
- 请求模型和响应模型分开定义

---

## 5.3 SQLAlchemy 2.x

推荐原因：

- 生态成熟
- 查询能力强
- 适合复杂一点的数据关系
- 更适合长期维护

为什么不推荐现在改用其他 ORM：

- 你当前项目虽然不算特别复杂，但会涉及：
  - 用户
  - 收藏关系
  - 排名
  - 多语言字段
  - 公开主页
- SQLAlchemy 对这些关系建模更稳

建议：

- 使用 SQLAlchemy 2.x 的现代写法
- ORM 模型与 Pydantic schema 分层
- Repository / Service 分层时可保持良好扩展性

---

## 5.4 Alembic

推荐原因：

- 数据库迁移标准方案
- 与 SQLAlchemy 配合自然
- 方便持续迭代表结构

建议：

- 每次修改数据表结构都生成 migration
- 不要手改线上数据库结构
- 开发阶段就养成 migration 管理习惯

---

## 6. 数据库选型与建模建议

## 6.1 PostgreSQL

推荐原因：

- 关系型数据支持稳定
- 适合用户系统、收藏系统、排序系统
- 支持索引、JSON、全文检索扩展能力
- 后续可平滑扩展搜索与统计能力

本地开发可以临时使用 SQLite，  
但正式开发阶段最好尽量按 PostgreSQL 的语义设计，避免后续迁移差异。

---

## 6.2 核心数据实体

建议最少包含以下实体：

- 用户
- 用户资料
- 动漫基础数据
- 动漫标题多语言数据
- 用户收藏记录
- 用户喜欢榜排序

---

## 6.3 推荐核心表结构

### 1. users
用途：

- 登录账号
- 基础认证信息

核心字段建议：

- id
- email / username
- password_hash
- is_active
- created_at
- updated_at

### 2. user_profiles
用途：

- 存放展示型资料

核心字段建议：

- user_id
- avatar_url
- display_name
- birthday
- bio
- public_slug / username_slug

### 3. anime
用途：

- 动漫主表

核心字段建议：

- id
- source_id
- cover_url
- source_cover_url
- year
- season
- status
- created_at
- updated_at

### 4. anime_translations
用途：

- 动漫名称、简介等多语言内容

核心字段建议：

- id
- anime_id
- language_code
- title
- summary

### 5. user_collections
用途：

- 用户收藏关系表

核心字段建议：

- id
- user_id
- anime_id
- collection_status
- added_at
- updated_at

状态建议枚举：

- completed
- watching
- plan_to_watch
- on_hold
- dropped

### 6. user_favorite_ranks
用途：

- 用户最喜欢动漫的排序

核心字段建议：

- id
- user_id
- anime_id
- rank_order
- created_at
- updated_at

---

## 6.4 多语言设计建议

如果你的网站要支持：

- 简体中文
- 繁体中文
- 英语
- 日语
- 韩语

建议拆分为两类国际化：

### A. UI 文案国际化
由前端 `vue-i18n` 负责。

### B. 动漫内容国际化
由后端数据库表负责，例如：

- `anime_translations.language_code`
- `anime_translations.title`
- `anime_translations.summary`

这样后续更容易按语言返回对应内容。

---

## 7. 系统模块拆分建议

## 7.1 前端页面模块

建议拆分：

1. 登录/注册页
2. 首页/收藏柜页
3. 搜索添加页
4. 喜欢榜管理页
5. 个人资料/设置页
6. 公开主页页

---

## 7.2 前端通用组件

建议优先封装这些组件：

- AnimeCoverCard（动漫封面卡片）
- CollectionSection（收藏分区）
- FavoriteRankList（喜欢榜组件）
- ProfileHeader（主页头部）
- ShareQRCodeCard（二维码分享模块）
- SearchBar（搜索框）
- EmptyState（空状态）
- LanguageSwitcher（语言切换器）

---

## 7.3 后端模块结构

建议后端按职责拆分：

```text
app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  repositories/
  utils/
```

说明：

- `api/`：路由层
- `core/`：配置、鉴权、通用逻辑
- `db/`：数据库连接与 session
- `models/`：ORM 模型
- `schemas/`：Pydantic 模型
- `services/`：业务逻辑
- `repositories/`：数据访问层
- `utils/`：工具函数

---

## 8. API 设计建议

推荐走 REST 风格接口。

建议接口分组：

### 8.1 认证接口

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
```

### 8.2 用户接口

```text
GET  /api/me
PUT  /api/me/profile
GET  /api/me/settings
PUT  /api/me/settings
```

### 8.3 动漫搜索接口

```text
GET /api/anime/search?q=
GET /api/anime/search/suggestions?q=
```

### 8.4 收藏接口

```text
GET    /api/me/collections
POST   /api/me/collections
PUT    /api/me/collections/{collection_id}
DELETE /api/me/collections/{collection_id}
```

### 8.5 喜欢榜接口

```text
GET /api/me/favorites
PUT /api/me/favorites/rank
```

### 8.6 公开主页接口

```text
GET /api/public/users/{username}
GET /api/public/users/{username}/collections
GET /api/public/users/{username}/favorites
```

---

## 9. 鉴权与权限设计

## 9.1 鉴权方案

推荐：

- JWT access token
- refresh token

原因：

- 适合前后端分离项目
- 与 FastAPI 配合自然
- 后续方便扩展登录态管理

建议：

- access token 生命周期短
- refresh token 生命周期更长
- 后端提供 refresh 接口

---

## 9.2 权限模型

当前只需要三种角色视角：

### 游客
- 只能访问登录注册页
- 只能访问公开主页

### 登录用户
- 可管理自己的资料
- 可管理自己的收藏
- 可管理自己的喜欢榜

### 管理员（后续可加）
- 动漫数据维护
- 内容清理
- 后台管理

MVP 阶段可以先不做管理员页面，只在数据库层预留角色字段。

---

## 10. 动漫搜索与数据源建议

## 10.1 搜索设计思路

当前网站的搜索是“搜索动漫并加入收藏”，不是复杂全文内容搜索。

MVP 建议：

- 动漫数据同步到本地数据库
- 搜索直接查本地数据表
- 前端调用 `/api/anime/search`

这样比直接前端请求第三方 API 更稳定。

---

## 10.2 动漫封面匹配建议

PRD 中强调：

- 添加动漫时自动匹配官方封面

建议实现方式：

1. 后端维护动漫基础表
2. 每条动漫记录保存封面地址
3. 用户搜索后直接返回本地已缓存的封面与基本信息
4. 后续可做封面本地化缓存

MVP 阶段不一定要做复杂图片转存，  
但数据模型中建议预留：

- source_cover_url
- local_cover_url
- cover_source

---

## 11. 前后端通信规范

建议统一以下规范：

### 11.1 时间格式
统一使用 ISO 8601。

### 11.2 枚举值
后端返回英文枚举，前端本地映射中文显示。

例如：

```text
completed
watching
plan_to_watch
on_hold
dropped
```

### 11.3 分页格式
统一为：

- items
- total
- page
- page_size

### 11.4 错误返回
统一包含：

- code
- message
- details（可选）

---

## 12. 开发阶段建议的实现顺序

推荐按照下面顺序开发：

### 第一阶段：项目骨架
- 初始化 Vue 3 + TS + Vite
- 初始化 FastAPI 项目
- 配置 PostgreSQL
- 初始化 SQLAlchemy + Alembic
- 搭建基础路由和页面框架

### 第二阶段：认证和用户系统
- 注册
- 登录
- 当前用户信息
- 编辑资料

### 第三阶段：动漫搜索与收藏
- 动漫基础数据导入
- 搜索接口
- 收藏接口
- 首页收藏柜展示

### 第四阶段：喜欢榜和公开主页
- 喜欢榜排序
- 公开主页接口
- 公开主页展示页

### 第五阶段：多语言支持和视觉完善
- vue-i18n 接入
- 后端多语言字段返回
- 页面统一视觉风格

---

## 13. 我对这套技术方案的最终建议

对于你现在的能力和项目方向，最适合的方案是：

### 前端
- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Axios
- TanStack Query
- Element Plus 或 Naive UI
- vue-i18n

### 后端
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- PostgreSQL

这套方案的优点：

1. 你可以快速上手，不需要额外学习全新主框架
2. 与你的 PRD 非常契合
3. 代码结构容易维护
4. 后续扩展搜索、统计、多语言、公开主页都很自然
5. 当前不考虑部署时，这已经足够支撑开发阶段所有工作

---

## 14. 后续可继续补充的设计文档

建议你在这份技术设计文档之后，继续补以下文档：

1. 数据库表结构详细设计
2. API 接口文档
3. 前端页面路由与状态设计
4. 动漫数据源接入方案
5. 前后端联调字段规范文档

---

## 15. 当前结论

本项目当前最合理的开发技术方案是：

**前端使用 Vue 3 生态，后端使用 FastAPI 生态，数据库使用 PostgreSQL，优先完成收藏、展示、搜索、喜欢榜、公开主页这些核心功能。**

并且：

**当前阶段不考虑部署设计，先把开发阶段的技术架构和实现路径定清楚。**
