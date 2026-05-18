# 背包与物品系统 — 详细设计文档

> 本文档描述 IntroCpp 项目中背包系统（Inventory）与物品系统（Item）的完整架构、类关系、数据流和功能分布。

---

## 一、系统总览

### 1.1 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                    表现层 (UI / 视觉)                         │
│   UW_InventoryUI (背包主界面)                                │
│   UW_InventorySlot (背包单格)                               │
│   UW_QuickSlot     (快捷栏单格)                             │
│   UDragItemOperation (拖拽数据载体)                          │
├─────────────────────────────────────────────────────────────┤
│                    行为层 (逻辑 / 交互)                       │
│   UInventoryComponent  (背包核心：CRUD + 装备 + 快捷栏)      │
│   APickupItem         (场景拾取物 Actor)                     │
│   UItemAction          (物品使用效果基类)                     │
│   ├─ UItemAction_Heal       (治疗效果)                      │
│   └─ UItemAction_RestoreMana (回蓝效果)                     │
│   UAnimNotify_UseItemComplete (动画帧通知)                   │
├─────────────────────────────────────────────────────────────┤
│                    数据层 (静态配置)                          │
│   UItemDataBase        (物品数据基类)                        │
│   ├─ UConsumableData   (消耗品子类)                          │
│   └─ UWeaponData       (武器子类)                            │
│   UItemDataSubsystem    (全局数据管理/缓存)                  │
├─────────────────────────────────────────────────────────────┤
│                    基础类型                                   │
│   FItemInstance (运行时实例结构体)                            │
│   EItemType    (物品类型枚举: 武器/消耗品/材料...)           │
│   EItemRarity  (稀有度枚举: 普通~传说)                      │
│   EWeaponAnimType (武器动画类型枚举)                         │
│   EBuffType    (Buff类型枚举)                               │
│   EDragSource  (拖拽来源枚举)                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 文件清单

| 层级 | 文件 | 职责 |
|------|------|------|
| **基础类型** | `EWeaponTypes.h` | `EWeaponAnimType` + `EBuffType` 枚举 |
| **基础类型** | `GlobalEvents.h` | 全局事件名常量 (`Item_Pickup`) |
| **数据层** | `ItemDataBase.h/.cpp` | 物品数据基类 + `FItemInstance` + `EItemType` + `EItemRarity` |
| **数据层** | `ConsumableData.h` | 消耗品子类 (HP回复/MP回复/Buff) |
| **数据层** | `WeaponData.h` | 武器子类 (投射物/动画/伤害参数) |
| **数据层** | `ItemDataSubsystem.h/.cpp` | 全局物品 DataAsset 管理器 (注册/查询/懒加载缓存) |
| **行为层** | `InventoryComponent.h/.cpp` | 背包组件 (CRUD/堆叠/重量/装备/快捷栏) |
| **行为层** | `PickupItem.h/.cpp` | 场景拾取物 Actor (碰撞检测→AddItem→Destroy) |
| **行为层** | `ItemAction.h` | 物品动作抽象基类 (Execute 模板方法模式) |
| **行为层** | `ItemAction_Heal.h/.cpp` | 治疗 Action (调用 AttributeComponent.ApplyHeal) |
| **行为层** | `ItemAction_RestoreMana.h/.cpp` | 回蓝 Action (调用 AttributeComponent.RestoreMana) |
| **行为层** | `AnimNotify_UseItemComplete.h/.cpp` | 使用物品动画完成通知 → Character.OnUseItemAnimFinished() |
| **表现层** | `UW_InventoryUI.h/.cpp` | 背包主 UI Widget (Grid + 详情面板 + 排序/关闭按钮) |
| **表现层** | `UW_QuickSlot.h/.cpp` | 快捷栏单格 Widget (图标+数量+拖拽) |
| **表现层** | `UDragItemOperation.h/.cpp` | Slate 拖拽操作 (携带源位置+物品数据+视觉图标) |

---

## 二、数据层详解

### 2.1 物品数据继承体系

```
UPrimaryDataAsset (UE 引擎)
 └── UItemDataBase              ← 所有物品的公共属性
      ├── UConsumableData       ← 消耗品特有：HP回复/MP回复/Buff
      └── UWeaponData           ← 武器特有：投射物/动画类型/伤害
```

