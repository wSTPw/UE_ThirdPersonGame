// Fill out your copyright notice in the Description page of Project Settings.
#include "MyPlayerCharacter.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "MyEventBusGameInstance.h"
#include "GlobalEvents.h"
#include "UW_InventoryUI.h"
#include "PickupItem.h" // Include头文件
#include "AttributeComponent.h" // 属性组件
#include "Animation/AnimMontage.h" // 攻击蒙太奇
#include "TimerManager.h"
#include "AFireballProjectile.h" // 火球发射
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"  // 特效/音效播放工具函数
#include "ItemDataSubsystem.h"      // Subsystem 查询（EquipWeapon 预加载用）

// ==============================================
// 构造函数：初始化组件
// ==============================================
AMyPlayerCharacter::AMyPlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    // 1. 创建弹簧臂（让摄像机跟随角色）
    SpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArm"));
    SpringArm->SetupAttachment(RootComponent);
    SpringArm->TargetArmLength = 300.0f; // 摄像机距离
    SpringArm->bUsePawnControlRotation = true; // 关键：让弹簧臂跟随鼠标旋转

    // 2. 创建摄像机
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(SpringArm);
    Camera->bUsePawnControlRotation = false; // 摄像机不需要自己旋转，跟着弹簧臂就行

    // 3. 角色移动设置（可选，调手感）
    GetCharacterMovement()->MaxWalkSpeed = 500.0f;  // 走路速度
    GetCharacterMovement()->JumpZVelocity = 600.0f;  // 跳跃高度
    GetCharacterMovement()->AirControl = 0.5f;        // 空中控制
    
    // 4. 创建背包组件
    InventoryComponent = CreateDefaultSubobject<UInventoryComponent>(TEXT("InventoryComponent"));
    InventoryComponent->MaxSlots = 20;      // 20个背包槽位
    InventoryComponent->MaxWeight = 100.0f; // 最大负重100

    // 5. 创建属性组件（HP/MP管理）
    AttributeComp = CreateDefaultSubobject<UAttributeComponent>(TEXT("AttributeComponent"));
    AttributeComp->MaxHealth = 100.0f;      // 初始最大生命值100
    AttributeComp->MaxMana = 50.0f;         // 初始最大魔法值50
}

// ==============================================
// 游戏开始：注入输入映射
// ==============================================
void AMyPlayerCharacter::BeginPlay()
{
    Super::BeginPlay();

    // 把我们的输入映射上下文（IMC）注入到玩家控制器
    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
            PC->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
        {
            if (InputMapping)
            {
                Subsystem->AddMappingContext(InputMapping, 0);
            }
        }
    }

    // ★ 绑定装备变更委托 → 自动同步武器到 Character
    if (InventoryComponent)
    {
        InventoryComponent->OnEquipmentChanged.AddDynamic(this, &AMyPlayerCharacter::HandleEquipmentChanged);
        // ★ 绑定快捷栏切换委托 → 自动装备武器/显示物品模型
        InventoryComponent->OnQuickSlotSelected.AddDynamic(this, &AMyPlayerCharacter::HandleQuickSlotSelectionChanged);
        // ★ 绑定快捷栏内容变化委托 → 拖放物品到当前槽位时刷新手部模型
        InventoryComponent->OnQuickSlotChanged.AddDynamic(this, &AMyPlayerCharacter::OnQuickSlotContentChanged);
    }

    // 游戏开始时显示状态栏
    ShowStatusBar();
}

// ==============================================
// 每帧逻辑（目前空着，以后可以加东西）
// ==============================================
void AMyPlayerCharacter::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
}

// ==============================================
// 输入绑定：把 IA 和函数连起来
// ==============================================
void AMyPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    // 转成增强输入组件
    if (UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(PlayerInputComponent))
    {
        // 绑定移动（持续触发）
        EnhancedInput->BindAction(IA_Move, ETriggerEvent::Triggered, this, &AMyPlayerCharacter::Move);

        // 绑定视角（持续触发）
        EnhancedInput->BindAction(IA_Look, ETriggerEvent::Triggered, this, &AMyPlayerCharacter::Look);

        // 绑定跳跃（按下时触发开始，松开时触发结束）
        EnhancedInput->BindAction(IA_Jump, ETriggerEvent::Started, this, &AMyPlayerCharacter::JumpStart);
        EnhancedInput->BindAction(IA_Jump, ETriggerEvent::Completed, this, &AMyPlayerCharacter::JumpEnd);

        // 绑定背包开关（按下Tab键）
        EnhancedInput->BindAction(IA_Inventory, ETriggerEvent::Started, this, &AMyPlayerCharacter::ToggleInventory);

        // 绑定攻击（按下鼠标左键）
        EnhancedInput->BindAction(IA_Attack, ETriggerEvent::Started, this, &AMyPlayerCharacter::AttackStarted);

        // 绑定使用物品（按住鼠标右键 → 播放动画 → 动画结束 → 执行效果）
        EnhancedInput->BindAction(IA_UseItem, ETriggerEvent::Started, this, &AMyPlayerCharacter::UseItemStarted);
        EnhancedInput->BindAction(IA_UseItem, ETriggerEvent::Completed, this, &AMyPlayerCharacter::UseItemCompleted);

        // 绑定快捷栏 1~5
        if (IA_QuickSlot1)
        {
            EnhancedInput->BindAction(IA_QuickSlot1, ETriggerEvent::Started, this, &AMyPlayerCharacter::OnQuickSlot1Pressed);
        }
        if (IA_QuickSlot2)
        {
            EnhancedInput->BindAction(IA_QuickSlot2, ETriggerEvent::Started, this, &AMyPlayerCharacter::OnQuickSlot2Pressed);
        }
        if (IA_QuickSlot3)
        {
            EnhancedInput->BindAction(IA_QuickSlot3, ETriggerEvent::Started, this, &AMyPlayerCharacter::OnQuickSlot3Pressed);
        }
        if (IA_QuickSlot4)
        {
            EnhancedInput->BindAction(IA_QuickSlot4, ETriggerEvent::Started, this, &AMyPlayerCharacter::OnQuickSlot4Pressed);
        }
        if (IA_QuickSlot5)
        {
            EnhancedInput->BindAction(IA_QuickSlot5, ETriggerEvent::Started, this, &AMyPlayerCharacter::OnQuickSlot5Pressed);
        }
    }
}

