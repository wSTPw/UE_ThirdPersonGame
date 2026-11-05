# CHG-20261030-007：解析器布局 hash 校验与流程页 `shlp` 口径修正

- 状态：completed（工具与文档）；未改游戏、未重抽、未改任何已发布数值。
- 日期：2026-10-30。
- 需求摘要：阅读并评估 Codex 产出的解包流程文档，采纳其中成立的问题修正。
- 关联：被评论文档 [解包流程](../Reference/MHWI-Unpacking-Workflow.md)（CHG-006）、[CHG-005](CHG-20261030-005-mhwi-rathalos-datamine.md)；问题 `R-DATA-002`。

## 原因与结果

[解包流程](../Reference/MHWI-Unpacking-Workflow.md) 与 [CHG-006](CHG-20261030-006-mhwi-unpacking-workflow.md) 对本项目脚本做了逐条静态核对。复核后确认其中若干判断成立，本轮就地修正两点：

1. **解析器确实缺少布局 hash 校验**（该文 `R-DATA-002` 指出）。若本地 `.cs` 布局被替换，字段顺序变化可能让错误解析看起来自洽。已补 `--pins`：解析前逐份比对 `Tools/MHW/mhw-editor-sources.json` 的 SHA256，不一致直接非零退出；报告 JSON 增加 `pins` 字段记录校验结果。
2. **流程页仍把 `shlp` 描述为"长度/读取失败"**，读者会以为修好长度即可拿到招式数值。已按 CHG-005 的负结果改写：`rShellParam` 结构不含伤害/击退/气绝字段，对齐长度也无产出。

## 修改清单

| 文件完整路径 | 修改内容 |
| --- | --- |
| `Scripts/MHWI/parse_em_params.py` | 新增 `--pins`、`verify_pins()`；报告增加 `pins`；未传该参数时行为不变 |
| `Docs/Reference/MHWI-Unpacking-Workflow.md` | 解析入口说明补 `shlp` 无伤害字段；历史结果段拆开 `dtt_eda` 与 `shlp`，并记录 `--pins` |
| `Docs/Known-Issues.md` | `R-DATA-002` 由 open 改为 partial，注明布局 hash 校验已补、剩余为跳过语义与部分 data |
| `Docs/Changes/README.md` | 新增本条索引 |

## 实际验证

| 操作 | 结果 |
| --- | --- |
| `parse_em_params.py --pins Tools/MHW/mhw-editor-sources.json`（`em001/00/data`） | 9 份布局 hash 全部通过；输出与加校验前一致：`dtt_agr` 144/144、`dtt_sta` 92/92 通过，`dtt_eda` 888/896、`dtt_epg` 442/1360 仍 MISMATCH |
| `python Scripts/Docs/check_docs.py` | 见下 |
| `git diff --check -- Docs Scripts` | 见下 |

校验只证明"用的是固定版本布局"，不证明字段语义正确；`dtt_eda`/`dtt_epg` 的差异仍未解决，本轮未重新发布任何数值。

## 风险与回退

- `--pins` 为可选参数；未传时与旧行为一致，不破坏既有调用。
- 回退：还原 `parse_em_params.py` 的 `--pins`/`verify_pins`、三处文档表述与本条记录。

## 已同步文档

- [解包流程](../Reference/MHWI-Unpacking-Workflow.md)
- [已知问题](../Known-Issues.md)
- [记录索引](README.md)
