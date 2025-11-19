"""
增强功能API接口
包括矩阵投放、代理管理、浏览器配置等功能的API接口
"""
from flask import Blueprint, request, jsonify
from myUtils.matrix_distribution import MatrixDistributor, AccountGroupManager
from myUtils.proxy_manager import ProxyManager, IPSwitchScheduler
from myUtils.browser_manager import BrowserConfigManager, CookieManager

# 创建蓝图
enhanced_api = Blueprint('enhanced_api', __name__, url_prefix='/api/enhanced')

# 初始化管理器
matrix_distributor = MatrixDistributor()
account_group_manager = AccountGroupManager()
proxy_manager = ProxyManager()
ip_switch_scheduler = IPSwitchScheduler()
browser_config_manager = BrowserConfigManager()
cookie_manager = CookieManager()


# ==================== 矩阵投放相关API ====================

@enhanced_api.route('/matrix/tasks', methods=['POST'])
def create_matrix_task():
    """创建矩阵投放任务"""
    try:
        data = request.get_json()
        
        task_id = matrix_distributor.create_matrix_task(
            task_name=data['task_name'],
            platform_type=data['platform_type'],
            file_ids=data['file_ids'],
            account_ids=data['account_ids'],
            title=data['title'],
            tags=data.get('tags', ''),
            category=data.get('category'),
            enable_timer=data.get('enable_timer', False),
            videos_per_day=data.get('videos_per_day', 1),
            daily_times=data.get('daily_times'),
            start_days=data.get('start_days', 0)
        )
        
        return jsonify({
            "code": 200,
            "msg": "矩阵投放任务创建成功",
            "data": {"task_id": task_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"创建任务失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/matrix/tasks/batch-distribute', methods=['POST'])
def batch_distribute_to_platform():
    """将素材批量分配给同平台的所有账号"""
    try:
        data = request.get_json()
        
        task_id = matrix_distributor.batch_distribute_to_platform_accounts(
            platform_type=data['platform_type'],
            file_ids=data['file_ids'],
            title=data['title'],
            tags=data.get('tags', ''),
            category=data.get('category'),
            enable_timer=data.get('enable_timer', False),
            videos_per_day=data.get('videos_per_day', 1),
            daily_times=data.get('daily_times'),
            start_days=data.get('start_days', 0)
        )
        
        return jsonify({
            "code": 200,
            "msg": "批量分配成功",
            "data": {"task_id": task_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"批量分配失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/matrix/tasks', methods=['GET'])
def get_matrix_tasks():
    """获取矩阵投放任务列表"""
    try:
        status = request.args.get('status', type=int)
        tasks = matrix_distributor.get_all_tasks(status)
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": tasks
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取任务列表失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/matrix/tasks/<int:task_id>', methods=['GET'])
def get_matrix_task_detail(task_id):
    """获取任务详情"""
    try:
        task = matrix_distributor.get_task_by_id(task_id)
        if not task:
            return jsonify({
                "code": 404,
                "msg": "任务不存在",
                "data": None
            }), 404
        
        subtasks = matrix_distributor.get_subtasks_by_task_id(task_id)
        statistics = matrix_distributor.get_task_statistics(task_id)
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": {
                "task": task,
                "subtasks": subtasks,
                "statistics": statistics
            }
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取任务详情失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/matrix/tasks/<int:task_id>', methods=['DELETE'])
def delete_matrix_task(task_id):
    """删除任务"""
    try:
        success = matrix_distributor.delete_task(task_id)
        
        if success:
            return jsonify({
                "code": 200,
                "msg": "删除成功",
                "data": None
            }), 200
        else:
            return jsonify({
                "code": 500,
                "msg": "删除失败",
                "data": None
            }), 500
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"删除任务失败: {str(e)}",
            "data": None
        }), 500


# ==================== 账号分组相关API ====================

@enhanced_api.route('/account-groups', methods=['POST'])
def create_account_group():
    """创建账号分组"""
    try:
        data = request.get_json()
        
        group_id = account_group_manager.create_group(
            group_name=data['group_name'],
            platform_type=data['platform_type'],
            account_ids=data['account_ids'],
            description=data.get('description', '')
        )
        
        return jsonify({
            "code": 200,
            "msg": "分组创建成功",
            "data": {"group_id": group_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"创建分组失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/account-groups', methods=['GET'])
def get_account_groups():
    """获取账号分组列表"""
    try:
        platform_type = request.args.get('platform_type', type=int)
        groups = account_group_manager.get_all_groups(platform_type)
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": groups
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取分组列表失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/account-groups/<int:group_id>', methods=['PUT'])
def update_account_group(group_id):
    """更新账号分组"""
    try:
        data = request.get_json()
        
        account_group_manager.update_group(
            group_id=group_id,
            group_name=data.get('group_name'),
            account_ids=data.get('account_ids'),
            description=data.get('description'),
            is_active=data.get('is_active')
        )
        
        return jsonify({
            "code": 200,
            "msg": "更新成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"更新分组失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/account-groups/<int:group_id>', methods=['DELETE'])
def delete_account_group(group_id):
    """删除账号分组"""
    try:
        account_group_manager.delete_group(group_id)
        
        return jsonify({
            "code": 200,
            "msg": "删除成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"删除分组失败: {str(e)}",
            "data": None
        }), 500


# ==================== 代理管理相关API ====================

@enhanced_api.route('/proxies', methods=['POST'])
def add_proxy():
    """添加代理配置"""
    try:
        data = request.get_json()
        
        proxy_id = proxy_manager.add_proxy(
            proxy_name=data['proxy_name'],
            proxy_type=data['proxy_type'],
            proxy_host=data['proxy_host'],
            proxy_port=data['proxy_port'],
            proxy_username=data.get('proxy_username', ''),
            proxy_password=data.get('proxy_password', ''),
            country=data.get('country', ''),
            provider=data.get('provider', ''),
            priority=data.get('priority', 0),
            max_concurrent_use=data.get('max_concurrent_use', 1),
            cooldown_minutes=data.get('cooldown_minutes', 30)
        )
        
        return jsonify({
            "code": 200,
            "msg": "代理添加成功",
            "data": {"proxy_id": proxy_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"添加代理失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/proxies', methods=['GET'])
def get_proxies():
    """获取代理列表"""
    try:
        is_active = request.args.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
        
        proxies = proxy_manager.get_all_proxies(is_active)
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": proxies
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取代理列表失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/proxies/<int:proxy_id>', methods=['GET'])
def get_proxy_detail(proxy_id):
    """获取代理详情和统计"""
    try:
        stats = proxy_manager.get_proxy_statistics(proxy_id)
        
        if not stats:
            return jsonify({
                "code": 404,
                "msg": "代理不存在",
                "data": None
            }), 404
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取代理详情失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/proxies/<int:proxy_id>', methods=['PUT'])
def update_proxy(proxy_id):
    """更新代理配置"""
    try:
        data = request.get_json()
        proxy_manager.update_proxy(proxy_id, **data)
        
        return jsonify({
            "code": 200,
            "msg": "更新成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"更新代理失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/proxies/<int:proxy_id>', methods=['DELETE'])
def delete_proxy(proxy_id):
    """删除代理配置"""
    try:
        proxy_manager.delete_proxy(proxy_id)
        
        return jsonify({
            "code": 200,
            "msg": "删除成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"删除代理失败: {str(e)}",
            "data": None
        }), 500


# ==================== IP切换调度相关API ====================

@enhanced_api.route('/ip-switch/init', methods=['POST'])
def init_ip_switch():
    """初始化账号的IP切换调度"""
    try:
        data = request.get_json()
        
        schedule_id = ip_switch_scheduler.init_account_schedule(
            account_id=data['account_id'],
            switch_interval_minutes=data.get('switch_interval_minutes', 60),
            auto_switch_enabled=data.get('auto_switch_enabled', True)
        )
        
        return jsonify({
            "code": 200,
            "msg": "初始化成功",
            "data": {"schedule_id": schedule_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"初始化失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/ip-switch/switch', methods=['POST'])
def switch_ip():
    """手动切换账号IP"""
    try:
        data = request.get_json()
        
        new_proxy = ip_switch_scheduler.switch_proxy_for_account(
            account_id=data['account_id'],
            country=data.get('country')
        )
        
        if new_proxy:
            return jsonify({
                "code": 200,
                "msg": "切换成功",
                "data": new_proxy
            }), 200
        else:
            return jsonify({
                "code": 500,
                "msg": "没有可用的代理",
                "data": None
            }), 500
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"切换失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/ip-switch/auto-switch', methods=['POST'])
def auto_switch_ips():
    """自动切换所有到期的账号IP"""
    try:
        results = ip_switch_scheduler.auto_switch_all_due_accounts()
        
        return jsonify({
            "code": 200,
            "msg": "自动切换完成",
            "data": results
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"自动切换失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/ip-switch/current-proxy/<int:account_id>', methods=['GET'])
def get_current_proxy(account_id):
    """获取账号当前使用的代理"""
    try:
        proxy = ip_switch_scheduler.get_account_current_proxy(account_id)
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": proxy
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取失败: {str(e)}",
            "data": None
        }), 500


# ==================== 浏览器配置相关API ====================

@enhanced_api.route('/browser-configs', methods=['POST'])
def create_browser_config():
    """创建浏览器配置"""
    try:
        data = request.get_json()
        
        config_id = browser_config_manager.create_browser_config(
            config_name=data['config_name'],
            browser_type=data.get('browser_type', 'chromium'),
            browser_path=data.get('browser_path'),
            headless=data.get('headless', True),
            user_data_dir=data.get('user_data_dir'),
            viewport_width=data.get('viewport_width', 1920),
            viewport_height=data.get('viewport_height', 1080),
            user_agent=data.get('user_agent'),
            proxy_config_id=data.get('proxy_config_id'),
            extra_args=data.get('extra_args'),
            is_default=data.get('is_default', False)
        )
        
        return jsonify({
            "code": 200,
            "msg": "配置创建成功",
            "data": {"config_id": config_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"创建配置失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/browser-configs', methods=['GET'])
def get_browser_configs():
    """获取浏览器配置列表"""
    try:
        configs = browser_config_manager.get_all_configs()
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": configs
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取配置列表失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/browser-configs/default', methods=['GET'])
def get_default_browser_config():
    """获取默认浏览器配置"""
    try:
        config = browser_config_manager.get_default_config()
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": config
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取默认配置失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/browser-configs/<int:config_id>', methods=['PUT'])
def update_browser_config(config_id):
    """更新浏览器配置"""
    try:
        data = request.get_json()
        browser_config_manager.update_config(config_id, **data)
        
        return jsonify({
            "code": 200,
            "msg": "更新成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"更新配置失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/browser-configs/<int:config_id>', methods=['DELETE'])
def delete_browser_config(config_id):
    """删除浏览器配置"""
    try:
        browser_config_manager.delete_config(config_id)
        
        return jsonify({
            "code": 200,
            "msg": "删除成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"删除配置失败: {str(e)}",
            "data": None
        }), 500


# ==================== Cookie管理相关API ====================

@enhanced_api.route('/cookies/auto-create-path', methods=['POST'])
def auto_create_cookie_path():
    """自动创建Cookie文件路径"""
    try:
        data = request.get_json()
        
        cookie_path = cookie_manager.auto_create_cookie_path(
            account_id=data['account_id'],
            platform_type=data['platform_type'],
            username=data['username']
        )
        
        return jsonify({
            "code": 200,
            "msg": "路径创建成功",
            "data": {"cookie_path": cookie_path}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"创建路径失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/cookies/init-management', methods=['POST'])
def init_cookie_management():
    """初始化Cookie管理"""
    try:
        data = request.get_json()
        
        management_id = cookie_manager.init_cookie_management(
            account_id=data['account_id'],
            cookie_path=data['cookie_path'],
            auto_refresh_enabled=data.get('auto_refresh_enabled', True),
            refresh_interval_hours=data.get('refresh_interval_hours', 24)
        )
        
        return jsonify({
            "code": 200,
            "msg": "初始化成功",
            "data": {"management_id": management_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"初始化失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/cookies/need-refresh', methods=['GET'])
def get_cookies_need_refresh():
    """获取需要刷新Cookie的账号列表"""
    try:
        accounts = cookie_manager.get_accounts_need_refresh()
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": accounts
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取失败: {str(e)}",
            "data": None
        }), 500


@enhanced_api.route('/cookies/mark-refreshed/<int:account_id>', methods=['POST'])
def mark_cookie_refreshed(account_id):
    """标记Cookie已刷新"""
    try:
        cookie_manager.mark_cookie_refreshed(account_id)
        
        return jsonify({
            "code": 200,
            "msg": "标记成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"标记失败: {str(e)}",
            "data": None
        }), 500