// ==============================================
// 移动逻辑：WASD
// ==============================================
void AMyPlayerCharacter::Move(const FInputActionValue& Value)
{
    // ★ 背包打开时禁止移动
    if (bIsInventoryOpen) return;

    // 拿到二维输入值（X=左右，Y=前后）
    FVector2D MoveVal = Value.Get<FVector2D>();

    if (Controller && MoveVal.Size() > 0.0f)
    {
        // 沿着角色面向的方向移动
        AddMovementInput(GetActorForwardVector(), MoveVal.Y);
        // 沿着角色右侧的方向移动
        AddMovementInput(GetActorRightVector(), MoveVal.X);
    }
}

// ==============================================
// 视角逻辑：鼠标
// ==============================================
void AMyPlayerCharacter::Look(const FInputActionValue& Value)
{
    // ★ 背包打开时禁止视角控制
    if (bIsInventoryOpen) return;

    // 拿到二维输入值（X=左右转，Y=上下看）
    FVector2D LookVal = Value.Get<FVector2D>();

    if (Controller)
    {
        // 控制角色左右转（偏航 Yaw）
        AddControllerYawInput(LookVal.X);
        // 控制摄像机上下看（俯仰 Pitch）
        AddControllerPitchInput(LookVal.Y);
    }
}

// ==============================================
// 跳跃开始
// ==============================================
void AMyPlayerCharacter::JumpStart()
{
    // ★ 背包打开时禁止跳跃
    if (bIsInventoryOpen) return;

    Jump(); // 调用 Character 父类自带的 Jump 函数

    UMyEventBusGameInstance* EventBus = UMyEventBusGameInstance::Get(this);
    if (EventBus)
        EventBus->Publish_NoParam(GlobalEvents::Player_Jump);
}

// ==============================================
// 跳跃结束
// ==============================================
void AMyPlayerCharacter::JumpEnd()
{
    StopJumping(); // 调用 Character 父类自带的 StopJumping 函数
}

// ==============================================
// 背包开关
// ==============================================
void AMyPlayerCharacter::ToggleInventory()
{
    // 检查 InventoryUIClass 是否设置
    if (!InventoryUIClass)
    {
        UE_LOG(LogTemp, Error, TEXT("[错误] InventoryUIClass 未设置！请在蓝图中指定背包UI类"));
        return;
    }

    if (!InventoryComponent)
    {
        UE_LOG(LogTemp, Error, TEXT("[错误] InventoryComponent 为 null！"));
        return;
    }

    // 创建UI（如果还没有）
    if (!InventoryUIInstance)
    {
        InventoryUIInstance = CreateWidget<UUW_InventoryUI>(GetWorld(), InventoryUIClass);
        if (InventoryUIInstance)
        {
            InventoryUIInstance->SetInventoryComponent(InventoryComponent);

            // ★ 订阅背包关闭事件（按钮关闭时也能恢复输入）
            InventoryUIInstance->OnInventoryClosed.AddDynamic(this, &AMyPlayerCharacter::OnInventoryUIClosed);
        }
        else
        {
            UE_LOG(LogTemp, Error, TEXT("[错误] UI创建失败！"));
            return;
        }
    }

    if (InventoryUIInstance->IsInViewport())
    {
        // ========== 关闭背包 ==========
        InventoryUIInstance->RemoveFromParent();
        bIsInventoryOpen = false;

        if (APlayerController* PC = Cast<APlayerController>(GetController()))
        {
            PC->bShowMouseCursor = false;
            PC->bEnableClickEvents = false;
            PC->bEnableMouseOverEvents = false;

            FInputModeGameOnly InputMode;
            PC->SetInputMode(InputMode);
        }

        UE_LOG(LogTemp, Log, TEXT("[Inventory] 背包已关闭，游戏输入恢复"));
    }
    else
    {
        // ========== 打开背包 ==========
        InventoryUIInstance->AddToViewport();
        bIsInventoryOpen = true;

        // ★ 清零速度，防止打开时保持移动
        GetCharacterMovement()->StopActiveMovement();

        if (APlayerController* PC = Cast<APlayerController>(GetController()))
        {
            PC->bShowMouseCursor = true;
            PC->bEnableClickEvents = true;
            PC->bEnableMouseOverEvents = true;

            FInputModeGameAndUI InputMode;
            InputMode.SetHideCursorDuringCapture(false);
            InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
            InputMode.SetWidgetToFocus(InventoryUIInstance->TakeWidget());
            PC->SetInputMode(InputMode);
        }

        UE_LOG(LogTemp, Log, TEXT("[Inventory] 背包已打开，游戏输入被拦截"));
    }
}