**设计原则**：
- 每个 `.uasset` 实例对应一种具体物品（如 `DA_HP_Potion`、`DA_WP_FireStaff`）
- 在 Content Browser 中右键 → Miscellaneous → Data Asset → 选择对应子类创建
- 通过 `UItemDataSubsystem` 统一管理生命周期，避免各模块散落引用

### 2.2 FItemInstance（运行时实例）

```cpp
USTRUCT(BlueprintType)
struct FItemInstance
{
    FName ItemID;      // 关联到哪个 DataAsset（如 "HP_Potion"）
    int32 Quantity;    // 数量（可堆叠）
};
```

- **存储位置**：`InventoryComponent::Inventory[]` 数组 和 `QuickSlots[]` 数组
- **生命周期**：运行时动态变化（添加/移除/丢弃），不序列化到磁盘（存档需额外实现）
- **关键方法**：`IsEmpty()` 判断空槽位、`IsSameType()` 判断同品类（用于堆叠）

### 2.3 UItemDataBase（物品数据基类）

| 分类 | 字段 | 说明 | 典型值 |
|------|------|------|--------|
| **标识** | `ItemID` | 唯一 ID，TMap 键 | `"HP_Potion"` |
| | `ItemName` | 显示名称 | `"生命药水"` |
| | `ItemDescription` | 描述文本 | `"恢复50点生命值"` |
| **分类** | `ItemType` | 物品大类 | `Consumable` |
| | `ItemRarity` | 稀有度（影响颜色等） | `Common` |
| **外观** | `ItemIcon` | 图标纹理 (软引用) | `T2D_Icon_HP` |
| | `ItemStaticMesh` | 手持模型 (软引用) | `SM_Potion` |
| | `UseMontage` | 使用动画 Montage | `MNT_DrinkPotion` |
| **关联** | `ItemClass` | 掉落物 Actor 类 (软引用) | `BP_Pickup_Potion` |
| | `ItemActionClasses` | 使用时执行的 Action 类列表 | `[BP_Action_Heal]` |
| **背包** | `MaxStackSize` | 最大堆叠数 (1=不可叠) | `10` |
| | `Weight` | 单个重量 | `0.5` |
| | `Value` | 金币价值 | `25` |
| **标志** | `bCanSell` | 可出售? | `true` |
| | `bCanUse` | 可使用? | `true` |
| | `bCanDrop` | 可丢弃? | `true` |

### 2.4 UConsumableData（消耗品子类）

继承自 `UItemDataBase`，新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `HealthRestore` | int32 | 使用后恢复的生命值 |
| `ManaRestore` | int32 | 使用后恢复的魔法值 |
| `BuffType` | EBuffType | Buff 类型 (None/Regeneration/Speed/Defense) |
| `BuffDuration` | float | Buff 持续时间(秒)，仅 BuffType!=None 有效 |
| `BuffValue` | float | Buff 数值，仅 BuffType!=None 有效 |

**注意**：构造函数自动设置 `ItemType = EItemType::Consumable`

### 2.5 UWeaponData（武器子类）

继承自 `UItemDataBase`，新增字段：

| 分类 | 字段 | 说明 |
|------|------|------|
| **战斗** | `WeaponProjectileClass` | 投射物 Actor 类 (软引用) |
| | `WeaponAnimType` | 攻击动画枚举 (决定角色用哪个 Montage) |
| | `bIsRangedWeapon` | 是否远程武器 (true=投射物, false=近战 SphereTrace) |
| | `WeaponManaCost` | 单次攻击消耗 MP |
| | `WeaponDamageOverride` | 伤害覆盖值 (0=投射物默认伤害) |
| | `WeaponFireSocketName` | 发射 Socket 名 (默认 "hand_r") |
| | `WeaponAttackCooldown` | 攻击冷却(秒) |
| | `OverrideAttackMontage` | 专属蒙太奇 (99%留空，1%特殊武器用) |
| **外观** | `WeaponStaticMesh` | 武器 StaticMesh (装备时附到手部 Socket) |
| | `HandSocketName` | 手部 Socket 名 (默认 "RightHand") |
| | `WeaponScale` | 武器缩放 (FVector) |

