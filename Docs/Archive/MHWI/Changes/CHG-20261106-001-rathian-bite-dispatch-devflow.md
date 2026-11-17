# CHG-20261106-001：Luna DevFlow推进BITE动作83只读取证

- 状态：completed（限定静态证据与流程）；THK83→BITE启动及完整首链仍partial。
- 日期：2026-11-06。
- 需求摘要：按推荐顺序追THK发出83后如何查找/启动BITE，使用devflow-orchestrator与Luna，沙箱暂缓。
- 关联：[当前计划M0](../Plans/MHWI-Current.md)、ADR-0002、BEH-02、R-DATA-006、R-AI-003。
- Git：工作区变更，未提交。用户已有未提交源码/资产保留。

## 原因与结果

前轮只闭合动作表布局/注册循环，尚缺THK动作递交和启动消费者。本轮新增 `0x140269c30` 返回指针存储、`0x140269ce0` 键形状探查及 `0x14026b410 → 0x14026b160` 条件回调的局部静态证据；明确lookup/processor receiver来自不同入参，关系未证。回调虚表+0x28不等于BITE enter的+0x30；不能据字段布局或槽非空把整桥升级为已证。

最终候选14锚/1494原始字节、11固定输入、3源码行范围hash。四桥分别unresolved/candidate/unresolved/unresolved，原作条件验证与运行对照仍0。结论见[当前总账](../Reference/MHWI-Rathian-Evidence.md)；推导与完整证据保留在[已接受报告](../../Tools/DevFlow/Rathian-BITE-Dispatch-20261106/accepted/report.md)。

## 修改清单

以下相对路径根为 `E:/Unreal Projects/IntorCpp`。

| 文件 | 内容与影响 |
| --- | --- |
| Tools/DevFlow/Rathian-BITE-Dispatch-20261106/task.json、config.json、verify_evidence.py、expected-inputs.json、planning.md | 冻结原生Luna合同及纯JSON/原始字节检查；候选仅两数据文件 |
| Tools/DevFlow/Rathian-BITE-Dispatch-20261106/accepted/ | 原样复制已ACCEPTED的evidence.json/report.md；acceptance.json记录模型/快照/检查与未闭合边界 |
| 同控制目录的review-1.json、raw-review-1.json、review-1-normalization.json、review-2.json、main-review-1.json、host-original-verification.json、review-packet-2.json | 保留拒绝、修订、批准与原件检查；未篡改候选/冻结验收 |
| Saved/DevFlow/Rathian-BITE-Dispatch-20261106-input、Runs-20261106/、Exports/ | 固定本地输入副本、运行原始证据、已导出补丁；忽略目录，不等于已纳管 |
| Docs/Reference/MHWI-Rathian-Evidence.md | 只增本轮结论/缺口；更正旧表头磁盘偏移与selected-source-track目录笔误 |
| Docs/Systems/MHWI-Rathian.md、Docs/Plans/MHWI-Current.md、Docs/Known-Issues.md | 同步本轮只读取证状态、优先顺序；不宣称玩法功能变化 |
| Docs/Changes/README.md、Docs/Archive/MHWI/README.md | 最近5条索引更新；最旧CHG-20261104-001移入Archive/MHWI/Changes，内容未改 |
| Docs/Changes/CHG-20261106-001-rathian-bite-dispatch-devflow.md | 本记录 |

无新运行模块/接口，modules.json不改。历史归档正文不重写。

## 官方机制与证据分级

