# CHG-20261030-021：按用户决定以雌火龙（em001）为目标，文档口径与文件名更正

- 状态：completed（文档）
- 日期：2026-10-30
- 需求摘要：用户决定继续使用 em001（雌火龙）数据，要求把文档改过来。
- 关联：[CHG-020](CHG-20261030-020-mhwi-monster-id-correction.md)（编号错误发现）、[雌火龙数据现状](../Reference/MHWI-Rathian-LR-Data-20261030.md)

## 决定与结果

用户决定：**本项目以雌火龙（em001）为目标继续**，已完成的提取、解析、转换、导入全部有效；火龙（em002）的 257 个文件保留在 `ArtSource/ThirdParty/MHWRathalos-em002/` 备用，暂不处理。

按此口径做文档更正：

1. **四份在用文档重命名**（`Rathalos` → `Rathian`）：
   - `Reference/MHWI-Rathian-LR-Data-20261030.md`（原 Rathalos-LR-Data）
   - `Reference/MHWI-Rathian-Format-Evidence-20261030.md`
   - `Plans/MHWI-Rathian-Datamine-Handoff.md`
   - `Plans/PLAN-20261030-003-mhwi-rathian-datamine.md`、`PLAN-20261030-004-mhwi-rathian-format-evidence.md`
2. **全库引用替换**（5 组精确文件名匹配，20 个文件），历史 CHG 文件名保持原样不改。
3. **标题与口径修正**：数据页标题改为"雌火龙（em001）"；文首更正块改写为"编号确认"口径（保留两条证据）；交接/PLAN/流程页/系统页中把 em001 批次的"火龙"表述改为"雌火龙"，em002 标注为火龙备用数据。
4. `Docs/README.md` 快速阅读表两行同步。

历史 CHG（005–020）正文不改——变更记录保留历史含义，编号错误的来龙去脉见 CHG-020。

## 未改（有意保留）

- `ArtSource/ThirdParty/MHWRathalos/`、`ArtSource/ThirdParty/MHWRathalos-em002/` 目录名与 `.gitignore` 条目（改目录会牵动脚本与忽略规则，属代码/资产范畴，本轮只动文档）。
- `/Game/MHWI/Rathalos/` 引擎资产路径（重命名 UE 资产破坏引用，需在编辑器内做）。
- 各 CHG 文件名。

## 验证

| 操作 | 结果 |
| --- | --- |
| `python Scripts/Docs/check_docs.py` | PASS：174 文件 / 1,474 链接（重命名后全库链接有效） |
| `git diff --check -- Docs` | 通过 |
| 残留检查 | `MHWI-Rathalos` 仅存在于历史 CHG 文件名与其正文中（保留历史含义），在用文档无残留 |