**注意**：构造函数自动设置 `ItemType = EItemType::Weapon`

### 2.6 UItemDataSubsystem（全局数据管理器）

**职责**：集中管理所有物品 DataAsset 的加载与缓存。

```
编辑器创建 DA_xxx.uasset → RegisterItemData() 注册到 ItemDataMap (软引用)
                                          ↓ 首次查询时
                              LoadSynchronous() 同步加载 → 存入 LoadedCache (硬指针)
                                          ↓ 后续查询
                              O(1) 直接返回缓存硬指针
```

**双层存储**：
- `ItemDataMap` (TMap\<FName, TSoftObjectPtr\>)：软引用映射表，注册时写入，零内存开销
- `LoadedCache` (TMap\<FName, UItemDataBase*\>)：硬指针缓存，首次查询时懒加载写入

**扫描策略**（优先级排序）：
1. **AssetManager PrimaryAsset** 扫描（配置了 Type="Item" 的资产）
2. **AssetRegistry 兜底扫描** `/Game/Data/Items` 目录（当方案1结果为0时）

**查询接口**：
```cpp
UItemDataBase*      GetItemData(FName ItemID);         // 通用
UConsumableData*    GetConsumableData(FName ID);       // 自动 Cast
UWeaponData*        GetWeaponData(FName ID);           // 自动 Cast
void                RegisterItemData(UItemDataBase*);  // 手动注册
```

---

## 三、行为层详解

### 3.1 InventoryComponent（背包组件）

**核心组件**，挂载在 Character（玩家/敌人）上。负责所有背包操作。

#### 3.1.1 数据结构

```
InventoryComponent
├── Inventory[MaxSlots=20]    // TArray<FItemInstance>  背包主存储
├── QuickSlots[5]             // TArray<FItemInstance>  快捷栏
├── EquippedSlotIndex         // int32  当前装备槽位 (-1=未装备)
├── MaxWeight                 // float  最大承重
├── CurrentWeight             // float  当前重量 (实时计算)
├── CurrentItemCount          // int32  当前物品种类数
└── [委托们]                  // 事件广播
```

#### 3.1.2 CRUD 操作

| 方法 | 功能 | 关键逻辑 |
|------|------|----------|
| `AddItem(ItemID, Qty)` | 添加物品 | 先尝试堆叠到已有同ID槽位 → 再找空槽位新建 → 检查重量限制 |
| `RemoveItem(ItemID, Qty)` | 按ID移除 | 遍历所有槽位逐个扣除，归零则 Empty() |
| `RemoveItemAt(Index, Qty)` | 按槽位移除 | 扣除指定槽位数量；若卸掉装备武器则自动 Unequip |
| `UseItem(SlotIndex)` | 使用物品 | 权限校验(服务器) → 加载执行 ItemActionClasses → bConsumed 则 RemoveItemAt(1) |
| `DropItem(SlotIndex)` | 丢弃物品 | 检查 bCanDrop → 在拥有者前方 Spawn ItemClass → RemoveItemAt |
| `SwapItems(i1, i2)` | 交换两格 | 直接 Swap，触发 BroadcastInventoryUpdate |
| `SortItems()` | 整理背包 | 提取非空 → 按 ItemID LexicalSort → 重新填充 |

#### 3.1.3 装备系统

```
EquipItem(SlotIndex):
  校验槽位有效且非空 → GetItemData 校验 ItemType==Weapon
  → 若已有装备 → 先 Unequip (广播旧武器 false)
  → 设置 EquippedSlotIndex = SlotIndex
  → 广播 OnEquipmentChanged(NewItemID, true)

UnequipItem():
  EquippedSlotIndex = -1
  → 广播 OnEquipmentChanged(OldItemID, false)

GetEquippedWeaponData():
  return GetWeaponData(Inventory[EquippedSlotIndex].ItemID)
  // 内部走 Subsystem → Cast<UWeaponData>
```

#### 3.1.4 快捷栏系统

