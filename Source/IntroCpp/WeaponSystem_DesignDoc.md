# 武器装备系统 — 完整设计方案

## 一、系统全景图

### 1.1 现状问题

```
当前：MyPlayerCharacter 硬编码了所有攻击参数
├── FireballClass        → 固定一种投射物
├── AttackManaCost       → 固定耗蓝
├── AttackMontage        → 固定攻击动画
└── FireFromHand()       → 只能生成火球

换武器 → 改蓝图参数，无法运行时切换
```

### 1.2 核心思路：PrimaryDataAsset 继承体系 + Subsystem 集中管理

**数据层设计原则**：

```
第一层：UItemDataBase (UPrimaryDataAsset 基类)
    └── 所有物品共有的基础信息（图标/名字/重量/堆叠等）
    └── 背包UI只需要读基类接口

第二层：类型专属子类（按需继承 UItemDataBase）
    ├── UWeaponData     → 武器才有的战斗属性（只有攻击/装备时读）
    ├── UConsumableData → 消耗品才有的恢复属性（只有使用时读）
    └── 未来: UArmorData / UMaterialData ...

第三层：UItemDataSubsystem (UGameInstanceSubsystem)
    └── TMap<FName, TSoftObjectPtr<UItemDataBase>> 懒加载缓存
    └── 全局唯一入口，任何类通过 Subsystem 获取物品数据
    
角色只持有"当前武器数据指针"，具体发射什么、消耗多少、用什么动画，全由武器数据决定。
```

> **为什么选择 PrimaryDataAsset 而非 DataTable**：
> - 支持 **蓝图继承**：`DA_LegendarySword` 继承 `DA_IronSword` 再覆写属性
> - 支持 **资产引用**：字段可直接引用 Mesh/Montage/Sound 等资产
> - 编辑器 **资产管理器可搜索/筛选**
> - 每个物品是独立 `.uasset` 文件，版本控制友好
> - 这是 Epic 官方（Lyra / ActionRPG）和业界主流方案

### 1.3 数据访问层：UItemDataSubsystem（核心架构）

**原则：任何类都不直接持有/查询物品数据资产，统一通过 Subsystem 访问。**

```
错误做法（耦合）:
  MyPlayerCharacter ──→ 直接持有 DA_Weapon 引用
  UW_InventoryUI    ──→ 直接加载 DA_Item 引用
  Enemy_AI          ──→ 又要持一份引用
  
问题: 每个需要数据的类各自加载 → 分散、重复、无法集中缓存/异步加载

正确做法（Subsystem 集中管理 + TMap 懒加载）:
                    ┌──────────────────────────────────┐
                    │      UItemDataSubsystem           │  ← 全局单例
                    │    (UGameInstanceSubsystem)        │
                    ├──────────────────────────────────┤
                    │ TMap<ItemID, SoftPtr<UItemBase>> │
                    │   ("WP_Fire") → DA_FireStaff'    │
                    │   ("HP_Pot")  → DA_HPPotion'     │
                    │                                  │
                    │ GetItemData(ID)  → UItemBase*    │  ← 懒加载
                    │ GetWeaponData(ID)→ UWeaponData*  │  ← 按需 Cast
                    │ GetConsumableData(ID)            │
                    └──────────┬───────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     MyPlayerCharacter   UW_InventoryUI    InventoryComponent
     (只调接口)          (只调接口)        (只调接口)
     不关心DataAsset     不关心DataAsset   不关心DataAsset
```

**继承关系：**
```
USubsystem (引擎基类)
  └── UGameInstanceSubsystem (随 GameInstance 自动创建/销毁，全局唯一)
        └── UItemDataSubsystem (新建的数据管理子系统)
```

**与现有 MyEventBusGameInstance 的关系：**
```
MyEventBusGameInstance (UGameInstance)     ← 不动！继续做事件总线
│
├── [自身逻辑] 事件订阅/发布 (Subscribe/Publish)
│
├── [内置子模块] UItemDataSubsystem         ← 新增！数据查询管理
│                 GetItemData() / GetWeaponData()
│
└── [未来] 其他 Subsystem...               ← 随便加，互不干扰

关键规则:
- UGameInstance          → 整个游戏只有 1 个 (你的 MyEventBusGameInstance)
- UGameInstanceSubsystem → 可以挂 N 个，全部自动跟随 GameInstance 创建/销毁
- 两者完全不冲突，Subsystem 是 GameInstance 的子模块
```

**UItemDataSubsystem 接口定义（方案三：TMap + 懒加载）：**
```cpp
// 文件: ItemDataSubsystem.h
#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UItemDataBase.h"  // PrimaryDataAsset 基类
#include "ItemDataSubsystem.generated.h"

UCLASS()
class INTROCPP_API UItemDataSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    // ========== 生命周期 ==========
    virtual void Initialize() override;    // 扫描或注册物品数据到映射表
    virtual void Deinitialize() override;  // 清理缓存

    // ========== 公开查询接口（懒加载） ==========
    
    /// 按 ItemID 获取物品基础数据（懒加载 + 缓存）
    UFUNCTION(BlueprintCallable, Category = "Item Data")
    UItemDataBase* GetItemData(FName ItemID);

    /// 获取武器数据（内部调用 GetItemData 后 Cast）
    UFUNCTION(BlueprintCallable, Category = "Item Data")
    UWeaponData* GetWeaponData(FName WeaponID);

    /// 获取消耗品数据（内部调用 GetItemData 后 Cast）
    UFUNCTION(BlueprintCallable, Category = "Item Data")
    UConsumableData* GetConsumableData(FName ConsumableID);

    /// 手册注册一个物品数据资产（用于编辑器挂载模式）
    UFUNCTION(BlueprintCallable, Category = "Item Data")
    void RegisterItemData(UItemDataBase* ItemData);

    /// 获取所有已注册的物品ID列表
    UFUNCTION(BlueprintCallable, Category = "Item Data")
    TArray<FName> GetAllRegisteredItemIDs() const;

private:
    // 核心：ItemID → 软引用映射（支持懒加载）
    UPROPERTY()
    TMap<FName, TSoftObjectPtr<UItemDataBase>> ItemDataMap;

    // 已加载的硬指针缓存（加速重复访问）
    UPROPERTY()
    TMap<FName, UItemDataBase*> LoadedCache;
};
```

