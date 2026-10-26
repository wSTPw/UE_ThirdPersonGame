"""UE editor startup script: real montage/action regression in disposable MyLevel PIE.

Run with -ExecutePythonScript=<absolute path>. Does not save any asset.
Writes Saved/ActionRefactor-20261019/PIE.json and leaves the editor open.
"""
import json
import time
import traceback
from pathlib import Path

import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / "ActionRefactor-20261019" / "PIE.json"
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
result = {"passed": False, "checks": [], "engine": unreal.SystemLibrary.get_engine_version()}
state = {"phase": "load", "started": time.monotonic(), "at": time.monotonic()}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def check(condition, label):
    result["checks"].append({"check": label, "passed": bool(condition)})
    assert condition, label


def phase(name):
    clock = unreal.GameplayStatics.get_time_seconds(state["world"]) if state.get("world") else time.monotonic()
    state.update(phase=name, at=clock)
    unreal.log("ACTION_PIE_PHASE: " + name)


def finish(error=None):
    if state.get("performance_settings"):
        state["performance_settings"].set_editor_property("bThrottleCPUWhenNotForeground", state["old_throttle"])
    if error:
        result["error"] = error
        unreal.log_error("ACTION_PIE_FAILED: " + error)
    else:
        result["passed"] = True
        unreal.log("ACTION_PIE_PASSED")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(handle)
    if level.is_in_play_in_editor():
        level.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def equip(data):
    item = unreal.ItemInstance(item_id=data.get_editor_property("item_id"), quantity=1)
    check(state["inv"].set_quick_slot(0, item), "weapon source set")
    state["inv"].select_quick_slot(0)
    state["player"].equip_weapon(data)


