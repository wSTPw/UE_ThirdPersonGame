"""Static and model checks for the MHWI PC keyboard adapter; no Unreal runtime."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CPP_PATH = ROOT / 'Source/IntroCpp/MHWI/MHWICharacter.cpp'
HEADER_PATH = ROOT / 'Source/IntroCpp/MHWI/MHWICharacter.h'
HUD_PATH = ROOT / 'Source/IntroCpp/MHWIUI/MHWIHUD.cpp'
REPORT_PATH = ROOT / 'Saved/MHWIImport/KeyboardAdaptation-static.json'

LIGHT, THRUST, SPIRIT = 'Light', 'Thrust', 'Spirit'
FORESIGHT, HELM, SPECIAL = 'Foresight', 'HelmBreaker', 'SpecialSheathe'
EVADE, TOGGLE, FADE, SLINGER = 'Evade', 'ToggleSheathe', 'FadeSlash', 'SlingerBurst'
ATTACKS = {LIGHT, THRUST, SPIRIT}


class KeyboardModel:
    """Executable specification of ResolveKeyboardFrameInputEdges, not engine proof."""
    def __init__(self):
        self.held = set()

    def frame(self, pressed=(), released=()):
        self.held.difference_update(released)
        edges = set(pressed)
        self.held.update(pressed)
        spirit = SPIRIT in self.held or SPIRIT in edges
        light = LIGHT in self.held or LIGHT in edges
        thrust = THRUST in self.held or THRUST in edges
        evade = EVADE in self.held or EVADE in edges
        chord = None
        if spirit and evade and edges & {SPIRIT, EVADE}:
            chord = SPECIAL
        elif spirit and light and edges & {SPIRIT, LIGHT}:
            chord = HELM
        elif spirit and thrust and edges & {SPIRIT, THRUST}:
            chord = FORESIGHT
        elif light and thrust and edges & {LIGHT, THRUST}:
            chord = FADE
        if chord:
            edges.difference_update(ATTACKS)
            if chord == SPECIAL:
                edges.discard(EVADE)
            edges.add(chord)
        # Chords are placed before leftover non-attack commands only for stable reports.
        ordered = ([chord] if chord else []) + [edge for edge in pressed if edge in edges and edge != chord]
        return ordered


def function_body(text, name, next_name):
    start = text.index('void AMHWICharacter::' + name + '(')
    end = text.index('void AMHWICharacter::' + next_name + '(', start)
    return text[start:end]


def main():
    cpp = CPP_PATH.read_text(encoding='utf-8')
    header = HEADER_PATH.read_text(encoding='utf-8')
    hud = HUD_PATH.read_text(encoding='utf-8')
    checks = []

    def check(condition, label):
        checks.append({'check': label, 'passed': bool(condition)})

    match = re.search(r'const FKey Keyboard\[\]\s*=\s*\{(.*?)\};', cpp, re.S)
    check(match is not None, 'Keyboard binding table exists')
    keys = re.findall(r'EKeys::(\w+)', match.group(1)) if match else []
    expected = ['LeftMouseButton', 'RightMouseButton', 'LeftControl', 'Invalid', 'Invalid',
                'Invalid', 'SpaceBar', 'E', 'Invalid', 'V']
    check(keys == expected, 'PC keys match LMB/RMB/Ctrl/chords/Space/E/V')
    check('RuntimeMapping->MapKey(Action, Keyboard[Index])' not in cpp,
          'Legacy gamepad actions cannot receive keyboard keys')
    check('RuntimeMapping->MapKey(KeyboardAction, Keyboard[Index])' in cpp,
          'Keyboard actions own the PC physical bindings')
    check('TEXT("MHWI_Command_%d")' in cpp and 'TEXT("MHWI_KeyboardCommand_%d")' in cpp,
          'Legacy names remain and keyboard action names are separate')
    check('RuntimeMapping->MapKey(KeyboardSprintAction, EKeys::LeftShift)' in cpp,
          'Left Shift uses the keyboard-only sprint action')
    check('RuntimeMapping->MapKey(SprintAction, EKeys::LeftShift)' not in cpp,
          'Gamepad sprint action has no keyboard binding')

    keyboard_start = cpp.index('void AMHWICharacter::KeyboardCommandStarted(')
    keyboard_end = cpp.index('void AMHWICharacter::ResolveFrameInputEdges(', keyboard_start)
    callbacks = cpp[keyboard_start:keyboard_end]
    check('bOriginalInputPreset' not in callbacks, 'PC callbacks do not branch on the gamepad preset')
    check('bSheathed && (Input == EMHWIInput::Thrust || Input == EMHWIInput::ToggleSheathe)' in callbacks,
          'Sheathed PC RMB/E are filtered without changing gamepad RequestInput')
    resolver = function_body(cpp, 'ResolveKeyboardFrameInputEdges', 'SetInputBlocked')
    check('HasNewMember' in resolver, 'Every PC chord is gated by a new member edge')
    for command in (SPECIAL, HELM, FORESIGHT, FADE):
        check(resolver.count('RequestInput(EMHWIInput::' + command + ')') == 1,
              command + ' has one chord submission site')
    check(resolver.index('EMHWIInput::SpecialSheathe') < resolver.index('EMHWIInput::HelmBreaker')
          < resolver.index('EMHWIInput::Foresight') < resolver.index('EMHWIInput::FadeSlash'),
          'Documented project chord priority is explicit')
    tick_start = cpp.index('void AMHWICharacter::Tick(float DeltaSeconds)')
    tick = cpp[tick_start:tick_start + 600]
    check('ResolveKeyboardFrameInputEdges();\n    if (bOriginalInputPreset) ResolveFrameInputEdges();' in tick,
          'PC resolver runs independently before the optional gamepad resolver')
    check('KeyboardFrameInputEdges.Reset();' in cpp, 'PC pending edges have an explicit clear path')
    check('bKeyboardSpiritHeld = bKeyboardLightHeld = bKeyboardThrustHeld = bKeyboardEvadeHeld = false;' in cpp,
          'UnPossessed clears all PC held state')
    check('LastRequestedInput = Input;\n    ++InputRequestSerial;' in cpp,
          'Read-only request diagnostics count every command attempt')
    check('GetInputRequestSerial()' in header and 'GetLastRequestedInput()' in header,
          'Blueprint-readable diagnostics are declared')

    for hint in ('Ctrl Spirit Blade', 'Ctrl + LMB Helm', 'Ctrl + RMB Foresight',
                 'Ctrl + Space Special Sheathe', 'LMB + RMB Fade', 'E Sheathe (drawn)',
                 'Shift Sprint/Sheathe'):
        check(hint in hud, 'HUD contains: ' + hint)
    for old_hint in ('R Spirit', 'F Foresight', 'G Hit Helm', 'Q Special Sheathe', 'C Fade'):
        check(old_hint not in hud, 'HUD removed old hint: ' + old_hint)

    model_cases = []
    def model_case(label, sequence, expected):
        model = KeyboardModel()
        actual = [model.frame(*frame) for frame in sequence]
        model_cases.append({'case': label, 'expected': expected, 'actual': actual,
                            'passed': actual == expected})

    for key in (LIGHT, THRUST, SPIRIT, EVADE, TOGGLE, SLINGER):
        model_case('single PC command: ' + key, [((key,), ())], [[key]])
    for keys, expected_command in (((SPIRIT, LIGHT), HELM), ((SPIRIT, THRUST), FORESIGHT),
                                   ((LIGHT, THRUST), FADE), ((SPIRIT, EVADE), SPECIAL)):
        model_case('same-frame official chord: ' + expected_command,
                   [(keys, ())], [[expected_command]])
    model_case('held modifier does not split the chord', [((SPIRIT,), ()), ((LIGHT,), ())],
               [[SPIRIT], [HELM]])
    model_case('reverse member order still forms one chord', [((LIGHT,), ()), ((SPIRIT,), ())],
               [[LIGHT], [HELM]])
    model_case('unrelated edge never re-triggers an old chord',
               [((SPIRIT, LIGHT), ()), ((SLINGER,), ()), ((), ())],
               [[HELM], [SLINGER], []])
    model_case('new evade selects special sheath instead of old helm plus evade',
               [((SPIRIT, LIGHT), ()), ((EVADE,), ())], [[HELM], [SPECIAL]])
    model_case('release restores single-key behavior',
               [((SPIRIT, LIGHT), ()), ((), (SPIRIT, LIGHT)), ((LIGHT,), ())],
               [[HELM], [], [LIGHT]])
    model_case('press and release inside one frame still resolves',
               [((SPIRIT, LIGHT), (SPIRIT, LIGHT))], [[HELM]])
    model_case('three attack keys use documented adapter priority',
               [((SPIRIT, LIGHT, THRUST), ())], [[HELM]])
    checks.extend(model_cases)

    passed = all(item['passed'] for item in checks)
    report = {
        'passed': passed,
        'scope': 'Static source checks plus a Python model; not Unreal compilation or PIE.',
        'checks': checks,
        'sources': [str(path.relative_to(ROOT)) for path in (CPP_PATH, HEADER_PATH, HUD_PATH)],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': passed, 'checks': len(checks),
                      'failed': [item['check'] for item in checks if not item['passed']],
                      'report': str(REPORT_PATH)}, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