```cpp
// 文件: ItemDataSubsystem.cpp
#include "ItemDataSubsystem.h"
#include "UWeaponData.h"
#include "UConsumableData.h"

void UItemDataSubsystem::Initialize()
{
    Super::Initialize();

    // 方式A（推荐）：如果使用 AssetRegistry 扫描，在此处扫描指定目录
    // 方式B：如果使用编辑器手动挂载，RegisterItemData 由外部/配置调用
    
    UE_LOG(LogTemp, Log, TEXT("[UItemDataSubsystem] Initialized. Registered items: %d"), 
        ItemDataMap.Num());
}

void UItemDataSubsystem::Deinitialize()
{
    Super::Deinitialize();
    ItemDataMap.Empty();
    LoadedCache.Empty();
}

UItemDataBase* UItemDataSubsystem::GetItemData(FName ItemID)
{
    // 1. 先查硬指针缓存（已加载过，直接返回）
    if (UItemBase** Cached = LoadedCache.Find(ItemID))
    {
        return *Cached;
    }

    // 2. 查软引用映射（未加载，执行懒加载）
    if (TSoftObjectPtr<UItemDataBase>* SoftPtr = ItemDataMap.Find(ItemID))
    {
        if (!SoftPtr->IsNull())
        {
            UItemBase* Loaded = SoftPtr->LoadSynchronous();
            if (Loaded)
            {
                LoadedCache.Add(ItemID, Loaded);
                return Loaded;
            }
        }
    }

    UE_LOG(LogTemp, Warning, TEXT("[UItemDataSubsystem] ItemData not found: %s"), *ItemID.ToString());
    return nullptr;
}

UWeaponData* UItemDataSubsystem::GetWeaponData(FName WeaponID)
{
    if (UItemDataBase* Base = GetItemData(WeaponID))
    {
        return Cast<UWeaponData>(Base);
    }
    return nullptr;
}

UConsumableData* UItemDataSubsystem::GetConsumableData(FName ConsumableID)
{
    if (UItemDataBase* Base = GetItemData(ConsumableID))
    {
        return Cast<UConsumableData>(Base);
    }
    return nullptr;
}

void UItemDataSubsystem::RegisterItemData(UItemDataBase* ItemData)
{
    if (!ItemData) return;
    
    ItemDataMap.Add(ItemData->ItemID, ItemData);
    UE_LOG(LogTemp, Log, TEXT("[UItemDataSubsystem] Registered item: %s -> %s"),
        *ItemData->ItemID.ToString(), *ItemData->GetName());
}
```

### 数据注册方式（二选一，可组合）

#### 方式A：AssetRegistry 扫描目录（全自动）

适用于物品数量多、需要 DLC 动态添加的场景：

```
Initialize() 时：
  1. AssetRegistry.GetAssetsByClass(UItemDataBase::StaticClass()->GetClassPathName())
  2. 遍历结果，对每个 AssetData.GetAsset() 调用 RegisterItemData()
  3. 新增的 .uasset 放入指定文件夹即自动被识别
```

#### 方式B：编辑器 Project Settings 手动挂载（可控）

适用于物品数量可控、需要精确控制哪些物品生效的场景：

```
步骤1: Edit → Project Settings → 搜索 "ItemData"

步骤2: 在 Subsystem 配置面板中看到:
┌─ Project Settings ────────────────────────────────┐
│ Game → Item Data Subsystem                        │
│                                                    │
│ Item Data Assets     [ + 添加 DA_xxx 条目 ]        │
│   [0] DA_FireStaff                                 │
│   [1] DA_IceStaff                                  │
│   [2] DA_HPPotion                                   │
│   [3] ...                                          │
│                                    [Reset to Default] │
└────────────────────────────────────────────────────┘

步骤3: 从 Content Browser 拖入对应的 DataAsset 资产
```

> **推荐**：开发阶段用方式B（直观可控），上线后可切方式A（自动化）。代码层面两种方式共存。

**全局调用方式（任何 UObject 子类中都可以这样写）：**
```cpp
// 获取 Subsystem 的标准写法:
auto* DataSys = GetGameInstance()->GetSubsystem<UItemDataSubsystem>();

// 查询示例（自动懒加载 + 缓存）:
UWeaponData* Weapon = DataSys->GetWeaponData(TEXT("WP_FireStaff"));
UItemDataBase* Item  = DataSys->GetItemData(TEXT("HP_Pot"));
```

**为什么 PrimaryDataAsset + Subsystem 比直挂 DataTable 好：**

| 维度 | 角色/UI 直持 DataTable | PrimaryDataAsset + Subsystem |
|------|---------------------|-------------------|
| 单一职责 | 角色既管战斗又管数据查询 | 角色只管战斗逻辑 |
| 复用性 | UI/AI/存档 各自重复查表 | 统一接口，任何地方调用 |
| 可测试性 | Mock 困难，依赖具体表格 | Mock Subsystem 即可测角色 |
| 缓存策略 | 分散在各处难统一 | 一处 TMap 懒加载全局生效 |
| 继承扩展 | 结构体无法继承 | 子类覆写属性，蓝图也可继承 |
| 资产引用 | TSoftObjectPtr 有限支持 | 原生支持硬引用/软引用 |
| 异步加载 | 改动点多 | 只改 Subsystem 内部 |

---

## 二、数据架构设计（PrimaryDataAsset 继承体系）

### 2.1 UItemDataBase — 物品数据基类（UPrimaryDataAsset）

**所有物品数据的根基类**，背包UI、拾取、丢弃等通用逻辑只依赖此基类接口。每个具体物品在编辑器中创建为独立 `.uasset` 资产。

```cpp
// 文件: UItemDataBase.h (新建)
#pragma once
#include "CoreMinimal.h"
#include "Engine/PrimaryDataAsset.h"
#include "ItemData.h"
#include "UItemDataBase.generated.h"

/**
 * 物品数据基类 (PrimaryDataAsset)
 * 所有物品（武器/消耗品/材料/装备）都继承此类。
 * 每个物品在 Content Browser 中是一个独立的 .uasset 文件。
 * 子类可在蓝图中创建，覆写或扩展属性。
 */
UCLASS(Abstract, Blueprintable)
class INTROCPP_API UItemDataBase : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // 唯一标识（对应 FItemInstance.ItemID）
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item")
    FName ItemID;

    // 基础显示信息
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Display")
    FText ItemName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Display", meta = (MultiLine = true))
    FText ItemDescription;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Display")
    EItemType ItemType = EItemType::Material;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Display")
    EItemRarity ItemRarity = EItemRarity::Common;

    // 外观资源（原生支持资产引用！相比 DataTable 的核心优势）
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
    TSoftObjectPtr<UTexture2D> ItemIcon;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
    TSoftClassPtr<AActor> ItemClass;

    // 物品动作列表（使用时按顺序执行）
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Actions")
    TArray<TSoftClassPtr<UItemAction>> ItemActionClasses;

    // 基本属性
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Properties")
    int32 MaxStackSize = 99;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Properties")
    float Weight = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Properties")
    int32 Value = 0;

    // 标志位
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flags")
    bool bCanSell = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flags")
    bool bCanUse = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flags")
    bool bCanDrop = true;
};
```

