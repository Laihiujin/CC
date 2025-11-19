# 🚀 增强功能快速入门指南

## 5分钟快速上手

### 第一步：部署增强功能

```bash
# 进入项目目录
cd social-auto-upload

# 运行一键部署脚本
python deploy_enhanced.py
```

这个脚本会自动：
- ✅ 创建所需的目录结构
- ✅ 初始化数据库表
- ✅ 创建默认配置
- ✅ 检查依赖

### 第二步：启动后端服务

```bash
python sau_backend.py
```

看到以下输出表示成功：
```
🚀 启动增强功能任务调度器...
✅ 任务调度器已启动
 * Running on http://0.0.0.0:5409
```

### 第三步：测试功能

打开新的终端窗口，测试API：

```bash
# 测试代理管理接口
curl http://localhost:5409/api/enhanced/proxies

# 测试任务列表接口
curl http://localhost:5409/api/enhanced/matrix/tasks
```

## 🎯 三大核心功能使用

### 1️⃣ 矩阵投放 - 一键分发到多账号

**场景**: 你有3个视频，想发布到抖音平台的所有账号上

**操作**:
```bash
curl -X POST http://localhost:5409/api/enhanced/matrix/tasks/batch-distribute \
  -H "Content-Type: application/json" \
  -d '{
    "platform_type": 3,
    "file_ids": [1, 2, 3],
    "title": "精彩视频",
    "tags": "#热门 #推荐"
  }'
```

**结果**: 自动为该平台的每个账号创建投放任务

### 2️⃣ IP管理 - 防止封禁

**第一步：添加代理**
```bash
curl -X POST http://localhost:5409/api/enhanced/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "proxy_name": "代理1",
    "proxy_type": "http",
    "proxy_host": "proxy.example.com",
    "proxy_port": 8080,
    "cooldown_minutes": 30
  }'
```

**第二步：为账号启用自动切换**
```bash
curl -X POST http://localhost:5409/api/enhanced/ip-switch/init \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "switch_interval_minutes": 60,
    "auto_switch_enabled": true
  }'
```

**结果**: 系统每小时自动为该账号切换IP

### 3️⃣ Cookie管理 - 自动化管理

**添加新账号时自动创建Cookie路径**:
```bash
curl -X POST http://localhost:5409/api/enhanced/cookies/auto-create-path \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "platform_type": 3,
    "username": "my_account"
  }'
```

**结果**: 
- 自动创建目录结构
- 生成Cookie文件
- 返回路径供后续使用

## 📱 使用Python客户端

复制 `examples/enhanced_features_demo.py` 到你的代码中：

```python
from enhanced_features_demo import EnhancedAPIClient

client = EnhancedAPIClient()

# 批量分配
result = client.batch_distribute(
    platform_type=3,
    file_ids=[1, 2, 3],
    title="视频标题"
)

# 添加代理
proxy = client.add_proxy(
    proxy_name="代理1",
    proxy_type="http",
    proxy_host="127.0.0.1",
    proxy_port=8080
)

# 切换IP
client.switch_ip(account_id=1)
```

## 🔍 常见问题

### Q1: 如何查看任务执行状态？

```bash
# 获取所有任务
curl http://localhost:5409/api/enhanced/matrix/tasks

# 获取特定任务详情
curl http://localhost:5409/api/enhanced/matrix/tasks/1
```

### Q2: 如何查看当前使用的代理？

```bash
curl http://localhost:5409/api/enhanced/ip-switch/current-proxy/1
```

### Q3: 如何停止自动切换IP？

```python
# 在数据库中更新或通过API
# 暂时没有直接API，可以更新 ip_switch_schedule 表的 auto_switch_enabled 字段
```

### Q4: 任务调度器是如何工作的？

任务调度器在后台自动运行，会：
- ⏰ 每30秒检查待执行的矩阵任务
- 🔄 每60秒检查需要切换IP的账号
- 🍪 每5分钟检查需要刷新的Cookie

### Q5: 可以手动触发某个任务吗？

目前任务由调度器自动执行。如需立即执行，可以：
1. 创建任务时不设置定时
2. 或修改子任务的 `scheduled_time` 为当前时间

## 📊 监控和日志

### 查看任务统计

```bash
curl http://localhost:5409/api/enhanced/matrix/tasks/1
```

返回包含统计信息：
```json
{
  "statistics": {
    "total": 10,
    "pending": 2,
    "running": 1,
    "success": 6,
    "failed": 1
  }
}
```

### 查看代理统计

```bash
curl http://localhost:5409/api/enhanced/proxies/1
```

返回代理使用统计：
```json
{
  "total_success_count": 50,
  "total_fail_count": 2,
  "current_use_count": 0,
  "last_used_at": "2025-11-20T10:30:00"
}
```

## 🎓 进阶使用

### 创建账号分组

```bash
curl -X POST http://localhost:5409/api/enhanced/account-groups \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "抖音A组",
    "platform_type": 3,
    "account_ids": [1, 2, 3, 4, 5],
    "description": "主要账号组"
  }'
```

### 定时投放

```bash
curl -X POST http://localhost:5409/api/enhanced/matrix/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "定时任务",
    "platform_type": 3,
    "file_ids": [1, 2, 3],
    "account_ids": [1, 2],
    "title": "定时发布",
    "enable_timer": true,
    "videos_per_day": 2,
    "daily_times": ["09:00", "18:00"],
    "start_days": 0
  }'
```

### 自定义浏览器配置

```bash
curl -X POST http://localhost:5409/api/enhanced/browser-configs \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "自定义配置",
    "browser_type": "chromium",
    "headless": false,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "is_default": false
  }'
```

## 📖 完整文档

- **功能详细说明**: `ENHANCED_FEATURES.md`
- **实现技术文档**: `IMPLEMENTATION_SUMMARY.md`
- **API参考**: `ENHANCED_FEATURES.md` 中的API文档部分
- **代码示例**: `examples/enhanced_features_demo.py`

## 🆘 获取帮助

如遇到问题：
1. 查看终端日志输出
2. 检查 `db/database.db` 是否存在
3. 确认后端服务正在运行
4. 查看完整文档

## ⭐ 下一步

现在你已经掌握了基础用法，可以：
- 🔧 根据需求调整配置参数
- 📊 监控任务执行情况
- 🚀 开始大规模矩阵投放
- 🛡️ 配置代理保护账号安全

祝使用愉快！🎉
