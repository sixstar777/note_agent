import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class ModelClient:
    def __init__(self):
        self.model_type = os.getenv("MODEL_TYPE", "ollama")
        self.model_name = os.getenv("MODEL_NAME", "qwen3.5:9b")
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "500"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        if self.model_type == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/") + "/v1"
            self.client = OpenAI(base_url=base_url, api_key="dummy")
        else:
            # 使用环境变量中的 OPENAI_API_KEY 和 OPENAI_BASE_URL
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            if api_key and base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                # 如果没设置，就使用默认（会从环境变量读取）
                self.client = OpenAI()

    def chat(self, messages, max_tokens=None):
        """
        调用大模型，返回包含内容和 token 统计的字典。
        如果 max_tokens 未指定，使用环境变量 MAX_OUTPUT_TOKENS。
        """
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens if max_tokens is not None else self.max_output_tokens,
                temperature=self.temperature,
            )
            elapsed = time.time() - start_time
            
            # 提取内容（兼容不同模型）
            message = response.choices[0].message
            content = getattr(message, 'content', None)
            if not content:
                content = getattr(message, 'reasoning', None)
            if not content:
                content = getattr(message, 'reasoning_content', None)
            if not content:
                content = "模型未返回有效内容"

            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            return {
                "content": content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "elapsed": elapsed,
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {"error": str(e), "elapsed": elapsed}