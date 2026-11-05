# 交接：雌火龙（em001）数据解包的当前结果与未解项

- 更新：2026-10-30；状态：数据收集 / partial。ACTP2完整结构与COL攻击原字段已解；部位破坏耐久、LR触发资格和完整动作时长仍未闭合。
- 本页按[CHG-011](../Changes/CHG-20261030-011-mhwi-rathalos-format-evidence.md)更新；CHG-009/010保留历史，不把旧的负结果当作当前限制。
- 当前只做离线数据，不接UE、不改Content/游戏安装、不启动游戏或做运行验证。

## 一、30秒摘要

已取得肉质/硬直组、发怒、疲劳与状态参数；新增：

1. **ACTP2结构已解**：205,037字节全消费且字节往返一致，342条ActionData/142启用/4,295属性项。存在维护者公开模板，不能再以“没有公开结构”为阻塞。
2. **COL攻击原字段已解**：42份COL中36份有ATK类型2，70条攻击（主35+shell35）；原日文名称、表索引/UID、Motion_Value、击退类型/等级、防御消耗和属性字段已读取。它们不是实战扣血表；同一00资源含G級标签，不能整批标LR专属。
3. **PBC三常量已解**：均为三层对象类名CRC；加载/保存器确认Info→State→Detail嵌套数组。4样本每层计数相同才展开为48字节，不能当通用固定步长。
4. **时间参数可读但语义未验**：DAMAGE_DOWN候选有mLoopTime=8；仍不是实机倒地总时长，未命名5.5/6.5不能猜为口水硬。

完整35条主攻击原字段表、直接来源及版本、全部新证据见[格式续查结果](../Reference/MHWI-Rathian-Format-Evidence-20261030.md)。

## 二、先读与数据位置

| 文件 | 职责 |
| --- | --- |
| [火龙数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md) | 已解状态值、提取范围与数据边界 |
| [本轮格式续查](../Reference/MHWI-Rathian-Format-Evidence-20261030.md) | 新解ACTP2/COL/PBC结构、原字段与验证证据 |
| [解包流程](../Reference/MHWI-Unpacking-Workflow.md) | 原始归档选择/来源清单/失败处理 |

原始300文件/80,708,036 B在`ArtSource/ThirdParty/MHWRathalos/nativePC/`，与`extraction-manifest.json`逐文件hash对应；297个00资源+3份itlot。二进制与archive-index忽略，分类状态在`Tools/MHW/em001-datamine-manifest.json`。

既有`dtt_epg`仍用`extract_native_parts.py` + `native-parts-layout.json`，不为统一入口改通用解析器；`dtt_agr/dtt_sta`完整消费，`dtt_eda`按888+8零尾判据保留状态参数。历史结果不等于本轮重跑。

## 三、可直接复现的工具

```powershell
python Scripts/MHWI/read_action_params.py --self-check
python Scripts/MHWI/read_monster_collision.py
python Scripts/MHWI/inspect_parts_break.py --self-check
python Scripts/MHWI/inspect_parts_break_native.py
```

| 工具 | 固定来源 / 输出 |
| --- | --- |
| `read_action_params.py` | Fexty模板`cea17f2…`，本地Property包装适配写入来源；完整报告`Saved/MHWRathalos-20261030-Format/actp2.json`，紧凑`Tools/MHW/em001-actp2-evidence.json` |
| `read_monster_collision.py` | Synthlight col.bt `b6ff379…`；完整报告同目录`collision.json`，紧凑`Tools/MHW/em001-collision-evidence.json`；OAP/CRC尾部保留opaque，不是全文件语义闭合 |
| `inspect_parts_break.py` | 4份固定样本/历史DTI，`Tools/MHW/em001-pbc-evidence.json`；只支持本轮确认形状，不是通用PBC反序列化器 |
| `inspect_parts_break_native.py` | 复用现有NativeTrace的固定EXE/text hash与owned unwind范围，`Tools/MHW/em001-pbc-native-layout-evidence.json`；不执行原作代码 |

