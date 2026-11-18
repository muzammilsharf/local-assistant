from local_assistant import memory


def test_check_remember():
    assert memory.check_remember("remember this I like dark mode") == "I like dark mode"
    assert memory.check_remember("remember that meeting is at 3pm") == "meeting is at 3pm"
    assert memory.check_remember("remember: buy groceries") == "buy groceries"
    assert memory.check_remember("REMEMBER THIS uppercase fact") == "uppercase fact"
    assert memory.check_remember("what is the weather today?") is None


def test_facts_lifecycle(tmp_path, monkeypatch):
    facts_file = tmp_path / "facts.txt"
    monkeypatch.setattr("local_assistant.memory.FACTS_FILE", facts_file)

    assert memory.load_facts() == ""

    memory.add_fact("User is studying software engineering")
    assert memory.load_facts() == "User is studying software engineering"

    memory.add_fact("Prefers Python")
    facts = memory.load_facts()
    assert "User is studying software engineering" in facts
    assert "Prefers Python" in facts


def test_history_lifecycle(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    monkeypatch.setattr("local_assistant.memory.HISTORY_FILE", history_file)

    assert memory.load_history() == []

    messages = [
        {"role": "user", "content": f"msg {i}"}
        for i in range(10)
    ]
    memory.save_history(messages)

    loaded = memory.load_history()
    assert len(loaded) == 6
    assert loaded[0]["content"] == "msg 4"
    assert loaded[-1]["content"] == "msg 9"


def test_history_corrupt_file(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    history_file.write_text("invalid json content")
    monkeypatch.setattr("local_assistant.memory.HISTORY_FILE", history_file)

    assert memory.load_history() == []
