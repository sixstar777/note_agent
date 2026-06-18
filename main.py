import argparse
import json
from dotenv import load_dotenv

load_dotenv()

from src.model_client import ModelClient

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-model", action="store_true", help="检查模型连接")
    parser.add_argument("--goal", type=str, help="设置智能体目标")
    args = parser.parse_args()

    if args.check_model:
        client = ModelClient()
        model_name = client.model_name
        try:
            result = client.chat([{"role": "user", "content": "Hello"}])
            print(f"模型名：{model_name}，成功：是，耗时：{result['elapsed']:.2f}秒，tokens：{result['total_tokens']}（提示：{result['prompt_tokens']}，生成：{result['completion_tokens']}）")
        except Exception as e:
            print(f"模型名：{model_name}，成功：否，错误信息：{str(e)}")
    elif args.goal:
        from src.workflow import AgentWorkflow
        workflow = AgentWorkflow()
        result = workflow.run(args.goal)
        print("结果：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n日志记录：")
        for log in result.get("logs", []):
            step = log.get("step", "?")
            action = log.get("action", "?")
            print(f"步骤 {step}: 动作 - {action}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()