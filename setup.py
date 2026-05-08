#!/usr/bin/env python
"""交互式配置向导 - 帮助用户快速配置 Content Distiller"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()


def main():
    """主配置流程"""
    console.print(Panel.fit(
        "[bold cyan]Content Distiller 配置向导[/bold cyan]\n\n"
        "本向导将帮助你完成初始配置",
        border_style="cyan"
    ))
    
    # 检查 .env 是否已存在
    env_file = Path(".env")
    skip_env_config = False
    
    if env_file.exists():
        console.print("\n[yellow].env 文件已存在[/yellow]")
        
        if not Confirm.ask("\n是否重新配置 .env 文件？", default=False):
            console.print("[green]跳过 .env 配置，使用现有配置[/green]")
            skip_env_config = True
    
    # 如果不跳过 .env 配置，执行完整配置流程
    if not skip_env_config:
        console.print("\n[bold]步骤 1/4: 选择 LLM 服务[/bold]")
        console.print("Content Distiller 支持以下 LLM 服务：")
        console.print("  1. Qwen (通义千问) - 推荐")
        console.print("  2. DeepSeek - 备选")
        
        model_choice = Prompt.ask(
            "\n请选择你要使用的服务",
            choices=["1", "2"],
            default="1"
        )
        
        # 收集 API Keys
        console.print("\n[bold]步骤 2/4: 配置 API Keys[/bold]")
        
        qwen_key = ""
        deepseek_key = ""
        
        if model_choice == "1":
            console.print("请前往 https://dashscope.aliyun.com/ 获取 Qwen API Key")
            qwen_key = Prompt.ask("请输入 Qwen API Key", password=True)
            
            if Confirm.ask("\n是否也配置 DeepSeek 作为备选？", default=False):
                console.print("请前往 https://platform.deepseek.com/ 获取 API Key")
                deepseek_key = Prompt.ask("请输入 DeepSeek API Key", password=True)
        else:
            console.print("请前往 https://platform.deepseek.com/ 获取 API Key")
            deepseek_key = Prompt.ask("请输入 DeepSeek API Key", password=True)
            
            if Confirm.ask("\n是否也配置 Qwen 作为备选？", default=False):
                console.print("请前往 https://dashscope.aliyun.com/ 获取 Qwen API Key")
                qwen_key = Prompt.ask("请输入 Qwen API Key", password=True)
        
        # 配置 RSS 源
        console.print("\n[bold]步骤 3/4: 配置 RSS 源[/bold]")
        console.print("你可以使用以下方式获取 RSS 链接：")
        console.print("  - ForgeRSS (https://github.com/tmwgsicp/ForgeRSS) - 开源RSS工具")
        console.print("  - wechat-download-api (https://github.com/tmwgsicp/wechat-download-api) - 微信公众号RSS订阅")
        console.print("  - Feedly, Inoreader - RSS聚合服务")
        console.print("  - 任意博客、新闻网站的原生RSS")
        
        rss_urls = []
        first_url = Prompt.ask("\n请输入第一个 RSS URL")
        rss_urls.append(first_url)
        
        while Confirm.ask("\n是否添加更多RSS源？", default=False):
            another_url = Prompt.ask("请输入RSS URL")
            rss_urls.append(another_url)
        
        # 用逗号连接所有URL
        rss_urls_str = ",".join(rss_urls)
        console.print(f"\n[green]已配置 {len(rss_urls)} 个RSS源[/green]")
        
        # 输出目录
        console.print("\n[bold]步骤 4/4: 配置输出目录[/bold]")
        output_dir = Prompt.ask(
            "蒸馏结果保存目录",
            default="./output"
        )
        
        # 生成 .env 文件
        env_content = f"""# API Keys
QWEN_API_KEY={qwen_key}
DEEPSEEK_API_KEY={deepseek_key}

# RSS Sources (multiple URLs separated by comma)
RSS_FEED_URLS={rss_urls_str}

# Output Settings
OUTPUT_DIR={output_dir}
"""
        
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 其他配置项（无论是否跳过 .env 都会执行）
    console.print("\n[bold]附加配置[/bold]")
    
    if Confirm.ask("\n是否查看提示词配置说明？", default=False):
        console.print("\n[cyan]提示词配置文件：prompts.yaml[/cyan]")
        console.print("你可以自定义：")
        console.print("  - 文章分类规则（categories）")
        console.print("  - 各类别的提取提示词")
        console.print("  - LLM 参数（temperature, max_tokens 等）")
        console.print("\n参考示例：prompts.example.yaml")
        console.print("直接编辑 prompts.yaml 即可生效")
    
    console.print("\n[green]✓ 配置完成！[/green]")
    console.print("\n[bold]下一步：[/bold]")
    console.print("  1. 安装依赖：[cyan]pip install -r requirements.txt[/cyan]")
    console.print("  2. 开始蒸馏：[cyan]python distill.py[/cyan]")
    console.print("  3. 测试运行：[cyan]python distill.py --limit 10[/cyan]")
    
    console.print("\n[yellow]提示：[/yellow]")
    console.print("  - 配置文件保存在 .env")
    console.print("  - 可以随时编辑 .env 修改配置")
    console.print("  - 提示词配置在 prompts.yaml")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]配置已取消[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]配置失败: {str(e)}[/red]")
        sys.exit(1)
