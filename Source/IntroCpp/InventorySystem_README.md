# 背包系统使用指南

## 系统概述

这是一个基于 **PrimaryDataAsset + UItemDataSubsystem** 的完整背包和物品系统，包含以下核心组件：

1. **UItemDataBase / UWeaponData / UConsumableData** -- 物品数据资产（PrimaryDataAsset 体系）
2. **UItemDataSubsystem** -- 数据管理子系统（TMap 懒加载缓存）
3. **InventoryComponent** -- 背包组件（附加到角色）
4. **UW_InventoryUI** -- 背包UI界面
5. **PickupItem** -- 拾取物品（已集成背包）

### 架构总览

```
UItemDataBase (PrimaryDataAsset 基类)    每个 .uasset 一个物品
  |-- UWeaponData (武器子类)            战斗属性
  |-- UConsumableData (消耗品子类)      恢复属性
  +-- DA_Wood 等通用物品              仅基础信息

UItemDataSubsystem (GameInstanceSubsystem)
  |-- TMap<ItemID, SoftPtr<UItemBase>>   全局唯一入口
  |-- GetItemData(ID) --> 懒加载 + 缓存    任何地方调用

InventoryComponent (ActorComponent)
  |-- TArray<FItemInstance> Inventory      运行时槽位数据
  |-- Equip/Unequip/Use/Drop 操作        委托给 Subsystem 获取数据
```

> **与旧版区别**: 本系统已从 **DataTable** 迁移至 **PrimaryDataAsset** 架构。
> - 不再使用 `DT_Items` / `DT_Weapons` 等 DataTable
> - 每个物品是 Content Browser 中的独立 `.uasset` DataAsset
> - 所有数据通过 `UItemDataSubsystem` 集中查询（懒加载 + TMap 缓存）
> - 支持蓝图继承：`DA_LegendarySword` 可继承 `DA_IronSword` 再覆写属性

## 快速开始

### 步骤1：在角色中添加背包组件

在你的角色类（如MyPlayerCharacter）中添加背包组件：

```cpp
// MyPlayerCharacter.h
UCLASS()
class INTROCPP_API AMyPlayerCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    // 背包组件
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory")
    UInventoryComponent* InventoryComponent;
};

// MyPlayerCharacter.cpp
AMyPlayerCharacter::AMyPlayerCharacter()
{
    // 创建背包组件
    InventoryComponent = CreateDefaultSubobject<UInventoryComponent>(TEXT("InventoryComponent"));
    
    // 设置背包容量
    InventoryComponent->MaxSlots = 20;      // 20个槽位
    InventoryComponent->MaxWeight = 100.0f; // 最大负重100
}
```

### 步骤2：创建物品 DataAsset

1. 在 Content Browser 中右键 → **Miscellaneous** → **Data Asset**
2. 选择父类：
   - `UItemDataBase` → 通用物品（材料、杂物等）
   - `UWeaponData` → 武器（含战斗属性）
   - `UConsumableData` → 消耗品（含恢复属性）
3. 命名：`DA_<类型>_<名称>` （例: `DA_Weapon_FireStaff`, `DA_Consum_HP_Potion`）

#### DataAsset 配置示例

**通用字段（所有类型共用）**:
| 字段 | 说明 | 示例 |
|------|------|------|
| ItemID | 唯一标识 | `HP_Pot` |
| ItemName | 显示名称 | `生命药水` |
| ItemDescription | 描述文字 | `恢复50点生命值` |
| ItemType | 物品大类 | `Consumable` |
| ItemIcon | 图标（直接拖Texture！） | `Tex_Potion` |
| ItemClass | 拾取物蓝图类 | `BP_PickupItem` |
| MaxStackSize | 最大堆叠数 | `10` |
| Weight | 重量 | `0.5` |
| Value | 价值 | `20` |

