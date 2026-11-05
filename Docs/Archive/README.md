# 文档归档

**这里的文件是历史快照，不是现状依据。** 引用前必须核对当前源码与现状页。

归档时保留了原始正文，包括当时的错误结论、被推翻的口径和批次说明。这样做的目的是让"为什么改成现在这样"可追溯，而不是让读者把它们当参考。

两个分区：

| 目录 | 内容 |
| --- | --- |
| [MHWI/](MHWI/README.md) | MHWI 还原的全部历史：方案 57、变更 78、取证 34 |
| [Legacy/](Legacy/README.md) | 非 MHWI 的历史：主菜单、Ninja 动画、Motion Matching、文档基线、环境修复 |

## 不要从这里开始

想知道当前状态，去：

- [当前 MHWI 计划](../Plans/MHWI-Current.md)
- [太刀训练模组](../Systems/MHWI-LongSword.md)
- [MHWI 雌火龙](../Systems/MHWI-Rathian.md)
- [太刀取证总账](../Reference/MHWI-LongSword-Evidence.md)
- [雌火龙取证总账](../Reference/MHWI-Rathian-Evidence.md)

## 维护规则

- 归档区不再更新。发现归档内容与现实不符时，**改现状页**，不要改这里。
- `check_docs.py` 跳过本目录，因此这里的相对链接可能失效。要查某份归档的原位置，用 `git log --follow`。
- 新增归档：把文件移入对应子目录，并在该分区的 README 索引里加一行主题说明。