**关键点：这个基类不包含任何战斗/恢复相关字段** -- 那些由子类负责。

---

### 2.2 UWeaponData — 武器数据子类

继承 `UItemDataBase`，添加武器专属的战斗属性。只有装备或攻击时才需要访问这些字段。

```cpp
// 文件: UWeaponData.h (新建)
#pragma once
#include "CoreMinimal.h"
#include "UItemDataBase.h"
#include "EWeaponTypes.h"
#include "UWeaponData.generated.h"

/**
 * 武器数据 (PrimaryDataAsset 子类)
 * 每把武器是一个独立的 .uasset，支持蓝图继承。
 */
UCLASS(Blueprintable)
class INTROCPP_API UWeaponData : public UItemDataBase
{
    GENERATED_BODY()

public:
    // 武器战斗属性
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    TSoftClassPtr<AActor> WeaponProjectileClass;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    EWeaponAnimType WeaponAnimType = EWeaponAnimType::None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    bool bIsRangedWeapon = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float WeaponManaCost = 0.f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    int32 WeaponDamageOverride = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    FName WeaponFireSocketName = TEXT("hand_r");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float WeaponAttackCooldown = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    UAnimMontage* OverrideAttackMontage = nullptr;
};
```

---

### 2.3 UConsumableData — 消耗品数据子类

继承 `UItemDataBase`，添加消耗品专属的恢复属性。只有使用物品时才需要访问这些字段。

```cpp
// 文件: UConsumableData.h (新建)
#pragma once
#include "CoreMinimal.h"
#include "UItemDataBase.h"
#include "EWeaponTypes.h"
#include "UConsumableData.generated.h"

/**
 * 消耗品数据 (PrimaryDataAsset 子类)
 */
UCLASS(Blueprintable)
class INTROCPP_API UConsumableData : public UItemDataBase
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Effect")
    int32 HealthRestore = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Effect")
    int32 ManaRestore = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Effect")
    EBuffType BuffType = EBuffType::None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Effect", meta = (EditCondition = "BuffType != EBuffType::None"))
    float BuffDuration = 0.f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Effect", meta = (EditCondition = "BuffType != EBuffType::None"))
    float BuffValue = 0.f;
};
```

> **注意**：原来 `FItemData` 中的 `HealthRestore` 和 `ManaRestore` 字段已迁移到 `UConsumableData` 子类中。

---

### 2.4 类继承关系图

```
UPrimaryDataAsset (UE 引擎基类)
  +-- UItemDataBase (通用物品基类)        <-- Subsystem 存的是这个指针*
       |
       |-- DA_FireStaff   (UWeaponData)     ItemID="WP_Fire"
       |     Projectile=BP_Fireball, Anim=Cast_1H, ManaCost=10
       |
       |-- DA_IceSword    (UWeaponData)     ItemID="WP_Ice"
       |     Projectile=BP_IceSpear, Anim=Cast_1H, ManaCost=15
       |
       |-- DA_IronSword   (UWeaponData)     ItemID="WP_Sword"
       |     bIsRanged=false, Anim=Slash_1H, DamageOverride=40
       |
       |-- DA_LegendaryBlade (UWeaponData, 蓝图继承自 DA_IronSword!)
       |     DamageOverride=80 (+OverrideMontage), 其余继承父类
       |
       |-- DA_HPPotion    (UConsumableData)  ItemID="HP_Pot"
       |     HealthRestore=50, MaxStack=10
       |
       |-- DA_MPPotion    (UConsumableData)  ItemID="MP_Pot"
       |     ManaRestore=30
       |
       +-- DA_Wood        (UItemDataBase)    ItemID="Wood"
             ItemType=Material, MaxStack=99

* Subsystem 的 TMap<FName, TSoftObjectPtr<UItemDataBase>> 存储所有子类的软引用
  查询时 GetItemData() 返回基类指针，需要子类数据时 Cast 即可
```

**查询时机（按需加载）：**
- `UItemDataBase*`  --> 背包UI显示/拾取/丢弃（高频，只读基类字段）
- `UWeaponData*`  --> 装备武器/执行攻击（低频，Get 后 Cast）
- `UConsumableData*` --> 使用药水（低频，Get 后 Cast）

### 2.5 与原 FItemData 的关系

原有的 `FItemData` 结构体（`ItemData.h`）保留用于 **运行时实例数据传递**，但 **不再作为主要的数据存储方式**。

```
原有用途（DataTable 行）              新用途（PrimaryDataAsset）
+-----------------------------+     +-----------------------------+
| FItemData (结构体)            |     | UItemDataBase (资产对象)      |
| - DataTable 行             | --> | - 每个 .uasset 一个实例      |
| - 无继承能力                 |     | - 支持蓝图/C++ 继承          |
| - 无法直接引用资产            |     | - 字段可硬引用 Mesh/Sound    |
+-----------------------------+     +-----------------------------+

FItemInstance (运行时槽位数据) ---不变--- 仍通过 ItemID 关联到 UItemDataBase
```

### 2.6 编辑器中的资产创建流程

```
步骤1: Content Browser 右键 --> Miscellaneous --> Data Asset

步骤2: 选择父类:
      +- UItemDataBase    --> 通用物品（材料、杂物等）
      +- UWeaponData      --> 武器
      +- UConsumableData  --> 消耗品

步骤3: 命名资产（建议格式: DA_<类型>_<名称>）
      例: DA_Weapon_FireStaff, DA_Consum_HP_Potion

步骤4: 在 Details 面板配置字段:
      +-- Details ---------------------------------------+
      | Item ID          [ WP_FireStaff                  ] |
      | Item Name         [ 火球法杖                       ] |
      | Item Type         [ Weapon v                      ] |
      | Item Icon         [ Tex_FireStaff        ]        | <- 直接拖入 Texture!
      | Max Stack Size    [ 1                             ] |
      | ... (基类字段)                                    |
      | --- Weapon Only (UWeaponData 特有) ----            |
      | Projectile Class  [ BP_Fireball          ]        | <- 直接拖入蓝图类!
      | Anim Type         [ Cast_1H v                     ] |
      | Mana Cost         [ 10                            ] |
      | Is Ranged         [ [v]                           ] |
      | Damage Override   [ 25                            ] |
      +--------------------------------------------------+

步骤5: 保存 (Ctrl+S)

完成! 这个 .uasset 被 UItemDataSubsystem 识别和使用
```

