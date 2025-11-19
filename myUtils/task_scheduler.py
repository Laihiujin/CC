"""
定时任务调度器
负责执行矩阵投放任务、自动切换IP、自动刷新Cookie等定时任务
"""
import asyncio
import threading
import time
from datetime import datetime
from typing import Optional
from pathlib import Path

from conf import BASE_DIR
from myUtils.matrix_distribution import MatrixDistributor
from myUtils.proxy_manager import ProxyManager, IPSwitchScheduler
from myUtils.browser_manager import CookieManager
from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.matrix_distributor = MatrixDistributor()
        self.proxy_manager = ProxyManager()
        self.ip_switch_scheduler = IPSwitchScheduler()
        self.cookie_manager = CookieManager()
        
        self.running = False
        self.thread = None
    
    def start(self):
        """启动调度器"""
        if self.running:
            print("⚠️ 调度器已经在运行中")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("✅ 任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 任务调度器已停止")
    
    def _run_scheduler(self):
        """运行调度器主循环"""
        last_ip_switch_check = 0
        last_matrix_task_check = 0
        last_cookie_refresh_check = 0
        
        # 检查间隔（秒）
        IP_SWITCH_INTERVAL = 60  # 每分钟检查一次IP切换
        MATRIX_TASK_INTERVAL = 30  # 每30秒检查一次矩阵任务
        COOKIE_REFRESH_INTERVAL = 300  # 每5分钟检查一次Cookie刷新
        
        while self.running:
            try:
                current_time = time.time()
                
                # 检查并执行IP自动切换
                if current_time - last_ip_switch_check >= IP_SWITCH_INTERVAL:
                    self._auto_switch_ips()
                    last_ip_switch_check = current_time
                
                # 检查并执行矩阵投放任务
                if current_time - last_matrix_task_check >= MATRIX_TASK_INTERVAL:
                    self._execute_pending_matrix_tasks()
                    last_matrix_task_check = current_time
                
                # 检查Cookie刷新（仅提示，不自动执行）
                if current_time - last_cookie_refresh_check >= COOKIE_REFRESH_INTERVAL:
                    self._check_cookie_refresh()
                    last_cookie_refresh_check = current_time
                
                # 休眠一段时间
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ 调度器执行出错: {e}")
                time.sleep(10)
    
    def _auto_switch_ips(self):
        """自动切换IP"""
        try:
            results = self.ip_switch_scheduler.auto_switch_all_due_accounts()
            
            if results:
                success_count = sum(1 for r in results if r['success'])
                print(f"🔄 自动切换IP: {success_count}/{len(results)} 个账号切换成功")
                
                for result in results:
                    if not result['success']:
                        print(f"⚠️ 账号 {result['account_id']} IP切换失败")
        except Exception as e:
            print(f"❌ 自动切换IP失败: {e}")
    
    def _execute_pending_matrix_tasks(self):
        """执行待处理的矩阵投放子任务"""
        try:
            # 获取待执行的子任务（限制一次最多执行5个）
            subtasks = self.matrix_distributor.get_pending_subtasks(limit=5)
            
            if not subtasks:
                return
            
            print(f"📋 发现 {len(subtasks)} 个待执行的矩阵投放子任务")
            
            for subtask in subtasks:
                try:
                    self._execute_subtask(subtask)
                except Exception as e:
                    print(f"❌ 执行子任务 {subtask['id']} 失败: {e}")
                    self.matrix_distributor.update_subtask_status(
                        subtask['id'],
                        status=3,  # 失败
                        error_message=str(e)
                    )
        except Exception as e:
            print(f"❌ 执行矩阵投放任务失败: {e}")
    
    def _execute_subtask(self, subtask):
        """执行单个子任务"""
        subtask_id = subtask['id']
        account_id = subtask['account_id']
        platform_type = subtask['platform_type']
        
        print(f"▶️ 开始执行子任务 {subtask_id} (账号:{account_id}, 平台:{platform_type})")
        
        # 更新状态为执行中
        self.matrix_distributor.update_subtask_status(subtask_id, status=1)
        
        try:
            # 检查是否需要切换IP
            current_proxy = self.ip_switch_scheduler.get_account_current_proxy(account_id)
            if current_proxy:
                print(f"  使用代理: {current_proxy['proxy_name']}")
            
            # 准备文件路径
            account_file = [subtask['account_file_path']]
            video_file = [subtask['video_file_path']]
            title = subtask['title']
            tags = subtask['tags']
            category = subtask['category']
            
            # 根据平台类型调用对应的上传函数
            if platform_type == 1:  # 小红书
                post_video_xhs(title, video_file, tags, account_file, category, False, 1, None, 0)
            elif platform_type == 2:  # 视频号
                post_video_tencent(title, video_file, tags, account_file, category, False, 1, None, 0)
            elif platform_type == 3:  # 抖音
                post_video_DouYin(title, video_file, tags, account_file, category, False, 1, None, 0)
            elif platform_type == 4:  # 快手
                post_video_ks(title, video_file, tags, account_file, category, False, 1, None, 0)
            else:
                raise ValueError(f"不支持的平台类型: {platform_type}")
            
            # 更新状态为成功
            self.matrix_distributor.update_subtask_status(subtask_id, status=2)
            print(f"✅ 子任务 {subtask_id} 执行成功")
            
            # 检查任务是否全部完成
            self._check_task_completion(subtask['task_id'])
            
        except Exception as e:
            print(f"❌ 子任务 {subtask_id} 执行失败: {e}")
            self.matrix_distributor.update_subtask_status(
                subtask_id,
                status=3,
                error_message=str(e)
            )
    
    def _check_task_completion(self, task_id):
        """检查任务是否全部完成"""
        stats = self.matrix_distributor.get_task_statistics(task_id)
        
        if stats['pending'] == 0 and stats['running'] == 0:
            # 所有子任务都已完成
            if stats['failed'] == 0:
                # 全部成功
                self.matrix_distributor.update_task_status(task_id, status=2)
                print(f"🎉 任务 {task_id} 全部完成！成功: {stats['success']}")
            else:
                # 有失败的
                self.matrix_distributor.update_task_status(task_id, status=3)
                print(f"⚠️ 任务 {task_id} 完成，但有失败项。成功: {stats['success']}, 失败: {stats['failed']}")
    
    def _check_cookie_refresh(self):
        """检查需要刷新的Cookie"""
        try:
            accounts = self.cookie_manager.get_accounts_need_refresh()
            
            if accounts:
                print(f"⚠️ 发现 {len(accounts)} 个账号的Cookie需要刷新")
                for account in accounts:
                    print(f"  - 账号ID: {account['account_id']}, 用户名: {account['userName']}")
        except Exception as e:
            print(f"❌ 检查Cookie刷新失败: {e}")


# 全局调度器实例
_scheduler_instance: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance


def start_scheduler():
    """启动全局调度器"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """停止全局调度器"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
