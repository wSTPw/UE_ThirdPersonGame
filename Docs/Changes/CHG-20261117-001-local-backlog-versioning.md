# CHG-20261117-001：本地积压改动入库与版本控制范围调整

- 状态：completed（版本控制范围与积压提交）；Rathalos 玩法仍为未开始
- 日期：2026-11-17
- 需求摘要：用户要求「检查本地修改」后按推荐方案入库并推送远端。本次将 2026-10-30 至 11-16 期间累积在工作区、从未提交的成果纳入版本管理，同时把可重建的大体量中间产物排除在仓库之外。
- 关联 PLAN：[PLAN-20261116-001](../Plans/PLAN-20261116-001-hunter-damage-reaction.md)、[PLAN-20261107-002](../Plans/PLAN-20261107-002-rathian-basic-assets-pie.md)
- Git：本次提交（见推送记录），此前 `10-30`–`11-16` 的改动均处于工作区未提交状态

## 原因与结果

起因是排查工作区时发现两个事实：

1. **功能代码引用了未入库的资产。** `MHWICharacter.cpp:149/154` 硬编码 `/Game/MHWI/Animations/DamageSource/A_co00_01_*`（含兜底 `A_co00_01_007`），而该目录 9 个 uasset 从未被 git 跟踪。后果是任何新克隆都能编译通过，但受击会静默退回 007 单片段——四方向 DAMAGE_S 与中大档起身链全部失效且不报错。原行为：仅在本机可用；当前行为：资产随源码同版入库。
2. **1.66 GB 的 Rathalos 全量动作库尚未接入玩法。** `Content/MHWI/Rathalos/Animations` 有 848 个 uasset（1.6 GB），而 `Source/` 中仅引用 `A_em001_02_001` 一个。该目录是 `Tools/MHW/convert_monster_animations.py` 的全量导出中间产物，源 LMT、导出脚本与 `rathalos-actp2-sources.json` 等证据均已入库，可重建。原行为：全量待入库，会一次性占用 GitHub LFS 配额；当前行为：排除在仓库外，按需导入（对齐 Rathian 的 34 个按需导入模式）。

同时修正 `.gitignore` 的对称性遗漏：`MHWRathalos/nativePC/` 与 `archive-index.json` 早已排除，但同批产出的 `MHWRathalos-em002/` 未排除，且其中的 `.tex` 不受 LFS 覆盖（`filter=unspecified`），会把 104 MB 游戏原始二进制以普通对象形式提交。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `.gitignore` | 新增 `/ArtSource/ThirdParty/MHWRathalos-em002/nativePC/`、`.../archive-index.json` | 与 `MHWRathalos/` 对称排除 datamine 二进制与索引，保留 `extraction-manifest.json` |
| `.gitignore` | 新增 `/Content/MHWI/Rathalos/Animations/` | 848 个 / 1.6 GB 可重建中间产物不入库，附重建方式注释 |
| `.gitignore` | 新增 `/Tools/DevFlow/` | 与 CHG-20261107-001「DevFlow 副本有私有基线，不是用户仓库提交」一致 |
| `Source/IntroCpp/IntroCpp.Build.cs` | `AnimGraphRuntime`（public）、`Json`（private） | 11-16 受击改造所需依赖，随源码入库 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` 等 9 个 C++ | 受击方向、`StartNativeImpact`、`SourceBindings` 白名单 | 已在 11-16 编译并 PIE 验证，本次仅补提交 |
| `Content/MHWI/Animations/DamageSource/*.uasset` | `A_co00_01_007/092/093/094/096/104/105/106/107` | **C++ 硬编码引用，本次必须入库** |
| `Content/MHWI/Rathian/**/*.uasset` | Basic 关卡 34 个动画与碰撞资产 | 雌火龙基础玩法资产入库 |
| `Content/MHWI/Rathalos/Mesh|Textures|Materials` | `SK_EM001_Body/Tail`、12 张贴图、4 个材质 | 模型贴图入库（66.7 MB）；对应 `CHG-20261030-014` |
| `Tools/MHW/*.json`、`Tools/MHW/*.py` | em001/pbc/actp2 证据与导出脚本 | 沿用「证据放 `Tools/MHW/`」既有约定 |
| `Scripts/MHWI/*`、`Docs/**`、`Docs/Archive/MHWI/Changes/*` | 脚本与现状层文档同步 | 见 CHG-20261106-002 至 CHG-20261116-001 |

## 接口、事件与资源影响

无 C++ 签名变更。资源面影响：`/Game/MHWI/Animations/DamageSource/` 由「仅本机存在」变为「随仓库分发」，是本次唯一会改变其他克隆运行行为的改动；其余为新增资产目录。

`Content/MHWI/Rathalos/Animations` 不入库，意味着新克隆在编辑器内看不到这 848 个动画，需用 `Tools/MHW/convert_monster_animations.py --mod3 <x.mod3> --lmt <x.lmt> --out-dir <dir>` 重新导出后导入。该过程依赖本机 nativePC 原始文件，原始文件同样不在仓库内。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `git check-ignore` 4 条新增规则 | 本机 | 4 项均被忽略；Mesh/Textures/`extraction-manifest.json`/DamageSource 未被误伤 | 见 `.gitignore` 与本次提交 |
| 新增 uasset LFS 属性 | 本机 | 69 个新增 uasset 全部 `filter=lfs`（`git check-attr --stdin`） | 暂存对象均为 `version https://git-lfs.github.com/spec/v1` 指针 |
| `python Scripts/Docs/check_docs.py` | 本机 | PASS：41 Markdown / 381 链接 / 16 模块 | — |
| `git diff --cached --check` | 本机 | 通过（修掉 3 个脚本的 EOF 空行后） | — |
| 编译 | — | **本次未执行**。C++ 自 11-16 17:03:18 后无改动，DLL 时间为 11-16 17:04:08，晚于全部源码；11-16 那次构建与 13 例 PIE 见 CHG-20261116-001 | `Binaries/Win64/UnrealEditor-IntroCpp.dll` 时间戳 |
| PIE | — | **本次未执行**，无运行时行为改动 | — |

## 风险、遗留与回退

- **LFS 配额**：本次新增约 122 MB，仓库 LFS 累计约 720 MB，仍在 GitHub 免费额度（1 GiB 存储 / 1 GiB 月流量）之内。若后续仍需同步 Rathalos 全量动作库，需升 LFS 数据包或改用第二 remote，不可直接 `git add` 1.6 GB。
- **Rathalos 玩法未开始**：按需导入是其前提，届时按 Rathian 的 34 个动作规模裁剪，不要恢复全量。
- **`git-lfs` 反复被清**：WorkBuddy PortableGit 升级会删除 `/mingw64/bin/git-lfs.exe`，症状是 `git diff` 报 `clean filter 'lfs' failed`、`git status` 计数为 0。已从 `~/.gitlfs/bin/git-lfs.exe`（3.8.0）还原。再次出现时按此恢复。
- **回退**：撤销入库只需 `git revert` 本次提交；被排除的目录始终留在本机磁盘上，未删除任何文件。

## 已同步文档

- [变更记录索引](README.md)（本行）
- [MHWI-LongSword](../Systems/MHWI-LongSword.md)、[MHWI-Rathian](../Systems/MHWI-Rathian.md)：现状层随本次提交同步
- [已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)：随本次提交同步