---

## 三、动画处理方案

### 3.1 核心原则：按"攻击模式"而非"武器种类"分动画

```
错误思路：
  火球杖 → M_Attack_Fireball_01
  冰霜杖 → M_Attack_IceSpear_01
  雷电杖 → M_Attack_Lightning_01
  ...每把武器一个动画 → 爆表

正确思路：按"动作模式"归类
  远程施法(单手)   → M_Attack_Cast_1H    ← 所有单手法杖共用
  远程施法(双手)   → M_Attack_Cast_2H    ← 双手仗共用
  单手挥砍         → M_Attack_Slash_1H    ← 剑/斧/匕首共用  
  双手挥砍         → M_Attack_Slash_2H    ← 大剑/长枪共用
  刺击             → M_Attack_Thrust      ← 枪/矛共用
  射箭             → M_Attack_Shoot       ← 弓/弩共用
```

### 3.2 EWeaponAnimType 枚举定义

```cpp
// 文件: EWeaponTypes.h (新建)
UENUM(BlueprintType)
enum class EWeaponAnimType : uint8
{
    Cast_1H,        // 单手施法
    Cast_2H,        // 双手施法
    Slash_1H,       // 单手挥砍
    Slash_2H,       // 双手挥砍
    Thrust,         // 刺击
    Shoot,          // 射箭/射击
    None            // 无攻击动作
};

// 同时在此文件中定义 EBuffType（供 UConsumableData 使用）
UENUM(BlueprintType)
enum class EBuffType : uint8
{
    None,
    Regeneration,
    Speed,
    Defense
};
```

### 3.3 两层动画设计

#### 第1层：EWeaponAnimType 枚举 -- 决定"用什么动画"

每个武器的 `UWeaponData` 中存一个枚举值，如 `Cast_1H`。

#### 第2层：角色持有一个 TMap\<EWeaponAnimType, UAnimMontage*\>

```
MyPlayerCharacter 上:
  AttackMontageMap (TMap)
  |-- [Cast_1H]  --> M_Attack_Cast_1H
  |-- [Slash_1H] --> M_Attack_Slash_1H
  |-- [Shoot]    --> M_Attack_Shoot
  +-- ...

不在武器数据上存 Montage 指针！
武器数据只存一个 EWeaponAnimType = Cast_1H
```

**为什么这样设计：**

| | Montage 存武器数据 | Montage 存角色 + 枚举选 |
|---|---|---|
| 10种同类型武器 | 10个重复引用 | 1个 Montage，10个枚举值 |
| 换皮肤/换模型 | 不影响 | 不影响 |
| 新增武器 | 必须拖 Montage | 只填枚举，零配置 |
| 动画升级换一套 | 改 N 个物品行 | 改角色上 1 个 Map |

### 3.4 运行时流程

```
玩家按下攻击键
    ↓
Attack()
    ↓
读取 CurrentWeaponData->WeaponAnimType  <-- 比如 Cast_1H
    ↓
从 AttackMontageMap[Cast_1H] 取出 Montage
    ↓
PlayAnimMontage(Montage)
    ↓
AnimNotify 触发 FireFromHand()
    ↓
读取 CurrentWeaponData->WeaponProjectileClass  <-- BP_Fireball / BP_IceSpear
SpawnActor(...)
```

**同一套施法动画可以配合不同投射物**：
- 火球杖：Cast_1H 动画 + BP_Fireball 投射物
- 冰霜杖：Cast_1H 动画 + BP_IceSpear 投射物
- 完全不需要新动画

### 3.5 近战 vs 远程的区别

```伪代码
void Attack() {
    Montage = AttackMontageMap[CurrentWeaponData->WeaponAnimType];
    PlayAnimMontage(Montage);
    
    if (CurrentWeaponData->bIsRangedWeapon) {
        // AnimNotify 会触发 FireFromHand() --> 生成投射物
        // 不需要额外操作，Notify 自然触发
    } else {
        // 近战：AnimNotify 触发 MeleeHitCheck() 
        // --> 在武器碰撞盒范围内做 Sweep 检测伤害
    }
}
```

### 3.6 专属蒙太奇（可选覆盖）

```cpp
// 武器数据(UWeaponData)上的可选字段:
UPROPERTY(EditAnywhere)
UAnimMontage* OverrideAttackMontage;   // 空 = 用枚举走 Map

// Attack() 中选择优先级:
UAnimMontage* MontageToPlay = CurrentWeaponData->OverrideAttackMontage
    ? CurrentWeaponData->OverrideAttackMontage
    : AttackMontageMap[CurrentWeaponData->WeaponAnimType];
```

99% 的普通武器不填这个字段，自动走共享动画池；只有少数特殊武器才覆盖。

---

## 四、投射物复用关系图

```
                    AAFireballProjectile (C++ 基类)
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    BP_Fireball      BP_IceSpear      BP_MagicArrow
    (蓝图子类)       (蓝图子类)       (蓝图子类)
    
UWeaponData 配置 (DA_xxx 资产中):
  DA_FireStaff  --> ProjectileClass = BP_Fireball     (火球)
  DA_IceStaff   --> ProjectileClass = BP_IceSpear     (冰枪)
  DA_ArcaneWand --> ProjectileClass = BP_Fireball     (共用！只改颜色/大小)
  DA_Bow        --> ProjectileClass = BP_MagicArrow   (魔法箭)
```

## 五、动画复用关系图

```
AttackMontageMap (角色上配置一次):
+-------------+---------------------+
| Cast_1H     | M_Attack_Cast_1H    | <-- 所有单手法杖共用
| Slash_1H    | M_Attack_Slash_1H   | <-- 所有单手近战共用
| Shoot       | M_Attack_Shoot      | <-- 弓弩共用
| ...         | ...                 |
+-------------+---------------------+

UWeaponData 中只需填一个枚举值:
  DA_FireStaff  --> AnimType = Cast_1H    --> 自动映射到 M_Attack_Cast_1H
  DA_IceStaff   --> AnimType = Cast_1H    --> 同一动画！不同投射物
  DA_Sword      --> AnimType = Slash_1H   --> M_Attack_Slash_1H
  DA_Legendary  --> AnimType = Slash_1H   
                 --> OverrideMontage = M_Legendary_Slash  (专属!)
```

