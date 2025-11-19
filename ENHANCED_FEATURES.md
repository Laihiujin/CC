# 增强功能使用指南

本项目新增了三大核心功能模块，用于提升矩阵投放效率和账号安全性。

## 📋 功能概览

### 1. 矩阵投放功能
- ✅ 一键将素材分配到同平台的多个账号
- ✅ 支持账号分组管理
- ✅ 支持定时投放和批量投放
- ✅ 任务状态跟踪和统计

### 2. 代理IP管理
- ✅ 代理IP池管理
- ✅ 自动切换IP防封禁
- ✅ IP使用统计和冷却时间管理
- ✅ 支持HTTP/HTTPS/SOCKS5代理

### 3. 浏览器和Cookie管理
- ✅ 统一的浏览器配置管理
- ✅ 自动创建和管理Cookie文件
- ✅ Cookie有效性检测
- ✅ 自动刷新提醒

## 🚀 快速开始

### 1. 初始化数据库

首次使用需要创建增强功能的数据表：

```bash
cd db
python enhanced_tables.py
```

### 2. 启动后端服务

```bash
python sau_backend.py
```

服务启动后会自动：
- 启动任务调度器
- 开启IP自动切换
- 开启Cookie监控

## 📖 API 接口文档

所有增强功能API接口前缀为：`/api/enhanced`

### 矩阵投放相关

#### 创建矩阵投放任务
```http
POST /api/enhanced/matrix/tasks
Content-Type: application/json

{
  "task_name": "测试任务",
  "platform_type": 3,
  "file_ids": [1, 2, 3],
  "account_ids": [1, 2, 3],
  "title": "视频标题",
  "tags": "标签1 标签2",
  "enable_timer": true,
  "videos_per_day": 2,
  "daily_times": ["10:00", "18:00"],
  "start_days": 0
}
```

#### 一键分配到同平台所有账号
```http
POST /api/enhanced/matrix/tasks/batch-distribute
Content-Type: application/json

{
  "platform_type": 3,
  "file_ids": [1, 2, 3],
  "title": "视频标题",
  "tags": "标签1 标签2"
}
```

#### 获取任务列表
```http
GET /api/enhanced/matrix/tasks?status=0
```

#### 获取任务详情
```http
GET /api/enhanced/matrix/tasks/{task_id}
```

#### 删除任务
```http
DELETE /api/enhanced/matrix/tasks/{task_id}
```

### 账号分组相关

#### 创建账号分组
```http
POST /api/enhanced/account-groups
Content-Type: application/json

{
  "group_name": "抖音矩阵A组",
  "platform_type": 3,
  "account_ids": [1, 2, 3, 4, 5],
  "description": "抖音矩阵账号第一组"
}
```

#### 获取分组列表
```http
GET /api/enhanced/account-groups?platform_type=3
```

#### 更新分组
```http
PUT /api/enhanced/account-groups/{group_id}
Content-Type: application/json

{
  "group_name": "新的分组名称",
  "account_ids": [1, 2, 3, 4, 5, 6]
}
```

#### 删除分组
```http
DELETE /api/enhanced/account-groups/{group_id}
```

### 代理管理相关

#### 添加代理
```http
POST /api/enhanced/proxies
Content-Type: application/json

{
  "proxy_name": "代理1",
  "proxy_type": "http",
  "proxy_host": "proxy.example.com",
  "proxy_port": 8080,
  "proxy_username": "username",
  "proxy_password": "password",
  "country": "US",
  "provider": "ProxyProvider",
  "priority": 10,
  "max_concurrent_use": 3,
  "cooldown_minutes": 30
}
```

#### 获取代理列表
```http
GET /api/enhanced/proxies?is_active=true
```

#### 获取代理统计
```http
GET /api/enhanced/proxies/{proxy_id}
```

#### 更新代理
```http
PUT /api/enhanced/proxies/{proxy_id}
Content-Type: application/json

{
  "is_active": true,
  "priority": 20
}
```

