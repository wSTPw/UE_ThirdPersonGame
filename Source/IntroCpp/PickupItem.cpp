// Fill out your copyright notice in the Description page of Project Settings.

#include "PickupItem.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SphereComponent.h"
#include "InventoryComponent.h"          // 拾取时需要调用 AddItem()
#include "MyEventBusGameInstance.h"      // 全局事件总线（发布 Item_Pickup 事件）
#include "GlobalEvents.h"                // GlobalEvents::Item_Pickup 常量

// ============================================================================
//  构造函数 — 创建组件
// ============================================================================

/**
 * 组件层次：
 * StaticMesh (RootComponent) ← 最外层，负责显示和物理
 *   └── SphereCollision (子组件, 附着StaticMesh) ← 仅用于拾取检测
 */
APickupItem::APickupItem()
{
	PrimaryActorTick.bCanEverTick = true;

	// 创建 StaticMesh 作为 Root（显示外观 + 作为物理体承载）
	StaticMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMesh"));
	RootComponent = StaticMesh;

	// 创建拾取检测球体，附着到 StaticMesh 上
	SphereCollision = CreateDefaultSubobject<USphereComponent>(TEXT("SphereCollision"));
	SphereCollision->SetupAttachment(StaticMesh);
	SphereCollision->SetSphereRadius(50.f);  // 默认拾取半径 50cm
	SetupCollisionComponent(SphereCollision);  // 配置碰撞参数
}

/**
 * 配置碰撞组件为"仅用于拾取检测"模式
 * 关键设置：
 * - GenerateOverlapEvents = true (启用重叠事件)
 * - CollisionEnabled = QueryOnly (不参与物理模拟/阻挡)
 * - Ignore All Channels + Only Overlap Pawn (只响应角色进入)
 */
void APickupItem::SetupCollisionComponent(UPrimitiveComponent* CollisionComp)
{
	if (!CollisionComp) return;

	CollisionComp->SetGenerateOverlapEvents(true);                    // 开启重叠事件
	CollisionComp->SetCollisionEnabled(ECollisionEnabled::QueryOnly); // 仅查询，不物理碰撞

	// 默认忽略所有碰撞通道，只对 Pawn 通道做 Overlap 响应
	// 这样火球、特效触发器等不会误触此拾取检测
	CollisionComp->SetCollisionResponseToAllChannels(ECR_Ignore);
	CollisionComp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

	// 编辑器中默认隐藏（调试时可以临时改 Visible）
	CollisionComp->SetVisibility(false);
}

// ============================================================================
//  生命周期回调
// ============================================================================

/** 编辑器中的构造脚本：确保 SphereCollision 始终保持 QueryOnly */
void APickupItem::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (SphereCollision)
	{
		SphereCollision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);  // 不覆盖 StaticMesh 的物理设置
		SphereCollision->SetVisibility(true);  // 编辑器调试时可见（方便调整半径）
	}
}

/** 游戏开始时绑定拾取检测的重叠事件 */
void APickupItem::BeginPlay()
{
	Super::BeginPlay();

	if (SphereCollision)
	{
		// 先移除再添加（防止重复绑定的安全写法）
		SphereCollision->OnComponentBeginOverlap.RemoveDynamic(this, &APickupItem::OnOverlapBegin);
		SphereCollision->OnComponentBeginOverlap.AddDynamic(this, &APickupItem::OnOverlapBegin);
	}
}

/** Actor 销毁前解绑委托（防止悬空引用导致 Crash）*/
void APickupItem::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (SphereCollision)
	{
		SphereCollision->OnComponentBeginOverlap.RemoveDynamic(this, &APickupItem::OnOverlapBegin);
	}

	Super::EndPlay(EndPlayReason);
}

/** Tick 预留扩展（如悬浮动画、旋转、闪烁效果等）*/
void APickupItem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	// 未来可在此处添加：
	// - 上下浮动动画 (Sin(GetTime()) * FloatAmplitude)
	// - 自转效果 (AddActorLocalRotation)
	// - 拾取前的发光/闪烁提示
}

// ============================================================================
//  核心交互 — 重叠拾取
// ============================================================================

/**
 * 当其他 Actor 进入 SphereCollision 范围时触发
 *
 * 处理流程：
 * 1. 忽略空指针和自身
 * 2. 检查对方是否有 InventoryComponent（只有能捡东西的角色才响应）
 * 3. 如果 bAutoPickup → 尝试 AddItem
 *    - 成功 → 发布全局事件 "Item_Pickup" → OnPickup() → Destroy()
 *    - 失败 → 打印警告日志（背包满或超重），物品保留在世界中等待再次尝试
 */
void APickupItem::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
                                 UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
                                 bool bFromSweep, const FHitResult& SweepResult)
{
	if (!OtherActor || OtherActor == this) return;  // 忽略无效和自身

	// ★ 只响应拥有 InventoryComponent 的 Actor（玩家、可拾取的 NPC 等）
	// 其他 Actor（如火球投射物、怪物、特效）直接忽略
	UInventoryComponent* InventoryComp = OtherActor->FindComponentByClass<UInventoryComponent>();
	if (!InventoryComp)
	{
		return;  // 不是有效的拾取者，完全忽略
	}

	if (bAutoPickup)
	{
		// 尝试将物品添加到对方的背包
		if (InventoryComp->AddItem(ItemID, ItemQuantity))
		{
			UE_LOG(LogTemp, Log, TEXT("物品已添加到背包: %s x %d"), *ItemID.ToString(), ItemQuantity);

			// ★ 发布全局事件 — 成就系统/任务系统/音效系统等可监听此事件
			if (UMyEventBusGameInstance* EventBus = UMyEventBusGameInstance::Get(this))
			{
				EventBus->Publish_StringParam(GlobalEvents::Item_Pickup, ItemID.ToString());
			}

			// 拾取成功 → 触发拾取回调（默认实现 = Destroy）
			OnPickup(OtherActor);
		}
		else
		{
			// 添加失败（可能背包满或超重）→ 物品保留在世界中，等玩家清理背包后再来捡
			UE_LOG(LogTemp, Warning, TEXT("无法添加物品到背包（可能已满或超重）: %s"), *ItemID.ToString());
		}
	}
	// !bAutoPickup 的情况：等待外部逻辑（如按键检测）手动调用拾取
}

// ============================================================================
//  拾取回调与辅助
// ============================================================================

/** 默认拾取实现：直接销毁此 Actor。蓝图可覆写以添加特效/声音/动画 */
void APickupItem::OnPickup_Implementation(AActor* OtherActor)
{
	Destroy();
}

/** 调试用日志方法 */
void APickupItem::OnPickup_Log(FString Message)
{
	UE_LOG(LogTemp, Warning, TEXT("OnPickup_Log: %s"), *Message);
}

/** 运行时初始化：设置 ItemID 和 Quantity（供 DropItem 等生成方调用）*/
void APickupItem::InitializePickup(FName InItemID, int32 InQuantity)
{
	ItemID = InItemID;
	ItemQuantity = InQuantity;
}