```
SelectQuickSlot(Index):  // 数字键 1-5 或滚轮
  切换选中高亮 → 广播 OnQuickSlotSelected
  ★ 不触发使用！使用由 UseSelectedQuickSlot() 或右键长按驱动

UseSelectedQuickSlot():  // 右键长按确认使用
  switch (ItemType):
    Weapon:
      在背包 FindItemSlot → EquipItem (找不到先 AddItem 回去再 Equip)
    Consumable:
      在背包 FindItemSlot → UseItem (同步快捷栏数量，用完 ClearQuickSlot)
      若背包没有该物品 → 直接扣减快捷栏数量 + 手动执行 ItemAction
```

#### 3.1.5 委托事件一览

| 委托名 | 类型 | 参数 | 触发时机 | 监听者 |
|--------|------|------|----------|--------|
| `OnInventoryUpdated` | Multicast (C++) | 无 | Add/Remove/Drop/Swap/Sort/Equip/Unequip 之后 | UW_InventoryUI::RefreshUI |
| `OnItemAdded` | Multicast (C++) | const FItemInstance& | AddItem 成功后 | UW_InventoryUI 更新统计数字 |
| `OnItemRemoved` | Multicast (C++) | const FItemInstance& | RemoveItem/RemoveItemAt 成功后 | UW_InventoryUI 更新统计+清除选中 |
| `OnItemUsed` | Multicast (C++) | const FItemInstance& | UseItem 消费成功后 | 未来扩展(成就/日志等) |
| `OnEquipmentChanged` | DynamicMulticast (BP+C++) | FName, bool | EquipItem / UnequipItem | 角色换装逻辑/UI更新 |
| `OnQuickSlotSelected` | DynamicMulticast | int32 SlotIndex | SelectQuickSlot | 快捷栏UI高亮切换 |
| `OnQuickSlotChanged` | DynamicMulticast | int32 SlotIndex | SetQuickSlot / ClearQuickSlot | 快捷栏UI刷新 |

### 3.2 APickupItem（场景拾取物）

```
APickupItem Actor
├── StaticMesh (RootComponent)     // 显示外观 + 物理
├── SphereCollision (附着StaticMesh) // 拾取检测范围 (半径50)
├── ItemID: FName                  // 对应哪个 DataAsset
├── ItemQuantity: int32            // 数量
└── bAutoPickup: bool              // 自动拾取 (Overlap即捡起)

流程:
  Player Overlap SphereCollision → OnOverlapBegin()
  → OtherActor 有 InventoryComponent?
    → Yes: InventoryComp->AddItem(ItemID, Quantity) 成功?
      → Yes: EventBus Publish("Item_Pickup") → OnPickup() → Destroy()
      → No: 日志警告(满/超重)
    → No: 忽略(不是有效拾取者)
```

**碰撞配置**：SphereCollision 设为 QueryOnly + 只响应 ECC_Pawn 通道 Overlap

### 3.3 ItemAction 系统（策略模式 + 模板方法）

```
使用物品时的执行链:

UseItem(SlotIndex):
  1. 读取 ItemData->ItemActionClasses (TArray<TSoftClassPtr<UItemAction>>)
  2. 遍历每个 SoftClassPtr:
     a. LoadSynchronous() 加载类
     b. NewObject<UItemAction>(this, ActionClass) 创建实例
     c. Action->InitializeFromItemData(ItemData)  // 从 DataAsset 读取参数初始化
     d. Action->Execute(Inventory, SlotIndex, Instigator)  // 执行效果，返回 bool
  3. 任一 Action 返回 true → bConsumed = true → RemoveItemAt(SlotIndex, 1)
```

**已实现的 Action 子类**：

| 类 | InitializeFromItemData | Execute 效果 | 返回值含义 |
|----|------------------------|-------------|-----------|
| `UItemAction_Heal` | Cast\<UConsumableData\> → 读取 HealthRestore | Instigator.AttributeComp.ApplyHeal(HealAmount) | 成功=true |
| `UItemAction_RestoreMana` | Cast\<UConsumableData\> → 读取 ManaRestore | Instigator.AttributeComp.RestoreMana(ManaAmount) | 成功=true |

**扩展方式**：新建 `UItemAction_xxx` 继承 `UItemAction`，覆写两个虚函数即可。