#### 删除代理
```http
DELETE /api/enhanced/proxies/{proxy_id}
```

### IP切换相关

#### 初始化IP切换调度
```http
POST /api/enhanced/ip-switch/init
Content-Type: application/json

{
  "account_id": 1,
  "switch_interval_minutes": 60,
  "auto_switch_enabled": true
}
```

#### 手动切换IP
```http
POST /api/enhanced/ip-switch/switch
Content-Type: application/json

{
  "account_id": 1,
  "country": "US"
}
```

#### 自动切换所有到期账号的IP
```http
POST /api/enhanced/ip-switch/auto-switch
```

#### 获取账号当前使用的代理
```http
GET /api/enhanced/ip-switch/current-proxy/{account_id}
```

### 浏览器配置相关

#### 创建浏览器配置
```http
POST /api/enhanced/browser-configs
Content-Type: application/json

{
  "config_name": "默认配置",
  "browser_type": "chromium",
  "headless": true,
  "viewport_width": 1920,
  "viewport_height": 1080,
  "is_default": true
}
```

#### 获取配置列表
```http
GET /api/enhanced/browser-configs
```

#### 获取默认配置
```http
GET /api/enhanced/browser-configs/default
```

#### 更新配置
```http
PUT /api/enhanced/browser-configs/{config_id}
Content-Type: application/json

{
  "headless": false,
  "proxy_config_id": 1
}
```

#### 删除配置
```http
DELETE /api/enhanced/browser-configs/{config_id}
```

### Cookie管理相关

#### 自动创建Cookie路径
```http
POST /api/enhanced/cookies/auto-create-path
Content-Type: application/json

{
  "account_id": 1,
  "platform_type": 3,
  "username": "test_user"
}
```

#### 初始化Cookie管理
```http
POST /api/enhanced/cookies/init-management
Content-Type: application/json

{
  "account_id": 1,
  "cookie_path": "douyin_uploader/test_user_1.json",
  "auto_refresh_enabled": true,
  "refresh_interval_hours": 24
}
```

#### 获取需要刷新的账号列表
```http
GET /api/enhanced/cookies/need-refresh
```

#### 标记Cookie已刷新
```http
POST /api/enhanced/cookies/mark-refreshed/{account_id}
```

## 💡 使用场景示例

### 场景1: 矩阵投放 - 一键分发素材到多账号

```python
import requests

# 1. 准备素材和账号
files = [1, 2, 3]  # 文件ID列表
platform = 3  # 抖音

# 2. 一键分配到该平台所有账号
response = requests.post('http://localhost:5409/api/enhanced/matrix/tasks/batch-distribute', json={
    "platform_type": platform,
    "file_ids": files,
    "title": "精彩视频合集",
    "tags": "#热门 #推荐",
    "enable_timer": True,
    "videos_per_day": 2,
    "daily_times": ["09:00", "18:00"],
    "start_days": 0
})

task = response.json()
print(f"任务ID: {task['data']['task_id']}")
```

### 场景2: IP管理 - 为账号配置自动切换IP

```python
import requests

# 1. 添加代理IP
proxy_response = requests.post('http://localhost:5409/api/enhanced/proxies', json={
    "proxy_name": "美国代理1",
    "proxy_type": "http",
    "proxy_host": "us-proxy.example.com",
    "proxy_port": 8080,
    "country": "US",
    "cooldown_minutes": 30
})

# 2. 为账号初始化IP切换调度
account_id = 1
requests.post('http://localhost:5409/api/enhanced/ip-switch/init', json={
    "account_id": account_id,
    "switch_interval_minutes": 60,  # 每小时切换一次
    "auto_switch_enabled": True
})

# 3. 手动切换IP（可选）
requests.post('http://localhost:5409/api/enhanced/ip-switch/switch', json={
    "account_id": account_id
})
```

### 场景3: 简化Cookie管理

