import unreal
lib=unreal.get_default_object(unreal.load_class(None,'/Script/EnhancedInput.EnhancedInputLibrary'))
try:
    v=lib.call_method('MakeInputActionValueOfType',(1.0,0.0,0.0,unreal.InputActionValueType.BOOLEAN))
    unreal.log('VALUE '+str(v))
    unreal.log('BOOL '+str(lib.call_method('Conv_InputActionValueToBool',(v,))))
except Exception as e:
    unreal.log_error(str(e))
