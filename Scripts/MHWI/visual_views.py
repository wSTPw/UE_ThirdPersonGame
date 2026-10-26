"""Temporary PIE views only. Author final transforms in author_assets.py, never this file."""
import unreal
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
def pawn(): return unreal.GameplayStatics.get_player_character(editor.get_game_world(),0)
def view(yaw):
 p=pawn()
 p.get_editor_property('spring_arm').set_editor_property('target_arm_length',270.0)
 p.get_editor_property('spring_arm').set_editor_property('socket_offset',unreal.Vector(0,0,10))
 unreal.GameplayStatics.get_player_controller(editor.get_game_world(),0).set_control_rotation(unreal.Rotator(pitch=-10,yaw=yaw))
def front(): view(160)
def side(): view(80)
def back(): view(0)
def draw():
 p=pawn()
 if p.is_sheathed(): p.request_input(unreal.MHWIInput.TOGGLE_SHEATHE)
 front()
def sheath():
 p=pawn()
 if not p.is_sheathed(): p.request_input(unreal.MHWIInput.TOGGLE_SHEATHE)
 back()
