#!/usr/bin/env python3
"""
Content Distiller - 主程序入口

用法:
    python distill.py              # 处理所有文章
    python distill.py --limit 10   # 只处理前10篇（测试用）
"""

import click
from rich.console import Console
from pathlib import Path

from src.config import Config
from src.fetcher import RSSFetcher
from src.cleaner import ContentCleaner
from src.classifier import ArticleClassifier
from src.synthesizer import KnowledgeSynthesizer
from src.organizer import KnowledgeOrganizer
from src.cache import CacheManager

console = Console()


@click.command()
@click.option(
    "--limit",
    type=int,
    default=None,
    help="限制处理的文章数量（用于测试）"
)
@click.option(
    "--model",
    type=click.Choice(["qwen", "deepseek", "mimo"]),
    default="qwen",
    help="选择 LLM 模型"
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="禁用缓存（从头开始）"
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="清除所有缓存后退出"
)
def main(limit: int, model: str, no_cache: bool, clear_cache: bool):
    """Content Distiller - 内容蒸馏工具"""
    
    # 处理清除缓存请求
    if clear_cache:
        cache = CacheManager()
        cache.clear_cache()
        return
    
    console.print("\n[bold magenta]═══════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]    Content Distiller v0.1.0[/bold magenta]")
    console.print("[bold magenta]    内容蒸馏 · 提炼知识体系[/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════[/bold magenta]\n")
    
    use_cache = not no_cache
    cache = CacheManager() if use_cache else None
    
    if use_cache:
        cache_info = cache.get_cache_info()
        if any(cache_info.values()):
            console.print("[yellow]>> 发现缓存，将从断点继续[/yellow]")
            console.print(f"   - 原始文章: {'[OK]' if cache_info['articles'] else '[ - ]'}")
            console.print(f"   - 清洗结果: {'[OK]' if cache_info['cleaned'] else '[ - ]'}")
            console.print(f"   - 分类结果: {'[OK]' if cache_info['categorized'] else '[ - ]'}")
            console.print(f"   - 合成批次: {cache_info['synthesis_batches']} 个\n")
    
    try:
        # 1. 验证配置
        console.print("[bold]步骤 1/5: 验证配置[/bold]")
        Config.validate()
        console.print("[green]>> 配置验证通过[/green]\n")
        
        # 2. 获取文章（支持缓存）
        console.print("[bold]步骤 2/5: 获取 RSS 文章[/bold]")
        if cache and cache.load_articles():
            articles = cache.load_articles()
        else:
            fetcher = RSSFetcher()
            articles = fetcher.fetch_all()
            if cache:
                cache.save_articles(articles)
        
        if not articles:
            console.print("[red]>> 未获取到任何文章，请检查 RSS 链接[/red]")
            return
        
        # 应用限制（测试用）
        if limit:
            console.print(f"[yellow]>> 测试模式：仅处理前 {limit} 篇文章[/yellow]\n")
            articles = articles[:limit]
        
        # 3. 清洗内容（支持缓存）
        console.print("[bold]步骤 3/5: 清洗文章内容[/bold]")
        if cache and cache.load_cleaned():
            cleaned_articles = cache.load_cleaned()
        else:
            cleaned_articles = ContentCleaner.clean_batch(articles)
            if cache:
                cache.save_cleaned(cleaned_articles)
        
        # 4. 智能分类（支持缓存）
        console.print(f"[bold]步骤 4/5: 智能分类[/bold]")
        if cache and cache.load_categorized():
            categorized = cache.load_categorized()
        else:
            classifier = ArticleClassifier()
            categorized = classifier.classify_batch(cleaned_articles)
            if cache:
                cache.save_categorized(categorized)
        
        # 5. AI 知识合成（核心步骤，支持断点续传）
        console.print(f"[bold]步骤 5/5: AI 知识合成（使用 {model}）[/bold]")
        synthesizer = KnowledgeSynthesizer(model=model, use_cache=use_cache)
        synthesized = synthesizer.synthesize_all(categorized)
        
        # 6. 生成最终文档
        console.print("[bold]生成最终文档[/bold]")
        organizer = KnowledgeOrganizer(Config.OUTPUT_DIR)
        organizer.organize(synthesized, categorized)  # 传入原文数据
        
        # 完成
        console.print("\n[bold green]========================================[/bold green]")
        console.print("[bold green]>> 蒸馏完成！[/bold green]")
        console.print(f"[bold green]>> 输出目录: {Config.OUTPUT_DIR}[/bold green]")
        console.print("[bold green]========================================[/bold green]\n")
        
        console.print("[cyan]>> 下一步：[/cyan]")
        console.print(f"   1. 查看 {Config.OUTPUT_DIR}/INDEX.md")
        console.print(f"   2. 在 VS Code 或 Obsidian 中打开知识库")
        console.print("   3. 开始学习和批注\n")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]>> 用户中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]>> 错误: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    main()
