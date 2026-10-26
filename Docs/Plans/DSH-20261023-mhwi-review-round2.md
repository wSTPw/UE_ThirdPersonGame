# MHWI Round 2：真实 PIE 验收返修

日期：2026-10-23。Codex 已完成最终 UBT 构建（87.03 秒成功），正式 DA/Montage 已保存。当前编辑器已加载最终二进制。

继续原 parent session 与原文件分工。只修当前证据所指问题，不扩范围。禁止修改 ACL、禁用沙箱、反复尝试 shell；使用 read/edit/write 工具，宿主负责命令与 UE。

## 第一处实际失败

方向套件报告：`Saved/MHWIImport/PIE-behavior-direction.json`（2026-10-23 01:39）。boot 22 项正常，进入 `dir_prepare` 后抛异常：

```
_phase_dir_prepare -> _check -> suite['checks'].append
KeyError: 'checks'
```

`_check` 的 `setdefault(current_suite, {'checks': []})` 无法给已创建但无 checks 字段的 suite 补字段。请 C 修复套件初始化与检查记录契约，并静态审查各 suite、phase、input、状态机中同类运行即报错的问题；不要弱化行为断言。修复范围只限 `Scripts/MHWI/pie_behavior_corrections.py` 与报告。读报告时不要整份复制 data。

修后立即回复。Codex 会继续实际运行四个套件。不要自行宣称 PIE 通过，不要调用 UE 或编译，不要改业务参数掩盖失败。