// ==============================================
// 背包UI关闭回调（按钮关闭时由委托触发）
// ==============================================
void AMyPlayerCharacter::OnInventoryUIClosed()
{
    bIsInventoryOpen = false;

    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        PC->bShowMouseCursor = false;
        PC->bEnableClickEvents = false;
        PC->bEnableMouseOverEvents = false;

        FInputModeGameOnly InputMode;
        PC->SetInputMode(InputMode);
    }

    UE_LOG(LogTemp, Log, TEXT("[Inventory] 按钮关闭背包，输入已恢复"));
}

// ==============================================
// 状态栏UI：显示HP/MP
// ==============================================
void AMyPlayerCharacter::ShowStatusBar()
{
    if (!StatusBarUIClass)
    {
        UE_LOG(LogTemp, Error, TEXT("[错误] StatusBarUIClass 未设置！请在蓝图中指定状态栏UI类"));
        return;
    }

    // 如果已经显示，不再重复创建
    if (StatusBarInstance && StatusBarInstance->IsInViewport())
    {
        return;
    }

    // 创建状态栏
    if (!StatusBarInstance)
    {
        StatusBarInstance = CreateWidget<UUW_StatusBar>(GetWorld(), StatusBarUIClass);
    }

	if (StatusBarInstance)
	{
		// 绑定属性组件（HP/MP）
		StatusBarInstance->InitWithAttributes(AttributeComp);

		// 绑定背包组件（快捷栏数据源）
		StatusBarInstance->InitWithInventory(InventoryComponent);

		// 显示在屏幕上
		StatusBarInstance->AddToViewport();

		UE_LOG(LogTemp, Log, TEXT("[StatusBar] Status bar shown"));
	}
}

void AMyPlayerCharacter::HideStatusBar()
{
    if (StatusBarInstance && StatusBarInstance->IsInViewport())
    {
        StatusBarInstance->RemoveFromParent();
        UE_LOG(LogTemp, Log, TEXT("[StatusBar] 状态栏已隐藏"));
    }
}

void AMyPlayerCharacter::ToggleStatusBar()
{
    if (StatusBarInstance && StatusBarInstance->IsInViewport())
    {
        HideStatusBar();
    }
    else
    {
        ShowStatusBar();
    }
}

// ==============================================
// 重写父类的端点（用于调试拾取物品的日志）
// 只保留一个 EndPlay 定义（避免重复定义）
// ==============================================
void AMyPlayerCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    // 在结束时解绑所有曾绑定的 Actor（安全清理）
    for (AActor* Actor : ItemOverlapEvents)
    {
        if (Actor)
        {
            Actor->OnActorBeginOverlap.RemoveDynamic(this, &AMyPlayerCharacter::OnItemPickup);
        }
    }
    ItemOverlapEvents.Empty();

	// 解绑装备变更委托
	if (InventoryComponent)
	{
		InventoryComponent->OnEquipmentChanged.RemoveDynamic(this, &AMyPlayerCharacter::HandleEquipmentChanged);
		InventoryComponent->OnQuickSlotSelected.RemoveDynamic(this, &AMyPlayerCharacter::HandleQuickSlotSelectionChanged);
		InventoryComponent->OnQuickSlotChanged.RemoveDynamic(this, &AMyPlayerCharacter::OnQuickSlotContentChanged);
	}

    Super::EndPlay(EndPlayReason);
}

// ==============================================
// 构造函数时（设计器/编辑时）清理绑定表
// ==============================================
void AMyPlayerCharacter::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);

    // 编辑器/构造时清理绑定
    ItemOverlapEvents.Empty();
}

// ==============================================
// 物品拾取：绑定和解绑（使用 AddDynamic / RemoveDynamic）
// ==============================================
void AMyPlayerCharacter::BindItemPickup(AActor* Actor)
{
    if (Actor && !ItemOverlapEvents.Contains(Actor))
    {
        Actor->OnActorBeginOverlap.AddDynamic(this, &AMyPlayerCharacter::OnItemPickup);
        ItemOverlapEvents.Add(Actor);
    }
}

void AMyPlayerCharacter::UnbindItemPickup(AActor* Actor)
{
    if (Actor && ItemOverlapEvents.Contains(Actor))
    {
        Actor->OnActorBeginOverlap.RemoveDynamic(this, &AMyPlayerCharacter::OnItemPickup);
        ItemOverlapEvents.Remove(Actor);
    }
}

