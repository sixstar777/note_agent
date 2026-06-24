import os
import re

def search_notes(query, top_k=3, notes_dir=None):
    if notes_dir is None:
        notes_dir = os.path.join("data", "notes")
    
    if not query or not query.strip():
        return {"error": "validation_error", "message": "查询不能为空"}
    if not os.path.exists(notes_dir):
        return {"error": "knowledge_base_missing", "message": f"笔记目录不存在: {notes_dir}"}

    files = [f for f in os.listdir(notes_dir) if f.endswith('.txt')]
    results = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for file in files:
        filepath = os.path.join(notes_dir, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = list(pattern.finditer(content))
        count = len(matches)
        if count == 0:
            continue
        first_match = matches[0]
        start = first_match.start()
        end = first_match.end()
        context_start = max(0, start - 50)
        context_end = min(len(content), end + 50)
        snippet = content[context_start:context_end]
        if context_start > 0:
            snippet = "..." + snippet
        if context_end < len(content):
            snippet = snippet + "..."
        results.append({
            "title": file,
            "snippet": snippet,
            "source": os.path.abspath(filepath),
            "count": count
        })

    results.sort(key=lambda x: x['count'], reverse=True)
    top_items = [{"title": r['title'], "snippet": r['snippet'], "source": r['source']} for r in results[:top_k]]
    return {"items": top_items}

def list_notes(notes_dir=None):
    if notes_dir is None:
        notes_dir = os.path.join("data", "notes")
    if not os.path.exists(notes_dir):
        return {"error": "knowledge_base_missing", "message": f"笔记目录不存在: {notes_dir}"}
    files = [f for f in os.listdir(notes_dir) if f.endswith('.txt')]
    return {"titles": files}