import json
from pathlib import Path


def test_default_config_is_valid():
    config = json.loads(Path("config/default.json").read_text(encoding="utf-8"))
    assert config["app_name"] == "Findupto AI"
    assert config["security"]["allow_network"] is False


def test_python_tool_timeout_and_bounded_builtins():
    from tools.python_tool import run_python

    ok, output = run_python("print(sum([1, 2, 3]))", timeout=2)
    assert ok is True
    assert output.strip() == "6"

    ok, _ = run_python("import os", timeout=2)
    assert ok is False

    ok, message = run_python("while True: pass", timeout=1)
    assert ok is False
    assert "timed out" in message.lower()


def test_knowledge_search_handles_natural_language(tmp_path):
    from knowledge.store import KnowledgeStore

    db = tmp_path / "knowledge.db"
    k = KnowledgeStore(str(db), chunk_size=20, overlap=3)
    k.ingest("local:test", "standalone local AI retrieval provenance")
    rows = k.search("Where is the retrieval provenance?")
    assert rows and rows[0]["source"] == "local:test"


def test_knowledge_document_management(tmp_path):
    from knowledge.store import KnowledgeStore

    k = KnowledgeStore(str(tmp_path / "knowledge.db"))
    k.ingest("local:one", "first document")
    k.ingest("local:two", "second document")
    assert {row["source"] for row in k.documents()} == {"local:one", "local:two"}
    assert k.delete("local:one") is True
    assert [row["source"] for row in k.documents()] == ["local:two"]
    assert k.search("first document") == []
    assert k.delete("local:missing") is False


def test_memory_store_is_thread_safe(tmp_path):
    from memory.store import MemoryStore
    import threading

    store = MemoryStore(str(tmp_path / "memory.db"))

    def write(i):
        store.add("user", f"message-{i}")

    threads = [threading.Thread(target=write, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(store.recent(20)) == 8
