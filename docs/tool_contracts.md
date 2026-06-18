## 协议化工具：search_notes
- **用途**：根据用户查询，在本地笔记目录中检索相关笔记片段
- **输入**：
  - `query` (string, required): 搜索关键词，不能为空
  - `top_k` (integer, 1-5, default=3): 返回最多结果数
- **输出（成功）**：`{"items": [{"title": string, "snippet": string, "source": string}]}`
- **输出（失败）**：
  - `validation_error`: query 为空
  - `knowledge_base_missing`: data/notes 目录不存在
- **安全边界**：只读取 `data/notes` 目录下的 .txt 文件，不访问任何其他本地路径
