"""
浏览器配置管理模块
简化浏览器配置和Cookie管理
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from conf import BASE_DIR


class BrowserConfigManager:
    """浏览器配置管理器"""
    
    def __init__(self):
        self.db_path = Path(BASE_DIR / "db" / "database.db")
        self.cookie_base_dir = Path(BASE_DIR / "cookiesFile")
        self.cookie_base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_browser_config(
        self,
        config_name: str,
        browser_type: str = "chromium",
        browser_path: Optional[str] = None,
        headless: bool = True,
        user_data_dir: Optional[str] = None,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: Optional[str] = None,
        proxy_config_id: Optional[int] = None,
        extra_args: Optional[Dict[str, Any]] = None,
        is_default: bool = False
    ) -> int:
        """
        创建浏览器配置
        
        Args:
            config_name: 配置名称
            browser_type: 浏览器类型
            browser_path: 自定义浏览器路径
            headless: 是否无头模式
            user_data_dir: 用户数据目录
            viewport_width: 视口宽度
            viewport_height: 视口高度
            user_agent: 自定义User-Agent
            proxy_config_id: 关联的代理配置ID
            extra_args: 额外启动参数
            is_default: 是否为默认配置
        
        Returns:
            配置ID
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 如果设置为默认，先取消其他默认配置
            if is_default:
                cursor.execute('''
                    UPDATE browser_configs SET is_default = 0
                ''')
            
            cursor.execute('''
                INSERT INTO browser_configs (
                    config_name, browser_type, browser_path, headless,
                    user_data_dir, viewport_width, viewport_height,
                    user_agent, proxy_config_id, extra_args, is_default
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config_name, browser_type, browser_path, 1 if headless else 0,
                user_data_dir, viewport_width, viewport_height,
                user_agent, proxy_config_id,
                json.dumps(extra_args) if extra_args else None,
                1 if is_default else 0
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_config_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取配置"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM browser_configs WHERE id = ?', (config_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                if result.get('extra_args'):
                    result['extra_args'] = json.loads(result['extra_args'])
                return result
        return None
    
    def get_default_config(self) -> Optional[Dict[str, Any]]:
        """获取默认配置"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM browser_configs WHERE is_default = 1 LIMIT 1')
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                if result.get('extra_args'):
                    result['extra_args'] = json.loads(result['extra_args'])
                return result
        return None
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有配置"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM browser_configs ORDER BY is_default DESC, created_at DESC')
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                data = dict(row)
                if data.get('extra_args'):
                    data['extra_args'] = json.loads(data['extra_args'])
                result.append(data)
            
            return result
    
    def update_config(self, config_id: int, **kwargs):
        """更新配置"""
        allowed_fields = [
            'config_name', 'browser_type', 'browser_path', 'headless',
            'user_data_dir', 'viewport_width', 'viewport_height',
            'user_agent', 'proxy_config_id', 'extra_args', 'is_default'
        ]
        
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'extra_args' and value is not None:
                    value = json.dumps(value)
                elif field in ['headless', 'is_default']:
                    value = 1 if value else 0
                
                updates.append(f'{field} = ?')
                params.append(value)
        
        if not updates:
            return
        
        # 如果设置为默认，先取消其他默认配置
        if kwargs.get('is_default'):
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE browser_configs SET is_default = 0')
                conn.commit()
        
        updates.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.append(config_id)
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE browser_configs
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            conn.commit()
    
    def delete_config(self, config_id: int):
        """删除配置"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM browser_configs WHERE id = ?', (config_id,))
            conn.commit()
    
    def build_playwright_config(
        self,
        config_id: Optional[int] = None,
        proxy_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建Playwright浏览器启动配置
        
        Args:
            config_id: 配置ID，如果为None则使用默认配置
            proxy_override: 代理覆盖配置
        
        Returns:
            Playwright配置字典
        """
        if config_id:
            config = self.get_config_by_id(config_id)
        else:
            config = self.get_default_config()
        
        if not config:
            # 返回默认配置
            return {
                'headless': True,
                'viewport': {'width': 1920, 'height': 1080}
            }
        
        playwright_config = {
            'headless': bool(config['headless']),
            'viewport': {
                'width': config['viewport_width'],
                'height': config['viewport_height']
            }
        }
        
        if config.get('browser_path'):
            playwright_config['executable_path'] = config['browser_path']
        
        if config.get('user_data_dir'):
            playwright_config['user_data_dir'] = config['user_data_dir']
        
        if config.get('user_agent'):
            playwright_config['user_agent'] = config['user_agent']
        
        # 处理代理配置
        if proxy_override:
            playwright_config['proxy'] = proxy_override
        elif config.get('proxy_config_id'):
            # 从代理配置表获取代理信息
            from myUtils.proxy_manager import ProxyManager
            proxy_manager = ProxyManager()
            proxy_config = proxy_manager.get_proxy_by_id(config['proxy_config_id'])
            
            if proxy_config:
                proxy_url = proxy_manager.format_proxy_url(proxy_config)
                playwright_config['proxy'] = {'server': proxy_url}
        
        # 额外参数
        if config.get('extra_args'):
            playwright_config.update(config['extra_args'])
        
        return playwright_config


class CookieManager:
    """Cookie管理器"""
    
    def __init__(self):
        self.db_path = Path(BASE_DIR / "db" / "database.db")
        self.cookie_base_dir = Path(BASE_DIR / "cookiesFile")
        self.cookie_base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def auto_create_cookie_path(
        self,
        account_id: int,
        platform_type: int,
        username: str
    ) -> str:
        """
        自动创建Cookie文件路径
        
        Args:
            account_id: 账号ID
            platform_type: 平台类型
            username: 用户名
        
        Returns:
            Cookie文件相对路径
        """
        platform_names = {
            1: "xiaohongshu",
            2: "tencent",
            3: "douyin",
            4: "kuaishou",
            5: "bilibili",
            6: "baijiahao",
            7: "tiktok"
        }
        
        platform_name = platform_names.get(platform_type, f"platform_{platform_type}")
        
        # 创建平台目录
        platform_dir = self.cookie_base_dir / f"{platform_name}_uploader"
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # Cookie文件名：username_accountid.json
        cookie_filename = f"{username}_{account_id}.json"
        cookie_path = platform_dir / cookie_filename
        
        # 如果文件不存在，创建空的JSON文件
        if not cookie_path.exists():
            cookie_path.write_text('{}')
        
        # 返回相对路径
        return str(cookie_path.relative_to(self.cookie_base_dir))
    
    def init_cookie_management(
        self,
        account_id: int,
        cookie_path: str,
        auto_refresh_enabled: bool = True,
        refresh_interval_hours: int = 24
    ) -> int:
        """
        初始化Cookie管理
        
        Args:
            account_id: 账号ID
            cookie_path: Cookie文件路径
            auto_refresh_enabled: 是否启用自动刷新
            refresh_interval_hours: 刷新间隔（小时）
        
        Returns:
            管理记录ID
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                'SELECT id FROM cookie_management WHERE account_id = ?',
                (account_id,)
            )
            
            existing = cursor.fetchone()
            if existing:
                return existing['id']
            
            now = datetime.now()
            next_refresh = now + timedelta(hours=refresh_interval_hours)
            
            cursor.execute('''
                INSERT INTO cookie_management (
                    account_id, cookie_path, last_refresh_time,
                    next_refresh_time, auto_refresh_enabled,
                    refresh_interval_hours
                )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                account_id, cookie_path, now.isoformat(),
                next_refresh.isoformat(),
                1 if auto_refresh_enabled else 0,
                refresh_interval_hours
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def update_cookie_validity(
        self,
        account_id: int,
        is_valid: bool,
        validation_message: Optional[str] = None
    ):
        """
        更新Cookie有效性
        
        Args:
            account_id: 账号ID
            is_valid: 是否有效
            validation_message: 验证信息
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE cookie_management
                SET cookie_valid = ?,
                    validation_message = ?,
                    updated_at = ?
                WHERE account_id = ?
            ''', (
                1 if is_valid else 0,
                validation_message,
                datetime.now().isoformat(),
                account_id
            ))
            
            conn.commit()
    
    def mark_cookie_refreshed(self, account_id: int):
        """标记Cookie已刷新"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT refresh_interval_hours FROM cookie_management
                WHERE account_id = ?
            ''', (account_id,))
            
            row = cursor.fetchone()
            if not row:
                return
            
            now = datetime.now()
            next_refresh = now + timedelta(hours=row['refresh_interval_hours'])
            
            cursor.execute('''
                UPDATE cookie_management
                SET last_refresh_time = ?,
                    next_refresh_time = ?,
                    cookie_valid = 1,
                    updated_at = ?
                WHERE account_id = ?
            ''', (
                now.isoformat(),
                next_refresh.isoformat(),
                now.isoformat(),
                account_id
            ))
            
            conn.commit()
    
    def get_accounts_need_refresh(self) -> List[Dict[str, Any]]:
        """获取需要刷新Cookie的账号列表"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT cm.*, ui.userName, ui.type as platform_type
                FROM cookie_management cm
                JOIN user_info ui ON cm.account_id = ui.id
                WHERE cm.auto_refresh_enabled = 1
                  AND (cm.next_refresh_time <= ? OR cm.cookie_valid = 0)
            ''', (now,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_cookie_path(self, account_id: int) -> Optional[str]:
        """获取账号的Cookie文件路径"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cookie_path FROM cookie_management
                WHERE account_id = ?
            ''', (account_id,))
            
            row = cursor.fetchone()
            if row:
                return str(self.cookie_base_dir / row['cookie_path'])
        
        return None
    
    def update_refresh_interval(self, account_id: int, interval_hours: int):
        """更新刷新间隔"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now()
            next_refresh = now + timedelta(hours=interval_hours)
            
            cursor.execute('''
                UPDATE cookie_management
                SET refresh_interval_hours = ?,
                    next_refresh_time = ?,
                    updated_at = ?
                WHERE account_id = ?
            ''', (
                interval_hours,
                next_refresh.isoformat(),
                now.isoformat(),
                account_id
            ))
            
            conn.commit()
    
    def enable_auto_refresh(self, account_id: int, enabled: bool = True):
        """启用/禁用自动刷新"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE cookie_management
                SET auto_refresh_enabled = ?,
                    updated_at = ?
                WHERE account_id = ?
            ''', (1 if enabled else 0, datetime.now().isoformat(), account_id))
            
            conn.commit()