**武器特有字段 (UWeaponData)**:
| 字段 | 说明 | 示例 |
|------|------|------|
| WeaponProjectileClass | 投射物蓝图类 | `BP_Fireball'` |
| WeaponAnimType | 攻击动画枚举 | `Cast_1H` |
| bIsRangedWeapon | 是否远程 | `true` |
| WeaponManaCost | 攻击耗蓝 | `10` |

**消耗品特有字段 (UConsumableData)**:
| 字段 | 说明 | 示例 |
|------|------|------|
| HealthRestore | 回复生命 | `50` |
| ManaRestore | 回复魔法 | `0` |

### 步骤3：配置 UItemDataSubsystem

编译后，打开 **Edit → Project Settings** → 搜索 `"ItemData"`：

```
Game -> Item Data Subsystem
  Item Data Assets
    [0] DA_HP_Potion         <-- 从 Content Browser 拖入
    [1] DA_WP_FireStaff
    [2] DA_Material_Wood
    [+]
```

保存项目。运行游戏后 Subsystem 会自动注册这些资产。

### 步骤4：在场景中使用 PickupItem

1. 将 PickupItem 拖入场景
2. 在 Details 面板配置：
   - **ItemID**: `HP_Potion` （对应 DataAsset 的 ItemID）
   - **ItemQuantity**: `3`
   - **bAutoPickup**: `true`

### 步骤5：打开/关闭背包UI

在你的 PlayerController 或 Character 中添加打开背包的功能：

```cpp
// MyPlayerCharacter.h
UFUNCTION(BlueprintCallable, Category = "Inventory")
void ToggleInventory();

UPROPERTY(EditDefaultsOnly, Category = "UI")
TSubclassOf<UUW_InventoryUI> InventoryUIClass;

UPROPERTY()
UUW_InventoryUI* InventoryUIInstance;

// MyPlayerCharacter.cpp
void AMyPlayerCharacter::ToggleInventory()
{
    if (!InventoryUIInstance)
    {
        InventoryUIInstance = CreateWidget<UUW_InventoryUI>(GetWorld(), InventoryUIClass);
        if (InventoryUIInstance)
        {
            InventoryUIInstance->SetInventoryComponent(InventoryComponent);
        }
    }

    if (InventoryUIInstance)
    {
        if (InventoryUIInstance->IsInViewport())
        {
            InventoryUIInstance->RemoveFromParent();
            if (APlayerController* PC = Cast<APlayerController>(GetController()))
            {
                PC->bShowMouseCursor = false;
                FInputModeGameOnly InputMode;
                PC->SetInputMode(InputMode);
            }
        }
        else
        {
            InventoryUIInstance->AddToViewport();
            if (APlayerController* PC = Cast<APlayerController>(GetController()))
            {
                PC->bShowMouseCursor = true;
                FInputModeGameAndUI InputMode;
                InputMode.SetHideCursorDuringCapture(false);
                PC->SetInputMode(InputMode);
            }
        }
    }
}

// 在 SetupPlayerInputComponent 中绑定按键
void AMyPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    
    if (UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(PlayerInputComponent))
    {
        EnhancedInput->BindAction(IA_Inventory, ETriggerEvent::Started, this, &AMyPlayerCharacter::ToggleInventory);
    }
}
```

## 高级功能

### 1. 程序化添加物品

```cpp
// 通过 Subsystem 查询后添加（推荐方式，自动校验数据存在性）
InventoryComponent->AddItem(FName("HP_Potion"), 10);

// 添加1把铁剑
InventoryComponent->AddItem(FName("WP_Sword"), 1);

// 注意: AddItem 内部会通过 Subsystem.GetItemData() 自动获取重量/堆叠信息
```

### 2. 检查物品

```cpp
if (InventoryComponent->HasItem(FName("Potion_HP")))
{
    int32 PotionCount = InventoryComponent->GetItemCount(FName("Potion_HP"));
    UE_LOG(LogTemp, Log, TEXT("你有 %d 瓶生命药水"), PotionCount);
}

if (InventoryComponent->HasSpace())
{
    UE_LOG(LogTemp, Log, TEXT("背包还有空位"));
}

if (InventoryComponent->CanCarryWeight(10.0f))
{
    UE_LOG(LogTemp, Log, TEXT("还能携带10单位重量的物品"));
}
```

