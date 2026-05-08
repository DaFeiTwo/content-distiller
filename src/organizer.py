"""体系化整理模块 - 新版：直接生成体系化文档"""
from pathlib import Path
from typing import Dict
from rich.console import Console

console = Console()


class KnowledgeOrganizer:
    """知识整理器 - 新版：生成体系化文档"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.category_names = {
            "投资": "投资体系",
            "个人成长": "个人成长",
            "育儿": "育儿理念",
            "其他": "其他主题"
        }
    
    def organize(self, synthesized_knowledge: Dict[str, str], categorized_articles: Dict[str, list] = None) -> None:
        """
        生成最终的知识库文档
        
        Args:
            synthesized_knowledge: 每个分类的合成文档
            categorized_articles: 按分类组织的原文（可选）
        """
        console.print("\n[bold cyan]开始生成最终文档...[/bold cyan]\n")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 为每个分类生成文档
        for category, content in synthesized_knowledge.items():
            if not content:
                continue
            
            self._generate_category_doc(category, content)
        
        # 生成原文合集（如果提供了原文）
        if categorized_articles:
            self._generate_source_collections(categorized_articles)
        
        # 生成总索引
        self._generate_index(synthesized_knowledge)
        
        console.print(f"\n[bold green]>> 知识库已生成到: {self.output_dir}[/bold green]\n")
    
    def _generate_category_doc(self, category: str, content: str) -> None:
        """生成分类的体系化文档"""
        category_name = self.category_names.get(category, category)
        filename = f"{category_name}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {category_name}\n\n")
            f.write(f"> 从博主的文章中提炼的{category_name}\n\n")
            f.write("---\n\n")
            f.write(content)
            f.write("\n")
        
        console.print(f"[green]>> 生成文档: {filename}[/green]")
    
    def _generate_source_collections(self, categorized_articles: Dict[str, list]) -> None:
        """生成原文合集文档"""
        console.print("\n[blue]生成原文合集...[/blue]")
        
        for category, articles in categorized_articles.items():
            if not articles:
                continue
            
            category_name = self.category_names.get(category, category)
            filename = f"{category_name}-原文合集.md"
            filepath = self.output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {category_name} - 原文合集\n\n")
                f.write(f"> 共 {len(articles)} 篇原文，按时间倒序排列\n\n")
                f.write("---\n\n")
                
                # 写入每篇文章
                for i, article in enumerate(articles, 1):
                    title = article.get("title", "无标题")
                    link = article.get("link", "")
                    published = article.get("published", "")
                    content = article.get("content", "") or article.get("summary", "")
                    
                    f.write(f"## {i}. {title}\n\n")
                    f.write(f"**发布时间：** {published}\n\n")
                    f.write(f"**原文链接：** [{link}]({link})\n\n")
                    f.write("### 正文\n\n")
                    f.write(content)
                    f.write("\n\n---\n\n")
            
            console.print(f"[green]>> 生成原文合集: {filename} ({len(articles)}篇)[/green]")
    
    def _generate_index(self, synthesized_knowledge: Dict[str, str]) -> None:
        """生成总索引"""
        index_path = self.output_dir / "INDEX.md"
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("# 知识库索引\n\n")
            f.write("> 从博主的文章中提炼的体系化知识库\n\n")
            f.write("## 使用说明\n\n")
            f.write("本知识库已经将400+篇文章提炼整合，形成体系化文档。\n\n")
            f.write("**推荐学习路径：**\n")
            f.write("1. 先阅读【投资体系】了解投资方法论\n")
            f.write("2. 再阅读【个人成长】和【育儿理念】\n")
            f.write("3. 在文档中添加自己的笔记和实践心得\n\n")
            f.write("---\n\n")
            f.write("## 知识库目录\n\n")
            
            for category, content in synthesized_knowledge.items():
                if content:
                    category_name = self.category_names.get(category, category)
                    f.write(f"### {category_name}\n\n")
                    f.write(f"- **体系化文档：** [{category_name}.md]({category_name}.md)\n")
                    f.write(f"- **原文合集：** [{category_name}-原文合集.md]({category_name}-原文合集.md)\n\n")
            
            f.write("\n---\n\n")
            f.write("## 使用技巧\n\n")
            f.write("- **快速学习：** 直接阅读体系化文档（如《投资体系.md》）\n")
            f.write("- **深度研究：** 体系化文档中提到某个观点，想看原文？打开对应的原文合集搜索关键词\n")
            f.write("- **添加笔记：** 在文档中直接标注你的思考和实践心得\n\n")
            f.write("---\n\n")
            f.write("*本知识库由 Content Distiller 自动生成*\n")
