#!/usr/bin/env python3
"""
增强功能快速部署脚本
一键初始化所有增强功能数据表和配置
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

def check_requirements():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    try:
        import flask
        import flask_cors
        print("✅ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"⚠️ 部分依赖缺失: {e}")
        print("提示: 如果已安装依赖，可以忽略此警告")
        # 继续执行，不强制退出
        return True

def init_database():
    """初始化数据库"""
    print("\n📦 初始化数据库...")
    
    # 检查数据库文件
    db_file = BASE_DIR / "db" / "database.db"
    
    if not db_file.exists():
        print("⚠️ 主数据库不存在，先创建基础表...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "db" / "createTable.py")],
            cwd=str(BASE_DIR / "db"),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ 创建基础表失败: {result.stderr}")
            return False
        
        print("✅ 基础表创建成功")
    
    # 创建增强功能表
    print("📋 创建增强功能数据表...")
    import subprocess
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "db" / "enhanced_tables.py")],
        cwd=str(BASE_DIR / "db"),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ 创建增强功能表失败: {result.stderr}")
        return False
    
    print(result.stdout)
    print("✅ 数据库初始化完成")
    return True

def create_directories():
    """创建必要的目录"""
    print("\n📁 创建目录结构...")
    
    directories = [
        BASE_DIR / "cookiesFile",
        BASE_DIR / "videoFile",
        BASE_DIR / "cookiesFile" / "xiaohongshu_uploader",
        BASE_DIR / "cookiesFile" / "tencent_uploader",
        BASE_DIR / "cookiesFile" / "douyin_uploader",
        BASE_DIR / "cookiesFile" / "kuaishou_uploader",
        BASE_DIR / "cookiesFile" / "bilibili_uploader",
        BASE_DIR / "cookiesFile" / "baijiahao_uploader",
        BASE_DIR / "cookiesFile" / "tiktok_uploader",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory.relative_to(BASE_DIR)}")
    
    print("✅ 目录创建完成")
    return True

def check_config():
    """检查配置文件"""
    print("\n⚙️ 检查配置文件...")
    
    conf_file = BASE_DIR / "conf.py"
    example_file = BASE_DIR / "conf.example.py"
    
    if not conf_file.exists():
        if example_file.exists():
            print("⚠️ conf.py 不存在，从 conf.example.py 复制...")
            import shutil
            shutil.copy(example_file, conf_file)
            print(f"✅ 已创建 conf.py")
            print("⚠️ 请编辑 conf.py 文件，配置 LOCAL_CHROME_PATH")
            return True
        else:
            print("❌ conf.example.py 不存在")
            return False
    
    print("✅ 配置文件存在")
    return True

def create_default_browser_config():
    """创建默认浏览器配置"""
    print("\n🌐 创建默认浏览器配置...")
    
    try:
        from myUtils.browser_manager import BrowserConfigManager
        
        manager = BrowserConfigManager()
        
        # 检查是否已有默认配置
        default_config = manager.get_default_config()
        
        if not default_config:
            config_id = manager.create_browser_config(
                config_name="默认配置",
                browser_type="chromium",
                headless=True,
                viewport_width=1920,
                viewport_height=1080,
                is_default=True
            )
            print(f"✅ 已创建默认浏览器配置 (ID: {config_id})")
        else:
            print(f"✅ 默认浏览器配置已存在 (ID: {default_config['id']})")
        
        return True
    except Exception as e:
        print(f"⚠️ 创建默认浏览器配置失败: {e}")
        return True  # 非关键错误，继续

def print_summary():
    """打印部署摘要"""
    print("\n" + "="*60)
    print("🎉 增强功能部署完成！")
    print("="*60)
    print("\n📝 下一步操作：")
    print("\n1. 配置浏览器路径（如果还没配置）:")
    print("   编辑 conf.py 文件，设置 LOCAL_CHROME_PATH")
    print("\n2. 启动后端服务:")
    print("   python sau_backend.py")
    print("\n3. 查看增强功能文档:")
    print("   cat ENHANCED_FEATURES.md")
    print("\n4. 测试API接口:")
    print("   访问 http://localhost:5409/api/enhanced/proxies")
    print("\n" + "="*60)
    print("\n💡 功能亮点：")
    print("  ✨ 矩阵投放 - 一键分发素材到多账号")
    print("  ✨ IP管理 - 自动切换IP防封禁")
    print("  ✨ Cookie管理 - 自动化Cookie管理")
    print("  ✨ 任务调度 - 智能任务调度系统")
    print("\n📚 详细文档: ENHANCED_FEATURES.md")
    print("="*60 + "\n")

def main():
    """主函数"""
    print("="*60)
    print("🚀 Social Auto Upload - 增强功能部署")
    print("="*60)
    
    # 检查依赖
    if not check_requirements():
        sys.exit(1)
    
    # 创建目录
    if not create_directories():
        sys.exit(1)
    
    # 检查配置
    if not check_config():
        sys.exit(1)
    
    # 初始化数据库
    if not init_database():
        sys.exit(1)
    
    # 创建默认配置
    create_default_browser_config()
    
    # 打印摘要
    print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