---

## 六、完整生命周期流程

### 阶段A：拾取物品

```
世界中的 PickupItem(WP_Fire) --> 玩家碰撞 
--> InventoryComponent.AddItem("WP_Fire", 1)
--> 通过 Subsystem 获取 UItemDataBase 基础信息（图标/名字/重量）--> 进入背包 Slot[N]
--> 此时不需要 Cast 到 UWeaponData!
```

### 阶段B：显示背包UI

```
打开背包 UI
--> 遍历 InventoryComponent 的所有槽位
--> 对每个槽位通过 Subsystem.GetItemData(ItemID) 获取 UItemDataBase*
--> 显示: 图标、名称、数量、重量（只读基类字段）
--> 不需要 Cast 到 UWeaponData / UConsumableData（UI不需要战斗数据）
```

### 阶段C：装备武器（3种触发方式）

方式1：背包UI中右键武器格子 --> 按钮"装备"
方式2：双击武器格子
方式3：快捷键(如数字键1)

EquipItem 内部逻辑：
1. 校验槽位有效且 ItemType == Weapon
2. 如果已有装备 --> 先 Unequip（标记旧武器槽位为普通状态）
3. 设置 EquippedSlotIndex = SlotIndex
4. **首次**通过 Subsystem.GetWeaponData() 获取 UWeaponData*（内部懒加载 + 缓存）
5. 将 UWeaponData* 传给 Character->EquipWeapon(WeaponData)
6. 广播 OnEquipmentChanged("WP_Fire", true)
7. UI 刷新（武器格子高亮 + 状态栏显示武器信息）

### 阶段D：角色接收装备数据

Character->EquipWeapon(UWeaponData*) 内部：
1. 缓存 CurrentWeaponData = WeaponData（指针引用，不拷贝）
2. 如果远程武器 --> 预加载 SoftClassPtr（ProjectileClass.LoadSynchronous）
3. 更新 StatusBar UI 显示武器名称和属性
4. 打印日志确认装备成功

### 阶段E：使用消耗品

玩家点击 Use（对药水）：
1. 校验槽位有效且 ItemType == Consumable
2. **首次**通过 Subsystem.GetConsumableData() 获取 UConsumableData*
3. 执行恢复效果（HealthRestore / ManaRestore）
4. 如果有 Buff --> 应用 Buff
5. 扣除数量

### 阶段F：攻击

玩家按 Attack 键 --> AttackStarted() --> Attack()

Attack() 重写：
1. if (!CurrentWeaponData) return;  // 未装备武器，不可攻击
2. if (bIsAttacking) return;         // 冷却中
3. 确定使用的 Montage：
   - CurrentWeaponData->OverrideAttackMontage 非空 --> 用它
   - 否则 --> AttackMontageMap[CurrentWeaponData->WeaponAnimType]
4. PlayAnimMontage(Montage)
5. bIsAttacking = true（冷却读取 WeaponAttackCooldown）
6. 动画播放完毕后重置 bIsAttacking

### 阶段G：发射/命中

AnimNotify_Fireball 触发 --> FireFromHand()

FireFromHand() 重写：
1. 从 CurrentWeaponData 读取全部参数（不再用成员变量）
2. 检查 MP >= CurrentWeaponData->WeaponManaCost
3. 扣 MP
4. 根据 bIsRangedWeapon 分支：
   - 远程：SpawnActor\<AActor\>(ProjectileClass, ...)（多态基类指针）
   - 近战：MeleeHitCheck()（Sweep检测+伤害计算）
5. 如果有 DamageOverride --> 覆盖基础伤害

### 阶段H：卸装武器

触发：装备新武器时自动卸旧 / UI按钮"卸装"

UnequipItem() --> Character->UnequipWeapon() --> 清空缓存 --> UI刷新

---

## 七、UI 设计

### 7.1 背包内嵌武器格

```
+------------------------------------------+
|  INVENTORY                    [Sort][X]  |
+------------------------------------------+
| +------+ +------+ +------+ +------+    |
| ?? Equip| |? x5  | | ?    | |      |    |
| *****  | |      | |      | |      |    |  <-- 已装备金色边框
+------+ +------+ +------+ +------+    |
| +------+ +------+ +------+ +------+    |
| |      | |      | |      | |      |    |
+------+ +------+ +------+ +------+    |
+------------------------------------------+
| Icon: [??]   Name: Fire Staff             |
| Desc: A basic fire magic staff            |
|           [Use]  [Equip]  [Drop]          |
+------------------------------------------+
| Weight: 12/100    Items: 6/20             |
+------------------------------------------+
```

**UI 变化点：**
- 武器类型选中时 Button 文字变为 **Equip/Unequip**
- 消耗品选中时 Button 保持 **Use**
- 已装备武器格显示金色高亮 + 角标
- 同一时间只能一把装备

### 7.2 状态栏武器信息区

```
+----------------------------------------+
| HP: ********??  80/100                 |
| MP: ******????  60/100                 |
| ------------------------------------- |
| ?? Fire Staff                           |  <-- 装备后显示
|    ATK: 25  MP: 10/cast  Ranged        |  <-- 从 UWeaponData 读取
|                                         |
| (未装备时灰色/隐藏)                      |
+----------------------------------------+
```

---

## 八、InventoryComponent 数据查询接口

> **核心变更：InventoryComponent 不再持有 DataTable/DataAsset 引用，所有数据查询通过 UItemDataSubsystem 完成。**

### 8.1 数据获取方式

```cpp
// 旧方式（不再使用）:
// UDataTable* ItemDataTable;          // 不再挂
// ItemDataTable->FindRow<FItemData>(...); // 不再直接查表

// 新方式 -- 通过 Subsystem 查询:
#include "ItemDataSubsystem.h"

// InventoryComponent 的任意方法内部:
auto* DataSys = GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
UItemDataBase* BaseData = DataSys->GetItemData(ItemID);
UWeaponData* WeaponData = DataSys->GetWeaponData(WeaponID);
UConsumableData* ConsumableData = DataSys->GetConsumableData(ConsumableID);
```

**InventoryComponent 上不需要新增任何 DataAsset/DataTable 属性引用。**

### 8.2 新增查询方法（内部委托给 Subsystem）

