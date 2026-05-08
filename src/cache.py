"""缓存管理模块 - 实现断点续传"""
import json
import pickle
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
import hashlib

console = Console()


class CacheManager:
    """缓存管理器 - 支持断点续传"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存文件路径
        self.articles_cache = self.cache_dir / "articles.pkl"
        self.cleaned_cache = self.cache_dir / "cleaned.pkl"
        self.categorized_cache = self.cache_dir / "categorized.pkl"
        self.synthesis_cache = self.cache_dir / "synthesis"
        self.synthesis_cache.mkdir(parents=True, exist_ok=True)
        
        # 进度文件
        self.progress_file = self.cache_dir / "progress.json"
    
    def get_cache_key(self, data: Any) -> str:
        """生成缓存键（基于数据的hash）"""
        data_str = str(data)
        return hashlib.md5(data_str.encode()).hexdigest()[:16]
    
    def save_articles(self, articles: List[Dict]) -> None:
        """保存原始文章"""
        with open(self.articles_cache, 'wb') as f:
            pickle.dump(articles, f)
        console.print(f"[dim]>> 缓存：保存 {len(articles)} 篇原始文章[/dim]")
    
    def load_articles(self) -> List[Dict]:
        """加载原始文章"""
        if self.articles_cache.exists():
            with open(self.articles_cache, 'rb') as f:
                articles = pickle.load(f)
            console.print(f"[yellow]>> 缓存：读取 {len(articles)} 篇原始文章[/yellow]")
            return articles
        return None
    
    def save_cleaned(self, cleaned: List[Dict]) -> None:
        """保存清洗后的文章"""
        with open(self.cleaned_cache, 'wb') as f:
            pickle.dump(cleaned, f)
        console.print(f"[dim]>> 缓存：保存 {len(cleaned)} 篇清洗后文章[/dim]")
    
    def load_cleaned(self) -> List[Dict]:
        """加载清洗后的文章"""
        if self.cleaned_cache.exists():
            with open(self.cleaned_cache, 'rb') as f:
                cleaned = pickle.load(f)
            console.print(f"[yellow]>> 缓存：读取 {len(cleaned)} 篇清洗后文章[/yellow]")
            return cleaned
        return None
    
    def save_categorized(self, categorized: Dict[str, List[Dict]]) -> None:
        """保存分类结果"""
        with open(self.categorized_cache, 'wb') as f:
            pickle.dump(categorized, f)
        total = sum(len(v) for v in categorized.values())
        console.print(f"[dim]>> 缓存：保存分类结果（{total}篇）[/dim]")
    
    def load_categorized(self) -> Dict[str, List[Dict]]:
        """加载分类结果"""
        if self.categorized_cache.exists():
            with open(self.categorized_cache, 'rb') as f:
                categorized = pickle.load(f)
            total = sum(len(v) for v in categorized.values())
            console.print(f"[yellow]>> 缓存：读取分类结果（{total}篇）[/yellow]")
            return categorized
        return None
    
    def save_batch_result(self, category: str, batch_idx: int, result: str) -> None:
        """保存单个批次的合成结果"""
        cache_file = self.synthesis_cache / f"{category}_batch_{batch_idx}.txt"
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(result)
        console.print(f"[dim]>> 缓存：保存【{category}】批次 {batch_idx}[/dim]")
    
    def load_batch_result(self, category: str, batch_idx: int) -> str:
        """加载单个批次的合成结果"""
        cache_file = self.synthesis_cache / f"{category}_batch_{batch_idx}.txt"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def get_completed_batches(self, category: str, total_batches: int) -> List[int]:
        """获取已完成的批次列表"""
        completed = []
        for i in range(total_batches):
            if (self.synthesis_cache / f"{category}_batch_{i}.txt").exists():
                completed.append(i)
        return completed
    
    def save_final_synthesis(self, category: str, result: str) -> None:
        """保存最终合成结果"""
        cache_file = self.synthesis_cache / f"{category}_final.txt"
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(result)
        console.print(f"[dim]>> 缓存：保存【{category}】最终合成[/dim]")
    
    def load_final_synthesis(self, category: str) -> str:
        """加载最终合成结果"""
        cache_file = self.synthesis_cache / f"{category}_final.txt"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def save_progress(self, step: str, details: Dict = None) -> None:
        """保存进度信息"""
        progress = {
            "current_step": step,
            "details": details or {},
            "timestamp": str(Path(self.progress_file).stat().st_mtime if self.progress_file.exists() else "")
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    
    def load_progress(self) -> Dict:
        """加载进度信息"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        console.print("[yellow]>> 已清除所有缓存[/yellow]")
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        info = {
            "articles": self.articles_cache.exists(),
            "cleaned": self.cleaned_cache.exists(),
            "categorized": self.categorized_cache.exists(),
            "synthesis_batches": len(list(self.synthesis_cache.glob("*.txt"))) if self.synthesis_cache.exists() else 0,
            "progress": self.progress_file.exists()
        }
        return info