### 3. 移除物品

```cpp
// 使用3个生命药水
InventoryComponent->RemoveItem(FName("Potion_HP"), 3);

// 丢弃指定槽位的物品
InventoryComponent->DropItem(5); // 丢弃第5个槽位的物品
```

### 4. 使用物品

```cpp
// 使用第0个槽位的物品（如果是消耗品会扣除）
InventoryComponent->UseItem(0);
```

### 5. 整理背包

```cpp
// 自动整理（按ID排序）
InventoryComponent->SortItems();
```

### 6. 武器装备系统

```cpp
// 装备指定槽位的武器（必须是 Weapon 类型）
InventoryComponent->EquipItem(3);  // 装备第3格的武器

// 卸下当前装备
InventoryComponent->UnequipItem();

// 查询是否装备了武器
bool bEquipped = InventoryComponent->IsWeaponEquipped();

// 获取当前装备的武器数据指针（可直接读战斗属性）
UWeaponData* EquippedWeapon = InventoryComponent->GetEquippedWeaponData();
if (EquippedWeapon)
{
    UE_LOG(LogTemp, Log, TEXT("当前武器: %s, 伤害: %d"), 
        *EquippedWeapon->ItemName.ToString(), EquippedWeapon->WeaponDamageOverride);
}
```

### 7. 背包事件监听

```cpp
// 在 Character 的 BeginPlay 中
void AMyPlayerCharacter::BeginPlay()
{
    Super::BeginPlay();
    
    if (InventoryComponent)
    {
        // 监听物品添加
        InventoryComponent->OnItemAdded.AddUObject(this, &AMyPlayerCharacter::OnItemAdded);
        
        // 监听物品移除
        InventoryComponent->OnItemRemoved.AddUObject(this, &AMyPlayerCharacter::OnItemRemoved);
        
        // 监听装备变更
        InventoryComponent->OnEquipmentChanged.AddUObject(this, &AMyPlayerCharacter::OnEquipmentChanged);
        
        // 监听背包更新
        InventoryComponent->OnInventoryUpdated.AddUObject(this, &AMyPlayerCharacter::OnInventoryUpdated);
    }
}

void AMyPlayerCharacter::OnItemAdded(const FItemInstance& Item)
{
    UE_LOG(LogTemp, Log, TEXT("获得物品: %s x %d"), *Item.ItemID.ToString(), Item.Quantity);
}

void AMyPlayerCharacter::OnEquipmentChanged(FName ItemID, bool bEquipped)
{
    if (bEquipped)
    {
        UE_LOG(LogTemp, Log, TEXT("已装备: %s"), *ItemID.ToString());
    }
    else
    {
        UE_LOG(LogTemp, Log, TEXT("已卸装: %s"), *ItemID.ToString());
    }
}
```

## UI自定义

### 修改背包UI样式

1. 创建 UW_InventoryUI 的蓝图子类
2. 在蓝图中设计界面：
   - 槽位网格（Uniform Grid Panel）
   - 重量显示（Text Block）
   - 数量显示（Text Block）
   - 按钮（排序、关闭、使用、丢弃、装备）

### 槽位样式

在 UW_InventorySlot 蓝图中可以自定义：
- 物品图标（Image）
- 数量文字（Text Block）
- 选中效果（边框高亮）
- 悬停效果

## 最佳实践

### 1. DataAsset 命名规范
- 使用英文和驼峰命名
- 格式：`DA_<类型>_<名称>`
- 示例：`DA_Consum_HP_Small`, `DA_Weapon_Iron`, `DA_Material_Wood`

### 2. 性能优化
- 背包事件不要频繁调用
- 使用 TSoftObjectPtr 异步加载大资源
- 批量添加物品时先检查空间
- Subsystem 的 TMap 缓存确保同一物品只 LoadSynchronous 一次

