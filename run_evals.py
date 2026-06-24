import json
import os
import sys

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 使用绝对路径指向笔记目录
    notes_dir = os.path.join(base_dir, "data", "notes")
    cases_file = os.path.join(base_dir, "evals", "cases.jsonl")

    if not os.path.exists(cases_file):
        print(f"错误：评估样本文件不存在: {cases_file}")
        return

    cases = load_cases(cases_file)
    results = []
    passed = 0
    total = len(cases)

    for idx, case in enumerate(cases, 1):
        goal = case["goal"]
        expect_success = case["expect_success"]
        expected_contains = case.get("expected_contains", [])

        print(f"\n--- 运行用例 {idx}/{total}: {goal} ---")
        try:
            # 传入绝对路径，确保能找到笔记
            workflow = AgentWorkflow(notes_dir=notes_dir)
            result = workflow.run(goal)
        except Exception as e:
            result = {"status": "failed", "reason": str(e)}

        actual_status = result.get("status", "failed")
        answer = result.get("answer", "")

        if expect_success:
            # 期望成功：状态必须为 success，且答案包含任一关键词（若有要求）
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
            "passed": check_passed,
            "answer_preview": str(answer)[:50] + "..." if len(str(answer)) > 50 else str(answer)
        })

    # 打印结果表格（尝试使用 tabulate，若未安装则用纯文本）
    try:
        from tabulate import tabulate
        headers = ["用例编号", "目标", "期望结果", "实际结果", "是否通过"]
        table = [[r["id"], r["goal"], r["expected"], r["actual"], "✓" if r["passed"] else "✗"] for r in results]
        print("\n" + tabulate(table, headers=headers, tablefmt="grid"))
        # 额外打印答案预览帮助调试
        print("\n答案预览：")
        for r in results:
            print(f"  [{r['id']}] {r['answer_preview']}")
    except ImportError:
        print("\n提示：安装 tabulate 可获得更美观的表格 (pip install tabulate)")
        print(f"{'编号':<4} {'目标':<20} {'期望':<15} {'实际':<10} {'结果'}")
        print("-" * 70)
        for r in results:
            print(f"{r['id']:<4} {r['goal']:<20} {r['expected']:<15} {r['actual']:<10} {'✓' if r['passed'] else '✗'}")

    print(f"\n通过率: {passed}/{total} 通过")

if __name__ == "__main__":
    run_evaluation()