```cpp
// 获取物品基础数据（用于 UI 显示、重量检查等）
bool GetItemData(FName ItemID, UItemDataBase*& OutData) const
{
    auto* DataSys = GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
    UItemDataBase* Found = DataSys ? DataSys->GetItemData(ItemID) : nullptr;
    if (Found) { OutData = Found; return true; }
    return false;
}

// 获取武器数据（仅在装备/攻击时调用，内部 Cast）
bool GetWeaponData(FName WeaponID, UWeaponData*& OutData) const
{
    auto* DataSys = GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
    UWeaponData* Found = DataSys ? DataSys->GetWeaponData(WeaponID) : nullptr;
    if (Found) { OutData = Found; return true; }
    return false;
}

// 获取消耗品数据（仅在使用时调用，内部 Cast）
bool GetConsumableData(FName ConsumableID, UConsumableData*& OutData) const
{
    auto* DataSys = GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
    UConsumableData* Found = DataSys ? DataSys->GetConsumableData(ConsumableID) : nullptr;
    if (Found) { OutData = Found; return true; }
    return false;
}
```

> **注意**: 返回类型从原来的 `FWeaponData&`（值拷贝结构体）改为 `UWeaponData*&`（指针引用 PrimaryDataAsset）。这是核心差异 -- 现在拿到的是真正的资产对象指针，可以直接访问其所有字段和方法。

### 8.3 装备管理方法

```cpp
// 当前装备所在槽位 (-1 = 未装备)
int32 EquippedSlotIndex = -1;

// 装备变更委托
DECLARE_MULTICAST_DELEGATE_TwoParams(FOnEquipmentChanged, FName /*ItemID*/, bool /*bEquipped*/);
FOnEquipmentChanged OnEquipmentChanged;

// 装备指定槽位的物品（必须是Weapon类型）
bool EquipItem(int32 SlotIndex);

// 卸下当前装备
void UnequipItem();

// 获取当前装备的武器数据（指针引用，无需拷贝）
UWeaponData* GetEquippedWeaponData() const;

// 便捷查询
bool IsWeaponEquipped() const;
FName GetEquippedItemID() const;
```

### 8.4 使用时机总结

| 操作 | 需要获取什么 | 说明 |
|------|------------|------|
| 拾取物品 | UItemDataBase* | 检查重量/堆叠即可（只读基类字段） |
| 背包UI显示 | UItemDataBase* | 只需图标/名字/数量 |
| 物品详情面板 | UItemDataBase* + 按需Cast | 选中时展示完整信息 |
| 装备武器 | UWeaponData* | 加载战斗属性（Get 后缓存） |
| 攻击 | 无需查 Subsystem | 直接读 CurrentWeaponData 缓存 |
| 使用药水 | UConsumableData* | 加载恢复属性（Get 后执行） |
| 丢弃物品 | UItemDataBase* | 检查 bCanDrop 标志 |

---

## 九、MyPlayerCharacter 改造

### 9.1 删除的硬编码字段

以下字段全部移除（由 UWeaponData 替代）：

| 原字段 | 替代来源 |
|--------|---------|
| `FireballClass` (TSubclassOf) | CurrentWeaponData->WeaponProjectileClass |
| `AttackManaCost` (float) | CurrentWeaponData->WeaponManaCost |
| `AttackMontage` (UAnimMontage*) | AttackMontageMap[AnimType] 或 OverrideMontage |
| `HandSocketName` (FName) | CurrentWeaponData->WeaponFireSocketName |

### 9.2 新增成员

```cpp
// 当前缓存的武器数据（由 InventoryComponent.Equip 时传入）
UWeaponData* CurrentWeaponData = nullptr;

// 当前装备的 ItemID（用于日志/调试等场景需要重新查 Subsystem 时）
FName CurrentWeaponID = NAME_None;

// 攻击动画共享池（蓝图中配置一次）
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attack")
TMap<EWeaponAnimType, UAnimMontage*> AttackMontageMap;
```

### 9.3 核心方法改造

#### EquipWeapon(UWeaponData* InData)

```
1. CurrentWeaponData = InData (保存指针，不拷贝!)
2. 如果 bIsRangedWeapon 且 ProjectileClass 是软引用 --> 预加载
3. 更新 StatusBar UI (武器名称/属性)
4. 日志确认
```

#### UnequipWeapon()

```
1. CurrentWeaponData = nullptr
2. 清空 StatusBar 武器区域
3. 日志确认
```

#### Attack() 重写

```
1. if (!CurrentWeaponData) { Warn + return; }
2. if (bIsAttacking) return;
3. 确定 Montage:
     OverrideAttackMontage ?用它 : AttackMontageMap[WeaponAnimType]
4. PlayAnimMontage(Montage)
5. bIsAttacking = true
6. 冷却计时 = WeaponAttackCooldown
7. 动画结束回调重置 bIsAttacking
```

#### FireFromHand() 重写

```
1. 全部参数从 CurrentWeaponData 读取（不查 Subsystem，直接读缓存）
2. MP检查: AttributeComp->GetCurrentMana() >= WeaponManaCost
3. 扣MP: AttributeComp->UseMana(WeaponManaCost)
4. 获取位置: GetMesh()->GetSocketLocation(WeaponFireSocketName)
5. 分支:
     if (bIsRangedWeapon) {
         // ProjectileClass 是 TSoftClassPtr，需要先加载
         auto ProjClass = CurrentWeaponData->WeaponProjectileClass.LoadSynchronous();
         SpawnActor<AActor>(ProjClass, ...)  // 多态基类指针!
     } else {
         MeleeHitCheck()  // 近战预留
     }
6. DamageOverride != 0 --> 覆盖投射物伤害
```

> **注意**: FireFromHand() 不调用 Subsystem！它只读 CurrentWeaponData 缓存。
> Subsystem 的查询发生在 EquipItem / UseItem 时，结果缓存后供攻击/发射直接使用。

---

## 十、近战系统的预留接口

虽然当前重点是远程武器，但 `bIsRangedWeapon` 分支应同步埋入：

```伪代码
// FireFromHand() 中:
if (CurrentWeaponData->bIsRangedWeapon) {
    // 远程: 生成投射物 (现有逻辑)
    SpawnActor(ProjectileClass, ...);
} else {
    // 近战: 即时判定 (最小可行实现)
    MeleeHitCheck();   // Step 4 只做空壳/Log, 后续完善
}
```

MeleeCheck() 最小实现：
- 从 WeaponFireSocketName 做 LineTrace/Sweep
- 命中 Actor 有 AttributeComponent --> ApplyDamage
- 后续迭代: 击退/格挡/连招