### 3. 扩展建议
- 新增物品类型只需新建 UItemDataBase 子类（如 UArmorData），无需改现有代码
- Subsystem 可扩展为 Replicated 支持多人游戏
- 蓝图可基于 C++ DataAsset 创建子类覆写属性

### 4. 调试技巧

```cpp
// 查看 Subsystem 注册了哪些物品
auto* DataSys = GetGameInstance()->GetSubsystem<UItemDataSubsystem>();
TArray<FName> IDs = DataSys->GetAllRegisteredItemIDs();
for (FName ID : IDs) { UE_LOG(LogTemp, Log, TEXT("已注册: %s"), *ID.ToString()); }

// 查看某个物品是否成功加载
UItemDataBase* Item = DataSys->GetItemData(TEXT("HP_Pot"));
if (Item) { UE_LOG(LogTemp, Log, TEXT("找到: %s"), *Item->GetName()); }
```

## 常见问题

### Q: 物品无法拾取？
A: 检查：
- 角色是否有 InventoryComponent
- ItemID 是否与某个 DataAsset.ItemID 匹配
- Subsystem 是否已注册该 DataAsset（Project Settings 或扫描模式）
- 背包是否有空间和负重

### Q: 背包UI不显示？
A: 检查：
- InventoryComponent 是否赋值给 UI
- UI 类是否正确设置
- Subsystem 是否正确配置并初始化

### Q: 物品图标不显示？
A: 检查：
- DataAsset 的 ItemIcon 是否填入了 Texture
- 尝试同步加载测试

### Q: 如何新增一个物品类型（如护甲）？
A:
1. 新建 `UArmorData.h`，继承 `UItemDataBase`
2. 添加护甲专属字段（Defense、Resistance 等）
3. 在 Subsystem 中新增 `GetArmorData()` 方法（内部 Get + Cast）
4. 在 Content Browser 创建 DA_Armor_xxx 资产
5. 无需改动 InventoryComponent 的核心逻辑

### Q: 与旧版 DataTable 方案的区别？
A: 核心差异：
| 旧版 (DataTable) | 新版 (PrimaryDataAsset) |
|---|---|
| DT_Items 单张大表 | 每个 .uasset 一个资产对象 |
| FTableRowBase 结构体 | UPrimaryDataAsset 类（支持继承） |
| 无法引用 Mesh/Sound | 字段原生支持资产引用 |
| 策划填表行 | 策划创建+配置资产 |
| 无蓝图扩展能力 | 蓝图/C++ 双层继承 |

## 完整系统架构

```
DA_HPPotion (UConsumableData)     PickupItem (场景中)
    ItemID="HP_Pot"               ItemID="HP_Pot"
    HealthRestore=50                Quantity=3
                                    ↓ OnOverlapBegin
                              InventoryComponent.AddItem("HP_Pot", 3)
                                    ↓ Subsystem.GetConsumableData("HP_Pot")
                              返回 UConsumableData* (懒加载+缓存)
                                    ↓ 存入 FItemInstance
UItemDataSubsystem                    ↓ 广播 OnItemData
  TMap<"HP_Pot" --> SoftPtr>     Slot[0]: {ItemID="HP_Pot", Qty=3}
  TMap<"HP_Pot" --> LoadedCache*       ↓
                                    UW_InventoryUI.RefreshUI()
  GetItemData() / GetWeaponData()     显示: 图标、名称、数量
  RegisterItemData()                   ↓
                                    UseItem(0)
                                    ↓ Subsystem.GetConsumableData()
                                    ↓ 执行 HealthRestore=50
                                    ↓ RemoveItemAt(0, 1)
                                    ↓ 广播 OnItemUsed
```

## 支持

如有问题，请检查：
1. 所有 C++ 类已编译
2. DataAsset 已创建并配置到 Subsystem（Project Settings 或扫描模式）
3. 组件和 UI 正确关联
4. 日志输出是否有错误
