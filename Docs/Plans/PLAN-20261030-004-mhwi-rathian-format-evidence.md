# PLAN-20261030-004：雌火龙未解格式的来源核对与离线读取

- 状态：implemented-scope / partial-semantics（离线读取落地，业务/运行未闭合）。
- 日期：2026-10-30。
- 用户需求：查看雌火龙数据交接中的未解项能否解决。
- 关联模块：mhwi-unpack-data；前序[方案](PLAN-20261030-003-mhwi-rathian-datamine.md)、[交接](MHWI-Rathian-Datamine-Handoff.md)。
- 实施记录：[CHG-011](../Changes/CHG-20261030-011-mhwi-rathalos-format-evidence.md)。

## 现状与目标

交接把 ACTP2 描述为无公开结构，并从 SHLP 无伤害字段推出伤害只能在 ACTP2；PBC 三个常量用 MurmurHash 试算未命中。只读核查已找到维护者 ACTP2/UnitProperty 模板、COL 类型2定义，以及项目既有 DTI 中与 PBC 三常量精确一致的类名 CRC。目标是按这些来源完成可复核的结构读取，修正前提，保留语义与运行缺口。

## 范围与验收标准

- ACTP2：按带类型属性读取，严格边界/完整消费，记录每个动作及属性位置；不依赖自相关步长。
- COL：按维护者类型2结构定位并读取攻击记录，记录 UID/索引/偏移/字段来源及几何边界；不宣称已恢复招式中文名或实战扣血。
- PBC：重算类名 CRC，与本地 dump 及原字节交叉核对；复用既有固定NativeTrace核对加载/保存及嵌套字段归属；未知载荷保留原值，不命名为耐久。
- 不启动原作/UE、不注入、不修改安装、Content 或现有玩法代码；不修通用 EPG 入口。

## 技术方案与来源

直接采用维护者既有格式定义，不确定字段保持 raw/unknown：

- [Fexty12573/MHW-010-Templates](https://github.com/Fexty12573/MHW-010-Templates)：actp2.bt 与 UnitProperty.bt；下载时固定 commit/SHA256，项目适配与上游原文分开留痕。
- [Synthlight/MHW-Editor col.bt](https://github.com/Synthlight/MHW-Editor/blob/master/010%20Templates/col.bt)、[Collisions](https://github.com/Synthlight/MHW-Editor/wiki/Collisions)：核对 Atk2，固定实际使用版本/hash。
- [Andoryuuta DTI dump](https://github.com/Andoryuuta/MHW-DTI-Dumps/blob/4a124e4073519eaf19e3a446cb62d375d8da3209/dti_prop_dump.h)：仅类名/CRC 元数据；不把旧虚表地址当当前 ABI。

新增独立离线读取脚本、来源指纹与紧凑证据到 Scripts/MHWI / Tools/MHW，完整可重建报告放 Saved。维护者资料支持读取机制，不证明所有原作消费者语义。没有直接布局的剩余字段不选择猜测性算法；列清缺口与候选后再由用户决定后续实质方向。

## 接口与数据迁移

无 UE/蓝图接口变更或资源迁移；新增离线 CLI 不覆盖原解析器及采集批次。输出应隔离目录，来源冲突/未知类型/截断/尾随非解释数据须失败。

## 实施步骤与依赖

1. 查询维护者资料，固定来源与本地资源 SHA。
2. 分别读取 ACTP2、COL 与 PBC 元数据；仅同源可解释的内容进入证据。
3. 用实际文件完整消费及损坏/尾随/未知字段拒绝检查验证读取边界。
4. 同步雌火龙现状、交接、前序方案、模块入口/问题与变更索引；历史 CHG 保持原义。

## 验证计划

| 场景 | 方法 | 期望 | 边界 |
| --- | --- | --- | --- |
| 已知文件 | 按清单 hash 核对、解析及重读/往返 | 字节及记录范围闭合 | 非实机机制验证 |
| 损坏/未知内容 | 进程内副本截断、改类型/计数、加尾部 | 明确拒绝 | 不修改原资源 |
| 文档/补丁 | check_docs.py、git diff --check | 通过 | 不编译 UE |

## 风险与回退

上游模板可能有局部错误，必须记录项目适配，不伪称原样执行；CRC 命中证明类型身份，不证明未知整数的业务含义。仅删除本轮新增脚本/来源/报告并撤回本轮文档段落即可回退，禁止整文件恢复覆盖用户既有修改。

## 文档同步清单

交接、火龙数据现状、PLAN-003、文档/方案/变更索引、modules.json、Known-Issues；完成后写入本批 CHG 与实际结果。
