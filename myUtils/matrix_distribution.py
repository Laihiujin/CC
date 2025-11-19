"""
矩阵投放功能模块
实现素材一键分配到同平台不同账号的功能
"""
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from conf import BASE_DIR


class MatrixDistributor:
    """矩阵投放管理器"""
    
    def __init__(self):
        self.db_path = Path(BASE_DIR / "db" / "database.db")
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_matrix_task(
        self,
        task_name: str,
        platform_type: int,
        file_ids: List[int],
        account_ids: List[int],
        title: str,
        tags: str = "",
        category: Optional[int] = None,
        enable_timer: bool = False,
        videos_per_day: int = 1,
        daily_times: Optional[List[str]] = None,
        start_days: int = 0,
        **kwargs
    ) -> int:
        """
        创建矩阵投放任务
        
        Args:
            task_name: 任务名称
            platform_type: 平台类型 (1:小红书 2:视频号 3:抖音 4:快手)
            file_ids: 文件ID列表
            account_ids: 账号ID列表
            title: 视频标题
            tags: 标签
            category: 分类
            enable_timer: 是否启用定时
            videos_per_day: 每天发布视频数
            daily_times: 发布时间点列表
            start_days: 开始天数
        
        Returns:
            任务ID
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 插入主任务
            cursor.execute('''
                INSERT INTO matrix_tasks (
                    task_name, platform_type, file_ids, account_ids,
                    title, tags, category, enable_timer,
                    videos_per_day, daily_times, start_days, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                task_name,
                platform_type,
                json.dumps(file_ids),
                json.dumps(account_ids),
                title,
                tags,
                category,
                1 if enable_timer else 0,
                videos_per_day,
                json.dumps(daily_times) if daily_times else None,
                start_days
            ))
            
            task_id = cursor.lastrowid
            
            # 创建子任务：为每个账号分配素材
            self._create_subtasks(
                cursor, task_id, file_ids, account_ids,
                enable_timer, videos_per_day, daily_times, start_days
            )
            
            conn.commit()
            
        return task_id
    
    def _create_subtasks(
        self,
        cursor,
        task_id: int,
        file_ids: List[int],
        account_ids: List[int],
        enable_timer: bool,
        videos_per_day: int,
        daily_times: Optional[List[str]],
        start_days: int
    ):
        """创建子任务"""
        from utils.files_times import generate_schedule_time_next_day
        
        # 为每个账号分配所有素材
        for account_id in account_ids:
            # 生成定时发布时间
            if enable_timer and daily_times:
                scheduled_times = generate_schedule_time_next_day(
                    len(file_ids), videos_per_day, daily_times, start_days
                )
            else:
                scheduled_times = [None] * len(file_ids)
            
            # 为每个文件创建子任务
            for idx, file_id in enumerate(file_ids):
                scheduled_time = scheduled_times[idx]
                
                cursor.execute('''
                    INSERT INTO matrix_subtasks (
                        task_id, account_id, file_id, status, scheduled_time
                    )
                    VALUES (?, ?, ?, 0, ?)
                ''', (task_id, account_id, file_id, scheduled_time))
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取任务"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM matrix_tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        return None
    
    def get_all_tasks(self, status: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有任务"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            if status is not None:
                cursor.execute(
                    'SELECT * FROM matrix_tasks WHERE status = ? ORDER BY created_at DESC',
                    (status,)
                )
            else:
                cursor.execute('SELECT * FROM matrix_tasks ORDER BY created_at DESC')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_subtasks_by_task_id(self, task_id: int) -> List[Dict[str, Any]]:
        """获取任务的所有子任务"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT st.*, ui.userName, fr.filename
                FROM matrix_subtasks st
                LEFT JOIN user_info ui ON st.account_id = ui.id
                LEFT JOIN file_records fr ON st.file_id = fr.id
                WHERE st.task_id = ?
                ORDER BY st.scheduled_time ASC
            ''', (task_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_task_status(self, task_id: int, status: int):
        """更新任务状态"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if status == 2:  # 已完成
                update_data['completed_at'] = datetime.now().isoformat()
            
            cursor.execute(f'''
                UPDATE matrix_tasks
                SET status = ?, updated_at = ?
                {', completed_at = ?' if status == 2 else ''}
                WHERE id = ?
            ''', (
                status,
                update_data['updated_at'],
                *([update_data['completed_at']] if status == 2 else []),
                task_id
            ))
            
            conn.commit()
    
    def update_subtask_status(
        self,
        subtask_id: int,
        status: int,
        error_message: Optional[str] = None
    ):
        """更新子任务状态"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            if status == 1:  # 执行中
                cursor.execute('''
                    UPDATE matrix_subtasks
                    SET status = ?, executed_at = ?
                    WHERE id = ?
                ''', (status, now, subtask_id))
            elif status in [2, 3]:  # 成功或失败
                cursor.execute('''
                    UPDATE matrix_subtasks
                    SET status = ?, completed_at = ?, error_message = ?
                    WHERE id = ?
                ''', (status, now, error_message, subtask_id))
            
            conn.commit()
    
    def get_pending_subtasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取待执行的子任务"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT st.*, mt.platform_type, mt.title, mt.tags, mt.category,
                       ui.filePath as account_file_path,
                       fr.file_path as video_file_path
                FROM matrix_subtasks st
                JOIN matrix_tasks mt ON st.task_id = mt.id
                JOIN user_info ui ON st.account_id = ui.id
                JOIN file_records fr ON st.file_id = fr.id
                WHERE st.status = 0
                  AND (st.scheduled_time IS NULL OR st.scheduled_time <= ?)
                ORDER BY st.scheduled_time ASC
                LIMIT ?
            ''', (now, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务及其子任务"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 删除子任务
                cursor.execute('DELETE FROM matrix_subtasks WHERE task_id = ?', (task_id,))
                
                # 删除主任务
                cursor.execute('DELETE FROM matrix_tasks WHERE id = ?', (task_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"删除任务失败: {e}")
            return False
    
    def batch_distribute_to_platform_accounts(
        self,
        platform_type: int,
        file_ids: List[int],
        title: str,
        tags: str = "",
        **kwargs
    ) -> int:
        """
        将素材批量分配给同平台的所有账号
        
        Args:
            platform_type: 平台类型
            file_ids: 文件ID列表
            title: 标题
            tags: 标签
        
        Returns:
            任务ID
        """
        # 获取该平台的所有有效账号
        account_ids = self._get_accounts_by_platform(platform_type)
        
        if not account_ids:
            raise ValueError(f"平台 {platform_type} 没有可用账号")
        
        # 创建矩阵投放任务
        task_name = f"批量投放-平台{platform_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return self.create_matrix_task(
            task_name=task_name,
            platform_type=platform_type,
            file_ids=file_ids,
            account_ids=account_ids,
            title=title,
            tags=tags,
            **kwargs
        )
    
    def _get_accounts_by_platform(self, platform_type: int) -> List[int]:
        """获取指定平台的所有账号ID"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM user_info WHERE type = ? AND status = 1',
                (platform_type,)
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]
    
    def get_task_statistics(self, task_id: int) -> Dict[str, int]:
        """获取任务统计信息"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) as failed
                FROM matrix_subtasks
                WHERE task_id = ?
            ''', (task_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else {}


class AccountGroupManager:
    """账号分组管理器"""
    
    def __init__(self):
        self.db_path = Path(BASE_DIR / "db" / "database.db")
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_group(
        self,
        group_name: str,
        platform_type: int,
        account_ids: List[int],
        description: str = ""
    ) -> int:
        """创建账号分组"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO account_groups (
                    group_name, platform_type, account_ids, description
                )
                VALUES (?, ?, ?, ?)
            ''', (group_name, platform_type, json.dumps(account_ids), description))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """获取分组信息"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM account_groups WHERE id = ?', (group_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                result['account_ids'] = json.loads(result['account_ids'])
                return result
        return None
    
    def get_all_groups(self, platform_type: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有分组"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            if platform_type is not None:
                cursor.execute(
                    'SELECT * FROM account_groups WHERE platform_type = ? ORDER BY created_at DESC',
                    (platform_type,)
                )
            else:
                cursor.execute('SELECT * FROM account_groups ORDER BY created_at DESC')
            
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                data = dict(row)
                data['account_ids'] = json.loads(data['account_ids'])
                result.append(data)
            
            return result
    
    def update_group(
        self,
        group_id: int,
        group_name: Optional[str] = None,
        account_ids: Optional[List[int]] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        """更新分组信息"""
        updates = []
        params = []
        
        if group_name is not None:
            updates.append('group_name = ?')
            params.append(group_name)
        
        if account_ids is not None:
            updates.append('account_ids = ?')
            params.append(json.dumps(account_ids))
        
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(1 if is_active else 0)
        
        updates.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        
        params.append(group_id)
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE account_groups
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            conn.commit()
    
    def delete_group(self, group_id: int):
        """删除分组"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM account_groups WHERE id = ?', (group_id,))
            conn.commit()
