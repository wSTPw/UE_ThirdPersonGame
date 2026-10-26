# MHWI 开发台账取证收尾（B17）

- 日期：2026-10-26
- 状态：**离线静态取证完成**；台账中仍需运行观测或语义闭合的项目继续开放。
- 原计划：[PLAN-20261026-001](../Plans/PLAN-20261026-001-mhwi-outstanding-evidence.md)。本报告是B13之后的接续结果，保留B13原报告的历史含义。
- 范围：逐项复核R07、R09、R10、R13、R18、R19、R20、R21、R29、R30，并复核与R16/R31相关的shell、时钟及伤害边界。只读指定游戏安装、原生归档和仓库内固定分析文件；没有启动游戏、UE或PIE，没有改玩法源码、正式资产或安装目录。

## 执行结论

这次完成了计划要求的离线来源复核、选择性归档提取、解析器重读、函数快照复验和逐项归纳。十项都获得了可复核的原生来源或消费者证据；但“静态取证工作已做完”不等于“十项玩法已完整还原”。凡依赖运行中的对象身份、伤害事件、取消时序、目标销毁、骨骼求解或坐标系的结论，仍明确标为未闭合，台账状态不升级。

游戏安装内存在 `nativePC` 覆盖。48项太刀参数/资源清单从压缩归档重新读取后全部匹配原有SHA；但当前运行优先级会加载其中5项本地覆盖。因此本报告把归档原件和当前安装覆盖分开处理：两项COL覆盖解析后仅在击退字段上出现记录差异；三个居合延迟SHLP覆盖大小各增加32字节，仓库无对应语义解码器，不能解释其字段意义。下文涉及原版数据时均指归档原件；涉及当前运行行为时必须考虑覆盖。

## 来源与复验

| 来源/检查 | 实际结果 | 证据位置 |
| --- | --- | --- |
| 指定安装 `F:/PCprogram/Steam/steamapps/common/Monster Hunter World` | EXE SHA-256 `c2ebbbd2c49f216d484e31a5219bed419eb1e5e7d206d02cba040a3ab79d90ea`，与分析源固定指纹一致；13个G归档的文件尺寸和修改时间与已有索引一致 | 本机 `Saved/MHWIRestoration/B17-20261026/native-parameter-fingerprint-verification.json`、`game-assets/archive-index.json` |
| 48项归档资源 | 使用仓库 `Tools/MHW/extract_resources.py` 的 `Archive.read` 从chunk解密/解压指定偏移，48/48与参数清单SHA一致；并记录当前 `nativePC` 覆盖 | 本机 `native-parameter-fingerprint-verification.json` |
| 原生太刀参数 | W03P重新解密/往返：425字段、100个已知标签、1572字节已解释、12字节零尾、源未改变 | 本机 `native-parameters/longsword-native-parameters.json` 与 `.bin` |
| B13原始证据重建 | `python Scripts/MHWI/build_outstanding_evidence.py`：PASS；18函数、113动作绑定、18项资源 | `Tools/MHW/native-outstanding-evidence.json` |
| B13续查函数 | `python Scripts/MHWI/verify_outstanding_followup.py` 固定分析.text重新追踪19个函数；19/19的入口、范围、指令、缺口和分支摘要一致。EXE与分析.text SHA均匹配固定指纹 | 脚本及快照 `Tools/MHW/native-outstanding-followup.json`；本机 `followup-function-revalidation.json` |
| 武器/部位表 | 解析器重读：320条太刀武器记录、7个部位映射、12行肉质、1条断尾；1351字节有布局解释，9字节零尾保留未映射 | `Scripts/MHWI/extract_native_parts.py`、`Tools/MHW/native-parts-layout.json`；本机B13资源输出 |
| 游戏资源选择提取 | 24个相关资源另存B17目录，包含COL、LMT、FSM、PLP、W03P、shell、部位数据；没有写入游戏安装 | 本机 `game-assets/extraction-manifest.json` 与 `game-assets/nativePC/` |

分析.text是仓库已有的固定版本离线代码区，不是直接把加密游戏归档当指令解码。19项快照复验确认的是固定源上的静态指令一致性，不表示脚本自动解释了完整原生语义。`Saved/MHWIRestoration/B17-20261026/` 是本机忽略目录，不随仓库提交；可用仓库解析器和源清单重建，公开C#布局缓存仍按既有流程通过SHA固定。

### 48项清单内发现的当前覆盖