// ==============================================
// 物品拾取实现（与APickupItem交互）
// ==============================================
void AMyPlayerCharacter::OnItemPickup(AActor* OverlappedActor, AActor* OtherActor)
{
    if (APickupItem* PickupItem = Cast<APickupItem>(OtherActor))
    {
        // 使用 PickupItem 的公开只读接口，避免直接访问受保护成员
        UE_LOG(LogTemp, Warning, TEXT("拾取物品：%s （数量：%d）"), *PickupItem->GetItemID().ToString(), PickupItem->GetItemQuantity());

        // 自动拾取逻辑（可以在这里添加背包逻辑）
        if (PickupItem->IsAutoPickup())
        {
            // 例如：添加物品到背包（假设背包组件有一个AddItem函数）
            // InventoryComponent->AddItem(PickupItem->GetItemID(), PickupItem->GetItemQuantity());

            // 销毁物品（如果需要的话）
            // PickupItem->Destroy();
        }
    }
}

// ==============================================
// 攻击系统
// ==============================================

void AMyPlayerCharacter::AttackStarted()
{
    // ★ 背包打开时禁止攻击
    if (bIsInventoryOpen) return;

    Attack();
}

// ==============================================
// 使用物品（右键长按，Minecraft 模式）
// ==============================================

void AMyPlayerCharacter::UseItemStarted()
{
	// 背包打开时禁止使用
	if (bIsInventoryOpen) return;
	// 正在使用中则忽略重复触发
	if (bIsUsingItem) return;

	UseHeldItem();
}

void AMyPlayerCharacter::UseItemCompleted()
{
	// 右键松开：目前不中断动画（让动画播完再执行效果）
	// 如果未来需要支持"松开即取消"，可以在这里加打断逻辑
}

void AMyPlayerCharacter::UseHeldItem()
{
	if (!InventoryComponent) return;

	// 获取当前选中的快捷栏物品
	int32 SlotIdx = InventoryComponent->SelectedQuickSlotIndex;
	if (SlotIdx < 0) return;

	FItemInstance SlotItem = InventoryComponent->GetQuickSlot(SlotIdx);
	if (SlotItem.IsEmpty())
	{
		UE_LOG(LogTemp, Log, TEXT("[UseHeldItem] 快捷栏 %d 为空，无法使用"), SlotIdx);
		return;
	}

	UItemDataBase* ItemData = InventoryComponent->GetItemData(SlotItem.ItemID);
	if (!ItemData) return;

	// 武器类型 → 不走使用流程（武器由左键攻击处理）
	if (ItemData->ItemType == EItemType::Weapon)
	{
		UE_LOG(LogTemp, Log, TEXT("[UseHeldItem] 武器 %s 不通过右键使用，请用左键攻击"), *ItemData->ItemName.ToString());
		return;
	}

	// 检查是否可使用
	if (!ItemData->bCanUse)
	{
		UE_LOG(LogTemp, Log, TEXT("[UseHeldItem] 物品 %s 不可使用 (bCanUse=false)"), *ItemData->ItemName.ToString());
		return;
	}

	bIsUsingItem = true;

	// 确定使用动画 Montage（直接读基类的 UseMontage 字段）
	UAnimMontage* UseAnim = ItemData->UseMontage;

	if (UseAnim)
	{
		// ★ AnimNotify 模式：暂存数据 → 播放动画 → 由 AnimNotify_UseItemComplete 在精确帧回调 OnUseItemAnimFinished()
		PendingUseItemData = ItemData;
		PendingUseSlotIdx = SlotIdx;

		float Duration = PlayAnimMontage(UseAnim);
		UE_LOG(LogTemp, Log, TEXT("[UseHeldItem] 开始使用 %s，播放动画 %s (%.2fs), 等待 AnimNotify 回调..."),
			*ItemData->ItemName.ToString(), *UseAnim->GetName(), Duration);

		if (Duration <= 0.0f)
		{
			// 动画时长为 0（异常）→ 直接生效
			OnUseItemAnimFinished();
		}
		// ★ 正常情况：不再用 Timer，等 AnimNotify_UseItemComplete 回调
	}
	else
	{
		// 无动画：立即生效
		UE_LOG(LogTemp, Log, TEXT("[UseHeldItem] 立即使用 %s（无动画）"), *ItemData->ItemName.ToString());
		ExecuteItemUseEffect(ItemData, SlotIdx);
		bIsUsingItem = false;
	}
}

/** AnimNotify_UseItemComplete 回调：在动画的"执行帧"触发实际效果 */
void AMyPlayerCharacter::OnUseItemAnimFinished()
{
	// 读取暂存数据并立即清空（防止重复触发）
	UItemDataBase* ItemData = PendingUseItemData;
	int32 SlotIdx = PendingUseSlotIdx;
	PendingUseItemData = nullptr;
	PendingUseSlotIdx = -1;

	if (!ItemData || SlotIdx < 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("[OnUseItemAnimFinished] 无 pending 数据，可能被多次调用"));
		bIsUsingItem = false;
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("[OnUseItemAnimFinished] 动画帧触发 → 执行效果: %s"), *ItemData->ItemName.ToString());

	ExecuteItemUseEffect(ItemData, SlotIdx);
	bIsUsingItem = false;
}

