# MHWI Round 4：积槽夹具的有界结束

Round3 已完成，宿主AST通过，正在运行 direction（脚本已加载）。本轮仍只修改 C 的测试脚本/报告，不碰业务、不运行UE/shell、不改ACL。无需再通读其他代理源码或全部任务上下文，请直接核对以下两个具体点。

`_phase_gauge_attack` 当前每逢新动作就重置 queued，在取消窗口继续 LMB，永远不主动停下。积到 goal 也继续循环，而只有 `_phase_gauge_idle` 检查 goal；因此可能一直不回 idle，并撞该 phase 8秒预算。请在槽达到 goal 后停止排新 LMB，等已排队动作结束再进入 idle；检查 pending 的影响，保持真实伤害/成本。若有更直接的真实原因，请给出对应代码而非盲改。

每次 `_phase_gauge_idle` 发起新普攻尝试也应重置 seen_move；现在 seen_move 可跨 attempt 残留，可能误判输入尚未开始已完成。结合 Round3 的输入确认契约处理，保留有限超时、失败证据。

完成后立即回复；不要再做整份验证脚本的泛化大改。宿主会跑 ground/air/lifecycle。当前 direction 在运行，新源码编辑不会影响已加载的Python类。
