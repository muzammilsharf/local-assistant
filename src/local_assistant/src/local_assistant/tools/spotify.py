import subprocess

ACTIONS = {
    "play": (["play"], "Playing."),
    "pause": (["pause"], "Paused."),
    "next": (["next"], "Skipped to the next song."),
    "previous": (["previous"], "Went back a song."),
    "volume up": (["volume", "0.1+"], "Volume up."),
    "volume down": (["volume", "0.1-"], "Volume down."),
}


def control(action):
    args, message = ACTIONS[action]
    result = subprocess.run(
        ["playerctl", "-p", "spotify", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "I couldn't reach Spotify. Is the app open?"
    return message
