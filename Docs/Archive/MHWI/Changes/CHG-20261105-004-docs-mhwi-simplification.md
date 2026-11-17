# CHG-20261105-004 MHWI 文档简化：归档历史、重写现状层

- 日期：2026-11-05
- 状态：completed（仅文档）
- 范围：`Docs/`、`Scripts/Docs/`、`Home.md`。**未改代码、资产、配置或游戏安装。**

## 原因

MHWI 文档累积到约 14,000 行 / 195 文件，其中 13,379 行是过程性文档（Plans 4,826 + Changes 5,129 + Reference 3,424）。全库统计到 27 处"保留历史"、24 处"撤回"、105 处"不再"、82 处"不等于"——每份文档都在声明"下面那段别信"。

四个具体耦合源：

1. 现状页被批次日志污染：`Systems/MHWI-LongSword.md` 206 行里 176 行是 B08→B24 倒序流水账
2. 同一页三个"当前接续点"并存（`MHWI-Restoration-Progress.md`）
3. 同主题多份报告互相覆盖：验收 3 份、交接 3 份、评审 3 份、挂接 2 份（旧结论已推翻）
4. 编号三重叠加：B01–B24 + R01–R35 + PLAN/CHG/DSH，加 `mhw`/`mhwi`/`rathalos`/`rathian` 四种拼写

## 改动

### 保底

`git add Docs` + 提交（77 文件，含 70 个未跟踪）作为回退基线，commit `docs: 归档重构前保底快照`。

### 归档

移动 189 份文件，保留原目录层级使相对引用不断：

| 目标 | Plans | Changes | Reference |
| --- | ---: | ---: | ---: |
| `Docs/Archive/MHWI/` | 57 | 78 | 34 |
| `Docs/Archive/Legacy/` | 7 | 13 | — |

`Changes/` 保留最近 4 条 + 本记录。`Legacy/` 承接非 MHWI 内容（主菜单、Ninja、MM、文档基线、Windows Sandbox 修复）。

### 新建（结论总账）

| 文件 | 内容 |
| --- | --- |
| `Reference/MHWI-LongSword-Evidence.md` | 源指纹、W03P 数值表、装备挂接（父骨选择/坐标/片段切换）、碰撞结论、动画/连接、U1–U9 未解清单 |
| `Reference/MHWI-Rathian-Evidence.md` | 编号更正、300 文件口径、肉质/硬直/发怒/疲劳/状态全套数值、格式边界、THK F1–F8 + fexty 映射、动作身份 285 条、首链九步、三 UID、未解清单 |
| `Plans/MHWI-Current.md` | 唯一活跃计划：两条产品线、M1–M4 里程碑、待拍板 3 项、风险、术语表 |
| `Systems/MHWI-Rathian.md` | 雌火龙现状：代码地图（首链 1546 行 + Approx 1172 行）、848 动画与资产、B1 已知缺陷、UE5.8 API 差异、构建命令 |

### 重写（现状层）

| 文件 | 原 → 现 |
| --- | --- |
| `Docs/README.md` | 61 → 62 行，但 MHWI 路由 20 条压到 5 条，状态描述改为纯导航 |
| `Systems/MHWI-LongSword.md` | 206 → 155 行，删掉 B08–B24 全部批次段落，改为"当前实现 + 未闭合" |
| `Systems/MHWI-Unpack-Data.md` | 229 → 175 行，合并原 `Reference/MHWI-Unpacking-Workflow.md` 的复现与失败边界，删掉全部批次说明 |
| `Plans/README.md` | 60 → 26 行，43 行方案表压到 1 行活跃 |
| `Changes/README.md` | 99 → 26 行，只列最近 5 条 |
| `Known-Issues.md` / `Interfaces.md` / `Development.md` / `ADR-0001` / `ADR-0002` / `Systems/Combat-AI.md` / `Inventory.md` / `Ninja-Animation-Configuration.md` / `UI-Assets.md` / `UE58-Upgrade.md` | 仅修复指向归档文件的链接（97 处） |
| `Reference/modules.json` | 4 个模块的 `document`/`sources` 改指新页；删除 3 条已并入总账的归档引用 |

### 工具

`Scripts/Docs/check_docs.py`：扫描时跳过 `Docs/Archive`（冻结历史不再维护内部链接），并加注释说明理由。

`Scripts/Docs/rewrite_archived_links.py`（新增）：按"缺失目标文件名 → 在 Archive 下唯一命中 → 重算相对路径"批量修复迁移断链。一次性工具，保留以备后续再次归档。

## 验证

```powershell
python Scripts/Docs/check_docs.py
git diff --check
```

实际结果：

- 首次运行报 98 项 `missing link target` + 9 项 `modules.json` 失效引用
- 跑 `rewrite_archived_links.py` 后修复 97 处链接（14 文件）
- 手工修 `modules.json` 4 模块定义
- 最终 `PASS`（本记录建立后复跑确认）

未执行：未启动 UE、未编译、未运行 PIE、未改动任何 `.uasset`/`.umap`/源码。

## 影响

- 无接口、蓝图、资产或运行时影响。纯文档结构变动。
- 读者入口变化：MHWI 相关从"20 条路由 + 43 行方案墙"改为"1 个当前计划 + 2 个系统页 + 2 份取证总账"。
- `git log --follow` 可追溯每份归档文件的原始位置。

## 未验证 / 遗留

- 归档区内部链接未维护（`check_docs.py` 跳过），部分相对链接已失效。查原位置用 `git log --follow`。
- `Tools/MHW/README.md` 与 `ArtSource/ThirdParty/MHWLongSword/README.md` 中的文档引用未改（不在 `check_docs.py` 扫描范围），若指向已归档页需自行核对。
- `Known-Issues.md` 只修链接未精简正文，其 69 行条目仍有冗长论证，留待单独处理。

## 回退

```powershell
git revert <本记录所在提交>
```

或从保底快照恢复：

```powershell
git checkout <保底快照提交> -- Docs
```
