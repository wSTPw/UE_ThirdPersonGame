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
#include "ConsumableData.h"          // UConsumableData（UseHeldItem 读取 UseMontage）

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
    Actions = CreateDefaultSubobject<UCharacterActionComponent>(TEXT("CharacterActions"));
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

    // ★ 攻击或使用物品时禁止移动（避免边走边砍）
    if (Actions && Actions->GetSnapshot().MoveScale <= 0.f) return;

    // 拿到二维输入值（X=左右，Y=前后）
    FVector2D MoveVal = Value.Get<FVector2D>();

    if (Controller && MoveVal.Size() > 0.0f)
    {
        // 沿着角色面向的方向移动
        AddMovementInput(GetActorForwardVector(), MoveVal.Y * (Actions ? Actions->GetSnapshot().MoveScale : 1.f));
        // 沿着角色右侧的方向移动
        AddMovementInput(GetActorRightVector(), MoveVal.X * (Actions ? Actions->GetSnapshot().MoveScale : 1.f));
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
    if (Actions && !Actions->GetSnapshot().bAllowJump) return;
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
    if (!bIsInventoryOpen && Actions && (Actions->IsBusy() || !AttributeComp || !AttributeComp->IsAlive())) return;
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
        if (Actions) Actions->SetUIBlocked(false);

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
        if (Actions) Actions->SetUIBlocked(true);

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
    if (Actions) Actions->SetUIBlocked(false);
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
    if (Actions) Actions->Interrupt(ECharacterActionEndReason::OwnerEnded);
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
	if (Actions && InventoryComponent) Actions->RequestUseItem(true, InventoryComponent->SelectedQuickSlotIndex);
}

/** AnimNotify_UseItemComplete 回调：在动画的"执行帧"触发实际效果 */
void AMyPlayerCharacter::OnUseItemAnimFinished()
{
	UE_LOG(LogTemp, Warning, TEXT("[Actions] Unkeyed item notification rejected."));
}

/** 执行物品使用的实际效果：只消耗 1 个，同步快捷栏，刷新手部模型 */
void AMyPlayerCharacter::ExecuteItemUseEffect(UItemDataBase* ItemData, int32 SlotIdx)
{
	UE_LOG(LogTemp, Warning, TEXT("[Actions] Direct item effect rejected; use an action request."));
}

/** 执行物品的 ItemAction 效果（仅在未走 UseItem 路径时调用） */
void AMyPlayerCharacter::ExecuteItemActions(UItemDataBase* ItemData, int32 SlotIdx)
{
	UE_LOG(LogTemp, Warning, TEXT("[Actions] Direct item action rejected; use an action request."));
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

	if (Actions && !Actions->CanChangeEquipment())
	{
		return;
	}

	InventoryComponent->SelectQuickSlot(SlotIndex);
}

void AMyPlayerCharacter::Attack()
{
	if (Actions) Actions->RequestAttack();
}

// ==============================================
// 火球发射
// ==============================================

void AMyPlayerCharacter::FireFromHand()
{
	UE_LOG(LogTemp, Warning, TEXT("[Actions] Unkeyed FireFromHand rejected; use Attack and an identified animation notify."));
}

// ==============================================
// 装备/卸装武器
// ==============================================

void AMyPlayerCharacter::EquipWeapon(UWeaponData* InWeaponData)
{
	if (!InWeaponData || (Actions && !Actions->CanChangeEquipment())) return;
	CurrentWeaponData = InWeaponData;
	CurrentWeaponID = InWeaponData->ItemID;
	ShowHeldItem(InWeaponData);
	if (!InWeaponData->WeaponProjectileClass.IsNull()) InWeaponData->WeaponProjectileClass.LoadSynchronous();
	if (!InWeaponData->MeleeComboData.IsNull()) InWeaponData->MeleeComboData.LoadSynchronous();
	UpdateLocomotionAnimType();
	if (StatusBarInstance) StatusBarInstance->RefreshQuickSlots();
}

void AMyPlayerCharacter::UnequipWeapon()
{
	if (Actions && !Actions->CanChangeEquipment()) return;
	ClearHeldItem();
	CurrentWeaponData = nullptr;
	CurrentWeaponID = NAME_None;
	UpdateLocomotionAnimType();
	if (StatusBarInstance) StatusBarInstance->RefreshQuickSlots();
}

void AMyPlayerCharacter::UpdateLocomotionAnimType()
{
	UMyAnimInstance* MyAnim = Cast<UMyAnimInstance>(GetMesh()->GetAnimInstance());
	if (!MyAnim) return;

	MyAnim->CurrentWeaponAnimType = CurrentWeaponData
		? CurrentWeaponData->WeaponAnimType
		: EWeaponAnimType::None;
}

void AMyPlayerCharacter::SetAttacking(bool bInAttacking)
{
	bIsAttacking = bInAttacking;

	if (UMyAnimInstance* Anim = Cast<UMyAnimInstance>(GetMesh()->GetAnimInstance()))
	{
		Anim->bIsAttacking = bInAttacking;
	}
}

// ==============================================
// 手持物品系统（快捷栏选中时在手上显示模型）
// ==============================================

void AMyPlayerCharacter::ShowHeldItem(UItemDataBase* ItemData)
{
	if (Actions && !Actions->CanChangeEquipment()) return;
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
	if (Actions && !Actions->CanChangeEquipment()) return;
	if (WeaponMeshComp)
	{
		WeaponMeshComp->DestroyComponent();
		WeaponMeshComp = nullptr;
	}
}

void AMyPlayerCharacter::HandleQuickSlotSelectionChanged(int32 SlotIndex)
{
	if (Actions && !Actions->CanChangeEquipment()) return;
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
// 近战命中检测（连击系统核心 — 支持 SubHits 多判定）
// ==============================================

void AMyPlayerCharacter::MeleeHitCheck()
{
	UE_LOG(LogTemp, Warning, TEXT("[Actions] Direct melee effect rejected; effects require an active execution."));
}

void AMyPlayerCharacter::OnMeleeHitNotify()
{
	UE_LOG(LogTemp, Warning, TEXT("[Actions] Unkeyed melee notification rejected."));
}
