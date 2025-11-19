"""
增强功能使用示例
演示如何使用矩阵投放、IP管理等功能
"""
import requests
import json
from typing import List

# API基础URL
BASE_URL = "http://localhost:5409/api/enhanced"


class EnhancedAPIClient:
    """增强功能API客户端"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    # ==================== 矩阵投放相关 ====================
    
    def batch_distribute(self, platform_type: int, file_ids: List[int], title: str, **kwargs):
        """一键分配素材到同平台所有账号"""
        url = f"{self.base_url}/matrix/tasks/batch-distribute"
        data = {
            "platform_type": platform_type,
            "file_ids": file_ids,
            "title": title,
            **kwargs
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def create_matrix_task(self, task_name: str, platform_type: int, 
                          file_ids: List[int], account_ids: List[int], 
                          title: str, **kwargs):
        """创建自定义矩阵投放任务"""
        url = f"{self.base_url}/matrix/tasks"
        data = {
            "task_name": task_name,
            "platform_type": platform_type,
            "file_ids": file_ids,
            "account_ids": account_ids,
            "title": title,
            **kwargs
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def get_tasks(self, status=None):
        """获取任务列表"""
        url = f"{self.base_url}/matrix/tasks"
        params = {"status": status} if status is not None else {}
        response = requests.get(url, params=params)
        return response.json()
    
    def get_task_detail(self, task_id: int):
        """获取任务详情"""
        url = f"{self.base_url}/matrix/tasks/{task_id}"
        response = requests.get(url)
        return response.json()
    
    # ==================== 代理管理相关 ====================
    
    def add_proxy(self, proxy_name: str, proxy_type: str, 
                 proxy_host: str, proxy_port: int, **kwargs):
        """添加代理"""
        url = f"{self.base_url}/proxies"
        data = {
            "proxy_name": proxy_name,
            "proxy_type": proxy_type,
            "proxy_host": proxy_host,
            "proxy_port": proxy_port,
            **kwargs
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def get_proxies(self, is_active=None):
        """获取代理列表"""
        url = f"{self.base_url}/proxies"
        params = {"is_active": str(is_active).lower()} if is_active is not None else {}
        response = requests.get(url, params=params)
        return response.json()
    
    # ==================== IP切换相关 ====================
    
    def init_ip_switch(self, account_id: int, switch_interval_minutes: int = 60):
        """初始化IP切换"""
        url = f"{self.base_url}/ip-switch/init"
        data = {
            "account_id": account_id,
            "switch_interval_minutes": switch_interval_minutes,
            "auto_switch_enabled": True
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def switch_ip(self, account_id: int, country=None):
        """手动切换IP"""
        url = f"{self.base_url}/ip-switch/switch"
        data = {"account_id": account_id}
        if country:
            data["country"] = country
        response = requests.post(url, json=data)
        return response.json()
    
    def get_current_proxy(self, account_id: int):
        """获取当前代理"""
        url = f"{self.base_url}/ip-switch/current-proxy/{account_id}"
        response = requests.get(url)
        return response.json()
    
    # ==================== 账号分组相关 ====================
    
    def create_group(self, group_name: str, platform_type: int, 
                    account_ids: List[int], description: str = ""):
        """创建账号分组"""
        url = f"{self.base_url}/account-groups"
        data = {
            "group_name": group_name,
            "platform_type": platform_type,
            "account_ids": account_ids,
            "description": description
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def get_groups(self, platform_type=None):
        """获取分组列表"""
        url = f"{self.base_url}/account-groups"
        params = {"platform_type": platform_type} if platform_type else {}
        response = requests.get(url, params=params)
        return response.json()
    
    # ==================== Cookie管理相关 ====================
    
    def auto_create_cookie_path(self, account_id: int, platform_type: int, username: str):
        """自动创建Cookie路径"""
        url = f"{self.base_url}/cookies/auto-create-path"
        data = {
            "account_id": account_id,
            "platform_type": platform_type,
            "username": username
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def init_cookie_management(self, account_id: int, cookie_path: str):
        """初始化Cookie管理"""
        url = f"{self.base_url}/cookies/init-management"
        data = {
            "account_id": account_id,
            "cookie_path": cookie_path,
            "auto_refresh_enabled": True,
            "refresh_interval_hours": 24
        }
        response = requests.post(url, json=data)
        return response.json()


def example_1_batch_distribute():
    """示例1: 批量分配素材到平台所有账号"""
    print("\n" + "="*60)
    print("示例1: 批量分配素材到平台所有账号")
    print("="*60)
    
    client = EnhancedAPIClient()
    
    # 假设已有文件ID为 1, 2, 3
    file_ids = [1, 2, 3]
    platform_type = 3  # 抖音
    
    result = client.batch_distribute(
        platform_type=platform_type,
        file_ids=file_ids,
        title="精彩视频合集",
        tags="#热门 #推荐",
        enable_timer=True,
        videos_per_day=2,
        daily_times=["09:00", "18:00"],
        start_days=0
    )
    
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result['code'] == 200:
        task_id = result['data']['task_id']
        print(f"\n✅ 任务创建成功，任务ID: {task_id}")
        
        # 查看任务详情
        detail = client.get_task_detail(task_id)
        print(f"任务详情: {json.dumps(detail, indent=2, ensure_ascii=False)}")


def example_2_proxy_management():
    """示例2: 代理IP管理"""
    print("\n" + "="*60)
    print("示例2: 代理IP管理")
    print("="*60)
    
    client = EnhancedAPIClient()
    
    # 1. 添加代理
    proxy_result = client.add_proxy(
        proxy_name="测试代理1",
        proxy_type="http",
        proxy_host="127.0.0.1",
        proxy_port=8080,
        country="CN",
        priority=10,
        cooldown_minutes=30
    )
    
    print(f"添加代理结果: {json.dumps(proxy_result, indent=2, ensure_ascii=False)}")
    
    if proxy_result['code'] == 200:
        # 2. 获取代理列表
        proxies = client.get_proxies(is_active=True)
        print(f"\n代理列表: {json.dumps(proxies, indent=2, ensure_ascii=False)}")


def example_3_ip_auto_switch():
    """示例3: 自动切换IP"""
    print("\n" + "="*60)
    print("示例3: 自动切换IP")
    print("="*60)
    
    client = EnhancedAPIClient()
    
    account_id = 1
    
    # 1. 初始化IP切换
    init_result = client.init_ip_switch(
        account_id=account_id,
        switch_interval_minutes=60
    )
    print(f"初始化结果: {json.dumps(init_result, indent=2, ensure_ascii=False)}")
    
    # 2. 手动切换IP
    switch_result = client.switch_ip(account_id)
    print(f"\n切换IP结果: {json.dumps(switch_result, indent=2, ensure_ascii=False)}")
    
    # 3. 查看当前代理
    current_proxy = client.get_current_proxy(account_id)
    print(f"\n当前代理: {json.dumps(current_proxy, indent=2, ensure_ascii=False)}")


def example_4_account_groups():
    """示例4: 账号分组管理"""
    print("\n" + "="*60)
    print("示例4: 账号分组管理")
    print("="*60)
    
    client = EnhancedAPIClient()
    
    # 创建分组
    group_result = client.create_group(
        group_name="抖音矩阵A组",
        platform_type=3,
        account_ids=[1, 2, 3, 4, 5],
        description="抖音矩阵账号第一组，主要用于测试"
    )
    
    print(f"创建分组结果: {json.dumps(group_result, indent=2, ensure_ascii=False)}")
    
    # 获取分组列表
    groups = client.get_groups(platform_type=3)
    print(f"\n分组列表: {json.dumps(groups, indent=2, ensure_ascii=False)}")


def example_5_cookie_management():
    """示例5: Cookie管理"""
    print("\n" + "="*60)
    print("示例5: Cookie管理")
    print("="*60)
    
    client = EnhancedAPIClient()
    
    account_id = 1
    platform_type = 3
    username = "test_user"
    
    # 1. 自动创建Cookie路径
    path_result = client.auto_create_cookie_path(
        account_id=account_id,
        platform_type=platform_type,
        username=username
    )
    
    print(f"Cookie路径创建结果: {json.dumps(path_result, indent=2, ensure_ascii=False)}")
    
    if path_result['code'] == 200:
        cookie_path = path_result['data']['cookie_path']
        
        # 2. 初始化Cookie管理
        init_result = client.init_cookie_management(
            account_id=account_id,
            cookie_path=cookie_path
        )
        
        print(f"\nCookie管理初始化结果: {json.dumps(init_result, indent=2, ensure_ascii=False)}")


def main():
    """主函数"""
    print("="*60)
    print("增强功能使用示例")
    print("="*60)
    print("\n⚠️ 注意：运行这些示例前，请确保：")
    print("1. 后端服务已启动 (python sau_backend.py)")
    print("2. 数据库已初始化 (python deploy_enhanced.py)")
    print("3. 已有测试数据（账号、文件等）")
    print("\n按Enter键继续...")
    input()
    
    try:
        # 运行示例
        # example_1_batch_distribute()
        example_2_proxy_management()
        example_3_ip_auto_switch()
        example_4_account_groups()
        example_5_cookie_management()
        
        print("\n" + "="*60)
        print("✅ 所有示例执行完成")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败！请确保后端服务已启动")
        print("运行: python sau_backend.py")
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
