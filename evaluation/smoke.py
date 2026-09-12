from knowledge.store import KnowledgeStore
from security.policy import Policy


def test_policy_defaults():
    p = Policy({"security": {}})
    assert p.network_allowed() is False
    assert p.shell_allowed() is False
    assert p.tool_confirmation_required() is True


def test_knowledge_roundtrip(tmp_path):
    db = tmp_path / "knowledge.db"
    k = KnowledgeStore(str(db), chunk_size=20, overlap=3)
    k.ingest("local:test", "standalone local AI retrieval provenance")
    rows = k.search("retrieval")
    assert rows and rows[0]["source"] == "local:test"
