"""配置管理模块"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（强制覆盖已存在的）
load_dotenv(override=True)


class Config:
    """项目配置"""
    
    # API Keys
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
    
    # RSS Sources
    RSS_FEED_URLS = os.getenv("RSS_FEED_URLS", "")
    
    @classmethod
    def get_rss_urls(cls) -> list:
        """获取RSS URL列表（支持逗号分隔的多个URL）"""
        urls_str = cls.RSS_FEED_URLS.strip()
        if not urls_str:
            return []
        
        # 支持逗号分隔的多个URL
        urls = [url.strip() for url in urls_str.split(',') if url.strip()]
        return urls
    
    # Output Settings
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
    
    # LLM Settings
    DEFAULT_MODEL = "qwen"  # qwen 或 deepseek
    QWEN_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL = "qwen-plus"
    DEEPSEEK_API_BASE = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"

    MIMO_API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
    MIMO_MODEL = "mimo-v2.5-pro"
    
    @classmethod
    def validate(cls):
        """验证配置"""
        errors = []
        
        if not cls.QWEN_API_KEY and not cls.DEEPSEEK_API_KEY and not cls.MIMO_API_KEY:
            errors.append("未设置 QWEN_API_KEY、DEEPSEEK_API_KEY 或 MIMO_API_KEY")
        
        urls = cls.get_rss_urls()
        if not urls:
            errors.append("未设置 RSS_FEED_URLS")
        
        if errors:
            raise ValueError(f"配置错误：\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
