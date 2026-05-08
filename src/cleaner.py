"""内容清洗模块"""
from bs4 import BeautifulSoup
import re
from typing import Dict
from rich.console import Console

console = Console()


class ContentCleaner:
    """内容清洗器"""
    
    @staticmethod
    def clean(article: Dict) -> Dict:
        """
        清洗文章内容
        
        Args:
            article: 原始文章数据
            
        Returns:
            清洗后的文章数据
        """
        cleaned = article.copy()
        
        # 清洗 HTML 标签
        if cleaned.get("content"):
            cleaned["content"] = ContentCleaner._clean_html(cleaned["content"])
        
        if cleaned.get("summary"):
            cleaned["summary"] = ContentCleaner._clean_html(cleaned["summary"])
        
        # 清洗标题
        if cleaned.get("title"):
            cleaned["title"] = ContentCleaner._clean_text(cleaned["title"])
        
        return cleaned
    
    @staticmethod
    def _clean_html(html_text: str) -> str:
        """去除 HTML 标签，保留纯文本"""
        if not html_text:
            return ""
        
        # 使用 BeautifulSoup 解析
        soup = BeautifulSoup(html_text, "lxml")
        
        # 移除 script 和 style 标签
        for tag in soup(["script", "style"]):
            tag.decompose()
        
        # 获取纯文本
        text = soup.get_text(separator="\n")
        
        # 清理多余空行
        text = re.sub(r"\n\s*\n", "\n\n", text)
        
        return text.strip()
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本中的特殊字符"""
        if not text:
            return ""
        
        # 移除多余空格
        text = re.sub(r"\s+", " ", text)
        
        # 移除特殊字符（保留中英文、数字、常见标点）
        text = re.sub(r"[^\w\s\u4e00-\u9fff.,!?;:，。！？；：、（）()【】\[\]《》<>\"\']+", "", text)
        
        return text.strip()
    
    @staticmethod
    def clean_batch(articles: list[Dict]) -> list[Dict]:
        """
        批量清洗文章
        
        Args:
            articles: 文章列表
            
        Returns:
            清洗后的文章列表
        """
        console.print("\n[bold cyan]开始清洗文章内容...[/bold cyan]\n")
        
        cleaned_articles = []
        for i, article in enumerate(articles, 1):
            console.print(f"[blue]清洗中 ({i}/{len(articles)}): {article.get('title', '无标题')[:50]}...[/blue]")
            cleaned = ContentCleaner.clean(article)
            cleaned_articles.append(cleaned)
        
        console.print(f"\n[bold green]>> 完成 {len(cleaned_articles)} 篇文章清洗[/bold green]\n")
        return cleaned_articles
