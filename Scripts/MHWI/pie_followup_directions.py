"""Live explicit-route rolls and free SpecialSheathe entry; no asset edits."""
from pathlib import Path
import math
import time
import unreal
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pie_behavior_corrections as base
_ACTIVE=None

class Directions(base.BehaviorRunner):
    def __init__(self):
        super().__init__('direction')
        self.suites=['followup_directions']
        base.SUITE_TIMEOUT['followup_directions']=180.
        self.report_file=Path(unreal.Paths.project_saved_dir())/'MHWIRestoration/B23-20261030/PIE-directions.json'
        self.report['notes']=['Production pawn/routes; OverheadSlash uses neutral StartMove fixture. Targets use RequestInput; movement uses Enhanced Input. No assets/costs/clocks edited.']
        self.cases=[('evade',0.,1.,0.,'Roll'),('evade',-1.,0.,0.,'RollLeft'),('evade',1.,0.,0.,'RollRight'),('evade',0.,-1.,0.,'RollBack')]
        for yaw in (35.,-110.):
            for degrees in range(0,360,45):
                r=math.radians(degrees)
                self.cases.append(('special',math.sin(r),math.cos(r),yaw,'SpecialSheathe'))
        self.cases.append(('special',0.,0.,70.,'SpecialSheathe'))
        self.index=0
    def _begin_suite(self,name):
        self.current_suite=name
        self.suite_started=time.monotonic()
        self._phase('direction_prepare',15.)
    def _phase_direction_prepare(self,elapsed):
        self._stop_inputs()
        if self.index==len(self.cases):
            self._suite_done();return
        if not self._idle():self.pawn.interrupt_move()
        self._require_drawn('direction_start',15.)
    def _phase_direction_start(self,elapsed):
        if elapsed<.02:
            self._reset_fixture(3000.)
            self._set_control_yaw(self.cases[self.index][3])
        if self.pawn.character_movement.is_falling():return
        self._check(self.pawn.start_move('OverheadSlash'),'source attack starts '+str(self.index))
        self.intent_sent=False
        self._phase('direction_window',10.)
    def _phase_direction_window(self,elapsed):
        command,x,y,yaw,expected=self.cases[self.index]
        if self._current()!='OverheadSlash':raise base.BehaviorFailure('source ended before request '+str(self.index))
        definition=self._def('OverheadSlash')
        if self._position()<.25:return
        if not self.intent_sent:
            self._move(x,y);self.intent_sent=True;self.intent_at=time.monotonic();return
        if time.monotonic()-self.intent_at<.06:return
        if not self._cancel_ready(definition,command):return
        if command=='evade':self._check(self._find_route(definition,'evade','Roll') is not None,'explicit Evade route exists')
        self.before_yaw=self._actor_yaw()
        dx,dy=self._world_intent(x,y)
        self.expected_yaw=math.degrees(math.atan2(dy,dx)) if x or y else self.before_yaw
        self.window=self._cancel_window(definition,command)
        self.request_position=self._position()
        enum=unreal.MHWIInput.EVADE if command=='evade' else unreal.MHWIInput.SPECIAL_SHEATHE
        self._check(self.pawn.request_input(enum),'target command accepted '+str(self.index))
        self._phase('direction_result',5.)
    def _phase_direction_result(self,elapsed):
        command,x,y,yaw,expected=self.cases[self.index]
        if self._current()=='OverheadSlash':return
        self._check(self._current()==expected,'selected '+expected+' case '+str(self.index))
        self._check(self.window[0]<=self.request_position<=self.window[1],'request inside matching window')
        target_yaw=(self.expected_yaw if expected=='Roll' and (x or y) else self.before_yaw) if command=='evade' else self.expected_yaw
        error=abs(base._yaw_delta(target_yaw,self._actor_yaw()))
        self._check(error<2.,'entry direction case '+str(self.index))
        self._record('direction_cases',case=self.index,input=command,x=x,y=y,camera_yaw=yaw,move=self._current(),expected_yaw=target_yaw,actual_yaw=self._actor_yaw(),error=error,request_position=self.request_position,window=self.window,diagnostic=self.pawn.get_native_playback_diagnostic())
        self._stop_inputs();self.pawn.interrupt_move();self.index+=1
        self._phase('direction_prepare',15.)

def run():
    global _ACTIVE
    if _ACTIVE and not _ACTIVE.done:raise RuntimeError('Direction test active')
    _ACTIVE=Directions();_ACTIVE.prepare_editor()
    _ACTIVE.handle=unreal.register_slate_post_tick_callback(_ACTIVE.tick)
    return str(_ACTIVE.report_file)
