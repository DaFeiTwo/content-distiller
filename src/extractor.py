"""知识提取模块"""
from typing import List, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from .llm_client import LLMClient

console = Console()


class KnowledgeExtractor:
    """知识提取器"""
    
    def __init__(self, model: str = "qwen"):
        self.llm = LLMClient(model=model)
    
    def extract(self, article: Dict) -> Dict:
        """
        从单篇文章提取知识
        
        Args:
            article: 文章数据
            
        Returns:
            提取的知识点
        """
        content = article.get("content", "") or article.get("summary", "")
        
        if not content or len(content) < 50:
            return {
                "title": article.get("title", ""),
                "skipped": True,
                "reason": "内容太短"
            }
        
        try:
            extraction = self.llm.extract_knowledge(content)
            
            return {
                "title": article.get("title", ""),
                "link": article.get("link", ""),
                "published": article.get("published", ""),
                "extraction": extraction,
                "skipped": False
            }
        except Exception as e:
            console.print(f"[red]提取失败: {str(e)}[/red]")
            return {
                "title": article.get("title", ""),
                "skipped": True,
                "reason": f"提取错误: {str(e)}"
            }
    
    def extract_batch(self, articles: List[Dict], limit: int = None) -> List[Dict]:
        """
        批量提取知识
        
        Args:
            articles: 文章列表
            limit: 限制处理数量（用于测试）
            
        Returns:
            提取的知识点列表
        """
        if limit:
            articles = articles[:limit]
        
        console.print("\n[bold cyan]开始提取知识点...[/bold cyan]\n")
        console.print(f"[yellow]共 {len(articles)} 篇文章待处理[/yellow]\n")
        
        extractions = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("提取中...", total=len(articles))
            
            for i, article in enumerate(articles, 1):
                title = article.get("title", "无标题")[:40]
                progress.update(task, description=f"[{i}/{len(articles)}] {title}...")
                
                extraction = self.extract(article)
                extractions.append(extraction)
                
                progress.advance(task)
        
        # 统计
        success_count = sum(1 for e in extractions if not e.get("skipped"))
        console.print(f"\n[bold green]>> 成功提取 {success_count}/{len(articles)} 篇[/bold green]\n")
        
        return extractions
