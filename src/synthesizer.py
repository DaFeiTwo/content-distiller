"""知识合成模块 - 将多篇文章合成体系化文档"""
from typing import List, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from .llm_client import LLMClient
from .cache import CacheManager
import tiktoken
import time
import yaml
from pathlib import Path

console = Console()


class KnowledgeSynthesizer:
    """知识合成器 - 核心模块（支持断点续传）"""
    
    def __init__(self, model: str = "qwen", use_cache: bool = True):
        self.llm = LLMClient(model=model)
        self.cache = CacheManager() if use_cache else None
        
        # 加载提示词配置
        self.prompts = self._load_prompts()
        
        # 使用 tiktoken 计算 token 数（近似）
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # 上下文窗口配置
        self.max_context = 120000  # Qwen-plus 支持 128K，留点余量
        self.max_output = self.prompts.get("settings", {}).get("max_tokens", 8000)
        self.reserved_tokens = 2000 # 保留给 prompt 的 token
        
        # 文章截取长度
        self.max_article_length = self.prompts.get("settings", {}).get("max_article_length", 3000)
    
    def _load_prompts(self) -> dict:
        """加载提示词配置"""
        prompts_file = Path("prompts.yaml")
        if not prompts_file.exists():
            console.print("[yellow]警告: prompts.yaml 不存在，使用默认提示词[/yellow]")
            return self._get_default_prompts()
        
        try:
            with open(prompts_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            console.print(f"[yellow]警告: 加载 prompts.yaml 失败 ({str(e)})，使用默认提示词[/yellow]")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> dict:
        """获取默认提示词"""
        return {
            "investment": {
                "system": "你是一位资深投资分析师。请从多篇文章中提取核心投资理念和方法论。"
            },
            "parenting": {
                "system": "你是一位教育专家。请从多篇文章中提取育儿理念和方法。"
            },
            "personal_growth": {
                "system": "你是一位人生导师。请从多篇文章中提取个人成长智慧。"
            },
            "general": {
                "system": "你是一位知识整理专家。请从多篇文章中提取核心观点和见解。"
            },
            "synthesis": {
                "system": "你是一位知识整合专家，擅长将分散的观点整合成体系化文档。"
            },
            "settings": {
                "batch_temperature": 0.3,
                "synthesis_temperature": 0.2,
                "max_tokens": 8000,
                "max_article_length": 3000
            }
        }
    
    def count_tokens(self, text: str) -> int:
        """统计文本的 token 数量"""
        try:
            return len(self.tokenizer.encode(text))
        except:
            # fallback: 粗略估计（中文约1.5字符/token）
            return len(text) // 1.5
    
    def create_batches(self, articles: List[Dict]) -> List[List[Dict]]:
        """
        智能分批：根据文章长度动态分组
        
        Args:
            articles: 文章列表
            
        Returns:
            批次列表
        """
        batches = []
        current_batch = []
        current_tokens = 0
        
        # 计算可用的输入 token 预算
        available_tokens = self.max_context - self.max_output - self.reserved_tokens
        
        for article in articles:
            content = article.get("content", "") or article.get("summary", "")
            # 根据配置截取文章长度（0表示不截取）
            max_len = self.max_article_length if self.max_article_length > 0 else len(content)
            article_tokens = self.count_tokens(content[:max_len])
            
            # 检查是否需要开新批次
            if current_tokens + article_tokens > available_tokens and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            
            current_batch.append(article)
            current_tokens += article_tokens
        
        # 添加最后一批
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def extract_batch_insights(self, articles: List[Dict], category: str) -> str:
        """
        从一批文章中提取核心观点（带错误重试）
        
        Args:
            articles: 文章列表
            category: 分类（投资/育儿/个人成长）
            
        Returns:
            提取的核心观点
        """
        # 构建输入文本
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get("title", "无标题")
            content = article.get("content", "") or article.get("summary", "")
            # 根据配置截取文章长度
            max_len = self.max_article_length if self.max_article_length > 0 else len(content)
            articles_text += f"\n\n### 文章 {i}: {title}\n{content[:max_len]}\n"
        
        # 根据分类获取提示词
        category_map = {
            "投资": "investment",
            "育儿": "parenting",
            "个人成长": "personal_growth",
            "其他": "general"
        }
        
        prompt_key = category_map.get(category, "general")
        system_prompt = self.prompts.get(prompt_key, {}).get("system", "")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下 {len(articles)} 篇文章：{articles_text}"}
        ]
        
        # 带重试的API调用
        max_retries = 3
        batch_temp = self.prompts.get("settings", {}).get("batch_temperature", 0.3)
        
        for attempt in range(max_retries):
            try:
                result = self.llm.chat(messages, temperature=batch_temp, max_tokens=self.max_output)
                return result
            except Exception as e:
                console.print(f"[red]API调用失败 (尝试 {attempt+1}/{max_retries}): {str(e)}[/red]")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    console.print(f"[yellow]等待 {wait_time} 秒后重试...[/yellow]")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"批次处理失败，已重试{max_retries}次: {str(e)}")
    
    def synthesize_category(self, articles: List[Dict], category: str) -> str:
        """
        合成某个分类的完整知识体系（支持断点续传）
        
        Args:
            articles: 该分类的所有文章
            category: 分类名称
            
        Returns:
            合成后的完整文档内容
        """
        if not articles:
            return ""
        
        # 检查是否有缓存的最终结果
        if self.cache:
            cached_result = self.cache.load_final_synthesis(category)
            if cached_result:
                console.print(f"[green]>> 使用缓存：【{category}】已完成合成[/green]\n")
                return cached_result
        
        console.print(f"\n[bold cyan]正在合成【{category}】知识体系...[/bold cyan]")
        console.print(f"[yellow]共 {len(articles)} 篇文章[/yellow]\n")
        
        # 智能分批
        batches = self.create_batches(articles)
        console.print(f"[blue]智能分批：分为 {len(batches)} 批处理[/blue]")
        for i, batch in enumerate(batches, 1):
            console.print(f"  - 批次 {i}: {len(batch)} 篇文章")
        console.print()
        
        # 检查已完成的批次
        completed_batches = []
        if self.cache:
            completed_batches = self.cache.get_completed_batches(category, len(batches))
            if completed_batches:
                console.print(f"[yellow]>> 发现已完成的批次: {completed_batches}[/yellow]")
        
        # 处理每一批
        batch_insights = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("合成中...", total=len(batches))
            
            for i, batch in enumerate(batches):
                # 检查缓存
                if self.cache and i in completed_batches:
                    cached = self.cache.load_batch_result(category, i)
                    if cached:
                        batch_insights.append(cached)
                        progress.update(task, description=f"[{i+1}/{len(batches)}] (使用缓存)...")
                        progress.advance(task)
                        continue
                
                # 处理新批次
                progress.update(task, description=f"处理批次 {i+1}/{len(batches)}...")
                
                try:
                    insight = self.extract_batch_insights(batch, category)
                    batch_insights.append(insight)
                    
                    # 保存批次结果
                    if self.cache:
                        self.cache.save_batch_result(category, i, insight)
                    
                except Exception as e:
                    console.print(f"\n[red]批次 {i+1} 处理失败: {str(e)}[/red]")
                    console.print(f"[yellow]>> 进度已保存，可使用相同命令继续[/yellow]\n")
                    raise
                
                progress.advance(task)
        
        # 如果只有一批，直接返回
        if len(batch_insights) == 1:
            result = batch_insights[0]
            if self.cache:
                self.cache.save_final_synthesis(category, result)
            console.print(f"[green]>> 完成【{category}】知识合成[/green]\n")
            return result
        
        # 多批需要最终整合
        console.print(f"[yellow]最终整合 {len(batch_insights)} 批结果...[/yellow]")
        
        # 使用配置的整合提示词
        synthesis_user_template = self.prompts.get("synthesis", {}).get(
            "user_template",
            "我从多批文章中提取了核心观点，现在需要你整合成一份完整、系统的文档。\n\n以下是 {batch_count} 批提取结果："
        )
        final_prompt = synthesis_user_template.format(batch_count=len(batch_insights))
        final_prompt += "\n\n"
        
        for i, insight in enumerate(batch_insights, 1):
            final_prompt += f"\n\n## 批次 {i} 的提取结果\n{insight}\n"
        
        synthesis_system = self.prompts.get("synthesis", {}).get(
            "system",
            "你是知识整合专家，擅长将分散的观点整合成体系化文档。"
        )
        synthesis_temp = self.prompts.get("settings", {}).get("synthesis_temperature", 0.2)
        
        messages = [
            {"role": "system", "content": synthesis_system},
            {"role": "user", "content": final_prompt}
        ]
        
        # 带重试的最终整合
        try:
            result = self.llm.chat(messages, temperature=synthesis_temp, max_tokens=self.max_output)
            
            # 保存最终结果
            if self.cache:
                self.cache.save_final_synthesis(category, result)
            
            console.print(f"[green]>> 完成【{category}】知识合成[/green]\n")
            return result
        
        except Exception as e:
            console.print(f"[red]最终整合失败: {str(e)}[/red]")
            console.print(f"[yellow]>> 批次结果已保存，可手动整合[/yellow]\n")
            raise
    
    def synthesize_all(self, categorized_articles: Dict[str, List[Dict]]) -> Dict[str, str]:
        """
        合成所有分类的知识体系
        
        Args:
            categorized_articles: 按分类组织的文章
            
        Returns:
            每个分类的合成文档
        """
        results = {}
        
        for category, articles in categorized_articles.items():
            if not articles:
                continue
            
            synthesized = self.synthesize_category(articles, category)
            results[category] = synthesized
        
        return results
