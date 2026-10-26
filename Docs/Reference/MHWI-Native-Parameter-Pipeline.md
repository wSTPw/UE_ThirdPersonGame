# MHWI 原始参数批处理

更新：2026-10-24。用户要求优先解包参数，减少逐动画人工比较。当前已实现读取、汇总和白名单导入；未知输入消费/IK执行仍未还原。实施见 [记录](../Changes/CHG-20261024-004-mhwi-native-parameter-pipeline.md)。

同日后续[批判性审查](MHWI-Restoration-Review.md)发现：`Gauge_No_Decay_Time_after_Spirit_Gauge_Upgrade`的10秒当前被用于暂停颜色T，Q却没有自然衰减；该消费者映射不能仅凭数值导入成功认定正确。气刃踏步cost20也未在本白名单中，正式DA仍为12。本文保留当时21处导入事实，不将其扩大为全部资源机制已原版还原。

B01后续现状：[原生基础修复](../Changes/CHG-20261024-007-mhwi-native-basics.md)已将气刃踏步cost20写入正式DA；原参数导入脚本也补入该字段，当前预览为18个招式属性+4个全局属性，共22处。下文21处是原批次历史规模。B01另以COL/FSM直接读取入口修正攻击与路线；不据此关闭十秒保护、shell和输入消费者取证项。

B02进一步确认该20为尝试强化消耗，非弱斩启动门槛：原COL无槽18/替换28及一手动作注记互证，已恢复不足槽免费弱斩，并按原序实现插入上挑的III/I槽条件分支。见[B02记录](../Changes/CHG-20261024-008-mhwi-spirit-branches.md)。数值来源仍为原文件，未推测窗口或其他未解消费者。

## 数据与出处

原安装只读，48项/约0.23MiB原始参数提取到 `ArtSource/ThirdParty/MHWLongSword/NativeParameters/nativePC/`，独立extraction-manifest记录包/偏移/大小/SHA256，不覆盖早期素材清单。

`wp03_param.w03p`为1584字节资源。依据 [Synthlight/MHW-Editor原作者定义](https://github.com/Synthlight/MHW-Editor/blob/b6ff379b13079a4abb99490590fb05dfe6851bbc/MHW-Generator/Weapons/Wp03Param.cs) 的固定commit、模板及公开资源读取实现解析。五个上游文件的URL/SHA256在 [版本指纹](../../Tools/MHW/native-parameter-sources.json)，缓存保持原样，不注册或改写第三方插件。

425个标量/文本字段覆盖1572字节，其中100项具有上游名称；尾部12个零字节明确保留为未解释区，不伪造字段。公开字段名称也不自动证明它由哪个动作过程消费。完整加解码往返、逐字段重编码、连续覆盖和原文件hash检查通过。

| 原始表字段/偏移 | 源值与项目转换 |
| --- | --- |
| 气刃I/II/III/回旋消耗，0x4a1..0x4ad | 0.15/0.15/0.20/0.25 → 项目0–100槽的15/15/20/25 |
| 正常见切所需槽，0x4c5 | 0.1 → 10；阈值由扣费前槽判断 |
| 白/黄/红持续，0x4f1..0x4f9 | 195/135/60秒 |
| 回旋升级后停止衰减，0x51d | 10秒 |
| 见切伤害倍率/霸体时长，0x525、0x534 | 1.3、1秒 |
| 居合保持/霸体，0x540、0x544 | 3.5秒、2秒 |
| 居合回槽，0x4e1..0x4ed | 普通15秒/反击30秒，原生period均15 → 项目100/15每秒 |
| 登龙回槽，0x4d1..0x4dd | 非红10秒/红15秒；period均15 |
| 居合速度，0x53c；登龙命中延迟/上限，0x5f8..0x604 | 原值0.4；首击0.4秒、后续0.05秒、上限7。已经提取，尚未盲目套到Montage PlayRate或当前Land窗口 |

百分比转换保留float32的7位有效十进制精度，防止0.150000006乘100形成阈值15.000001。报告同时保留原float、偏移、转换和项目值。

## 一次运行生成什么

根目录运行：

```powershell
python Scripts/MHWI/extract_native_longsword_params.py --fetch-layout
python Scripts/MHWI/build_native_action_database.py
```

`--fetch-layout`仅在缓存缺失时按固定URL恢复，校验SHA256，拒绝覆盖不同的已有缓存；正常已缓存执行不联网。依赖本机Node.js的OpenSSL legacy Blowfish资源读取，参数在内存解码，源文件不改。

统一结果：`Saved/MHWIImport/NativeParameterResearch-20261024/native-action-database.json`，含425字段、164动作全部TIML、90个FSM节点/307条有序边/307棵条件树、299条输入轨/961个key以及4条完整IK链。原始mask、value、control、插值码与条件树均保留；不再逐招人工抄参数。

IK的XFS19已完整消费5982字节/件，原始链为左臂6/7/8、右臂10/11/12、左腿14/15/16、右腿18/19/20；含偏移矩阵、限角和控制字段。类型19按16个float、35按3个float读取，所有嵌套记录长度和文件尾均校验；不是已经迁移原作IK解算器，也不直接当UE compact-pose索引。

[原作者资源类表](https://gist.github.com/Andoryuuta/7520bcded08f8d5830baaee4b3b99671)确认CMS是相机设置，不能当整件武器挂接表。Arm/Leg Manager、IKCtrl、CTM目前仅做原始资源目录/指纹，不猜其匿名二进制为挂点。

## UE批量导入

新二进制已加载且PIE停止后，通过MCP门控执行：

```python
import author_native_parameters as native_parameters
native_parameters.run(save=False)  # 完整预览，不写正式UObject
native_parameters.run(save=True)   # 备份后写入并逐项读回
```

正式资产为 `/Game/MHWI/Data/DA_MHWI_LongSword`（UMHWIMovesetData），当前白名单覆盖11招的17个属性和4个全局属性，共21处。每次重新验证源文件/模板，不直接信任可编辑JSON。保存前后核对Montage、武器事件和每条Route；原输入覆盖不丢弃。

原生表与此前公开表校准值在这21处一致，所以本次主要将数值来源改为可重建的原文件，不宣称出现21项新的视觉变化。预览/保存报告记录旧值、源字段、偏移、转换、新值与资产hash。

## 自动化边界

源输入299条轨的value均属于各自control_l掩码，但transition5消费/触发与接收/执行/缓存的对应关系仍未知。FSM保留原运算码和完整有序树，不把数字猜成已确认AND/OR，也不把首个非零key当取消帧。现有23招148条路由窗口仍是显式项目调校。

匿名ActionParam块有Gravity/TimeRate/初速度，但缺动作消费者映射；不能见到-3000就给某动作赋值。居合速度0.4也不能直接当全局动画倍率。原生shell延迟需要独立延迟命中消费模型，当前值只导出，避免修改Land窗口后被合法取消提前清掉。后续只补缺失消费者映射和少量自动抽检，无须恢复全量逐动画目测路径。