---

## 十一、详细实现步骤（共10步，按顺序执行）

### 步骤1：新建 EWeaponTypes.h

- 定义 `EWeaponAnimType` 枚举（Cast_1H / Cast_2H / Slash_1H / Slash_2H / Thrust / Shoot / None）
- 定义 `EBuffType` 枚举（None / Regeneration / Speed / Defense），供 UConsumableData 使用
- `uint8` 底层 + `BlueprintType` UENUM

### 步骤2：新建 PrimaryDataAsset 类

**新建文件**:
- `UItemDataBase.h` + `UItemDataBase.cpp` -- 物品基类（第2.1节所有字段）
- `UWeaponData.h` -- 武器子类（第2.2节所有字段）
- `UConsumableData.h` -- 消耗品子类（第2.3节所有字段）

### 步骤3：精简 FItemData（ItemData.h）

**修改文件**: `ItemData.h`
- **删除** `HealthRestore`、`ManaRestore` 字段（已移至 UConsumableData）
- **删除** `AttackBonus`、`DefenseBonus` 字段（如需要移至各自子类）
- FItemData 结构体保留给 FItemInstance 运行时使用
- **不加**任何武器字段

### 步骤4：新建/完善 UItemDataSubsystem（数据访问核心）

**修改文件**: `ItemDataSubsystem.h` + `ItemDataSubsystem.cpp`

这是整个架构的关键新增项：

- 继承自 `UGameInstanceSubsystem`
- 核心: `TMap<FName, TSoftObjectPtr<UItemDataBase>> ItemDataMap` （软引用映射）
- 辅助: `TMap<FName, UItemDataBase*> LoadedCache` （已加载硬指针缓存）
- `Initialize()`: 扫描目录或等待外部 RegisterItemData
- 提供 3 个公开查询接口（带懒加载）:
  - `GetItemData(FName)` --> UItemDataBase* （懒加载 + 缓存）
  - `GetWeaponData(FName)` --> UWeaponData* （内部 Get + Cast）
  - `GetConsumableData(FName)` --> UConsumableData* （内部 Get + Cast）
- 提供 `RegisterItemData()` 用于编辑器手动挂载模式
- **随 GameInstance 自动创建/销毁**

#### 步骤4.1：编辑器配置（如果使用方式B 手动挂载）

编译后，打开 **Edit --> Project Settings**，搜索 `"ItemData"`:

```
+-- Project Settings -------------------------------------------+
| Game --> Item Data Subsystem                                  |
|                                                               |
| Item Data Assets     [+ 添加 DA_xxx 条目]                   |
|   [0] DA_FireStaff                                          |
|   [1] DA_IceStaff                                           |
|   [2] DA_HPPotion                                            |
|   [3] ...                                                   |
|                                             [Reset to Default] |
+---------------------------------------------------------------+
```

从 Content Browser 拖入对应的 DataAsset 资产到每个槽位。保存项目 (Ctrl+S)。

> **验证方式**: 运行游戏后观察 Output Log 出现 `[UItemDataSubsystem] Initialized` 即表示成功。

### 步骤5：扩展 InventoryComponent

**修改文件**: `InventoryComponent.h` + `InventoryComponent.cpp`
- **删除** `UDataTable* ItemDataTable` 属性（由 Subsystem 接管）
- **修改** `GetItemData()` 签名: 从 `(FName, FItemData&)` 改为 `(FName, UItemBase*&)` -- 返回指针而非拷贝
- 新增 `GetWeaponData()` 和 `GetConsumableData()` 查询方法（内部调用 Subsystem + Cast）
- 新增装备管理: `EquippedSlotIndex`、`OnEquipmentChanged` 委托
- 新增 `EquipItem()` / `UnequipItem()` / `GetEquippedWeaponData()` / `IsWeaponEquipped()`
  - EquipItem 内部通过 Subsystem.GetWeaponData() 获取 UWeaponData* 后传给 Character
- 修改 `RemoveItemAt()` / `DropItem()`：卸下装备槽位时自动 Unequip
- **使用消耗品时**: `UseItem()` 内部根据 ItemType 通过 Subsystem.GetConsumableData() 执行恢复

### 步骤6：MyPlayerCharacter 接入装备系统

**修改文件**: `MyPlayerCharacter.h` + `MyPlayerCharacter.cpp`
- Include `EWeaponTypes.h`、`UWeaponData.h`、`ItemDataSubsystem.h`
- **删除**: `FireballClass`、`AttackManaCost`、`AttackMontage`、`HandSocketName`
- **新增**: `CurrentWeaponData`(UWeaponData*)、`CurrentWeaponID`(FName)、`AttackMontageMap`(TMap)
- **新增**: `EquipWeapon(UWeaponData*)`、`UnequipWeapon()`
- **改写**: `Attack()`（读动态数据）、`FireFromHand()`（全参数动态化）
- **新增**: `MeleeHitCheck()`（空壳）
- 订阅 `OnEquipmentChanged` 委托

### 步骤7：编辑器中创建并配置 DataAsset

在 Content Browser 中：

**通用物品 UItemDataBase 子类资产**:
```
右键 --> Miscellaneous --> Data Asset --> UItemDataBase (或其子类)
命名: DA_<类型>_<名称>
例: DA_Material_Wood, DA_Quest_GoblinTooth
```

**武器资产 (UWeaponData)**:
| 资产名 | ItemID | ProjectileClass | AnimType | IsRanged | ManaCost | DmgOverride | Socket | Cooldown |
|--------|--------|-----------------|----------|----------|----------|------------|--------|----------|
| DA_WP_FireStaff | WP_Fire | BP_Fireball' | Cast_1H | true | 10 | 25 | hand_r | 0.5 |
| DA_WP_IceStaff | WP_Ice | BP_IceSpear' | Cast_1H | true | 15 | 35 | hand_r | 0.8 |
| DA_WP_Bow | WP_Bow | BP_Arrow' | Shoot | true | 0 | 20 | hand_r | 1.0 |
| DA_WP_Sword | WP_Sword | (none) | Slash_1H | false | 0 | 40 | weapon | 0.6 |
| DA_WP_Legendary | WP_Legendary | (none) | Slash_1H | false | 0 | 80 | weapon | 0.4 (+OverrideMontage) |

**消耗品资产 (UConsumableData)**:
| 资产名 | ItemID | HealthRestore | ManaRestore | BuffType | Duration | Value |
|--------|--------|---------------|-------------|----------|----------|-------|
| DA_HP_Potion | HP_Pot | 50 | 0 | None | 0 | 0 |
| DA_MP_Potion | MP_Pot | 0 | 30 | None | 0 | 0 |
| DA_HP_Regen | HP_Regen | 10 | 0 | Regeneration | 10.0 | 5.0 |

