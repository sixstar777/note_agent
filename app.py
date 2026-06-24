import streamlit as st
import json
import os

# 导入工作流
from src.workflow import AgentWorkflow

# 页面配置
st.set_page_config(
    page_title="智能笔记研究助手",
    page_icon="",
    layout="wide"
)

# 自定义 CSS 提升专业感
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        letter-spacing: -0.5px;
        color: #1f1f1f;
        padding-bottom: 0.2rem;
        border-bottom: 2px solid #e6e6e6;
    }
    .sub-header {
        color: #666666;
        font-size: 0.95rem;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }
    .config-title {
        font-weight: 600;
        font-size: 1.1rem;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    .log-json {
        background-color: #f8f8f8;
        padding: 0.8rem;
        border-radius: 4px;
        border-left: 3px solid #cccccc;
    }
    .status-success {
        background-color: #e8f5e9;
        padding: 1rem 1.2rem;
        border-radius: 4px;
        border-left: 4px solid #2e7d32;
        color: #1e3a1e;
    }
    .status-error {
        background-color: #ffebee;
        padding: 1rem 1.2rem;
        border-radius: 4px;
        border-left: 4px solid #c62828;
        color: #4a1414;
    }
    .status-reject {
        background-color: #fff3e0;
        padding: 1rem 1.2rem;
        border-radius: 4px;
        border-left: 4px solid #e65100;
        color: #4a2a0a;
    }
    .status-info {
        background-color: #e3f2fd;
        padding: 1rem 1.2rem;
        border-radius: 4px;
        border-left: 4px solid #0d47a1;
        color: #0a1e3a;
    }
</style>
""", unsafe_allow_html=True)

# 顶部标题
st.markdown('<p class="main-header">智能笔记研究助手</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">基于本地笔记检索与大模型生成的智能问答系统</p>', unsafe_allow_html=True)

# ---------- 侧边栏配置 ----------
with st.sidebar:
    st.markdown('<p class="config-title">系统配置</p>', unsafe_allow_html=True)
    
    # 笔记目录选择器
    notes_dir = st.text_input(
        "笔记存储路径",
        value="data/notes",
        help="指定存放 .txt 笔记文件的目录路径"
    )
    
    st.caption("当前模型: DeepSeek API (deepseek-chat)")
    
    st.markdown("---")
    
    st.markdown('<p class="config-title">使用说明</p>', unsafe_allow_html=True)
    st.markdown(
        """
        - 输入与学习相关的问题
        - 系统将在指定目录中检索笔记
        - 结合检索结果生成回答
        - 若未找到相关内容，会明确告知
        - 危险操作（如删除命令）将被拦截
        """
    )
    
    st.markdown("---")
    st.caption("笔记目录需包含 .txt 文件")

# ---------- 主界面 ----------
col_input, col_button = st.columns([5, 1])
with col_input:
    goal = st.text_input(
        "输入你的问题",
        placeholder="例如: 解释一下机器学习中的梯度下降",
        label_visibility="collapsed"
    )
with col_button:
    submitted = st.button("执行", type="primary", use_container_width=True)

# 中间分隔线
st.markdown("---")

# 结果展示区域
if submitted:
    if not goal or not goal.strip():
        st.markdown(
            '<div class="status-info">请输入有效的问题。</div>',
            unsafe_allow_html=True
        )
    else:
        with st.spinner("智能体正在检索笔记并生成回答..."):
            try:
                # 实例化工作流，传入自定义目录
                workflow = AgentWorkflow(notes_dir=notes_dir)
                result = workflow.run(goal)
                
                # 根据状态显示不同的结果框
                status = result.get("status")
                
                if status == "success":
                    st.markdown(
                        '<div class="status-success">执行成功</div>',
                        unsafe_allow_html=True
                    )
                    answer = result.get("answer", "无返回内容")
                    # 如果 answer 是字典（比如 list_notes 的结果），美化展示
                    if isinstance(answer, dict):
                        st.json(answer)
                    else:
                        st.write(answer)
                
                elif status == "rejected":
                    reason = result.get("reason", "未知原因")
                    st.markdown(
                        f'<div class="status-reject">请求被拒绝: {reason}</div>',
                        unsafe_allow_html=True
                    )
                
                else:
                    reason = result.get("reason", "未知错误")
                    st.markdown(
                        f'<div class="status-error">执行失败: {reason}</div>',
                        unsafe_allow_html=True
                    )
                
                # 可折叠的执行日志（专业风格）
                with st.expander("查看执行日志"):
                    logs = result.get("logs", [])
                    if logs:
                        for log in logs:
                            # 用灰色块展示每条日志
                            st.markdown(
                                f'<div class="log-json"><pre style="margin:0; font-size:0.85rem;">{json.dumps(log, ensure_ascii=False, indent=2)}</pre></div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.caption("无日志记录")
                
                # Token 统计（如果有）
                if "token_usage" in result:
                    tokens = result["token_usage"]
                    st.caption(
                        f"Token 消耗: 提示 {tokens.get('prompt_tokens', 0)} | "
                        f"生成 {tokens.get('completion_tokens', 0)} | "
                        f"总计 {tokens.get('total_tokens', 0)}"
                    )
            
            except Exception as e:
                st.markdown(
                    f'<div class="status-error">系统异常: {str(e)}</div>',
                    unsafe_allow_html=True
                )
                st.exception(e)

else:
    st.markdown(
        '<div class="status-info">输入问题后点击「执行」按钮开始检索。</div>',
        unsafe_allow_html=True
    )