### 3.4 AnimNotify_UseItemComplete（动画完成通知）

```
Montage 时间轴:
  [Start] =======> [Notify Frame] ======> [End]
                         ↓
              AnimNotify_UseItemComplete::Notify()
                         ↓
              MeshComp.GetOwner() → Cast<AMyPlayerCharacter>
                         ↓
              PlayerChar->OnUseItemAnimFinished()
                         ↓
              执行实际扣减 + 效果（延迟到动画"喝下药水"那一帧才扣血）
```

**用途**：将视觉效果与数值效果解耦——播放喝药水动画，动画播到"吞咽"帧才真正回血。

---

## 四、表现层（UI）详解

### 4.1 背包主界面 UW_InventoryUI

```
┌─────────────────────────────────────────────┐
│  [Sort]                    [Close]          │
├─────────────────────────────────────────────┤
│  Weight: 12.5 / 100.0   Items: 8           │
├─────────────────────────────────────────────┤
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ │               │
│  │HP│ │MP│ │SW│ │  │ │  │ │               │  ← UniformGridPanel (5列)
│  │x5│ │x3│ │x1│ │  │ │  │ │               │     最多20个 UW_InventorySlot
│  └──┘ └──┘ └──┘ └──┘ └──┘ │               │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ │               │
│  │  │ │  │ │  │ │  │ │  │ │               │
│  └──┘ └──┘ └──┘ └──┘ └──┘ │               │
│  ...                                 (4行)  │
├─────────────────────────────────────────────┤
│  📷 [Icon]                                 │
│  名称: 生命药水                             │  ← 选中详情面板 (BindWidgetOptional)
│  描述: 恢复50点生命值                       │
│  [Use]  [Drop]                             │
└─────────────────────────────────────────────┘
```

**关键功能**：
- `InitializeSlots()`：创建 20 个 `UW_InventorySlot` 放入 UniformGridPanel（每行5格）
- `RefreshUI()`：遍历 Inventory 数据 → 调用每个 Slot 的 UpdateSlot()
- `UpdateSelectedItemInfo()`：显示选中槽位的 Icon/Name/Description，控制 Use/Drop 按钮 Enable 状态
- `LoadItemIconAsync()`：通过 StreamableManager 异步加载图标纹理（避免卡顿）
- 拖拽工厂方法 `CreateDragOperation()`：生成含视觉图标的 DragDropOperation

**委托绑定**：
- `SetInventoryComponent()` 时绑定 `OnInventoryUpdated` → RefreshUI
- `OnItemAdded` → UpdateInventoryInfo（只刷新重量/数量数字，不重建全部格子）
- `OnItemRemoved` → UpdateInventoryInfo + 如果选中的被删了则清除选中状态

### 4.2 单格背包槽位 UW_InventorySlot

```
每个 Slot Widget:
┌──────────────┐
│ Button_Slot  │  (HitTestInvisible，透传鼠标事件)
│ ┌──────────┐ │
│ │  Icon    │ │  Image_ItemIcon (HitTestInvisible)
│ │  x5      │ │  Text_ItemQuantity (数量>1时显示)
│ └──────────┘ │
└──────────────┘
```

**交互流程**（标准 Slate 拖拽）：

```
NativeOnMouseButtonDown(LMB):
  空槽位 → OnSlotSelected() 选中
  有物品 → DetectDragIfPressed() 让 Slate 开始检测拖拽阈值

NativeOnDragDetected:
  创建 UDragItemOperation (EDragSource::Inventory, SlotIndex, CachedItem, IconTexture)
  隐藏自身图标 (Collapsed)

NativeOnDrop(接收方):
  Cast<UDragItemOperation> → ParentUI.HandleInventorySlotDrop()
  → 背包内交换 / 快捷栏→背包 放入

NativeOnDragCancelled:
  恢复自身图标可见性 (HitTestInvisible)
```

### 4.3 快捷栏单格 UW_QuickSlot

```
每个 QuickSlot Widget:
┌────────────────┐
│ Border_Highlight│  (选中时 Visible，否则 Hidden)
│ ┌────────────┐ │
│ │   Icon     │ │  Image_ItemIcon
│ │   x3       │ │  Text_Count (数量>1时显示)
│ └────────────┘ │
└────────────────┘
```

