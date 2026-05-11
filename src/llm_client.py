"""LLM 客户端模块"""
from openai import OpenAI
from typing import Optional
from .config import Config


class LLMClient:
    """LLM API 客户端（支持 Qwen 和 DeepSeek）"""
    
    def __init__(self, model: str = "qwen"):
        """
        初始化 LLM 客户端

        Args:
            model: 使用的模型，qwen、deepseek 或 mimo
        """
        self.model = model

        if model == "qwen":
            self.client = OpenAI(
                api_key=Config.QWEN_API_KEY,
                base_url=Config.QWEN_API_BASE,
            )
            self.model_name = Config.QWEN_MODEL
        elif model == "deepseek":
            self.client = OpenAI(
                api_key=Config.DEEPSEEK_API_KEY,
                base_url=Config.DEEPSEEK_API_BASE,
            )
            self.model_name = Config.DEEPSEEK_MODEL
        elif model == "mimo":
            self.client = OpenAI(
                api_key=Config.MIMO_API_KEY,
                base_url=Config.MIMO_API_BASE,
            )
            self.model_name = Config.MIMO_MODEL
        else:
            raise ValueError(f"不支持的模型: {model}")
    
    def chat(
        self, 
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        发送对话请求
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            LLM 的回复文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM API 调用失败: {str(e)}")
    
    def extract_knowledge(self, article_content: str) -> dict:
        """
        从文章中提取知识点
        
        Args:
            article_content: 文章内容
            
        Returns:
            提取的知识点（dict格式）
        """
        system_prompt = """你是一个专业的知识提取助手。你的任务是从投资类文章中提取核心信息。

请从以下几个维度提取内容：
1. **核心观点**：文章的主要论点（1-3句话）
2. **投资方法论**：涉及的投资理念、分析框架、决策方法
3. **具体案例**：提到的股票、公司、投资案例
4. **关键洞察**：有价值的思考、金句、经验总结
5. **分类标签**：文章属于哪个领域（投资/个人成长/育儿/其他）

请以结构化的方式输出，格式如下：
---
分类: [投资/个人成长/育儿/其他]
核心观点: ...
投资方法论: ...
具体案例: ...
关键洞察: ...
---"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下文章：\n\n{article_content[:3000]}"}
        ]
        
        response = self.chat(messages, temperature=0.3)
        
        # 解析响应（简单版本，后续可以优化）
        return {
            "raw_extraction": response,
            "content": article_content
        }
