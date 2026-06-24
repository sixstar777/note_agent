import os
from src.model_client import ModelClient
from src.tools import search_notes, list_notes
from src.guardrails import validate_input, human_confirm

class AgentWorkflow:
    def __init__(self, notes_dir=None):
        self.client = ModelClient()
        # 如果未指定，默认使用 data/notes
        self.notes_dir = notes_dir if notes_dir else os.path.join("data", "notes")
        self.logs = []

    def run(self, goal):
        # 安全护栏：输入验证
        valid, error_msg = validate_input(goal)
        if not valid:
            # 检查是否是危险操作，尝试人工确认
            dangerous_keywords = ["rm -rf", "delete", "drop table", "shutdown"]
            lower_goal = goal.lower()
            is_dangerous = any(kw in lower_goal for kw in dangerous_keywords)
            
            if is_dangerous:
                # 人工确认
                confirmed = human_confirm(goal)
                if not confirmed:
                    print(f"========== 输入验证失败 ==========")
                    print(f"原因: 用户取消操作")
                    return {"status": "rejected", "reason": "用户取消操作", "logs": []}
                else:
                    # 人工放行，记录日志
                    print(f"========== 人工放行 ==========")
                    print(f"操作已被用户确认放行")
                    self.logs.append({"step": 0, "action": "human_override", "goal": goal})
            else:
                # 非危险操作的验证失败（空输入、过长等）
                print(f"========== 输入验证失败 ==========")
                print(f"原因: {error_msg}")
                return {"status": "rejected", "reason": error_msg, "logs": []}
        else:
            self.logs = []

        # 如果还没有初始化日志（正常流程）
        if not self.logs:
            self.logs = []

        # 步骤 0：规划
        self.logs.append({"step": 0, "action": "plan", "goal": goal})
        print(f"========== 步骤 0: 规划 ==========")
        print(f"目标: {goal}")
        print(f"笔记目录: {self.notes_dir}")

        # 步骤 1：工具调用（传入 self.notes_dir）
        if "列表" in goal or "列出" in goal:
            tool_name = "list_notes"
            tool_result = list_notes(notes_dir=self.notes_dir)
        else:
            tool_name = "search_notes"
            tool_result = search_notes(goal, top_k=3, notes_dir=self.notes_dir)

        self.logs.append({"step": 1, "action": "tool_call", "tool": tool_name, "result": tool_result})
        print(f"========== 步骤 1: 工具调用 ==========")
        print(f"工具: {tool_name}")
        if "items" in tool_result:
            print(f"结果: 找到 {len(tool_result['items'])} 个匹配")
        elif "titles" in tool_result:
            print(f"结果: 找到 {len(tool_result['titles'])} 个笔记")
        elif "error" in tool_result:
            print(f"结果: 错误 - {tool_result.get('message', tool_result['error'])}")

        # 步骤 2：检查错误
        if "error" in tool_result:
            reason = tool_result.get("message", str(tool_result["error"]))
            self.logs.append({"step": 2, "action": "fail", "reason": reason})
            print(f"========== 步骤 2: 失败 ==========")
            print(f"原因: {reason}")
            return {"status": "failed", "reason": reason, "logs": self.logs}

        # 如果工具是 list_notes，直接返回笔记列表
        if tool_name == "list_notes":
            self.logs.append({"step": 2, "action": "output", "answer": tool_result})
            print(f"========== 步骤 2: 直接返回 ==========")
            print(f"返回笔记列表，共 {len(tool_result.get('titles', []))} 个")
            return {"status": "success", "answer": tool_result, "logs": self.logs}

        # 如果工具是 search_notes 但无结果
        items = tool_result.get("items", [])
        if not items:
            answer = "未找到相关笔记"
            self.logs.append({"step": 2, "action": "output", "answer": answer})
            print(f"========== 步骤 2: 无结果 ==========")
            print(f"未找到匹配的笔记")
            return {"status": "success", "answer": answer, "logs": self.logs}

        # 构建提示词，调用大模型
        note_context = "\n".join([f"来源 {item['title']}: {item['snippet']}" for item in items])
        prompt = f"""根据以下笔记片段回答用户的问题：
用户问题：{goal}
笔记片段：
{note_context}
请给出简洁、准确的回答，并注明信息来自哪个笔记文件。"""

        print(f"========== 步骤 2: 大模型生成 ==========")
        print(f"提示词长度: {len(prompt)} 字符")
        print(f"笔记来源: {[item['title'] for item in items]}")

        try:
            resp = self.client.chat([{"role": "user", "content": prompt}])
            
            # 检查响应中是否包含错误
            if isinstance(resp, dict) and "error" in resp:
                error_msg = resp.get("error", "未知错误")
                self.logs.append({"step": 2, "action": "fail", "reason": error_msg})
                print(f"========== 步骤 2: 失败 ==========")
                print(f"大模型返回错误: {error_msg}")
                return {"status": "failed", "reason": error_msg, "logs": self.logs}
            
            # 提取 content
            if isinstance(resp, dict) and "content" in resp:
                answer = resp.get("content", "")
                if not answer:
                    answer = "未生成有效回答，请检查模型输出"
            else:
                answer = "未生成有效回答，请检查模型输出"
            
            tokens_info = {
                "prompt_tokens": resp.get("prompt_tokens", 0) if isinstance(resp, dict) else 0,
                "completion_tokens": resp.get("completion_tokens", 0) if isinstance(resp, dict) else 0,
                "total_tokens": resp.get("total_tokens", 0) if isinstance(resp, dict) else 0,
            }
            self.logs.append({"step": 2, "action": "llm_generate", "tokens": tokens_info})
            print(f"Tokens: 提示={tokens_info['prompt_tokens']}, 生成={tokens_info['completion_tokens']}, 总计={tokens_info['total_tokens']}")
            print(f"========== 完成 ==========")
            return {"status": "success", "answer": answer, "logs": self.logs}
        except Exception as e:
            self.logs.append({"step": 2, "action": "fail", "reason": str(e)})
            print(f"========== 步骤 2: 失败 ==========")
            print(f"大模型调用错误: {str(e)}")
            return {"status": "failed", "reason": str(e), "logs": self.logs}