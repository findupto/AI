from apps.export_conversation import select_session


def test_select_session_accepts_id_and_case_insensitive_title():
    sessions = [{"id": "abc", "title": "My Chat"}]
    assert select_session(sessions, "abc")["id"] == "abc"
    assert select_session(sessions, "MY CHAT")["id"] == "abc"
    assert select_session(sessions, "missing") is None