```python
import requests

# 1. 添加新账号时自动创建Cookie路径
response = requests.post('http://localhost:5409/api/enhanced/cookies/auto-create-path', json={
    "account_id": 1,
    "platform_type": 3,
    "username": "my_douyin_account"
})

cookie_path = response.json()['data']['cookie_path']
print(f"Cookie路径: {cookie_path}")

# 2. 初始化Cookie自动管理
requests.post('http://localhost:5409/api/enhanced/cookies/init-management', json={
    "account_id": 1,
    "cookie_path": cookie_path,
    "auto_refresh_enabled": True,
    "refresh_interval_hours": 24
})

# 3. 查看需要刷新的账号
refresh_needed = requests.get('http://localhost:5409/api/enhanced/cookies/need-refresh')
print(refresh_needed.json())
```

## 🔧 配置说明

### 平台类型对照表

| 平台类型 | 数值 | 说明 |
|---------|------|------|
| 小红书   | 1    | xiaohongshu |
| 视频号   | 2    | tencent |
| 抖音     | 3    | douyin |
| 快手     | 4    | kuaishou |
| B站      | 5    | bilibili |
| 百家号   | 6    | baijiahao |
| TikTok  | 7    | tiktok |

### 任务状态说明

| 状态 | 数值 | 说明 |
|------|------|------|
| 待执行 | 0 | 任务已创建，等待执行 |
| 执行中 | 1 | 任务正在执行 |
| 已完成 | 2 | 任务已成功完成 |
| 失败   | 3 | 任务执行失败 |

### 代理类型说明

- `http`: HTTP代理
- `https`: HTTPS代理
- `socks5`: SOCKS5代理

## 🎯 最佳实践

### 1. IP切换策略

- **建议切换间隔**: 30-60分钟
- **冷却时间**: 至少30分钟
- **代理数量**: 建议准备账号数量的1.5-2倍的代理IP
- **优先级设置**: 给稳定性高的代理设置更高优先级

### 2. 矩阵投放策略

- **错峰发布**: 设置不同的发布时间，避免集中发布
- **内容差异化**: 同一素材可以配置不同的标题和标签
- **分组管理**: 将账号按照特征分组，便于管理

### 3. Cookie管理

- **定期刷新**: 建议每24小时刷新一次
- **有效性检测**: 发布前检查Cookie是否有效
- **备份**: 定期备份Cookie文件

## ⚠️ 注意事项

1. **数据库备份**: 使用前请备份 `db/database.db` 文件
2. **代理质量**: 使用高质量的代理IP，避免使用免费代理
3. **发布频率**: 控制发布频率，避免被平台识别为机器人
4. **内容合规**: 确保上传内容符合平台规范
5. **账号安全**: 定期检查账号状态，及时处理异常

## 🐛 故障排查

### 问题1: 任务调度器未启动

**解决方案**:
```python
# 检查日志输出是否有 "🚀 启动增强功能任务调度器..."
# 如果没有，检查是否正确初始化了数据表
cd db
python enhanced_tables.py
```

### 问题2: IP切换不生效

**解决方案**:
```python
# 1. 检查代理配置是否正确
GET /api/enhanced/proxies/{proxy_id}

# 2. 检查IP切换调度是否初始化
GET /api/enhanced/ip-switch/current-proxy/{account_id}

# 3. 手动触发切换测试
POST /api/enhanced/ip-switch/switch
```

### 问题3: Cookie路径找不到

**解决方案**:
```python
# 使用自动创建路径功能
POST /api/enhanced/cookies/auto-create-path
{
  "account_id": 1,
  "platform_type": 3,
  "username": "your_username"
}
```

## 📞 技术支持

如有问题，请：
1. 查看日志输出
2. 检查数据库表是否正确创建
3. 在项目GitHub Issues中提问

## 📝 更新日志

### v2.0.0 (2025-11-20)
- ✨ 新增矩阵投放功能
- ✨ 新增代理IP管理和自动切换
- ✨ 新增浏览器和Cookie统一管理
- ✨ 新增任务调度器
- 🔧 优化账号管理流程
- 📚 完善API文档

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！