/** 执行物品使用的实际效果：只消耗 1 个，同步快捷栏，刷新手部模型 */
void AMyPlayerCharacter::ExecuteItemUseEffect(UItemDataBase* ItemData, int32 SlotIdx)
{
	if (!InventoryComponent || !ItemData) return;

	FItemInstance SlotItem = InventoryComponent->GetQuickSlot(SlotIdx);
	if (SlotItem.IsEmpty()) return;

	bool bConsumed = false;

	// 1. 优先在背包中找到并使用（UseItem 内部已处理：扣1个 + 执行 ItemAction 效果）
	int32 InvSlot = InventoryComponent->FindItemSlot(SlotItem.ItemID);
	if (InvSlot >= 0)
	{
		bConsumed = InventoryComponent->UseItem(InvSlot);
	}

	if (bConsumed)
	{
		// 2. 同步快捷栏数量（背包已扣1个，快捷栏也需要对应减1）
		FItemInstance CurrentSlot = InventoryComponent->GetQuickSlot(SlotIdx);
		if (CurrentSlot.Quantity > 1)
		{
			// 还有剩余 → 快捷栏减1
			InventoryComponent->SetQuickSlot(SlotIdx, FItemInstance(CurrentSlot.ItemID, CurrentSlot.Quantity - 1));
		}
		else
		{
			// 用完了 → 清空快捷槽
			InventoryComponent->ClearQuickSlot(SlotIdx);
		}
	}
	else if (InvSlot < 0)
	{
		// 背包中没有（全在快捷栏）→ 直接扣减快捷栏 1 个
		if (SlotItem.Quantity > 1)
		{
			InventoryComponent->SetQuickSlot(SlotIdx, FItemInstance(SlotItem.ItemID, SlotItem.Quantity - 1));
			// 手动执行 ItemAction 效果（因为没走 UseItem）
			ExecuteItemActions(ItemData, SlotIdx);
		}
		else
		{
			// 最后1个 → 清空
			InventoryComponent->ClearQuickSlot(SlotIdx);
			// 手动执行 ItemAction 效果
			ExecuteItemActions(ItemData, SlotIdx);
		}
	}

	// 3. 刷新手部模型（无论结果如何，都重新评估当前槽位应该显示什么）
	RefreshHeldItemDisplay();
}

/** 执行物品的 ItemAction 效果（仅在未走 UseItem 路径时调用） */
void AMyPlayerCharacter::ExecuteItemActions(UItemDataBase* ItemData, int32 SlotIdx)
{
	if (!ItemData || ItemData->ItemActionClasses.Num() == 0) return;

	AActor* ItemInstigator = this;
	for (const TSoftClassPtr<UItemAction>& SoftActionClass : ItemData->ItemActionClasses)
	{
		if (SoftActionClass.IsNull()) continue;
		UClass* ActionClass = SoftActionClass.LoadSynchronous();
		if (!ActionClass) continue;

		UItemAction* Action = NewObject<UItemAction>(InventoryComponent, ActionClass);
		if (!Action) continue;

		Action->InitializeFromItemData(ItemData);
		Action->Execute(InventoryComponent, SlotIdx, ItemInstigator);
	}
}

/** 刷新当前手部模型显示（重新评估选中槽位应显示的物品/武器） */
void AMyPlayerCharacter::RefreshHeldItemDisplay()
{
	if (!InventoryComponent) return;
	HandleQuickSlotSelectionChanged(InventoryComponent->SelectedQuickSlotIndex);
}

// ==============================================
// 快捷栏输入
// ==============================================

void AMyPlayerCharacter::OnQuickSlot1Pressed() { OnQuickSlotPressed(0); }
void AMyPlayerCharacter::OnQuickSlot2Pressed() { OnQuickSlotPressed(1); }
void AMyPlayerCharacter::OnQuickSlot3Pressed() { OnQuickSlotPressed(2); }
void AMyPlayerCharacter::OnQuickSlot4Pressed() { OnQuickSlotPressed(3); }
void AMyPlayerCharacter::OnQuickSlot5Pressed() { OnQuickSlotPressed(4); }

void AMyPlayerCharacter::OnQuickSlotPressed(int32 SlotIndex)
{
	if (!InventoryComponent) return;

	// ★ 攻击或使用物品期间禁止切换快捷栏（避免动画中途切换导致状态不一致）
	if (bIsAttacking || bIsUsingItem)
	{
		return;
	}

	InventoryComponent->SelectQuickSlot(SlotIndex);
}

