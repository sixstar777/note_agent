## AI Agent Playbook

### 1. 任务目标

智能体接受用户输入的自然语言问题，通过检索本地笔记库中的相关内容，结合大模型生成带有来源引用的回答。

**核心目标**：让用户从自己的笔记库中快速获取有依据的信息，而不是依赖大模型的固有知识。

### 2. 执行流程

智能体采用“计划 → 工具调用 → 评估 → 生成”的四步工作流：

| 步骤 | 动作 | 说明 |
| :--- | :--- | :--- |
| 步骤 0 | 输入校验 | 检查输入是否为空、超长（>500字符）或包含危险关键词（如 `rm -rf`、`delete` 等） |
| 步骤 1 | 规划与工具选择 | 判断用户目标：若含“列表”关键词则调用 `list_notes`，否则调用 `search_notes` |
| 步骤 2 | 工具执行 | 调用对应工具检索本地笔记，记录输入输出到日志 |
| 步骤 3 | 失败判断 | 若工具返回 `error`，终止流程并返回失败原因 |
| 步骤 4 | 大模型生成 | 拼接检索片段和提示词，调用 DeepSeek API 生成最终回答 |
| 步骤 5 | 返回结果 | 返回 `status`、`answer` 和完整执行日志 |

### 3. 工具与 API 使用方式

| 工具名称 | 功能 | 输入 | 输出 |
| :--- | :--- | :--- | :--- |
| `search_notes` | 在本地笔记目录中检索匹配片段 | `query` (string), `top_k` (1-5) | `{"items": [{"title", "snippet", "source"}]}` |
| `list_notes` | 列出所有笔记文件名 | 无 | `{"titles": ["file1.txt", ...]}` |

**大模型 API**：DeepSeek API（模型 `deepseek-chat`），通过 OpenAI 兼容接口调用。

### 4. 关键决策逻辑

- **工具选择决策**：用户输入包含“列表/列出” → `list_notes`；否则 → `search_notes`。
- **安全拦截决策**：输入包含 `rm -rf`、`delete`、`drop table`、`shutdown` 等关键词 → 触发人工确认（`human_confirm`），用户取消则直接拒绝。
- **失败出口决策**：工具返回 `error` → 立即终止并记录 `failed` 状态，不继续调用大模型。

### 5. 异常处理策略

| 异常类型 | 处理方式 |
| :--- | :--- |
| 输入为空或超长 | 返回 `rejected`，提示具体原因 |
| 笔记目录不存在 | 返回 `knowledge_base_missing` 错误 |
| 大模型 API 调用失败 | 捕获异常，返回 `failed` 并记录错误信息 |
| 危险操作（人工取消） | 返回 `rejected`，不执行任何工具调用 |
| 检索无匹配结果 | 返回“未找到相关笔记”，不调用大模型（节省 token） |

### 6. 日志与可观测性

每次运行均输出结构化日志，包含：
- 步骤编号（`step`）
- 动作类型（`plan` / `tool_call` / `llm_generate` / `output` / `fail`）
- 工具名称及输入摘要
- Token 消耗（提示 tokens / 生成 tokens / 总计）
- 最终状态（`success` / `rejected` / `failed`）

### 7. 运行示例

```bash
# 正常查询
python main.py --goal "机器学习"

# 列出所有笔记
python main.py --goal "列出所有笔记"

# 危险操作（触发人工确认）
python main.py --goal "rm -rf /"

# 启动 Web 界面
streamlit run app.py