def tick(delta):
    try:
        wall_now = time.monotonic()
        now = unreal.GameplayStatics.get_time_seconds(state["world"]) if state.get("world") else wall_now
        if wall_now - state["started"] > 180:
            finish("PIE timeout in " + state["phase"])
            return
        p = state["phase"]
        elapsed = now - state["at"]
        if p == "load":
            check(level.load_level("/Game/MyStuff/MyLevel"), "MyLevel loaded")
            phase("begin")
        elif p == "begin":
            level.editor_request_begin_play()
            phase("wait_player")
        elif p == "wait_player":
            world = editor.get_game_world()
            if not world:
                return
            player = unreal.GameplayStatics.get_player_character(world, 0)
            if not player:
                return
            state.update(world=world, player=player, actions=player.get_editor_property("actions"),
                         inv=player.get_editor_property("inventory_component"),
                         attrs=player.get_editor_property("attribute_comp"))
            settings_class = unreal.load_class(None, "/Script/UnrealEd.EditorPerformanceSettings")
            if settings_class:
                # Use the reflected C++ name; CPU acronym snake-case varies by wrapper.
                settings = unreal.get_default_object(settings_class)
                state.update(performance_settings=settings, old_throttle=settings.get_editor_property("bThrottleCPUWhenNotForeground"))
                settings.set_editor_property("bThrottleCPUWhenNotForeground", False)
            state["attrs"].set_editor_property("mana_regen_per_second", 0.0)
            state["attrs"].set_editor_property("health_regen_per_second", 0.0)
            state["sword"] = unreal.load_asset("/Game/Data/Items/Weapons/DA_WP_LongSword")
            state["staff"] = unreal.load_asset("/Game/Data/Items/Weapons/DA_WP_FireStaff")
            state["potion"] = unreal.load_asset("/Game/Data/Items/DA_HP_Potion")
            check(all(state[k] for k in ("actions", "inv", "attrs", "sword", "staff", "potion")), "runtime components and exact assets exist")
            phase("warmup")
        elif p == "warmup" and elapsed > 1:
            equip(state["sword"])
            request = state["actions"].request_attack()
            check(request.status == unreal.CharacterActionRequestStatus.STARTED, "longsword starts")
            state.update(combo=0, combo_at=now, buffered=False, combos=[0])
            phase("combo")
        elif p == "combo":
            actions = state["actions"]
            snapshot = actions.get_snapshot()
            if snapshot.combo_index != state["combo"] and actions.is_busy():
                state.update(combo=snapshot.combo_index, combo_at=now, buffered=False)
                state["combos"].append(snapshot.combo_index)
            if actions.is_busy() and not state["buffered"] and now - state["combo_at"] > 0.42:
                request = actions.request_attack()
                check(request.status == unreal.CharacterActionRequestStatus.BUFFERED, "one buffered input accepted in combo " + str(state["combo"]))
                state["buffered"] = True
            if not actions.is_busy():
                check(state["combos"] == [0, 1, 2, 3], "all four combo sections reached once")
                check(actions.get_last_failure() == unreal.CharacterActionFailure.NONE, "combo received every required event")
                check(snapshot.kind == unreal.CharacterActionKind.NONE, "action snapshot returns to idle")
                phase("cast_cancel_start")
            elif elapsed > 12:
                raise AssertionError("combo did not finish")
        elif p == "cast_cancel_start":
            equip(state["staff"])
            state["attrs"].set_mana(50.0)
            state["mp_before"] = state["attrs"].get_current_mana()
            check(state["actions"].request_attack().status == unreal.CharacterActionRequestStatus.STARTED, "fireball starts")
            phase("cast_cancel")
        elif p == "cast_cancel" and elapsed > 0.1:
            state["actions"].interrupt()
            check(not state["actions"].is_busy(), "cast interrupt releases foreground")
            check(state["attrs"].get_current_mana() == state["mp_before"], "interrupt before commit spends no mana")
            phase("cast_start")
        elif p == "cast_start" and elapsed > 0.25:
            check(state["actions"].request_attack().status == unreal.CharacterActionRequestStatus.STARTED, "fireball restarts safely on same montage")
            state["projectile_seen"] = False
            phase("cast")
        elif p == "cast":
            for actor in unreal.GameplayStatics.get_all_actors_of_class(state["world"], unreal.Actor):
                if actor.get_owner() == state["player"] and "fireball" in actor.get_class().get_name().lower():
                    state["projectile_seen"] = True
                    state["projectile_damage"] = actor.get_editor_property("damage")
            if not state["actions"].is_busy():
                check(state["projectile_seen"], "real fireball spawned with player owner")
                cost = state["staff"].get_editor_property("weapon_mana_cost")
                check(abs(state["attrs"].get_current_mana() - (state["mp_before"] - cost)) < 0.01, "fireball spends mana once")
                override = state["staff"].get_editor_property("weapon_damage_override")
                if override:
                    check(state["projectile_damage"] == override, "projectile receives damage override")
                state["attrs"].set_mana(0.0)
                check(state["actions"].request_attack().failure == unreal.CharacterActionFailure.INSUFFICIENT_MANA, "insufficient mana rejects before playback")
                phase("potion_start")
            elif elapsed > 7:
                raise AssertionError("fireball did not finish")
        elif p == "potion_start":
            inv = state["inv"]
            potion_id = state["potion"].get_editor_property("item_id")
            inv.set_item_at(0, unreal.ItemInstance(item_id=potion_id, quantity=5))
            check(inv.set_quick_slot(0, unreal.ItemInstance(item_id=potion_id, quantity=1)), "last quickslot potion prepared")
            inv.select_quick_slot(0)
            state["attrs"].set_health(30.0)
            check(state["actions"].request_use_item(True, 0).status == unreal.CharacterActionRequestStatus.STARTED, "drink starts from original quickslot")
            check(not inv.set_quick_slot(0, unreal.ItemInstance(item_id=potion_id, quantity=9)), "source replacement rejected while drinking")
            check(state["actions"].request_attack().failure == unreal.CharacterActionFailure.BUSY, "attack cannot overlap drink")
            phase("potion")
        elif p == "potion":
            if not state["actions"].is_busy():
                check(state["attrs"].get_current_health() > 30.0, "real drink notify applies heal")
                check(state["inv"].get_quick_slot(0).quantity == 0, "last original quickslot item consumed")
                check(state["inv"].get_item_at(0).quantity == 5, "same-ID backpack source unchanged")
                check(state["actions"].get_last_failure() == unreal.CharacterActionFailure.NONE, "drink ends cleanly")
                phase("potion_interrupt_start")
            elif elapsed > 7:
                raise AssertionError("drink did not finish")
        elif p == "potion_interrupt_start":
            check(state["actions"].request_use_item(False, 0).status == unreal.CharacterActionRequestStatus.STARTED, "backpack source uses same action backend")
            phase("potion_interrupt")
        elif p == "potion_interrupt" and elapsed > 0.1:
            state["actions"].interrupt()
            check(state["inv"].get_item_at(0).quantity == 5, "interrupt before drink commit leaves source intact")
            check(not state["actions"].is_busy(), "all scenarios release foreground")
            equip(state["sword"])
            check(state["actions"].request_attack().status == unreal.CharacterActionRequestStatus.STARTED, "authored cancel scenario starts")
            state["cancel_run"] = state["actions"].get_snapshot().run_id
            check(not state["actions"].try_cancel_action(state["cancel_run"] + 100), "stale cancel identity rejected")
            check(not state["actions"].try_cancel_action(state["cancel_run"]), "cancel before authored window rejected")
            phase("cancel_window")
        elif p == "cancel_window":
            montage = unreal.load_asset("/Game/MyStuff/Model/Robot/M_LongSwordAttack")
            position = state["player"].get_editor_property("Mesh").get_anim_instance().montage_get_position(montage)
            if position >= 0.94:
                check(state["actions"].try_cancel_action(state["cancel_run"]), "authored cancel window permits current run")
                check(not state["actions"].is_busy(), "voluntary cancel releases foreground")
                check(state["actions"].request_use_item(False, 0).status == unreal.CharacterActionRequestStatus.STARTED, "death scenario starts drink")
                phase("death")
            elif elapsed > 4:
                raise AssertionError("cancel window never reached")
        elif p == "death" and elapsed > 0.1:
            state["attrs"].set_health(0.0)
            check(not state["actions"].is_busy(), "real death during montage releases foreground")
            check(state["inv"].get_item_at(0).quantity == 5, "death before commit does not consume item")
            check(state["actions"].request_attack().failure == unreal.CharacterActionFailure.DEAD, "dead actor cannot start attack")
            check(state["actions"].get_snapshot().move_scale == 0.0, "dead snapshot disables movement")
            finish()
    except Exception:
        finish(traceback.format_exc())


handle = unreal.register_slate_post_tick_callback(tick)
