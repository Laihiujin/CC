import sqlite3
import os
from pathlib import Path

# 数据库文件路径
db_file = './database.db'

# 连接到SQLite数据库
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 1. 创建矩阵投放任务表
cursor.execute('''
CREATE TABLE IF NOT EXISTS matrix_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,                    -- 任务名称
    platform_type INTEGER NOT NULL,              -- 平台类型 (1:小红书 2:视频号 3:抖音 4:快手)
    file_ids TEXT NOT NULL,                      -- 文件ID列表（JSON格式）
    account_ids TEXT NOT NULL,                   -- 账号ID列表（JSON格式）
    title TEXT,                                  -- 视频标题
    tags TEXT,                                   -- 标签
    category INTEGER,                            -- 分类
    enable_timer INTEGER DEFAULT 0,              -- 是否启用定时
    videos_per_day INTEGER DEFAULT 1,            -- 每天发布视频数
    daily_times TEXT,                            -- 发布时间点（JSON格式）
    start_days INTEGER DEFAULT 0,                -- 开始天数
    status INTEGER DEFAULT 0,                    -- 任务状态 (0:待执行 1:执行中 2:已完成 3:失败)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
)
''')

# 2. 创建矩阵投放子任务表（记录每个账号的投放详情）
cursor.execute('''
CREATE TABLE IF NOT EXISTS matrix_subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,                    -- 关联主任务ID
    account_id INTEGER NOT NULL,                 -- 账号ID
    file_id INTEGER NOT NULL,                    -- 文件ID
    status INTEGER DEFAULT 0,                    -- 子任务状态 (0:待执行 1:执行中 2:成功 3:失败)
    error_message TEXT,                          -- 错误信息
    retry_count INTEGER DEFAULT 0,               -- 重试次数
    scheduled_time DATETIME,                     -- 计划执行时间
    executed_at DATETIME,                        -- 实际执行时间
    completed_at DATETIME,                       -- 完成时间
    FOREIGN KEY (task_id) REFERENCES matrix_tasks(id)
)
''')

# 3. 创建浏览器配置表
cursor.execute('''
CREATE TABLE IF NOT EXISTS browser_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name TEXT NOT NULL,                   -- 配置名称
    browser_type TEXT DEFAULT 'chromium',        -- 浏览器类型 (chromium/firefox/webkit)
    browser_path TEXT,                           -- 自定义浏览器路径
    headless INTEGER DEFAULT 1,                  -- 是否无头模式
    user_data_dir TEXT,                          -- 用户数据目录
    viewport_width INTEGER DEFAULT 1920,         -- 视口宽度
    viewport_height INTEGER DEFAULT 1080,        -- 视口高度
    user_agent TEXT,                             -- 自定义User-Agent
    proxy_config_id INTEGER,                     -- 关联的代理配置ID
    extra_args TEXT,                             -- 额外启动参数（JSON格式）
    is_default INTEGER DEFAULT 0,                -- 是否为默认配置
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proxy_config_id) REFERENCES proxy_configs(id)
)
''')

# 4. 创建代理IP池表
cursor.execute('''
CREATE TABLE IF NOT EXISTS proxy_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proxy_name TEXT NOT NULL,                    -- 代理名称
    proxy_type TEXT NOT NULL,                    -- 代理类型 (http/https/socks5)
    proxy_host TEXT NOT NULL,                    -- 代理服务器地址
    proxy_port INTEGER NOT NULL,                 -- 代理端口
    proxy_username TEXT,                         -- 代理用户名
    proxy_password TEXT,                         -- 代理密码
    country TEXT,                                -- 国家/地区
    provider TEXT,                               -- 代理提供商
    is_active INTEGER DEFAULT 1,                 -- 是否激活
    priority INTEGER DEFAULT 0,                  -- 优先级（数字越大越优先）
    max_concurrent_use INTEGER DEFAULT 1,        -- 最大并发使用数
    current_use_count INTEGER DEFAULT 0,         -- 当前使用数
    total_success_count INTEGER DEFAULT 0,       -- 总成功次数
    total_fail_count INTEGER DEFAULT 0,          -- 总失败次数
    last_used_at DATETIME,                       -- 最后使用时间
    cooldown_minutes INTEGER DEFAULT 30,         -- 冷却时间（分钟）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 5. 创建代理使用记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS proxy_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proxy_id INTEGER NOT NULL,                   -- 代理ID
    account_id INTEGER,                          -- 使用的账号ID
    task_id INTEGER,                             -- 关联的任务ID
    platform_type INTEGER,                       -- 平台类型
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    status INTEGER DEFAULT 0,                    -- 状态 (0:使用中 1:成功 2:失败)
    error_message TEXT,                          -- 错误信息
    FOREIGN KEY (proxy_id) REFERENCES proxy_configs(id),
    FOREIGN KEY (account_id) REFERENCES user_info(id)
)
''')

