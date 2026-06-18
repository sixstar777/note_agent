import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class ModelClient:
    def __init__(self):
        self.model_type = os.getenv("MODEL_TYPE", "ollama")
        self.model_name = os.getenv("MODEL_NAME", "qwen3.5:9b")
        if self.model_type == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/") + "/v1"
            self.client = OpenAI(base_url=base_url, api_key="dummy")
        else:
            self.client = OpenAI()

    def chat(self, messages):
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "500")),
            )
            elapsed = time.time() - start_time
            
            # 打印原始返回对象用于调试
            print(f"[DEBUG] 原始 response 对象类型: {type(response)}")
            print(f"[DEBUG] response.choices 数量: {len(response.choices)}")
            print(f"[DEBUG] response.choices[0].message: {response.choices[0].message}")
            
            # 提取消息对象
            message = response.choices[0].message
            
            # 提取 content
            content = getattr(message, 'content', None)
            print(f"[DEBUG] message.content: {content}")
            
            # 如果 content 为空，尝试 reasoning
            if not content:
                content = getattr(message, 'reasoning', None)
                print(f"[DEBUG] message.content 为空，尝试 message.reasoning: {content}")
            
            # 如果 reasoning 也为空，尝试其他可能的推理字段
            if not content:
                content = getattr(message, 'reasoning_content', None)
                print(f"[DEBUG] 尝试 message.reasoning_content: {content}")
            
            # 如果所有字段都为空，使用默认值
            if not content:
                content = "模型未返回有效内容"
                print(f"[DEBUG] 所有内容字段均为空，使用默认值")
            
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0
            
            if hasattr(response, 'usage') and response.usage:
                print(f"[DEBUG] response.usage: prompt_tokens={response.usage.prompt_tokens}, completion_tokens={response.usage.completion_tokens}, total_tokens={response.usage.total_tokens}")
            else:
                print(f"[DEBUG] response.usage: {response.usage}")
            
            result = {
                "content": content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "elapsed": elapsed,
            }
            print(f"[DEBUG] 最终返回字典: {result}")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"API调用失败: {str(e)}"
            print(f"[DEBUG] 异常: {error_msg}")
            return {"error": error_msg, "elapsed": elapsed}