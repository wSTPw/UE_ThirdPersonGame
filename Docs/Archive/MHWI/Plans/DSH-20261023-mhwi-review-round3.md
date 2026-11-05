# MHWI Round 3：异步输入等待契约

仅 C 脚本/报告返修，复用原子代理；禁改业务与资产，禁 ACL/shell 修复。Round2 的 Python AST 已由宿主通过。

重新 direction，2026-10-23 01:46:08 boot 正常，01:46:09 在 `ensure_drawn_wait` 失败：`real E input reaches the drawn stance`。详见正式报告（先保留为 fail2，勿复制全部 data）。

根因候选：Slate post-tick `_press('toggle')` 只排队 Enhanced Input，下一次 callback 可能仍 idle/sheathed，当前 wait 一看到 idle 就立刻断言。请审查真实异步输入：启动、观察活跃、结束后断言应区分；使用状态确认和有限超时，不靠本轮 callback 立即消费。Draw/Sheath 的 Montage 和 bSheathed 切换有时序。

请修好 `_phase_ensure_drawn_wait` / sheathed 对称路径，并审查其他按键后 next-phase 立即 idle 判断、尚未观察启动就判结束的同类错误。报告需要记录 observed move/stance 等关键事实，不要仅延长所有等待或弱化断言。参考已通过历史 pie_animation_corrections.py 的异步注入形式，但保留本轮正式数据和新行为。

修改完成即回复，Codex 继续验收；若发现实际业务问题先清楚汇报，不擅自扩大文件范围。