| 资源 | 归档原件SHA-256 | 当前`nativePC` SHA-256 | 大小（归档→覆盖） |
| --- | --- | --- | ---: |
| `hm/wp/wp03/collision/wp03.col` | `5f3791b307bb1c6afe3f46b09dc97a771daf61df13ff5dc1ee70a0a8aa009c27` | `37ccaace087d3f4c7090b2e8b3c39fb0a4fcdabf698fcff47bed94319fc07475` | 20408→20408 |
| `hm/wp/wp03/shell/collision/object.col` | `a350e96b5ceeb98a08bc5cabe2a996e5e795e63240293bb8dc81c0473c8dc2dc` | `599792c457667c2a830abf375fab6e1e98476238fb173be3d5431bb890a45101` | 4197→4197 |
| `hm/wp/wp03/shell/data/iaikijin_delay_hit_red.shlp` | `ea59fd435d60db32b5a40b376da307ef6766ba74df52d2efc62b3bd06693b0cc` | `f7bb36ca52f9ff07309247f6a88ad9414c86b87efbd89ad9e4ab123d13b8b76f` | 1872→1904 |
| `hm/wp/wp03/shell/data/iaikijin_delay_hit_white.shlp` | `28fce4d163a7227a5e54e09c140c4dc97555fe8a94a2076b6693a8e8cba445f6` | `a2bc4abc7c56ce9d67bc503dca2eecf845352c7c859a46b7ad97638ba8ed2a8c` | 1872→1904 |
| `hm/wp/wp03/shell/data/iaikijin_delay_hit_yellow.shlp` | `6e363d4ba8c7b5f6212a1ac9eb63cc9c3126151e36ce5c12d16f74123e6e9ef9` | `996e0b85113ccd0c7f2186224b33441ce95d44241c21654ee93513bf5dfba82c` | 1872→1904 |

## 十项逐项结论

| 台账项 | 本次完成的离线证据链 | 仍不能从当前静态证据推出 |
| --- | --- | --- |
| **R07 精确取消** | 更正对象身份：`actor+0xe480` 是 `PlMotionInput`，getter `0x141f62080`；次级参数位于`+0x60`。`e490/0x141f62090`是另一音频对象。输入管理器命令许可按137项ID表映射执行位；缓存许可独立读取，另有全局202/203位及命令156特例。缓存写入、许可丢失清除、当前/保存状态谓词、成功命令写入武器控制器的链均已定位。 | 已编译的条件注册含777项，但FSM属性到实际命令ID/位、transition5求值和逐动作窗口映射仍未可靠解码。双许可链不能折算成统一取消时间，也不能由原始TIML位直接声称取消生效。 |
| **R09 转向/方向** | 公共加载器`0x141387920`读20行、stride `0x20`至公共参数`+0x90`；动作更新在公共trigger bit11时取角度索引`+0x110`并清触发。方向向量、最小角差、可选反向门限、满角分支/布尔分支、行内插值时间以及yaw提交函数`0x141f755c0`已连上。 | 20行与每个动作索引的完整映射、镜头/移动坐标来源和实际插值播放结果仍需运行观测。表值不是“每秒转速”。 |
| **R10 Q自然衰减** | W03P `0x499=120`、`0x49d=0.05`加载到参数`+0x800/+0x804`；更新按秒增量推进倒计时，严格小于0时重置0.05并扣Q 0.05，名义间隔6秒。单帧最多扣一次；Q改写会重置计时；回槽计时期间自然衰减分支被跳过。 | 上游资格位的全部来源、各技能/暂停条件以及hitstop与低帧顺序没有全覆盖；公式是静态分支结论，尚无游戏行为记录。 |
| **R13 回旋清槽** | Action69只有合格接触回调才置锁存；update的公共bit30或动作exit会调用同一提交函数。提交检查锁存后升色、清Q、刷新颜色余量、赋10秒暂停并清锁存；空挥退出不会清Q。 | bit30准确帧、所有目标/接触类别资格和命中后中断顺序未穷尽，不能写成任何退出都会升色。 |
| **R18 刀刃/部位空间** | 正确部位资源为`em001.dtt_epg`（不是`.em_dmg`）；完整表解析如上。原版太刀COL为59记录；当前 `wp03.col` 覆盖仍为59记录，解析字段中52条只在`Flinch_Value`不同。原版shell COL为16记录；覆盖中12条只在该字段不同。当前覆盖没有改变本解析器识别出的几何、伤害映射及其他记录字段。 | COL局部几何到骨骼/武器空间的完整变换、命中部位索引如何选中肉质表及完整伤害消费者仍未闭合。`em001.dtt_epg`的表值不能单独证明游戏实际命中行。 |
| **R19 延迟shell** | Action91/92合格接触捕获首目标、颜色、部位和目标相对位置；首延迟0.4秒，后续间隔0.05秒，队列上限7。更新按玩家秒计时，到期用目标当前姿态重投影保存位置再创建shell；单个接触可填充多个后续项。Action102居合追加shell使用独立0.5秒参数并有动作/目标条件。 | 取消、退出、目标销毁/失效、多个同时目标选择，以及从SHLP到碰撞/伤害的所有下游仍有未覆盖分支。三个当前SHLP覆盖存在32字节格式差异，但缺少语义解码器。 |
| **R20 耐力** | PLP一次性消耗表行0/1为25/50，stride `0x18`，由`0x1402deb10`读取；持续表由另一参数区按秒增量消耗。公共bit16走一次扣除，bit30可走持续消耗；覆盖索引为负时回退公共`+0xa8`。扣除后余额钳至0..最大。motion140首帧索引1/触发与50基础消费相符。 | 各回避motion的索引/触发绑定、体力恢复及不足时拒绝逻辑、技能倍率的完整优先级和项目耐力实现仍未覆盖。 |
| **R21 普通回避保护** | Action18入口经公共保护设置选择行0；PLP技能0x4e索引钳制0..5，六个帧值为13/15/17/19/22/25，衣装值30；角色字段`+0xe168`存浮点帧，更新递减并设置角色/碰撞保护位。 | 保护位到各种伤害类型判定的完整消费者、保护窗的起止帧和其余四方向构造路径尚未闭合。13帧仅为静态标尺，不能作为本轮实机验证。 |
| **R29 特殊纳刀等待** | Action98请求motion306；Action99不再发motion请求并按秒倒数W03P 3.5秒（有技能分支）。原始LMT/TIML为272/271帧、loop129；`mActionPhase`及`mWeaponMotionNo`在73/80帧有事件。 | 全局播放、循环及持刀姿态消费者未证明Action99期间motion必然继续或必然冻结；73帧冻结仍是项目适配。需要运行观测才能确认事件和姿态。 |
| **R30 装配/IK** | 4条IK链资源SHA重验；XFS19解析器对每条IK记录完整消费5982字节，解析关节索引6/7/8、10/11/12、14/15/16、18/19/20。IKCTRL含12条类型/路径记录，4条非空路径对应四链。定位ARM/LEG/IKCTRL加载器及`cpIKCtrl`逐帧遍历12槽并调用虚方法求解。 | 管理器匿名字段的完整语义、solver虚方法实际坐标系、骨骼空间转换及角色/武器初始装配矩阵未完全解码。CTM保留为原始592字节资源；项目0.7缩放仍是拟合值，不能冒充原生挂接矩阵。 |

