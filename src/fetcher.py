"""RSS 获取模块"""
import feedparser
import requests
from typing import List, Dict
from rich.console import Console
from .config import Config

console = Console()


class RSSFetcher:
    """RSS 文章获取器"""
    
    def __init__(self):
        self.feed_urls = Config.get_rss_urls()
    
    def fetch_feed(self, url: str) -> List[Dict]:
        """
        获取 RSS feed
        
        Args:
            url: RSS feed URL
            
        Returns:
            文章列表
        """
        try:
            console.print(f"[blue]正在获取 RSS: {url[:50]}...[/blue]")
            
            # 获取 RSS 内容
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析 RSS
            feed = feedparser.parse(response.content)
            
            articles = []
            for entry in feed.entries:
                article = {
                    "title": entry.get("title", "无标题"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "content": self._extract_content(entry),
                }
                articles.append(article)
            
            console.print(f"[green]>> 获取到 {len(articles)} 篇文章[/green]")
            return articles
            
        except Exception as e:
            console.print(f"[red]>> 获取失败: {str(e)}[/red]")
            return []
    
    def _extract_content(self, entry) -> str:
        """提取文章正文内容"""
        # 优先从 content 字段获取
        if hasattr(entry, "content") and entry.content:
            return entry.content[0].get("value", "")
        
        # 其次从 summary 获取
        if hasattr(entry, "summary"):
            return entry.summary
        
        # 最后从 description 获取
        if hasattr(entry, "description"):
            return entry.description
        
        return ""
    
    def fetch_all(self) -> List[Dict]:
        """
        获取所有RSS源的文章
        
        Returns:
            所有文章列表（已去重）
        """
        console.print("\n[bold cyan]开始获取 RSS 文章...[/bold cyan]\n")
        console.print(f"[yellow]配置了 {len(self.feed_urls)} 个RSS源[/yellow]\n")
        
        all_articles = []
        
        # 遍历所有RSS源
        for i, url in enumerate(self.feed_urls, 1):
            console.print(f"[yellow]正在获取第 {i}/{len(self.feed_urls)} 个RSS源[/yellow]")
            articles = self.fetch_feed(url)
            all_articles.extend(articles)
            console.print()
        
        # 去重（基于 link）
        unique_articles = []
        seen_links = set()
        
        for article in all_articles:
            if article["link"] not in seen_links:
                unique_articles.append(article)
                seen_links.add(article["link"])
        
        console.print(f"[bold green]>> 总共获取 {len(unique_articles)} 篇文章（去重后）[/bold green]\n")
        return unique_articles
