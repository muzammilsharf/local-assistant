import json
from unittest.mock import patch

from local_assistant import router


def test_route_spotify_commands():
    with patch("local_assistant.router.control", return_value="Playing.") as mock_ctrl:
        assert router.route("play music") == "Playing."
        mock_ctrl.assert_called_once_with("play")

    with patch("local_assistant.router.control", return_value="Paused.") as mock_ctrl:
        assert router.route("pause") == "Paused."
        mock_ctrl.assert_called_once_with("pause")

    with patch("local_assistant.router.control", return_value="Skipped.") as mock_ctrl:
        assert router.route("next song") == "Skipped."
        mock_ctrl.assert_called_once_with("next")

    with patch("local_assistant.router.control", return_value="Volume up.") as mock_ctrl:
        assert router.route("louder") == "Volume up."
        mock_ctrl.assert_called_once_with("volume up")


def test_route_open_folder(tmp_path, monkeypatch):
    folder_dir = tmp_path / "documents"
    folder_dir.mkdir()
    folders_file = tmp_path / "folders.json"
    folders_file.write_text(json.dumps({"documents": str(folder_dir)}))

    monkeypatch.setattr("local_assistant.tools.files.FOLDERS_FILE", folders_file)

    with patch("subprocess.Popen") as mock_popen:
        res = router.route("open my documents folder")
        assert res == "Opened documents."
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args == ["xdg-open", str(folder_dir)]


def test_route_open_folder_missing(tmp_path, monkeypatch):
    folders_file = tmp_path / "folders.json"
    folders_file.write_text(json.dumps({"uni": str(tmp_path / "nonexistent")}))

    monkeypatch.setattr("local_assistant.tools.files.FOLDERS_FILE", folders_file)

    res = router.route("open uni")
    assert "doesn't exist" in res


def test_route_unknown_folder(tmp_path, monkeypatch):
    folders_file = tmp_path / "folders.json"
    folders_file.write_text(json.dumps({"downloads": str(tmp_path)}))

    monkeypatch.setattr("local_assistant.tools.files.FOLDERS_FILE", folders_file)

    res = router.route("open music")
    assert "I don't know a folder called 'music'" in res


def test_route_unmatched():
    assert router.route("create a document about trees") is None
    assert router.route("hello there") is None