# 6. 创建IP切换调度表
cursor.execute('''
CREATE TABLE IF NOT EXISTS ip_switch_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,                 -- 账号ID
    current_proxy_id INTEGER,                    -- 当前使用的代理ID
    next_switch_time DATETIME,                   -- 下次切换时间
    switch_interval_minutes INTEGER DEFAULT 60,  -- 切换间隔（分钟）
    auto_switch_enabled INTEGER DEFAULT 1,       -- 是否启用自动切换
    last_switch_time DATETIME,                   -- 上次切换时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES user_info(id),
    FOREIGN KEY (current_proxy_id) REFERENCES proxy_configs(id)
)
''')

# 7. 创建账号-平台关联表（用于矩阵投放账号分组）
cursor.execute('''
CREATE TABLE IF NOT EXISTS account_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,                    -- 分组名称
    platform_type INTEGER NOT NULL,              -- 平台类型
    account_ids TEXT NOT NULL,                   -- 账号ID列表（JSON格式）
    description TEXT,                            -- 分组描述
    is_active INTEGER DEFAULT 1,                 -- 是否激活
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 8. 创建Cookie自动管理表
cursor.execute('''
CREATE TABLE IF NOT EXISTS cookie_management (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,                 -- 账号ID
    cookie_path TEXT NOT NULL,                   -- Cookie文件路径
    last_refresh_time DATETIME,                  -- 最后刷新时间
    next_refresh_time DATETIME,                  -- 下次刷新时间
    auto_refresh_enabled INTEGER DEFAULT 1,      -- 是否启用自动刷新
    refresh_interval_hours INTEGER DEFAULT 24,   -- 刷新间隔（小时）
    cookie_valid INTEGER DEFAULT 1,              -- Cookie是否有效
    validation_message TEXT,                     -- 验证信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES user_info(id)
)
''')

# 9. 创建系统配置表
cursor.execute('''
CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,             -- 配置键
    config_value TEXT,                           -- 配置值
    config_type TEXT DEFAULT 'string',           -- 配置类型 (string/int/bool/json)
    description TEXT,                            -- 配置描述
    is_encrypted INTEGER DEFAULT 0,              -- 是否加密存储
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 10. 插入默认系统配置
default_configs = [
    ('browser_auto_manage', 'true', 'bool', '是否自动管理浏览器配置', 0),
    ('cookie_auto_refresh', 'true', 'bool', '是否启用Cookie自动刷新', 0),
    ('ip_auto_switch', 'true', 'bool', '是否启用IP自动切换', 0),
    ('max_retry_count', '3', 'int', '最大重试次数', 0),
    ('task_concurrent_limit', '5', 'int', '并发任务限制', 0),
    ('default_cooldown_minutes', '30', 'int', '默认IP冷却时间（分钟）', 0),
    ('default_switch_interval', '60', 'int', '默认IP切换间隔（分钟）', 0),
]

for config in default_configs:
    cursor.execute('''
        INSERT OR IGNORE INTO system_configs (config_key, config_value, config_type, description, is_encrypted)
        VALUES (?, ?, ?, ?, ?)
    ''', config)

# 提交更改
conn.commit()
print("✅ 增强功能数据表创建成功！")
print("📋 创建的表包括：")
print("  1. matrix_tasks - 矩阵投放任务表")
print("  2. matrix_subtasks - 矩阵投放子任务表")
print("  3. browser_configs - 浏览器配置表")
print("  4. proxy_configs - 代理IP池表")
print("  5. proxy_usage_logs - 代理使用记录表")
print("  6. ip_switch_schedule - IP切换调度表")
print("  7. account_groups - 账号分组表")
print("  8. cookie_management - Cookie管理表")
print("  9. system_configs - 系统配置表")

# 关闭连接
conn.close()
