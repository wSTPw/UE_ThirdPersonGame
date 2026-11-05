# CHG-20261102-002：THK VM 条件语义静态取证（负结果固化与统计收敛）

- 状态：completed-scope（本轮可闭合事实全部固化；逐函数语义被工具链阻塞，交接文档已交付）
- 日期：2026-11-02
- 需求摘要：用户授权"按最有希望的方式取证，穷尽方法无法解决再交付交接文档"。目标 BEH-01（THK 条件函数语义，E01/AI-01）。
- 关联 PLAN / ADR / 问题 / 接口 ID：[VM 语义交接文档](../Plans/MHWI-Rathian-VM-Semantics-Handoff.md)、PLAN-20261031-003（E01）、PLAN-20261031-004（AI-01）、[完整性核对页 BEH-01](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)。
- Git：工作区变更，未提交。

## 原因与结果

原行为：BEH-01 为"未开始"状态——锁定地址未验证过载体、functionType 语义无任何统计画像、分发机制未知。

当前行为（全部为只读静态发现，未执行原生字节、未启动原作）：

1. **载体闭合（F1）**：锁定地址对应 `analysis-text.bin`（解包后 .text 镜像，48,304,640B，sha256 `9b48a849…`）；直接反汇编 exe 文件偏移得到乱码（负例）。双 hash（exe `c2ebbbd2…` + text.bin）锁定并内建于脚本。
2. **VM 主循环结构（F2/F3）**：vm_tick 对象化执行（288B/64B 两层迭代、守卫 0x1423fc990 实为 30B 小函数、回调经 0x142458b20 数组取元素进 callback_dispatch）。
3. **段字段偏移铁证（F4）**：functionType@+8、parameter1@+12、parameter2@+32、actionID@+76（维护者 thk.py 与 128B 段大小互证）。
4. **条件空间收敛（F5/F6）**：13,015 段仅 60 种 functionType（max 202），32/60 参数组合唯一；ctx55 咬击链画像（0x1f 谓词 ×43；ft6/600、ft8/1000 阈值候选；ft0 权重候选）。
5. **负结果（F7）**：全 .text 四种编码穷举 + 2,857 个 jmp reg 站点解析，无 >202 条目分发表；VM 模块 0 个注册器调用。分发为运行时注册对象机制（推断）。
6. **名称注册证据（F8）**：name_lookup 为字符串注册表遍历器——语义名以字符串注册，注册桩描述符格式未解。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Scripts/MHWI/disasm_thk_native_semantics.py` | 新增（DualImage/.pdata 边界/handler 特征提取） | E01 静态取证主脚本；hash 不匹配即拒绝运行 |
| `Scripts/MHWI/scan_thk_jump_tables.py` | 新增（四编码穷举扫描） | 跳转表负结果的可复现工具 |
| `Saved/MHWI-Rathian-FirstChain/thk-condition-semantics-20261102.json` | 新增 21.7KB | F1–F8 证据固化（images/pinned/vm_tick/evaluator_wrapper/function_type_usage/boundary） |
| `Docs/Plans/MHWI-Rathian-VM-Semantics-Handoff.md` | 新增 | 用户要求的交接文档：已闭合事实/阻塞原因/三条最短路径 |
| `Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md` | BEH-01 行更新 | 记录本轮进展与新边界 |

## 接口、事件与资源影响

无既有接口/签名/蓝图/资产变更；不修改游戏安装、不修改 848 动画与既有证据 JSON。新增依赖仅 Python 包 capstone 5.0.7 与 pefile 2024.8.26（pip，本机环境）。用户既有未提交修改保持原样。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 双 hash 校验 | Python hashlib 流式 | exe 与 text.bin 均匹配 pinned | 脚本内建，不匹配即 SystemExit |
| 求值器/vm_tick 反汇编 | capstone 5.0.7 | 干净 MSVC 代码（对比 exe 偏移乱码） | JSON `evaluator_wrapper/vm_tick` |
| 跳转表穷举 | 四编码 + jmp-reg 回溯 | 0 表 >202 条目（负结果） | `scan_thk_jump_tables.py` 输出 |
| functionType 统计 | thk-all-raw.json 全量 | 60 种/max202/32 参数唯一 | JSON `function_type_usage` |
| 文档检查 | `python Scripts/Docs/check_docs.py`；`git diff --check` | 通过（本轮新增链接无错误） | 本记录 |
| PIE/原作运行/编辑器 | — | 未执行（静态边界） | — |

## 风险、遗留与回退

- 遗留：逐函数语义闭合（BEH-01）阻塞于工具链，恢复路径 R1（Ghidra 类型恢复）/R2（授权后运行时转储）/R3（数据侧数值匹配）见交接文档；LR 资格（BEH-03）独立未闭合。
- 回退：删除上表新增的 2 脚本 + 1 JSON + 1 交接文档即完全回退；核对页 BEH-01 行还原为原描述。不影响任何既有数据。
- 数值巧合假设（ft6/600=Build_to_Trigger 等）未验证前不得进入忠实 profile。

## 已同步文档

[VM 语义交接文档](../Plans/MHWI-Rathian-VM-Semantics-Handoff.md)、[完整性核对页](../Reference/MHWI-Rathian-Completeness-Check-20261102.md)、[Plans 索引](../Plans/README.md)、[Changes 索引](README.md)。
