# 注册人数监控说明

## 已实现能力

后端提供受密钥保护的统计接口：

```text
GET /api/admin/stats
```

统计内容包括：

- 总注册人数
- 活跃用户数
- 今日新增注册人数
- 近 7 天新增注册人数
- 近 30 天新增注册人数
- 近 30 天每日注册趋势
- 总收藏数
- 已建立展柜的用户数
- 总排行榜条目数
- 已设置排行榜的用户数
- 注册事件统计

## 本地验收查看方式

启动项目：

```powershell
cd G:\codex_projects\kobox
.\scripts\start_acceptance.ps1
```

查看注册人数：

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8001/api/admin/stats `
  -Headers @{ "X-Admin-Token" = "local-dev-admin-stats-token" }
```

如果只想看总注册人数：

```powershell
(Invoke-RestMethod `
  -Uri http://127.0.0.1:8001/api/admin/stats `
  -Headers @{ "X-Admin-Token" = "local-dev-admin-stats-token" }).total_users
```

如果只想看今日新增：

```powershell
(Invoke-RestMethod `
  -Uri http://127.0.0.1:8001/api/admin/stats `
  -Headers @{ "X-Admin-Token" = "local-dev-admin-stats-token" }).today_users
```

## 正式上线配置

在后端生产环境变量中配置：

```text
ADMIN_STATS_TOKEN=<一串足够长的随机密钥>
```

上线后访问：

```powershell
Invoke-RestMethod `
  -Uri https://你的后端域名/api/admin/stats `
  -Headers @{ "X-Admin-Token" = "<你的 ADMIN_STATS_TOKEN>" }
```

也可以使用 Bearer Token：

```powershell
Invoke-RestMethod `
  -Uri https://你的后端域名/api/admin/stats `
  -Headers @{ "Authorization" = "Bearer <你的 ADMIN_STATS_TOKEN>" }
```

## 安全注意

- 不要把 `ADMIN_STATS_TOKEN` 写到前端代码里。
- 不要把生产密钥提交到 Git。
- 如果怀疑密钥泄露，直接更换后端环境变量并重启服务。
