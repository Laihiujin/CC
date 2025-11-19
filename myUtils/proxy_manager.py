"""
代理IP管理和自动切换模块
防止同一IP地址批量投放视频被平台封禁
"""
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from conf import BASE_DIR


class ProxyManager:
    """代理IP管理器"""
    
    def __init__(self):
        self.db_path = Path(BASE_DIR / "db" / "database.db")
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_proxy(
        self,
        proxy_name: str,
        proxy_type: str,
        proxy_host: str,
        proxy_port: int,
        proxy_username: str = "",
        proxy_password: str = "",
        country: str = "",
        provider: str = "",
        priority: int = 0,
        max_concurrent_use: int = 1,
        cooldown_minutes: int = 30
    ) -> int:
        """
        添加代理配置
        
        Args:
            proxy_name: 代理名称
            proxy_type: 代理类型 (http/https/socks5)
            proxy_host: 代理服务器地址
            proxy_port: 代理端口
            proxy_username: 代理用户名
            proxy_password: 代理密码
            country: 国家/地区
            provider: 代理提供商
            priority: 优先级
            max_concurrent_use: 最大并发使用数
            cooldown_minutes: 冷却时间（分钟）
        
        Returns:
            代理ID
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO proxy_configs (
                    proxy_name, proxy_type, proxy_host, proxy_port,
                    proxy_username, proxy_password, country, provider,
                    priority, max_concurrent_use, cooldown_minutes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                proxy_name, proxy_type, proxy_host, proxy_port,
                proxy_username, proxy_password, country, provider,
                priority, max_concurrent_use, cooldown_minutes
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_proxy_by_id(self, proxy_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取代理配置"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM proxy_configs WHERE id = ?', (proxy_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        return None
    
    def get_all_proxies(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取所有代理配置"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            if is_active is not None:
                cursor.execute(
                    'SELECT * FROM proxy_configs WHERE is_active = ? ORDER BY priority DESC, id ASC',
                    (1 if is_active else 0,)
                )
            else:
                cursor.execute('SELECT * FROM proxy_configs ORDER BY priority DESC, id ASC')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_available_proxy(
        self,
        country: Optional[str] = None,
        exclude_ids: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取可用的代理
        
        Args:
            country: 指定国家/地区
            exclude_ids: 排除的代理ID列表
        
        Returns:
            可用的代理配置，如果没有可用代理则返回None
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now()
            
            # 构建查询条件
            conditions = ['is_active = 1', 'current_use_count < max_concurrent_use']
            params = []
            
            if country:
                conditions.append('country = ?')
                params.append(country)
            
            if exclude_ids:
                placeholders = ','.join('?' * len(exclude_ids))
                conditions.append(f'id NOT IN ({placeholders})')
                params.extend(exclude_ids)
            
            # 查询可用代理
            query = f'''
                SELECT * FROM proxy_configs
                WHERE {' AND '.join(conditions)}
                  AND (last_used_at IS NULL 
                       OR datetime(last_used_at, '+' || cooldown_minutes || ' minutes') <= ?)
                ORDER BY priority DESC, total_fail_count ASC, RANDOM()
                LIMIT 1
            '''
            params.append(now.isoformat())
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        return None
    
    def acquire_proxy(self, proxy_id: int, account_id: Optional[int] = None) -> bool:
        """
        获取代理使用权
        
        Args:
            proxy_id: 代理ID
            account_id: 账号ID
        
        Returns:
            是否成功获取
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 检查是否可用
                cursor.execute('''
                    SELECT current_use_count, max_concurrent_use
                    FROM proxy_configs
                    WHERE id = ? AND is_active = 1
                ''', (proxy_id,))
                
                row = cursor.fetchone()
                if not row or row['current_use_count'] >= row['max_concurrent_use']:
                    return False
                
                # 增加使用计数
                now = datetime.now().isoformat()
                cursor.execute('''
                    UPDATE proxy_configs
                    SET current_use_count = current_use_count + 1,
                        last_used_at = ?
                    WHERE id = ?
                ''', (now, proxy_id))
                
                # 记录使用日志
                cursor.execute('''
                    INSERT INTO proxy_usage_logs (
                        proxy_id, account_id, start_time, status
                    )
                    VALUES (?, ?, ?, 0)
                ''', (proxy_id, account_id, now))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"获取代理失败: {e}")
            return False
    
    def release_proxy(
        self,
        proxy_id: int,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        释放代理
        
        Args:
            proxy_id: 代理ID
            success: 是否成功
            error_message: 错误信息
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 减少使用计数
            if success:
                cursor.execute('''
                    UPDATE proxy_configs
                    SET current_use_count = MAX(0, current_use_count - 1),
                        total_success_count = total_success_count + 1
                    WHERE id = ?
                ''', (proxy_id,))
            else:
                cursor.execute('''
                    UPDATE proxy_configs
                    SET current_use_count = MAX(0, current_use_count - 1),
                        total_fail_count = total_fail_count + 1
                    WHERE id = ?
                ''', (proxy_id,))
            
            # 更新使用日志
            now = datetime.now().isoformat()
            status = 1 if success else 2
            
            cursor.execute('''
                UPDATE proxy_usage_logs
                SET end_time = ?, status = ?, error_message = ?
                WHERE proxy_id = ? AND status = 0
                ORDER BY start_time DESC
                LIMIT 1
            ''', (now, status, error_message, proxy_id))
            
            conn.commit()
    
    def update_proxy(
        self,
        proxy_id: int,
        **kwargs
    ):
        """更新代理配置"""
        allowed_fields = [
            'proxy_name', 'proxy_type', 'proxy_host', 'proxy_port',
            'proxy_username', 'proxy_password', 'country', 'provider',
            'is_active', 'priority', 'max_concurrent_use', 'cooldown_minutes'
        ]
        
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f'{field} = ?')
                params.append(value)
        
        if not updates:
            return
        
        updates.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.append(proxy_id)
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE proxy_configs
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            conn.commit()
    
    def delete_proxy(self, proxy_id: int):
        """删除代理配置"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM proxy_configs WHERE id = ?', (proxy_id,))
            conn.commit()
    
    def get_proxy_statistics(self, proxy_id: int) -> Dict[str, Any]:
        """获取代理统计信息"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 获取基本信息
            cursor.execute('SELECT * FROM proxy_configs WHERE id = ?', (proxy_id,))
            proxy_info = dict(cursor.fetchone())
            
            # 获取使用记录统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_uses,
                    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as fail_count,
                    MAX(start_time) as last_used
                FROM proxy_usage_logs
                WHERE proxy_id = ?
            ''', (proxy_id,))
            
            stats = dict(cursor.fetchone())
            
            return {**proxy_info, **stats}
    
    def format_proxy_url(self, proxy_config: Dict[str, Any]) -> str:
        """
        格式化代理URL
        
        Args:
            proxy_config: 代理配置字典
        
        Returns:
            代理URL字符串，格式如: http://username:password@host:port
        """
        proxy_type = proxy_config['proxy_type']
        host = proxy_config['proxy_host']
        port = proxy_config['proxy_port']
        username = proxy_config.get('proxy_username', '')
        password = proxy_config.get('proxy_password', '')
        
        if username and password:
            return f"{proxy_type}://{username}:{password}@{host}:{port}"
        else:
            return f"{proxy_type}://{host}:{port}"


class IPSwitchScheduler:
    """IP切换调度器"""
    
    def __init__(self):
        self.db_path = Path(BASE_DIR / "db" / "database.db")
        self.proxy_manager = ProxyManager()
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_account_schedule(
        self,
        account_id: int,
        switch_interval_minutes: int = 60,
        auto_switch_enabled: bool = True
    ) -> int:
        """
        初始化账号的IP切换调度
        
        Args:
            account_id: 账号ID
            switch_interval_minutes: 切换间隔（分钟）
            auto_switch_enabled: 是否启用自动切换
        
        Returns:
            调度ID
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                'SELECT id FROM ip_switch_schedule WHERE account_id = ?',
                (account_id,)
            )
            
            existing = cursor.fetchone()
            if existing:
                return existing['id']
            
            # 创建新调度
            next_switch_time = datetime.now() + timedelta(minutes=switch_interval_minutes)
            
            cursor.execute('''
                INSERT INTO ip_switch_schedule (
                    account_id, switch_interval_minutes,
                    auto_switch_enabled, next_switch_time
                )
                VALUES (?, ?, ?, ?)
            ''', (
                account_id,
                switch_interval_minutes,
                1 if auto_switch_enabled else 0,
                next_switch_time.isoformat()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_account_current_proxy(self, account_id: int) -> Optional[Dict[str, Any]]:
        """获取账号当前使用的代理"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT pc.*
                FROM ip_switch_schedule iss
                JOIN proxy_configs pc ON iss.current_proxy_id = pc.id
                WHERE iss.account_id = ?
            ''', (account_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def switch_proxy_for_account(
        self,
        account_id: int,
        country: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        为账号切换代理
        
        Args:
            account_id: 账号ID
            country: 指定国家/地区
        
        Returns:
            新的代理配置
        """
        # 获取当前代理
        current_proxy = self.get_account_current_proxy(account_id)
        current_proxy_id = current_proxy['id'] if current_proxy else None
        
        # 获取新的可用代理（排除当前代理）
        new_proxy = self.proxy_manager.get_available_proxy(
            country=country,
            exclude_ids=[current_proxy_id] if current_proxy_id else None
        )
        
        if not new_proxy:
            print(f"账号 {account_id} 没有可用的代理")
            return None
        
        # 更新调度记录
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now()
            
            cursor.execute('''
                SELECT switch_interval_minutes FROM ip_switch_schedule
                WHERE account_id = ?
            ''', (account_id,))
            
            schedule = cursor.fetchone()
            if not schedule:
                # 如果没有调度记录，先创建
                self.init_account_schedule(account_id)
                cursor.execute('''
                    SELECT switch_interval_minutes FROM ip_switch_schedule
                    WHERE account_id = ?
                ''', (account_id,))
                schedule = cursor.fetchone()
            
            interval = schedule['switch_interval_minutes']
            next_switch_time = now + timedelta(minutes=interval)
            
            cursor.execute('''
                UPDATE ip_switch_schedule
                SET current_proxy_id = ?,
                    last_switch_time = ?,
                    next_switch_time = ?,
                    updated_at = ?
                WHERE account_id = ?
            ''', (
                new_proxy['id'],
                now.isoformat(),
                next_switch_time.isoformat(),
                now.isoformat(),
                account_id
            ))
            
            conn.commit()
        
        print(f"账号 {account_id} 已切换到代理: {new_proxy['proxy_name']}")
        return new_proxy
    
    def get_accounts_need_switch(self) -> List[Dict[str, Any]]:
        """获取需要切换IP的账号列表"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT * FROM ip_switch_schedule
                WHERE auto_switch_enabled = 1
                  AND next_switch_time <= ?
            ''', (now,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def auto_switch_all_due_accounts(self):
        """自动切换所有到期的账号IP"""
        accounts = self.get_accounts_need_switch()
        
        results = []
        for account in accounts:
            account_id = account['account_id']
            new_proxy = self.switch_proxy_for_account(account_id)
            
            results.append({
                'account_id': account_id,
                'success': new_proxy is not None,
                'new_proxy': new_proxy
            })
        
        return results
    
    def update_switch_interval(self, account_id: int, interval_minutes: int):
        """更新切换间隔"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now()
            next_switch_time = now + timedelta(minutes=interval_minutes)
            
            cursor.execute('''
                UPDATE ip_switch_schedule
                SET switch_interval_minutes = ?,
                    next_switch_time = ?,
                    updated_at = ?
                WHERE account_id = ?
            ''', (
                interval_minutes,
                next_switch_time.isoformat(),
                now.isoformat(),
                account_id
            ))
            
            conn.commit()
    
    def enable_auto_switch(self, account_id: int, enabled: bool = True):
        """启用/禁用自动切换"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE ip_switch_schedule
                SET auto_switch_enabled = ?,
                    updated_at = ?
                WHERE account_id = ?
            ''', (1 if enabled else 0, datetime.now().isoformat(), account_id))
            
            conn.commit()
