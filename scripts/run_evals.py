import json
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow import AgentWorkflow

def load_cases(filepath):
    cases = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases

def run_evaluation():
    cases_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evals", "cases.jsonl")
    cases = load_cases(cases_file)

    results = []
    passed = 0
    total = len(cases)

    for idx, case in enumerate(cases, 1):
        goal = case["goal"]
        expect_success = case["expect_success"]
        expected_contains = case.get("expected_contains", [])

        try:
            workflow = AgentWorkflow()
            result = workflow.run(goal)
        except Exception as e:
            result = {"status": "failed", "reason": str(e)}

        actual_status = result.get("status", "failed")
        answer = result.get("answer", "")

        if expect_success:
            # 期望成功：状态为 success，且答案包含任一关键词
            check_passed = False
            if actual_status == "success":
                if expected_contains:
                    answer_str = str(answer)
                    check_passed = any(kw in answer_str for kw in expected_contains)
                else:
                    check_passed = True
            passed += 1 if check_passed else 0
        else:
            # 期望失败：状态为 rejected 或 failed
            check_passed = actual_status in ("rejected", "failed")
            passed += 1 if check_passed else 0

        results.append({
            "id": idx,
            "goal": goal,
            "expected": "success" if expect_success else "rejected/failed",
            "actual": actual_status,
            "passed": check_passed
        })

    # 打印结果
    try:
        from tabulate import tabulate
        headers = ["用例编号", "目标", "期望结果", "实际结果", "是否通过"]
        table = [[r["id"], r["goal"], r["expected"], r["actual"], "✓" if r["passed"] else "✗"] for r in results]
        print(tabulate(table, headers=headers, tablefmt="grid"))
    except ImportError:
        print("提示：未安装 tabulate 库，使用纯文本输出。请运行 pip install tabulate 以获得更美观的表格。\n")
        print(f"{'用例编号':<8} {'目标':<15} {'期望结果':<20} {'实际结果':<15} {'是否通过'}")
        print("-" * 75)
        for r in results:
            print(f"{r['id']:<8} {r['goal']:<15} {r['expected']:<20} {r['actual']:<15} {'✓' if r['passed'] else '✗'}")

    print(f"\n通过率: {passed}/{total} passed")

if __name__ == "__main__":
    run_evaluation()