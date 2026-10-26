"""Run with UnrealEditor -ExecutePythonScript to verify startup and a short PIE session.

Writes Saved/Upgrade-UE58/EditorSmoke.json; does not save project assets.
"""
import json
import time
import traceback
from pathlib import Path

import unreal

output = Path(unreal.Paths.project_saved_dir()) / "Upgrade-UE58" / "EditorSmoke.json"
output.parent.mkdir(parents=True, exist_ok=True)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
result = {
    "engine_version": unreal.SystemLibrary.get_engine_version(),
    "project_dir": unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "editor_world": editor.get_editor_world().get_path_name(),
    "editor_actor_count": len(actors.get_all_level_actors()),
    "passed": False,
    "sessions": [],
}
assert result["engine_version"].startswith("5.8."), result
assert "/Game/MyStuff/Lvl_Start" in result["editor_world"], result
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
started = time.monotonic()
state = {"phase": "starting", "playing_at": None, "map": "Lvl_Start"}


def finish(error=None):
    if error:
        result["error"] = error
        unreal.log_error("UE58_SMOKE_FAILED: " + error)
    else:
        result["passed"] = True
        unreal.log("UE58_SMOKE_PASSED: " + json.dumps(result))
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(tick_handle)
    if level.is_in_play_in_editor():
        level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def tick(delta_seconds):
    try:
        now = time.monotonic()
        if now - started > 180:
            finish("PIE smoke test timed out")
            return
        if state["phase"] == "starting" and level.is_in_play_in_editor():
            world = editor.get_game_world()
            if not world:
                return
            if not world.get_name().endswith(state["map"]):
                return
            result["game_world"] = world.get_path_name()
            result["game_actor_count"] = len(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor))
            state.update(phase="playing", playing_at=now)
        elif state["phase"] == "playing" and now - state["playing_at"] >= 10:
            if not level.is_in_play_in_editor():
                finish("PIE ended before the 10-second smoke test completed")
                return
            result["pie_seconds"] = round(now - state["playing_at"], 2)
            level.editor_request_end_play()
            state["phase"] = "stopping"
        elif state["phase"] == "stopping" and not level.is_in_play_in_editor():
            result["sessions"].append({key: result[key] for key in ("game_world", "game_actor_count", "pie_seconds")})
            if len(result["sessions"]) == 1:
                if not level.load_level("/Game/MyStuff/MyLevel"):
                    finish("Could not load /Game/MyStuff/MyLevel")
                    return
                state.update(phase="loading", map="MyLevel")
            else:
                finish()
        elif state["phase"] == "loading":
            if "/Game/MyStuff/MyLevel." in editor.get_editor_world().get_path_name():
                state["phase"] = "starting"
                level.editor_request_begin_play()
    except Exception:
        finish(traceback.format_exc())


tick_handle = unreal.register_slate_post_tick_callback(tick)
level.editor_request_begin_play()
