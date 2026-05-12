"""RSS 获取模块"""
import time
import feedparser
import requests
from typing import List, Dict
from rich.console import Console
from .config import Config

console = Console()

# 浏览器 UA，部分 RSS 服务对默认 python-requests UA 不友好
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
}

# 可选：使用 curl_cffi 来伪装浏览器 TLS 指纹，绕过部分 WAF/Cloudflare 的拦截
try:
    from curl_cffi import requests as cffi_requests  # type: ignore
    _HAS_CURL_CFFI = True
except Exception:  # pragma: no cover
    cffi_requests = None  # type: ignore
    _HAS_CURL_CFFI = False


def _http_get(url: str, timeout: int = 30):
    """
    获取一个 URL。优先用 curl_cffi 伪装 Chrome TLS 指纹，
    握手失败时回退到普通 requests。
    返回一个带 .content / .status_code / .raise_for_status() 的对象。
    """
    if _HAS_CURL_CFFI:
        try:
            return cffi_requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=timeout,
                impersonate="chrome",
            )
        except Exception as e:
            console.print(
                f"[yellow]   curl_cffi 失败，回退到 requests: "
                f"{type(e).__name__}: {str(e)[:80]}[/yellow]"
            )
    return requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)


class RSSFetcher:
    """RSS 文章获取器"""
    
    def __init__(self):
        self.feed_urls = Config.get_rss_urls()
    
    def fetch_feed(self, url: str, max_retries: int = 3) -> List[Dict]:
        """
        获取 RSS feed（带重试）

        Args:
            url: RSS feed URL
            max_retries: 最大重试次数

        Returns:
            文章列表
        """
        console.print(f"[blue]正在获取 RSS: {url[:50]}...[/blue]")

        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                response = _http_get(url, timeout=30)
                response.raise_for_status()

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
                last_err = e
                console.print(
                    f"[yellow]>> 第 {attempt}/{max_retries} 次获取失败: "
                    f"{type(e).__name__}: {str(e)[:120]}[/yellow]"
                )
                if attempt < max_retries:
                    sleep_s = 2 * attempt
                    console.print(f"[yellow]   {sleep_s}s 后重试...[/yellow]")
                    time.sleep(sleep_s)

        console.print(f"[red]>> 获取失败（已重试 {max_retries} 次）: {last_err}[/red]")
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
