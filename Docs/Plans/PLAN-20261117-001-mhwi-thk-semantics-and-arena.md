# PLAN-20261117-001：THK 条件语义审计（M1/M2）与斗技场场景提取

- 日期：2026-11-17。前置：编号确认（em001=雌火龙）与 Basic 版已完成；本轮全部离线，不启动原作/UE。
- 依据：[MHWI-Current.md](MHWI-Current.md) 里程碑 M1/M2；用户指令"按推荐顺序，本轮完成再报告"。

## 任务

1. **M2 v1**：从冻结的 `thk-all-raw.json`（105 thk / 1795 节点 / 13015 段）提取全部动作发射段（`actionID != 0`），映射 Leviathon ActionDumps（285 条），列出 0xB8 rank 门。CFG 级 LR 剪枝暂缓（段流语义需反编译器输出）。
2. **M1**：对 27 类已命名 functionType 做"参数取值与声明语义自洽"审计，产出三栏表（已证/冲突/未知）；未命名类按用例排序附参数分布。
3. **斗技场**：先找现成模型（Sketchfab API/Models-Resource）→ 无果；改走解包，锁定 stage 编号候选（st201/st202）后整批提取，转换验证后续。

## 产出与验收

- M2：`Tools/MHW/rathian-action-emission-inventory-20261117.json` + `Tools/MHW/ActionDumps/em001-actiondump.txt`（入库证据）
- M1：`Tools/MHW/rathian-thk-condition-semantics-20261117.json` + `Docs/Reference/MHWI-Rathian-THK-Condition-Semantics-20261117.md`
- Arena：`ArtSource/ThirdParty/MHWI-Stages/`（已 gitignore，146 文件）
- CHG-20261117-004 记录实际结果；`MHWI-Current.md` 的 M1/M2 状态行更新。

## 边界

- M2 v1 不做 CFG 剪枝，"LR 专属动作"暂不能圈定（rank 门全是 HR/MR 增量，无 LR 专属门是本轮发现）。
- M1 只验参数自洽，不证明原作运行等价。
- Arena 只提取未转换；sobj→FBX 转换器未验证。
