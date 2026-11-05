# PLAN-20261030-003：雌火龙（em001）下位完整数据收集

- 状态：partial（ACTP2结构/COL攻击原字段已读；LR资格/AI/破坏耐久未闭合）
- 日期：2026-10-30
- 关联：[数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)、[本批记录](../Changes/CHG-20261030-005-mhwi-rathalos-datamine.md)
- 用户目标：解包火龙完整数据，**以下位数值为准**，覆盖模型、动画、数值、AI、机制、各招式伤害/击退、部位破坏、硬直、倒地、口水硬、发怒、虚弱等；此阶段只做数据收集。

## 一、范围与口径

| 项 | 决定 | 依据 |
| --- | --- | --- |
| 怪物 | `em001`（Rathalos 火龙） | 归档目录 `em/em001/` |
| 变体目录 | 只取 `00/` | `01/`、`02/` 的 `actp2` 更大且 `02/` 多出 shell ID 100–151，属派生变体；变体身份本身为推断 |
| 等级 | 取各文件内的 `_LR_` 段/字段 | `dtt_sta` 同文件并列 LR/HR/MR；`Parts*` 并列 `Part_Id_LR_HR1_*` 与 `Part_Id_MR1_*` |
| 不做 | 不接 UE、不改 `Content/`、不改玩法代码、不写游戏安装、不做运行验证 | 用户明确"现阶段只做数据收集" |

## 二、阶段划分

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| S1 提取 | `em/em001/00/**` + 三份 `itlot`，带 SHA256 清单 | **完成**：300 文件 / 76.97 MiB |
| S2 分类归位 | 每个后缀映射到 MT Framework 类名与用途 | **完成**：300 条写入 `Tools/MHW/em001-datamine-manifest.json` |
| S3 明文参数解码 | `dtt_agr`、`dtt_sta` | **完成**：字节完全消费 |
| S4 加密参数解码 | `dtt_epg`、`dtt_eda`、`shlp` | 完成：`dtt_epg` 沿用 B13 已校验结果；`dtt_eda` 888+8 零尾通过；`shlp` 判明结构无伤害字段（路线否决） |
| S5 招式判定 | SHLP关联的COL/TIML与攻击字段 | COL类型2已读70攻击原记录（主35+shell35），原名/UID/索引可追；LR触发资格、几何与最终伤害仍未闭合 |
| S6 部位破坏与反应 | em_pbc、em_dmg、dtt_epg | PBC类CRC/嵌套数组与对象字段归属已定，业务耐久语义未知；EM_DMG未完整解码 |
| S7 AI 与动作 | actp2、thk(105)、thklst、at、lmt | ACTP2完整结构342记录/4295属性已读；名字候选与时间字段有证据，原作执行/AI仍开放 |
| S8 模型/贴图 | `mod3`/`mrl3`/`tex` | 仅提取，未拆 |

## 三、方法（已定）

1. **提取**：只用 `Tools/MHW/extract_resources.py`，输出到独立目录，不复用 LS 目录以免覆盖其 manifest。
2. **结构来源**：MHW-Editor（Synthlight fork）生成的结构定义，commit 与逐文件 SHA256 记入 `Tools/MHW/mhw-editor-sources.json`。只当读取规格用，不执行上游代码。
3. **解密**：复用项目既有 `decrypt_resource`（Blowfish-ECB + 4 字节交换 + 加解密往返自检），扩展名到密钥的映射取自 `EncryptionKeys.cs`。
4. **自检**：解析必须字节完全消费，否则判失败并记录差异；不允许猜测补齐。
5. **边界**：类名/字段名来自社区生成结构，不代表 Capcom 官方语义；字段中文含义为推断，需与实机观测交叉验证后才可写入还原依据。

## 四、未决与下一步

2026-10-30按[PLAN-004](PLAN-20261030-004-mhwi-rathian-format-evidence.md)完成维护者模板与固定代码续查，直接来源/版本及已执行结果见[格式续查](../Reference/MHWI-Rathian-Format-Evidence-20261030.md)、[CHG-011](../Changes/CHG-20261030-011-mhwi-rathalos-format-evidence.md)。

| 缺口 | 当前事实 / 有来源的后续候选 | 代价 |
| --- | --- | --- |
| ACTP2结构 | 已完整消费并字节往返，不再受无模板/自相关步长阻塞 | 已实现 |
| 攻击原字段 | COL Atk2的70条可读；“伤害只能从ACTP2取”已否决 | 已实现静态读取 |
| LR触发资格/最终伤害 | 按COL UID及ATK索引连接动作/时间轴和等级/任务倍率，必要运行另行安排 | 大，未定新方案 |
| PBC耐久 | 类CRC和三层嵌套已定；继续真实字段读消费者，而非Murmur/部件词表 | 中到大，语义未知 |
| 倒地/口水硬完整时长 | ACTP2时间参数可读；需当前动作名注册/EM_DMG分派/时间消费者与动画阶段 | 中到大，候选待选择 |
| THK/AI、肉质组号到部位名、变体身份 | 本轮未完成；不以限定搜索断言无公开结构 | 另行确定 |

SHLP尾部不再为取得攻击数值的阻塞；DTT_EDA已按888+8零尾判据接受。保持当前数据收集限制，后续业务方向须用户选择。

## 五、验收口径

- 数字只有在"字节完全消费 + 字段来源可追"时才写入数据文档。
- 已解码与待解码必须分表列出，不允许把"文件已提取"写成"数据已解读"。
- 与 MHWI 原作对比属于后续阶段，本阶段不做忠实度结论。

## 六、回退

新增内容全部为：`ArtSource/ThirdParty/MHWRathalos/`（二进制已忽略）、`Scripts/MHWI/parse_em_params.py`、`Tools/MHW/em001-datamine-manifest.json`、`Tools/MHW/mhw-editor-sources.json`、`Tools/MHW/Source/MHW-Editor-b6ff379/`（已忽略）、两篇文档与 `.gitignore` 两行。删除上述即可回退，不涉及玩法代码与资产。
