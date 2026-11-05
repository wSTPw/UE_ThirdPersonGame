# PLAN-20261030-005：雌火龙遗漏动画补齐

- 状态：implemented-scope；目标em001，沿用现有141骨SK_EM001_Body_Skeleton。
- 用户需求：解包并导入遗漏动画。旧24条与用户资产保持，不改玩法蓝图。
- 官方来源：[Epic UE5.8 FBX动画导入](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-animations-using-fbx-in-unreal-engine)，动画单独导入应指定既有Skeleton；源读取沿用项目已使用的Feuleur 1.3.9。

## 当前证据与方案

CHG-022仅完成em001_00前24条。实际编辑器读回24 AnimSequence，均为4.15秒，静态发现旧导出未设scene帧范围。本轮枚举原采集批次的19个LMT，与归档索引/源hash核对；按非零动作指针与源帧数生成差集，只导出缺少的资产。每动作显式设置0..frame_count-1，60FPS；单帧最少一个采样间隔，报告例外。空容器/空槽单列，不生成伪动画。所有新资产复用原Skeleton，不迁移路径。

## 验证与回退

建立逐bank/动作/源hash/帧数/FBX/UE路径清单；逐条核对类、Skeleton、时长、磁盘保存；保存旧24条hash比较。核对导入集合覆盖所有有效LMT动作，失败不记完成。抽查动画实际骨轨变化，不以仅文件存在作为可播放证明。原作姿态/叠加层忠实度不在本批验收。无C++变化，不编译引擎。

回退仅删除本批清单列出的新增动画，保留旧24条；新增转换/导入脚本与文档可定点撤回。实际结果见[CHG-023](../Changes/CHG-20261030-023-mhwi-rathian-animation-completion.md)及[动画库现状](../Systems/MHWI-Rathian-Animations.md)，不回写历史CHG-022。
