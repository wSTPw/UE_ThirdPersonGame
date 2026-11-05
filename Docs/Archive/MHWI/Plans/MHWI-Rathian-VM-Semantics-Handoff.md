# 交接：THK VM 条件语义取证（E01/BEH-01）当前结果与被阻塞原因

> **2026-11-05首链增补**：[只读审查](../Reference/MHWI-Rathian-FirstChain-Audit-20261105.md)纠正旧动作表name/id/vtable解释，保留raw83，给出THK55/n200的两个条件九步受控候选路径与原始偏移。原生条件/控制消费者仍未闭合；下文历史全局分发推断不作为本轮前提，不因静态表交叉一致升级为运行验证。用户已暂缓Sandbox修复，本轮未运行游戏/UE或DevFlow候选。

> **2026-11-03 重要更新**：Leviathon `default.fexty`（本地缓存已有，此前漏读）提供 27/58 条件类型的社区命名映射，覆盖 81.5% 条件段使用，参数形态全部自洽。本交接文档 R1 路线随之降级为"定向校验"而非"全面逆向"；最新路线见 [PLAN-20261103-001](PLAN-20261103-001-rathian-review-adoption.md)。下文保留 2026-11-02 的静态取证结论作为历史。

- 日期：2026-11-02（2026-11-03 更新顶部结论）。
- 背景：用户授权"按最有希望的方式取证，穷尽方法无法解决再交付交接文档"。本文档即该交付。
- 目标：闭合 MHWI 雌火龙 THK 决策的条件函数语义（BEH-01），使 UE 执行器能宣称"原作决策等价"。
- 结论先行：**静态路线在无完整逆向工具链条件下已到边界**。本轮闭合了地址载体、VM 主循环结构、段字段偏移与全量条件统计；穷举排除了跳转表分发；确认分发走运行时注册对象机制。逐函数语义需要 Ghidra/IDA 级类型恢复或受控运行采样，均为本轮不可得条件。

## 一、已闭合事实（均带证据，可复现）

| # | 事实 | 证据 |
| --- | --- | --- |
| F1 | 锁定地址对应 `Saved/MHWIRestoration/B05-20261024/analysis-text.bin`（解包后 .text 镜像，48,304,640B，sha256 `9b48a849…`），**不是** exe 原始文件偏移（直接反汇编 exe 偏移得到乱码，负例记录在案）；exe 本体 sha256 `c2ebbbd2…` 同步锁定 | 本轮双 hash 验证；`thk-condition-semantics-20261102.json#images` |
| F2 | `vm_tick`(0x1423fe8d0) 为主循环：rcx=VM 上下文；`[rcx+0x10]` 计数门控；288B 步长数组（`[rbx+0x18]`）与 64B 步长节点槽（`[rbx+0x20]`）两层迭代；每节点先调守卫 `0x1423fc990`，回调经 `0x142458b20`（数组取元素，`[rcx+0x30]` 基址/`[rcx+0x28]` 计数）取对象后进 `callback_dispatch`(0x1423ffaf0) | capstone 反汇编，指令级摘录见证据 JSON `vm_tick` |
| F3 | `0x1423fc990`（前称 condition_evaluator）实为 30B 守卫函数：`cmp dword [rdx+0x30],0` 返回 bool，不是 functionType 分发器 | 同上 `evaluator_wrapper` |
| F4 | THK 段（128B）字段偏移：endRandom@0、flowControl@1、branchingControl@2、**functionType@+8**、parameter1@+12、parameter2@+32、actionID@+76 | Leviathon `thk.py`（commit 1e647f08）与段大小 128B 互证 |
| F5 | functionType 全量统计：13,015/13,015 段有值；**仅 60 种**（max 202）；头部：0x2(7947)/0x0(2877)/0x70(263)/0x8(258)/0x5(248)/0x5a(186)；**32/60 参数组合唯一** | `thk-all-raw.json` 全表统计，见 JSON `function_type_usage` |
| F6 | ctx55（咬击链）画像：`(bc=2, ft=0x1f, p1=0, p2=0)`×43 即冲撞分支谓词；ft6 带参数 600、ft8 带参数 1000（阈值类候选）；ft0 带参数 20/25/30/35/50（权重类候选） | 同上 |
| F7 | **负结果**：全 .text 四种编码形式穷举（jmp [idx×8+disp] 绝对 / jmp [base+idx×8] / movsxd 相对 rel4 / movsxd 绝对）+ 2,857 个 `jmp reg` 站点回溯解析，未发现任何 >202 条目分发表；VM 模块（0x1423e0000–0x142420000）内 0 个注册器（0x14216ed60）调用（全 .text 共 24,366 个） | `scan_thk_jump_tables.py` 与脚本内嵌统计 |
| F8 | `name_lookup`(0x142400150) 为**字符串注册表遍历器**（`[node+8]`=串指针、`[node+0x28]`=next 的链式匹配，返回节点句柄）——条件语义名在运行时以字符串注册 | capstone 反汇编，JSON `pinned` |

由 F7+F8 的推论（推断，非已证）：functionType 分发走**运行时注册的对象/字符串注册表机制**（phase/DTI 系统，注册发生在启动期静态初始化区，pinned 的 phase_type_registration 0x1401e15c0 一带），不是编译期 switch。

## 二、被阻塞原因（为什么本轮无法闭合逐函数语义）