void AMyPlayerCharacter::Attack()
{
	// 1. 未装备武器 → 无法攻击
	if (!CurrentWeaponData)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Attack] 未装备武器，无法攻击"));
		return;
	}

	if (bIsAttacking)
	{
		return;
	}

	// 2. 确定 Montage（优先级：专属覆盖 > 共享枚举映射）
	UAnimMontage* MontageToPlay = nullptr;

	if (CurrentWeaponData->OverrideAttackMontage)
	{
		// 特殊武器有专属蒙太奇 → 直接使用
		MontageToPlay = CurrentWeaponData->OverrideAttackMontage;
	}
	else if (UAnimMontage** Found = AttackMontageMap.Find(CurrentWeaponData->WeaponAnimType))
	{
		// 普通武器 → 从共享池按枚举取 Montage
		MontageToPlay = *Found;
	}

	if (!MontageToPlay)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Attack] 武器 %s 未配置有效 Montage (AnimType=%d)"),
			*CurrentWeaponID.ToString(), static_cast<int32>(CurrentWeaponData->WeaponAnimType));
		return;
	}

	bIsAttacking = true;

	UE_LOG(LogTemp, Log, TEXT("[Attack] 攻击! 武器=%s, Montage=%s"),
		*CurrentWeaponID.ToString(), *MontageToPlay->GetName());

	float Duration = PlayAnimMontage(MontageToPlay);
	float Cooldown = CurrentWeaponData->WeaponAttackCooldown > 0.0f
		? CurrentWeaponData->WeaponAttackCooldown
		: Duration;

	if (Duration > 0.0f)
	{
		FTimerHandle AttackResetHandle;
		GetWorld()->GetTimerManager().SetTimer(AttackResetHandle, [this]()
		{
			bIsAttacking = false;
			UE_LOG(LogTemp, Log, TEXT("[Attack] 攻击冷却结束，可再次攻击"));
		}, Cooldown, false);
	}
	else
	{
		bIsAttacking = false;
	}
}

// ==============================================
// 火球发射
// ==============================================

void AMyPlayerCharacter::FireFromHand()
{
	// 1. 必须有武器数据
	if (!CurrentWeaponData)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Fire] CurrentWeaponData 为空，无法发射"));
		return;
	}

	// 2. 检查 MP（从武器数据读取消耗）
	float ManaCost = CurrentWeaponData->WeaponManaCost;
	if (AttributeComp && AttributeComp->GetCurrentMana() < ManaCost)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Fire] MP不足！当前=%.1f, 需要=%.1f"),
			AttributeComp->GetCurrentMana(), ManaCost);
		return;
	}

	// 3. 扣除 MP
	if (AttributeComp && ManaCost > 0.0f)
	{
		AttributeComp->UseMana(ManaCost);
	}

	// 4. 获取发射 Socket 位置（从武器数据读取）
	FName SocketName = CurrentWeaponData->WeaponFireSocketName;
	USkeletalMeshComponent* SkMesh = GetMesh();
	FVector SpawnLocation;
	FRotator SpawnRotation;

	if (SkMesh && SkMesh->DoesSocketExist(SocketName))
	{
		SpawnLocation = SkMesh->GetSocketLocation(SocketName);
		SpawnRotation = SkMesh->GetSocketRotation(SocketName);
		// 微小前偏移，避免嵌入手模型内部
		SpawnLocation += SpawnRotation.RotateVector(FVector(10.0f, 0.0f, 0.0f));
	}
	else
	{
		// Socket 不存在 → 后备方案：角色位置 + 摄像机前方
		SpawnLocation = GetActorLocation() + FVector(0.f, 0.f, 80.f);
		SpawnRotation = Controller ? Controller->GetControlRotation() : GetActorRotation();
		UE_LOG(LogTemp, Warning, TEXT("[Fire] Socket '%s' 不存在，使用后备出生位置"), *SocketName.ToString());
	}

	// 5. 获取发射方向（摄像机朝向）
	FVector FireDirection = Camera->GetForwardVector();
	SpawnRotation = FireDirection.Rotation();

	// 6. 分支：远程投射物 / 近战判定
	if (CurrentWeaponData->bIsRangedWeapon)
	{
		// ---- 远程武器：生成投射物 ----
		TSoftClassPtr<AActor>& SoftProjClass = CurrentWeaponData->WeaponProjectileClass;
		if (SoftProjClass.IsNull())
		{
			UE_LOG(LogTemp, Warning, TEXT("[Fire] 武器 %s 未配置 ProjectileClass"), *CurrentWeaponID.ToString());
			// 失败退还 MP
			if (AttributeComp) AttributeComp->RestoreMana(ManaCost);
			return;
		}

		UClass* ProjClass = SoftProjClass.LoadSynchronous();
		if (!ProjClass)
		{
			UE_LOG(LogTemp, Error, TEXT("[Fire] ProjectileClass 加载失败"));
			if (AttributeComp) AttributeComp->RestoreMana(ManaCost);
			return;
		}

		FTransform SpawnTransform(SpawnRotation, SpawnLocation);
		AActor* SpawnedActor = GetWorld()->SpawnActor<AActor>(ProjClass, SpawnTransform);

		if (AAFireballProjectile* Projectile = Cast<AAFireballProjectile>(SpawnedActor))
		{
			Projectile->SetInstigator(this);

			// 设置初速度方向
			float Speed = Projectile->ProjectileMovement->InitialSpeed > 0.0f
				? Projectile->ProjectileMovement->InitialSpeed
				: 1500.0f;
			Projectile->ProjectileMovement->Velocity = FireDirection.GetSafeNormal() * Speed;

			// ★ DamageOverride 覆盖（非0则覆盖投射物基础伤害）
			if (CurrentWeaponData->WeaponDamageOverride != 0)
			{
				// 投射物如果有伤害属性则在此覆写（具体字段名取决于 AAFireballProjectile）
				UE_LOG(LogTemp, Log, TEXT("[Fire] 伤害已覆盖: %d"), CurrentWeaponData->WeaponDamageOverride);
			}

			UE_LOG(LogTemp, Log, TEXT("[Fire] 发射成功! 武器=%s, 方向=(%.1f,%.1f,%.1f), MP=%.1f"),
				*CurrentWeaponID.ToString(), FireDirection.X, FireDirection.Y, FireDirection.Z, ManaCost);
		}
		else if (SpawnedActor)
		{
			// 非火球类投射物（其他 AActor 子类）也设置 Instigator
			SpawnedActor->SetInstigator(this);
			UE_LOG(LogTemp, Log, TEXT("[Fire] 发射非标准投射物: %s"), *SpawnedActor->GetName());
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("[Fire] SpawnActor 失败！"));
			if (AttributeComp) AttributeComp->RestoreMana(ManaCost);
		}
	}
	else
	{
		// ---- 近战武器：执行命中检测 ----
		MeleeHitCheck();
	}
}