上游缓存位于`Tools/MHW/Source/`及既有Saved路径，恢复时遵守各`rathalos-*-sources.json`的commit/尺寸/SHA256；模板原文不改。缺依赖或来源变化时停止，不把新版本套旧资格结果。报告重跑/覆盖差异见格式续查页；新提取仍必须使用独立批次，原清单不会自动合并。

## 四、剩余未解项

### A. 部位破坏耐久：结构与对象归属已定，业务语义未定

`em001.em_pbc` 256 B，5个Info，各含1个State/1个Detail。三类CRC：`0x0befc97f / 0x6900901d / 0x5dc14d7c`。Murmur或部件词表路线无需继续。

| 当前样本相对偏移 | 对象字段 | 火龙00值 |
| ---: | --- | --- |
| +20 | Detail+0x10 | 5 / 1 / 4 / 3 / 2 |
| +24 | Detail+0x20 | **-1 / 2006 / 2006 / 2006 / 2006** |
| +28 | Detail+0x28 | 0 / 4 / 1 / 2 / 8 |
| +32 | State+0x10 | 全-1 |
| +36 / +40 / +44 | Info+0x28 / +0x2c / +0x30 | 全0 / -1 / 2 |

雌火龙后4条+24为2007；首条仍-1。没有证据证明这些是耐久或部位ID，不发布破坏阈值。后续候选是沿固定加载器已确认的对象字段追真实消费者，与EPG对照；尚未选择新推断路线。

### B. 下位有效招式、实战伤害与击退表现

原始70条ATK已读，不再卡在“没有伤害载体”。仍须将COL Names/UID、LMT/TIML与动作/等级资格闭合，随后才可讨论任务倍率、玩家防御和实际反应。主35原名表在格式续查页，不擅自翻译类型数字；不能把G級标签项列成LR已确认动作。

### C. 倒地/口水硬动作总时长

ACTP2中时间字段可读，319条有历史DTI衍生nameCRC候选、23条未命名。DAMAGE_DOWN候选`mLoopTime=8`、DAMAGE_STUN/RIDE_DOWN候选`=10`都是原参数，不是全程秒数验收。需要当前动作注册/EM_DMG分派及时间字段消费者，再结合动画入场/循环/起身；325/326的5.5/6.5禁止按经验命名。

## 五、已更正的旧判断

| 旧判断 | 当前证据 |
| --- | --- |
| ACTP2没有公开结构 | Fexty维护者有actp2.bt + UnitProperty.bt；本机格式2完整往返 |
| SHLP无伤害字段，所以伤害只能在ACTP2 | 推论不成立，COL Atk2有攻击/击退原字段；SHLP的无直接伤害字段负结果仍保留 |
| PBC三常量需猜部件名哈希 | 已精确命中对象类名CRC，且当前加载/保存器对应嵌套层级 |
| PBC通用步长48 | 仅4个样本相同嵌套计数下展开为48；通用格式是数组嵌套 |
| 每条PBC +24 都是2006/2007 | 首条是-1，只有后4条为该值 |

仍保留：EM_DMG是受击动作选择，不是攻击伤害数值表；Health3000不是任务实际血量；肉质组号不直接等于部位名；00目录不等于下位专属；Stun/Dizziness/Concussion名称不能直接互换。

## 六、完成标准与下一步选择

- 已完成的是静态字段读取、类型身份与嵌套序列；字段消费者/运行时钟/最终数值未闭合必须保留unknown。
- 耐久至少需要真实消费者或独立业务证据；仅类CRC不能证明耐久。
- 实战伤害、完整动作时长仍需消费者链及必要运行证据；本阶段禁止运行，不能以当前源参数代替验收。
- 有来源后续候选及代价见格式续查页末节；维护者无可直接采用的完整业务方案，等待用户选择下一实质方向。
- 同步现状、方案/变更索引；`check_docs.py`与`git diff --check`。已有玩法代码、资产、通用解析器与历史CHG保持原有工作。
