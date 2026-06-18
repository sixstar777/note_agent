import os

def validate_input(user_input):
    if not user_input or not user_input.strip():
        return False, "输入不能为空"
    if len(user_input) > 500:
        return False, "输入过长，超过500字符限制"
    dangerous_keywords = ["rm -rf", "delete", "drop table", "shutdown"]
    lower_input = user_input.lower()
    for kw in dangerous_keywords:
        if kw in lower_input:
            return False, "检测到潜在危险操作，已拒绝"
    return True, ""

def human_confirm(goal):
    print(f"警告：检测到敏感操作 \"{goal}\"，是否继续？(输入 y 继续 / n 取消)")
    user_input = input().strip().lower()
    if user_input == 'y':
        return True
    else:
        return False