// ==============================================
// 装备/卸装武器
// ==============================================

void AMyPlayerCharacter::EquipWeapon(UWeaponData* InWeaponData)
{
	if (!InWeaponData)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Equip] 尝试装备空武器数据"));
		return;
	}

	CurrentWeaponData = InWeaponData;
	CurrentWeaponID = InWeaponData->ItemID;

	// ---- 附加武器网格体到手部 ----
	if (!InWeaponData->WeaponStaticMesh.IsNull())
	{
		UStaticMesh* LoadedMesh = InWeaponData->WeaponStaticMesh.LoadSynchronous();
		if (LoadedMesh)
		{
			if (!WeaponMeshComp)
			{
				// 动态创建 StaticMeshComponent
				WeaponMeshComp = NewObject<UStaticMeshComponent>(this, UStaticMeshComponent::StaticClass(), TEXT("EquippedWeapon"));
				WeaponMeshComp->SetupAttachment(GetMesh(), InWeaponData->HandSocketName);
				WeaponMeshComp->RegisterComponent();
				// 关闭碰撞，避免挡住投射物（火球等）
				WeaponMeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			}

			WeaponMeshComp->SetStaticMesh(LoadedMesh);
			WeaponMeshComp->SetRelativeScale3D(InWeaponData->WeaponScale);

			UE_LOG(LogTemp, Log, TEXT("[Equip] 武器 StaticMesh 已附加到 Socket: %s"), *InWeaponData->HandSocketName.ToString());
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[Equip] 武器 StaticMesh 加载失败"));
		}
	}
	else
	{
		UE_LOG(LogTemp, Log, TEXT("[Equip] 武器 %s 未配置 StaticMesh"), *InWeaponData->ItemName.ToString());
	}

	// 远程武器 → 预加载投射物软引用（避免发射时卡顿）
	if (InWeaponData->bIsRangedWeapon && !InWeaponData->WeaponProjectileClass.IsNull())
	{
		InWeaponData->WeaponProjectileClass.LoadSynchronous();
		UE_LOG(LogTemp, Log, TEXT("[Equip] 预加载投射物类完成: %s"), *CurrentWeaponID.ToString());
	}

	UE_LOG(LogTemp, Log, TEXT("[Equip] 已装备武器: %s (类型=%s, %s)"),
		*InWeaponData->ItemName.ToString(),
		InWeaponData->bIsRangedWeapon ? TEXT("远程") : TEXT("近战"),
		*UEnum::GetValueAsString(InWeaponData->WeaponAnimType));

	// Update StatusBar UI quick slots
	if (StatusBarInstance)
	{
		StatusBarInstance->RefreshQuickSlots();
	}
}

void AMyPlayerCharacter::UnequipWeapon()
{
	if (!CurrentWeaponData)
	{
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("[Unequip] Unequipped weapon: %s"), *CurrentWeaponID.ToString());

	ClearHeldItem();

	CurrentWeaponData = nullptr;
	CurrentWeaponID = NAME_None;

	// Clear StatusBar UI quick slots
	if (StatusBarInstance)
	{
		StatusBarInstance->RefreshQuickSlots();
	}
}

// ==============================================
// 手持物品系统（快捷栏选中时在手上显示模型）
// ==============================================

