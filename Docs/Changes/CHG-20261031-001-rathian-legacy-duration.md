# CHG-20261031-001：旧24条雌火龙动画源时长重导

- 状态：completed-scope；工作区未提交。
- 需求：修复旧24条固定时长，保留引用。
- 方案：[PLAN](../Plans/PLAN-20261031-001-rathian-legacy-duration.md)。

## 修改与结果

新增Tools/MHW/repair_rathian_legacy_export.py与Scripts/MHWI/repair_rathian_legacy_import.py，沿用已验证Feuleur读取与Epic UE5.8动画-only同Skeleton导入设置。只选择原24条，按源帧数设置0..frame_count-1、60FPS；FBX在Saved/RathianLegacyRepair-20261031。原uasset先备份至该目录Backup，再在原/Game/MHWI/Rathalos/Animations路径替换导入；不删除或改名、不创建重定向器，不改Skeleton、蓝图或Montage引用。

24/24转换及导入成功。每条检查AnimSequence类、原对象身份与对象路径、Skeleton、源预期时长（误差小于一个采样间隔）、保存结果、前后referencer列表一致。逐条数据见[证据](../../Tools/MHW/rathian-legacy-duration-repair.json)。引用列表为空时仅表示未发现磁盘包引用，不扩大为所有动态路径证明。当前编辑器此前关闭，本轮启动后执行，不编译引擎。

## 验证与边界

Blender无头转换exit0；UE-MCP四批各6条，最终imported24/pending0；无导入错误。原固定4.15秒问题已由源帧数替代。未做原作逐帧对照或PIE玩法验收。文档/空白检查见本次工具输出。

## 回退

仅本24条可使用Saved/RathianLegacyRepair-20261031/Backup备份恢复；避免编辑器内已加载版本覆盖恢复文件。新脚本、证据和文档可定点撤回。用户其他修改保持，前批CHG历史不改。