1. **分发机制是注册表+对象虚调用**。闭合语义需完整类型恢复：枚举 2.4 万注册桩→解析描述符结构→关联虚表与 evaluate 方法→逐个反编译。这是 Ghidra/IDA 会话级工程，ad-hoc capstone 脚本无法在本轮内收敛（跳转表路线已穷尽并排除，见 F7）。
2. **工具链缺口**：[PLAN-20261031-003](PLAN-20261031-003-rathian-evidence-pipeline.md) 已记录 REA 6.8.0 无打开目标、Ghidra 因 `GHIDRA_INSTALL_DIR` 未配置不可启动。本轮 capstone 5.0.7+pefile 为唯一手段，已用尽。
3. **运行采样路线未获授权**：受控运行原作可经 hook `name_lookup`(0x142400150) 直接 dump 注册表（名称↔句柄映射），但按项目边界启动原作需用户明确授权与观测工具建设，本轮未执行。
4. **描述符格式未解**：注册桩模式为 `lea rcx/rdx/r8,[rip+desc]` + `r9d=结构大小` + `call 0x14216ed60`；描述符→名称字符串的映射格式需反编译 registrar 本体才能解析。

## 三、下一步最短路径（按性价比排序）

| 路线 | 做法 | 产出 | 前置 |
| --- | --- | --- | --- |
| R1 Ghidra/IDA 类型恢复 | 配置 `GHIDRA_INSTALL_DIR` → 加载 exe（基址 0x140000000，.text 磁盘即明文，text.bin 可旁证）→ 以 registrar 0x14216ed60 为根 xref → 解析描述符 → 恢复 functionType→{名称,evaluate} 注册表 → 只反编译 60 个已用函数的 evaluate | 60 个条件函数语义（具名+逻辑） | 安装/配置 Ghidra，约 1–2 个工作会话 |
| **R2 运行时观测（2026-11-03 更新为 LuaEngine 路线）** | MHW 为 MT Framework，主流注入方案是 **LuaEngine（Gitee 系，轻量注入器：直接内存读写 + ImGui）**，非 REFramework（后者面向 RE Engine）。授权启动原作后：① 运行时 hook 已锁定的 `vm_tick`(0x1423fe8d0)/条件守卫/`name_lookup`(0x142400150)，dump 注册表与函数名映射；② 对 THK 决策链做受控观测采样（固定任务/装备/无 nativePC 覆盖）；③ 顺带 dump EM_DMG 受击选择与 PBC 实际耐久。偏移与我们的 exe hash（c2ebbbd2…）对应，MHWI 已停更、偏移稳定 | 名称↔句柄映射 + 决策观测样本（支持 BEH-01/EM_DMG/PBC） | **用户授权启动原作**；注入器为第三方软件，装前快照游戏目录、不改安装 |
| R3 数据侧继续收敛 | 60 函数中 32 个参数唯一；与已证数值做数值匹配（例：ft6 参数 600 恰等于 dtt_agr `Build_to_Trigger=600`，ft8 参数 1000 与耐力区间同量级——均为**待检验假设**）；向 Leviathon 维护者仓库求 condition 名称资源（.nack 语法含 functionName/functionLiteral，社区 wisdom 可能已有表） | 部分函数的具名候选 | 无（可立即做，但产出是候选不是闭合） |

R3 的 600 对应 dtt_agr Build_to_Trigger 属数值巧合级假设，未验证前不得写入忠实 profile。

### 工具路线对照（2026-11-03 调研结论）

| 层 | 现有方案 | 结论 |
| --- | --- | --- |
| 文件层解包 | MHWNoChunk 原理（本项目 extract_resources.py 已复用：按需提取、无中间 PKG、2x 速度/0.5x 磁盘） | **已是最优**，社区无质变替代品；改进=用已建 171,615 条索引做单文件精准提取（秒级、增量 MB 级） |
| 数值层 | 网上已验证数据库（Kiranico/wiki）+ 本机解包字节回读 | **最优组合**：占位 0/耗时 0；双源一致升为 cross-verified（NUM-03 已按此闭合） |
| 运行时层 | x64dbg 自写脚本（原 R2） | **被 LuaEngine 替代**：Lua 脚本门槛远低于逆向调试器脚本，占位几十 MB |
| 格式解析层 | Python construct（Leviathon 同栈） | 010 Editor 为商业付费，ImHex 免费但换栈无净收益；**维持现状** |

R3 的 600 对应 dtt_agr Build_to_Trigger 属数值巧合级假设，未验证前不得写入忠实 profile。

## 四、复现与产物

```powershell
python Scripts/MHWI/disasm_thk_native_semantics.py --self-check   # 事实+统计+负结果固化
python Scripts/MHWI/scan_thk_jump_tables.py                        # 跳转表穷举负结果复现
```

依赖：`pip install capstone pefile`（本轮装 5.0.7 / 2024.8.26）。输入 hash 校验内建于脚本，不匹配即拒绝运行。
产物：`Saved/MHWI-Rathian-FirstChain/thk-condition-semantics-20261102.json`（21.7KB）。

## 五、关联文档

- [总体方案](PLAN-20261031-002-rathian-restoration-master.md)、[证据管线 E01](PLAN-20261031-003-rathian-evidence-pipeline.md)、[AI 细案 AI-01](PLAN-20261031-004-rathian-ai-world.md)
- [完整性核对页 BEH-01](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)
- 首链实施：[PLAN-007](PLAN-20261031-007-rathian-first-chain.md)、[CHG-20261031-003](../Changes/CHG-20261031-003-rathian-first-chain.md)
- 本轮记录：[CHG-20261102-002](../Changes/CHG-20261102-002-rathian-vm-semantics-recon.md)