采用已选固定镜像静态路线，无新增架构方向。[Microsoft x64 ABI](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170)、[x64 unwind](https://learn.microsoft.com/en-us/cpp/build/exception-handling-x64?view=msvc-170)、[PE格式](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)解释参数寄存器、函数范围与VA/磁盘偏移；文档视图msvc-170适用于Windows x64机制，不宣称游戏使用该版编译器，更不证明MHWI业务语义。[Capstone维护方说明](https://www.capstone-engine.org/lang_python)支持静态反汇编方式。原生事实必须回到已锁EXE/text字节，字段名称/对象身份推断保留候选。

## DevFlow实际流程与拒绝记录

使用 `C:/Users/Butter cookies/.agents/skills/devflow-orchestrator/SKILL.md` v2：prepare→原生执行→capture/check→全新审查→风险决策→export。源仓库是独立小输入Git副本，基线 `f5d5c1fb292f5a27595378d3f88428388c5620c3`；没有清理或提交原工作区。工作副本不提供ACL隔离。检查器仅标准库解析数据，不导入/执行候选代码；本任务不依赖Sandbox，UE/构建验证通道本轮未调用。

1. 首轮质量8/9通过，THK地址多了file+前缀。执行者第一次修复仅改地址写法，检查器不变。
2. 该快照9/9通过，但独立Luna要求撤回“注册与查找同一表实例”；主代理也拒绝。主代理追加发现receiver入参不同、selector检查和部分窗口分配语义过强。
3. 执行者第二次也是最后一次修复只收窄文字/资格：整桥降candidate，保留局部static事实；14锚字节不变。
4. 新快照 `5735540e1a61782f48cd5560ff085090bb65fb3afce92498db52f12478bb4564` 再次9/9通过，另一个全新Luna批准，主代理抽查后ACCEPTED。旧拒绝不被覆盖，未对失败证据强制放行。

执行者 `/root/luna_bite_executor`；两审查者 `/root/luna_bite_reviewer`、`/root/luna_bite_reviewer_final`，均由宿主明确请求 `gpt-6-luna/high/fork_turns=none`。实际创建/完成凭据为parent-tool-attestation，不是模型自报。运行时登记5条模型记录（3执行尝试+2审查）；宿主创建/续派共6次，差额为审查格式回传。首审findings.evidence数组由主代理无实质改动地规范为字符串，原始回复及规范说明均保留。内部轮次/令牌/费用不可见，记null，不推算节省。

## 实际验证

| 检查/命令 | 结果与边界 |
| --- | --- |
| prepare/capture/check | 最终仅evidence.json/report.md改变；无越界；9案例通过，检查前后快照/控制不变 |
| 全新Luna独立审查+主代理record-decision/decide | 最终approve、ACCEPTED，无硬阻塞；仅接受限定静态报告 |
| export + 小输入仓库git apply --check | exit0；补丁SHA256 `f8fdfc8424ff41476866b6ab6717d4b36b3ed8b7c98c1316fcb36cc5983d91ae`；未向项目根应用补丁 |
| 已接受两文件hash核对 | evidence `5e7fafe04edf399605c3034e9674bbf06fd3f3fa5127ac24b5e9005288d0a56a`；report `46b5ac0c5b41ace6b16321be82078fa0a9a98b6c04bb900f9a4d8eed0f8fdf9a`，与最终快照一致 |
| 原件核对 | 归并前11原始输入全匹配；26源码/资产/既有工具证据保护文件全匹配。现状文档归并后另增补，输入副本不变 |
| python Scripts/Docs/check_docs.py | PASS：35份活动Markdown、334本地链接、16模块及快照JSON；不检查归档正文/标题或玩法 |
| git diff --check | exit0；最终26个保护文件、11份固定输入副本及两接受文件hash复核一致，检查器AST有效 |

未运行构建、项目测试、PIE、原作、注入/附加、依赖安装或重解包；未修Sandbox、未重启或关机。报告末尾“执行者未运行冻结验收”为交付时事实，后续父流程结果以[acceptance.json](../../Tools/DevFlow/Rathian-BITE-Dispatch-20261106/accepted/acceptance.json)为准。

## 风险、遗留与回退

THK83递交、receiver/对象身份、callback→enter、caller怪物归属仍开放；不能把报告ACCEPTED当忠实功能通过。不改旧JSON资格、不补假默认值。下轮继续从THK递交及wrapper调用者追两个receiver，再追callback记录/enter；未发现需重解包的文件缺口。Sandbox保持用户暂缓状态。

回退仅撤销本轮新控制/证据文件及现状页增补；把归档CHG移回原处、恢复两个索引。不reset、删除或覆盖用户已有工作；本地大输入副本/运行日志保持不自动清理。

## 已同步文档

[总账](../Reference/MHWI-Rathian-Evidence.md)、[系统页](../Systems/MHWI-Rathian.md)、[当前计划](../Plans/MHWI-Current.md)、[已知问题](../Known-Issues.md)、[变更索引](README.md)、[历史入口](../Archive/MHWI/README.md)。