> **蓝图继承示例**: 可以在蓝图中基于 `DA_WP_Sword` 创建 `DA_WP_LegendarySword`，仅覆写 DamageOverride=80 和 OverrideAttackMontage，其余字段自动继承！

### 步骤8：角色蓝图配置

BP_MyPlayerCharacter 的 Defaults:
- **Attack Montage Map**: Cast_1H-->M_Cast_1H, Slash_1H-->M_Slash_1H, Shoot-->M_Shoot...
- 删除旧的 FireballClass / AttackMontage / AttackManaCost
- InventoryComponent 中 **不再需要拖入 DataAsset 或 DataTable**（由 Subsystem 管理）

### 步骤9：UI 适配 -- UW_InventoryUI

- 选中物品时判断 ItemType:
  - Weapon --> 按钮显示 Equip/Unequip
  - Consumable --> 按钮 Use
  - 其他 --> 按钮置灰或隐藏
- 新增 `OnButton_EquipItemClicked()` 调用 InventoryComponent.Equip/Unequip
- RefreshUI 中遍历格子，EquippedSlotIndex 高亮
- UI 显示物品信息时也通过 Subsystem 查询（如需要展示详细属性面板时）

### 步骤10：UI 适配 -- UW_InventorySlot + UW_StatusBar

- UW_InventorySlot: `SetEquippedHighlight(bool)` 金色边框
- UW_StatusBar: 武器信息区 `UpdateWeaponInfo(UWeaponData*)`
  - 有数据显示/无数据隐藏
  - 由 EquipWeapon/UnequipWeapon 回调驱动

---

## 十二、文件改动清单汇总

| 文件 | 操作 | 内容 |
|------|------|------|
| `EWeaponTypes.h` | **新建** | EWeaponAnimType + EBuffType 枚举 (~25行) |
| `UItemDataBase.h` | **新建** | 物品数据 PrimaryDataAsset 基类 (~70行) |
| `UItemDataBase.cpp` | **新建** | 基类构造函数 (~5行) |
| `UWeaponData.h` | **新建** | 武器子类 (~35行) |
| `UConsumableData.h` | **新建** | 消耗品子类 (~25行) |
| `ItemDataSubsystem.h` | **重写** | TMap + 懒加载 Subsystem 声明 (~55行) |
| `ItemDataSubsystem.cpp` | **重写** | 懒加载实现 + 注册/查询接口 (~90行) |
| `ItemData.h` | **修改** | 删 HealthRestore/ManaRestore/AttackBonus |
| `InventoryComponent.h` | **修改** | 删 DataTable 属性 + 装备管理声明 (~15行改动) |
| `InventoryComponent.cpp` | **修改** | 查询改走 Subsystem + Equip/Unequip逻辑 + UseItem分流 (~110行) |
| `MyPlayerCharacter.h` | **修改** | 删~8行硬编码 + ~18行动态数据+CurrentWeaponID |
| `MyPlayerCharacter.cpp` | **修改** | 重写 Attack/FireFromHand + ~110行 |
| `UW_InventoryUI.h/cpp` | **修改** | Equip按钮 + 高亮 (~50行) |
| `UW_InventorySlot.h/cpp` | **修改** | 装备高亮 (~15行) |
| `UW_StatusBar.h/cpp` | **修改** | 武器信息区 (~30行) |
| **DA_xxx 资产** (编辑器) | **新建** | 每种物品一个 DataAsset (.uasset) |

---

## 十三、架构优势总结

| 维度 | 原方案（DataTable） | 新方案（PrimaryDataAsset + Subsystem） |
|------|---------------------|-------------------|
| **数据访问方式** | 各类直挂 DataTable，分散耦合 | UItemDataSubsystem 统一接口 + TMap 懒加载 |
| **职责清晰度** | FItemData 既管显示又管战斗又管恢复 | 基类管通用，子类管专属，Subsystem 专职查询 |
| **字段污染** | 药水行全是空的武器字段 | 每个子类只有自己需要的字段 |
| **扩展性** | 加护甲 --> 再污染 FItemData | 新建 UArmorData 子类即可，不影响已有代码 |
| **继承能力** | 结构体无法继承 | C++/蓝图均可继承，DA_Legendary 继承 DA_Common 再覆写 |
| **团队协作** | 策划看同一张大表 | 战斗策划配 DA_Weapon，道具策划配 DA_Consumable |
| **查询效率** | 查一次拿到所有（但很多无用数据） | 按需 Cast，基类查询轻量快速 |
| **内存占用** | DataTable 全量加载到内存 | TSoftObjectPtr 按需 LoadSynchronous |
| **资产管理** | 无法搜索/筛选 | 编辑器资产管理器原生支持 |
| **版本控制** | 单个大表易冲突 | 每个 .uasset 独立文件，合并冲突少 |
| **复杂度** | 低（但脏） | 中（但干净，易维护，标准工业实践） |
| **与现有系统兼容性** | N/A | 与 MyEventBusGameInstance 完全独立互不干扰 |
| **业界认可度** | 小项目常用 | Lyra / ActionRPG / 大型商业项目均采用此方案 |

---

## 十四、未来扩展路线图

```
当前阶段 (v1): PrimaryDataAsset + Subsystem
+-- UItemDataBase + UWeaponData + UConsumableData  <-- 本文档范围
+-- UItemDataSubsystem (TMap 懒加载)               <-- 本文档范围
    
v2: 护甲/饰品系统
+-- 新建 UArmorData (Defense / Resistance / SetBonus)
    +-- 继承 UItemDataBase，添加护甲专属字段
    +-- InventoryComponent 加 EquipmentSlot[] (多装备槽)
    
v3: 技能/附魔系统
+-- 新建 USkillData / UEnchantData
    +-- 复杂嵌套结构也适合用 PrimaryDataAsset
    
v4: DLC / 热更新支持
+-- 方式A AssetRegistry 扫描自动识别新 .uasset
+-- 方式B 插件化 Module 加载新类型子系统
    
v5: 网络同步 (DSO/Replication)
+-- PrimaryDataAsset 天然支持网络序列化
+-- Subsystem 可扩展为 ReplicatedSubsystem
```

**关键原则：PrimaryDataAsset 是 UE 数据系统的标准基础设施，一次投入长期受益。**
