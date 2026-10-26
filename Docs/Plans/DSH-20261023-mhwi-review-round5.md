# MHWI Round 5：移动输入必须连续注入

Codex实际方向报告 01:50:43..47，已另存 fail3：E拔刀正常（观察Draw并结束持刀），W/S袈裟实际后退约175cm/yaw不变通过；A却选FadeSlash后退，预期FadeSlashLeft。报告不是业务映射结论。

明确夹具根因：`_move()` 只调用一次 `inject_input_vector_for_action`。该注入只持续一帧；`dir_case_start`注入后等待0.05秒，却在等待各帧不续注入，Move Completed已清空角色MoveInput。注释说保持输入，但实现没有保持；普通/派生转向测试也多只调用一次_move。不要为此修改业务或改方向断言。

仅C脚本/报告返修：给真实移动输入做明确的持续注入生命周期，例如保存held vector并在每个Slate tick注入，`_stop_inputs()`释放为0，finish也确保释放。首帧/阶段转换要考虑0覆盖和重复注入累积，不要在同一帧重复叠加方向。保留方向选择前基底重置、真实位移断言、无输入后退对照。检查Sprint如果需要保持也用相同契约。字段缓存的是测试输入，不能设置角色业务MoveInput或伪造GetCurrentMove。

范围仍仅 `Scripts/MHWI/pie_behavior_corrections.py` 和报告；不要再读取整份旧计划或全部角色源码。宿主独立AST/运行验收，禁止自行宣称通过、操作UE/构建、修ACL。完成即回复。
