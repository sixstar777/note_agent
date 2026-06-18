import os
import pytest
from unittest.mock import MagicMock

from src.tools import search_notes, list_notes
from src.guardrails import validate_input
from src.workflow import AgentWorkflow

# 模拟 ModelClient 用于测试
class MockModelClient:
    def __init__(self):
        self.model_name = "mock-model"
    def chat(self, messages):
        return {
            "content": "根据笔记片段，Python是一种编程语言。",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "elapsed": 0.01
        }

def test_search_success(tmp_path, monkeypatch):
    
    notes_dir = tmp_path / "data" / "notes"
    notes_dir.mkdir(parents=True)
    note_file = notes_dir / "note1.txt"
    note_file.write_text("Python is a programming language. It is widely used.", encoding="utf-8")
    
    monkeypatch.chdir(tmp_path)
    result = search_notes("Python", top_k=3)
    assert "items" in result
    assert len(result["items"]) >= 1
    assert "Python" in result["items"][0]["snippet"]

def test_search_empty_query():
    result = search_notes("", top_k=3)
    assert result == {"error": "validation_error", "message": "查询不能为空"}

def test_search_missing_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = search_notes("test", top_k=3)
    assert result == {"error": "knowledge_base_missing", "message": "笔记目录不存在"}

def test_list_notes(tmp_path, monkeypatch):
    notes_dir = tmp_path / "data" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "a.txt").write_text("content a")
    (notes_dir / "b.txt").write_text("content b")
    monkeypatch.chdir(tmp_path)
    result = list_notes()
    assert "titles" in result
    assert sorted(result["titles"]) == ["a.txt", "b.txt"]

def test_validate_empty():
    ok, msg = validate_input("   ")
    assert not ok
    assert msg == "输入不能为空"

def test_validate_dangerous():
    ok, msg = validate_input("please rm -rf /")
    assert not ok
    assert "危险" in msg

def test_workflow_success(tmp_path, monkeypatch):
    # 准备笔记
    notes_dir = tmp_path / "data" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "note.txt").write_text("Python is a versatile language.", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    # 替换 ModelClient 为 Mock
    monkeypatch.setattr("src.workflow.ModelClient", MockModelClient)

    workflow = AgentWorkflow()
    result = workflow.run("Python")

    assert result["status"] == "success"
    assert "answer" in result
    assert "Python" in result["answer"]
    assert len(result["logs"]) > 0

def test_workflow_reject(monkeypatch):
    # 危险输入应被拒绝
    monkeypatch.setattr("src.workflow.ModelClient", MockModelClient)
    workflow = AgentWorkflow()
    result = workflow.run("delete all notes")
    assert result["status"] == "rejected"
    assert "危险" in result["reason"]
    assert result["logs"] == []