# MHWI Round 6：袈裟导入方向反置；普通RMB独立覆盖

沿用parent与原B/C子代理，可并行，文件所有权不交叉；不读全部旧任务。禁止shell/ACL修复、UE或构建操作，宿主执行集成。

## B：真实运行发现的映射问题

方向报告 `Saved/MHWIImport/PIE-behavior-direction-fail4-lateral-mirror.json`：A输入已正确持续，选中 `FadeSlashLeft` / M_FadeSlashLeft /127，选择基底side=-1、actorRight=(0,1)，但真实位移断言为“向右”，左移断言失败。W/S后退约175cm/yaw0正常。127源rootX为负，128为正，不能直接当UE角色左/右（导入基底/mesh yaw影响）。

请B把**语义映射整体**改为 FadeSlashLeft=128、Right=127，同步两条各自源node/action/collision/速度/取消窗口/clip长度与制作器；不要只改角色选择条件来掩盖。`moveset_mapping.json` 交换完整来源记录并加校正说明，`extract_moveset_mapping.py`两项同步真实node/clip组合，author_assets及author_behavior_corrections定向更新两定义的时间与SourcePlayRates（保留伤害/收益/路由、转向关闭）。先读实际映射两对象，源node不可凭数字反推。不要全量重生成映射。

宿主将先备份新增范围、MCP交换两个Montage段，再运行定向制作。请给可调用入口/准确步骤，报告实际范围。

另：宿主查到MCP新建RollStepSlash默认混入/混出0.25，已显式持久化0.10/0.12。请确保定向制作对**已存在**该Montage也维护计划混合值，保留129+101两段；不能重建/覆盖段。

## C：覆盖缺口

ground 的六次RMB目前是三轮气刃插入，并未验证用户独立要求“中立持刀右键=Thrust/RisingSlash循环”。请在ground新增独立真实RMB六招序列 `[Thrust,RisingSlash]*3`，不改DA/成本/窗口，观察真实顺序并在取消窗口按键，完成后衔接原ground流程。原气刃插入三轮保留，明确分开报告。

Round4 的积槽goal到达才停止续排有必要，但phase固定8s可能不足100槽的完整正常链；请按实际执行（不是随便提高整体超时）保证准备链有有限预算/进展诊断。每个实际启动/伤害断言保留。

方向失败是资产真实语义问题，不弱化方向断言、不对调测试预期。新增blend与左右窗口读回可以加入资产断言。C只改验证脚本/报告；B只改原B源文件/报告。

各自完成立即回复，宿主继续验收。无需重新设计整个系统。