**与 InventorySlot 的差异**：
- QuickSlot 的 `SetItemData()` 用**同步加载**图标（快捷栏只有5格，不需要异步）
- `NativeOnDrop` 中直接操作数据（不经过父 UI 中转），因为 QuickSlot 可能独立于背包 UI 存在
- 支持**从背包拖入**和**快捷栏内部交换**

### 4.4 拖拽系统 (UDragItemOperation)

```
拖拽数据载体:

UDragItemOperation : UDragDropOperation
├── SourceType:    EDragSource (Inventory / QuickSlot)  // 从哪来
├── SourceIndex:   int32                                // 源槽位索引
├── DraggedItem:   FItemInstance                        // 拖的是什么物品
├── ItemIconTexture: TSoftObjectPtr<UTexture2D>         // 用于生成拖拽视觉
└── DefaultDragVisual: UImage*                          // 跟随鼠标的图标Widget
```

**支持的全部拖拽场景**：

| 源 → 目标 | 处理函数 | 逻辑 |
|-----------|----------|------|
| 背包槽位 → 背包槽位 | HandleInventorySlotDrop | SwapItems(i1, i2) |
| 背包槽位 → 快捷栏 | HandleQuickSlotDrop (或 NativeOnDrop) | 目标空则移动+清源；目标非空则交换 |
| 快捷栏 → 背包槽位 | HandleInventorySlotDrop | 目标空则移动+清源；目标非空则交换 |
| 快捷栏 → 快捷栏 | HandleQuickSlotDrop (或 NativeOnDrop) | SetQuickSlot 双向交换 |

---

## 五、数据流全景

### 5.1 拾取物品流程

```
[场景] APickupItem (bAutoPickup=true)
  ↓ Player Capsule Overlap SphereCollision
[Actor] OnOverlapBegin()
  ↓ OtherActor.FindComponentByClass<UInventoryComponent>()
[Component] InventoryComp->AddItem("HP_Potion", 3)
  ↓ Subsystem.GetItemData("HP_Potion") → 读取 MaxStackSize/Weight
  ↓ 检查 CanCarryWeight → 堆叠已有 / 找空槽位新建
  ↓ UpdateWeight() + Broadcast OnInventoryUpdated + OnItemAdded
[GlobalEvent] EventBus.Publish("Item_Pickup", "HP_Potion")
  ↓ (其他系统可监听此事件，如成就系统)
[Actor] Pickup->Destroy()
```

### 5.2 使用物品流程（有动画版）

```
[Input] 玩家长按右键 (或快捷栏确认)
  ↓
[Character] MyPlayerCharacter::UseHeldItem()
  ↓ 检查 UseMontage 是否配置
  ├── 有 Montage → PlayAnimMontage(UseMontage) → 等待动画帧通知
  │                  ↓ 动画播到 Notify 帧
  │         [AnimNotify] AnimNotify_UseItemComplete::Notify()
  │                  ↓
  │         [Character] OnUseItemAnimFinished()
  │                  ↓
  └── 无 Montage → 立即执行 ↓
  ↓
[Component] InventoryComp->UseItem(SlotIndex) 或 UseSelectedQuickSlot()
  ↓ 服务器权限检查
  ↓ 遍历 ItemActionClasses:
  ├── NewObject<UItemAction_Heal>
  ├── HealAction->InitializeFromItemData(Data)  // 读取 HealthRestore=50
  ├── HealAction->Execute(Inv, Slot, this)
  │   ↓ this->AttributeComp->ApplyHeal(50.f)  // HP +50
  │   └── return true  (表示消费了)
  └── bConsumed = true
  ↓
[Component] RemoveItemAt(SlotIndex, 1)  // 数量-1，归零则清空
  ↓ Broadcast OnItemUsed + OnInventoryUpdated
[UI] UW_InventoryUI::OnInventoryUpdated() → RefreshUI()  // 自动刷新
```

### 5.3 丢弃物品流程

