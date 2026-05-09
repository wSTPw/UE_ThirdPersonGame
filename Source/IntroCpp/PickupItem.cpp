#include "PickupItem.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SphereComponent.h"
#include "InventoryComponent.h"
#include "MyEventBusGameInstance.h"
#include "GlobalEvents.h"

// 构造：创建 StaticMesh 和 SphereCollision，SphereCollision 附着到 StaticMesh
APickupItem::APickupItem()
{
	PrimaryActorTick.bCanEverTick = true;

	// 使用 StaticMesh 作为显示与物理承载
	StaticMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMesh"));
	RootComponent = StaticMesh;

	// 拾取检测使用 SphereCollision，附着到 StaticMesh（作为子物体）
	SphereCollision = CreateDefaultSubobject<USphereComponent>(TEXT("SphereCollision"));
	SphereCollision->SetupAttachment(StaticMesh);
	SphereCollision->SetSphereRadius(50.f);
	SetupCollisionComponent(SphereCollision);
}

void APickupItem::SetupCollisionComponent(UPrimitiveComponent* CollisionComp)
{
	if (!CollisionComp) return;

	// 仅用于触发拾取检测：开启生成重叠事件并设置为查询（QueryOnly）
	CollisionComp->SetGenerateOverlapEvents(true);
	CollisionComp->SetCollisionEnabled(ECollisionEnabled::QueryOnly);

	// 默认忽略所有通道，只对 Pawn 做 Overlap（避免不必要的重叠回调）
	CollisionComp->SetCollisionResponseToAllChannels(ECR_Ignore);
	CollisionComp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

	// 编辑器中可见性根据需要设置（默认隐藏）
	CollisionComp->SetVisibility(false);
}

void APickupItem::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	// 确保拾取检测球体处于 QueryOnly（不覆盖 StaticMesh 的碰撞设置）
	if (SphereCollision)
	{
		SphereCollision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		SphereCollision->SetVisibility(true); // 编辑器调试时可见
	}
	// 注意：不再在这里修改 StaticMesh 的碰撞或物理参数，交由美术/编辑器或其他逻辑控制
}

void APickupItem::BeginPlay()
{
	Super::BeginPlay();

	// 绑定拾取检测的重叠事件
	if (SphereCollision)
	{
		SphereCollision->OnComponentBeginOverlap.RemoveDynamic(this, &APickupItem::OnOverlapBegin);
		SphereCollision->OnComponentBeginOverlap.AddDynamic(this, &APickupItem::OnOverlapBegin);
	}
}

void APickupItem::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// 解绑（安全）
	if (SphereCollision)
	{
		SphereCollision->OnComponentBeginOverlap.RemoveDynamic(this, &APickupItem::OnOverlapBegin);
	}

	Super::EndPlay(EndPlayReason);
}

void APickupItem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}

void APickupItem::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
                                 UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
                                 bool bFromSweep, const FHitResult& SweepResult)
{
	if (!OtherActor || OtherActor == this) return;

	// ★ 只响应拥有 InventoryComponent 的角色（如玩家），忽略火球/怪物等其他Actor
	UInventoryComponent* InventoryComp = OtherActor->FindComponentByClass<UInventoryComponent>();
	if (!InventoryComp)
	{
		return;  // 不是有效的拾取者，直接忽略
	}

	if (bAutoPickup)
	{
		if (InventoryComp->AddItem(ItemID, ItemQuantity))
		{
			UE_LOG(LogTemp, Log, TEXT("物品已添加到背包: %s x %d"), *ItemID.ToString(), ItemQuantity);
			if (UMyEventBusGameInstance* EventBus = UMyEventBusGameInstance::Get(this))
			{
				EventBus->Publish_StringParam(GlobalEvents::Item_Pickup, ItemID.ToString());
			}
			OnPickup(OtherActor);  // 成功拾取才销毁
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("无法添加物品到背包（可能已满或超重）: %s"), *ItemID.ToString());
		}
	}
}

void APickupItem::OnPickup_Implementation(AActor* OtherActor)
{
	Destroy();
}

void APickupItem::OnPickup_Log(FString Message)
{
	UE_LOG(LogTemp, Warning, TEXT("OnPickup_Log: %s"), *Message);
}

void APickupItem::InitializePickup(FName InItemID, int32 InQuantity)
{
	// 运行时设置物品 ID 和数量
	ItemID = InItemID;
	ItemQuantity = InQuantity;
}