### 相关边界更正

- **R16/R19**：有色居合追加使用独立0.5秒队列；R19登龙延迟shell使用0.4秒首延迟。接触坐标保存为相对目标位置，目标移动后在生成时重投影；不能将0.4秒当作hit lag或动画冻结时间。
- **R11/R31**：W03P 10秒是颜色衰减暂停计时，不是Q衰减抑制；B12依据已由B13报告更正。运行效果及hitstop顺序未在本批验证。
- **当前安装覆盖**：48项复核清单中5项有`nativePC`覆盖；3个居合SHLP文件大小从1872变为1904字节。COL击退字段变化会影响当前安装的击退语义，不能把原归档原值直接代表当前运行；SHLP差异未解码，不推测它改变了哪些属性。

## 状态与交接

本批把PLAN-001范围内可完成的离线取证和数据复核收尾。R07/R09/R10/R13/R18/R19/R20/R21/R29/R30在开发台账仍保持“取证中”，因为每项都保留了上表具体未闭合的原生语义或运行边界；没有把快照复验、文件提取或静态调用链写成游戏验证。不得因本报告关闭B16用户运行验收、R-COMBAT-017/018行为确认或其余项目状态。

运行侧下一步由用户在该安装上按台账用例记录：输入边界、回旋空挥/命中后中断、Q与颜色时钟、登龙/居合位移及目标失效、回避受击类型边界、特殊纳刀73/80事件和IK姿态。测试时须注明加载了上述 `nativePC` 覆盖。其余纯静态未知若要继续，需针对编译条件表、shell格式、伤害消费者和IK虚函数增加专门解码；当前证据不足以把它们作为已知事实。

## 本批实际验证

```powershell
python Scripts/MHWI/build_outstanding_evidence.py
python Scripts/MHWI/verify_outstanding_followup.py
python Scripts/MHWI/extract_native_parts.py
python Scripts/Docs/check_docs.py
git diff --check
```

前两条实际结果分别为`passed=true, functions=18, actions=113, resources=18`及`melee_entries=320, flinches=7, hitzones=12, severs=1, consumed=1351, unmapped_zero_tail=9`。B17保存结果另记48/48资源SHA和19/19函数快照匹配。未运行编译、自动化、UE、游戏或PIE；后三者不是离线取证的验证手段。文档检查在本记录更新后执行并写入CHG。
