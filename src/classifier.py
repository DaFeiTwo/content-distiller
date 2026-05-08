"""文章分类模块"""
from typing import List, Dict
from rich.console import Console
from pathlib import Path
import yaml

console = Console()


class ArticleClassifier:
    """文章分类器"""
    
    def __init__(self):
        """初始化，从配置文件加载分类规则"""
        self.categories = self._load_categories()
    
    def _load_categories(self) -> Dict[str, List[str]]:
        """从 prompts.yaml 加载分类配置"""
        prompts_file = Path("prompts.yaml")
        
        if not prompts_file.exists():
            console.print("[yellow]警告: prompts.yaml 不存在，使用默认分类规则[/yellow]")
            return self._get_default_categories()
        
        try:
            with open(prompts_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            categories_config = config.get("categories", {})
            if not categories_config:
                console.print("[yellow]警告: prompts.yaml 中未找到 categories 配置，使用默认分类[/yellow]")
                return self._get_default_categories()
            
            # 转换格式：{分类名: [关键词列表]}
            categories = {}
            for cat_name, cat_config in categories_config.items():
                if isinstance(cat_config, dict) and "keywords" in cat_config:
                    categories[cat_name] = cat_config["keywords"]
                else:
                    console.print(f"[yellow]警告: 分类 '{cat_name}' 配置格式错误，跳过[/yellow]")
            
            return categories
            
        except Exception as e:
            console.print(f"[yellow]警告: 加载 prompts.yaml 失败 ({str(e)})，使用默认分类[/yellow]")
            return self._get_default_categories()
    
    def _get_default_categories(self) -> Dict[str, List[str]]:
        """默认分类规则（仅作为备用）"""
        return {
            "投资": ["投资", "股票", "市场", "估值"],
            "育儿": ["孩子", "育儿", "教育"],
            "个人成长": ["成长", "思考", "认知", "人生"]
        }
    
    def classify(self, article: Dict) -> str:
        """
        对单篇文章分类
        
        Args:
            article: 文章数据
            
        Returns:
            分类标签
        """
        title = article.get("title", "")
        content = article.get("content", "") or article.get("summary", "")
        text = title + " " + content[:500]  # 只看标题和前500字
        
        scores = {}
        for category, keywords in self.categories.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score
        
        # 返回得分最高的分类
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "其他"
    
    def classify_batch(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        批量分类文章
        
        Args:
            articles: 文章列表
            
        Returns:
            按分类组织的文章字典
        """
        console.print("\n[bold cyan]开始智能分类文章...[/bold cyan]\n")
        
        categorized = {cat: [] for cat in list(self.categories.keys()) + ["其他"]}
        
        for article in articles:
            category = self.classify(article)
            categorized[category].append(article)
        
        # 打印统计
        console.print("[bold]分类统计：[/bold]")
        for category, items in categorized.items():
            if items:
                console.print(f"  - {category}: {len(items)} 篇")
        
        console.print()
        return categorized