void AMyPlayerCharacter::ShowHeldItem(UItemDataBase* ItemData)
{
	if (!ItemData) return;

	// 优先从武器子类取 WeaponStaticMesh，否则用基类的 ItemStaticMesh
	UStaticMesh* MeshToUse = nullptr;
	FName SocketName = TEXT("RightHand");
	FVector Scale = FVector(1.0f, 1.0f, 1.0f);

	if (UWeaponData* WeaponData = Cast<UWeaponData>(ItemData))
	{
		// 武器：使用 WeaponStaticMesh + 武器的专用配置
		if (!WeaponData->WeaponStaticMesh.IsNull())
		{
			MeshToUse = WeaponData->WeaponStaticMesh.LoadSynchronous();
			SocketName = WeaponData->HandSocketName;
			Scale = WeaponData->WeaponScale;
		}
	}
	else if (!ItemData->ItemStaticMesh.IsNull())
	{
		// 非武器物品：使用基类通用字段
		MeshToUse = ItemData->ItemStaticMesh.LoadSynchronous();
	}

	if (!MeshToUse)
	{
		UE_LOG(LogTemp, Log, TEXT("[HeldItem] 物品 %s 没有可用的 StaticMesh，不显示手持模型"), *ItemData->ItemName.ToString());
		return;
	}

	// 清除旧模型（如果有）
	ClearHeldItem();

	// 创建新的 StaticMeshComponent 并挂到手部
	WeaponMeshComp = NewObject<UStaticMeshComponent>(this, UStaticMeshComponent::StaticClass(), TEXT("HeldItem"));
	WeaponMeshComp->SetupAttachment(GetMesh(), SocketName);
	WeaponMeshComp->RegisterComponent();
	WeaponMeshComp->SetStaticMesh(MeshToUse);
	WeaponMeshComp->SetRelativeScale3D(Scale);
	WeaponMeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	UE_LOG(LogTemp, Log, TEXT("[HeldItem] 手持物品 %s 已显示于 Socket: %s"), *ItemData->ItemName.ToString(), *SocketName.ToString());
}

void AMyPlayerCharacter::ClearHeldItem()
{
	if (WeaponMeshComp)
	{
		WeaponMeshComp->DestroyComponent();
		WeaponMeshComp = nullptr;
	}
}

void AMyPlayerCharacter::HandleQuickSlotSelectionChanged(int32 SlotIndex)
{
	if (!InventoryComponent) return;

	// 1. 先清除当前手上的东西（无论是什么）
	ClearHeldItem();
	UnequipWeapon();

	// 2. 获取新选中的快捷栏物品
	FItemInstance SlotItem = InventoryComponent->GetQuickSlot(SlotIndex);
	if (SlotItem.IsEmpty()) return;

	// 3. 获取物品数据
	UItemDataBase* ItemData = InventoryComponent->GetItemData(SlotItem.ItemID);
	if (!ItemData) return;

	if (ItemData->ItemType == EItemType::Weapon)
	{
		// 武器 → 完整装备（显示模型 + 启用攻击能力）
		UWeaponData* WeaponData = Cast<UWeaponData>(ItemData);
		if (WeaponData)
		{
			EquipWeapon(WeaponData);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[QuickSlot] 武器数据 Cast 失败: %s"), *SlotItem.ItemID.ToString());
		}
	}
	else if (!ItemData->ItemStaticMesh.IsNull() || 
	         (Cast<UWeaponData>(ItemData) && !Cast<UWeaponData>(ItemData)->WeaponStaticMesh.IsNull()))
	{
		// 非武器但有手持模型 → 只显示视觉，不启用攻击
		ShowHeldItem(ItemData);
	}
}

void AMyPlayerCharacter::OnQuickSlotContentChanged(int32 SlotIndex)
{
	// 仅当变化的槽位是当前选中的槽位时，才刷新手部模型
	if (!InventoryComponent) return;
	if (SlotIndex == InventoryComponent->SelectedQuickSlotIndex)
	{
		UE_LOG(LogTemp, Log, TEXT("[QuickSlot] 当前选中槽 %d 内容变化，刷新手部模型"), SlotIndex);
		RefreshHeldItemDisplay();
	}
}

void AMyPlayerCharacter::HandleEquipmentChanged(FName ItemID, bool bEquipped)
{
	if (bEquipped)
	{
		// 装备 → 通过 InventoryComponent 获取武器数据指针
		UWeaponData* WeaponData = InventoryComponent ? InventoryComponent->GetEquippedWeaponData() : nullptr;
		if (WeaponData)
		{
			EquipWeapon(WeaponData);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[HandleEquipment] 装备 %s 但获取武器数据失败"), *ItemID.ToString());
		}
	}
	else
	{
		// 卸装
		UnequipWeapon();
	}
}

// ==============================================
// 近战命中检测（预留接口，当前仅 Log）
// ==============================================

void AMyPlayerCharacter::MeleeHitCheck()
{
	if (!CurrentWeaponData)
	{
		return;
	}

	FName SocketName = CurrentWeaponData->WeaponFireSocketName;
	int32 DmgOverride = CurrentWeaponData->WeaponDamageOverride;

	UE_LOG(LogTemp, Log, TEXT("[Melee] 近战命中检测触发! 武器=%s, Socket=%s, DamageOverride=%d [预留]"),
		*CurrentWeaponID.ToString(), *SocketName.ToString(), DmgOverride);

	// TODO 后续完善：
	// 1. 从 WeaponFireSocketName 做 LineTrace/Sweep
	// 2. 命中 Actor 检查 AttributeComponent → ApplyDamage
	// 3. 击退/格挡/连招
}