```
[UI] 点击 Drop 按钮
  ↓
[Component] InventoryComp->DropItem(SlotIndex)
  ↓ 检查 bCanDrop
  ↓ 读取 ItemData->ItemClass (TSoftClassPtr<AActor>)
  ↓ LoadSynchronous → World->SpawnActor<AActor>(SpawnClass, Owner前方100cm)
  ↓ if (Cast<APickupItem>) → Pickup->InitializePickup(ItemID, Qty)
  ↓ RemoveItemAt(SlotIndex, FullQty)  // 整格移除
```

### 5.4 装备武器流程

```
[UI/输入] 双击武器 or 快捷栏选中武器
  ↓
[Component] InventoryComp->EquipItem(SlotIndex)  或 UseSelectedQuickSlot()
  ↓ 校验 ItemType == Weapon
  ↓ if 已有装备 → UnequipItem() (广播旧武器 false)
  ↓ EquippedSlotIndex = SlotIndex
  ↓ OnEquipmentChanged.Broadcast(NewWeaponID, true)
  ↓
[Character] 监听 OnEquipmentChanged → 更新手部武器Mesh
  ↓ 读取 WeaponData->WeaponStaticMesh.LoadSynchronous()
  ↓ AttachToComponent(HandSocket)
```

---

## 六、扩展指南

### 6.1 添加新物品类型（如护甲）

1. 新建 `UEquipmentData.h` 继承 `UItemDataBase`
2. 添加护甲特有字段（防御力、部位枚举等）
3. 构造函数设 `ItemType = EItemType::Equipment`
4. 在 Subsystem 中添加 `GetEquipmentData()` 便捷方法（可选）
5. 创建 DataAsset 实例 `DA_Armor_IronChest`

### 6.2 添加新的 ItemAction（如 buff 药水）

1. 新建 `UItemAction_SpeedBoost.h/.cpp` 继承 `UItemAction`
2. 覆写 `InitializeFromItemData()` 读取 BuffDuration/BuffValue
3. 覆写 `Execute_Implementation()` 调用角色 MovementComponent 修改 WalkSpeed
4. 在 `UConsumableData` 的 `ItemActionClasses` 中填入新 Action 类

### 6.3 添加存档支持

`InventoryComponent::Inventory[]` 和 `QuickSlots[]` 目前是纯运行时数据。
需要持久化时建议：
- 将 `FItemInstance` 序列化为 `FString`（格式 `"ItemID:Quantity"`）
- 在 `USaveGame` 子类的 `SaveGame()/LoadGame()` 中读写
- 或接入 UE 的 `Archive` 系统进行二进制序列化

### 6.4 多人网络同步注意事项

当前 `InventoryComponent` 的 `UseItem()` 包含 `HasAuthority()` 检查但未实现 RPC：
- 需添加 `ServerUseItem()` RPC 供客户端请求
- `AddItem()`/`RemoveItem()` 等修改操作需加 Server RPC + Multicast RepNotify
- 或改用 `UReplicatedSubobject` + `OnRep_*` 模式

---

## 七、模块依赖关系图

```
                    ┌──────────────┐
                    │  MyPlayerChar │
                    │ (ACharacter) │
                    └──────┬───────┘
                           │ owns
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌─────────────┐ ┌──────────┐ ┌────────────┐
    │ Inventory    │ │Attribute │ │ Event Bus  │
    │ Component    │ │ Component│ │ (Global)   │
    └──────┬──────┘ └────┬─────┘ └──────┬─────┘
           │ uses           │ uses          │ publish
           ▼                ▼               ▼
    ┌──────────────┐  ┌──────────┐  ┌──────────────┐
    │ ItemData      │  │ Item     │  │ GlobalEvents │
    │ Subsystem     │  │ Actions  │  │ (.h常量)     │
    └──────┬───────┘  └────┬─────┘  └──────────────┘
           │ queries         │ creates
           ▼                ▼
    ┌─────────────────────────────────────┐
    │         Data Assets (.uasset)        │
    │  UItemDataBase / UConsumableData /   │
    │  UWeaponData (Content/Data/Items/)   │
    └─────────────────────────────────────┘
```

---

*文档版本：v1.0 | 最后更新：2026-05-11*
