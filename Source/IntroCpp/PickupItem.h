// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PickupItem.generated.h"

/**
 * APickupItem — 场景中的可拾取物品 Actor
 *
 * 【职责】
 * 作为掉落物/场景中散落物品的视觉和交互载体。
 * 玩家走近时触发 Overlap → 检测是否有 InventoryComponent → 自动添加到背包。
 *
 * 【组件构成】
 * - StaticMesh (RootComponent): 3D 显示外观 + 物理承载
 * - SphereCollision (附着StaticMesh): 仅用于拾取检测（QueryOnly, Pawn Only）
 *
 * 【两种使用方式】
 * 1. 编辑器直接拖入场景：在 Details 面板配置 ItemID + ItemQuantity
 * 2. 运行时动态生成：DropItem() 或怪物死亡时 Spawn，然后调用 InitializePickup()
 *
 * 【生命周期】
 * Spawn → BeginPlay 绑定 Overlap → Player 走进范围
 * → OnOverlapBegin → AddItem 成功? → OnPickup() → Destroy()
 */
UCLASS()
class INTROCPP_API APickupItem : public AActor
{
	GENERATED_BODY()

public:
	APickupItem();

	/**
	 * 运行时初始化拾取数据
	 * 由 InventoryComponent::DropItem() 或其他生成方在 Spawn 后立即调用
	 *
	 * @param InItemID    物品标识符（需与已注册的 DataAsset ID 一致）
	 * @param InQuantity  掉落数量
	 */
	UFUNCTION(BlueprintCallable, Category = "Pickup")
	void InitializePickup(FName InItemID, int32 InQuantity);

protected:
	virtual void BeginPlay() override;
	virtual void OnConstruction(const FTransform& Transform) override;  // 编辑器中刷新
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override; // 清理解绑

public:
	virtual void Tick(float DeltaTime) override;

protected:

	// ====== 可编辑属性（编辑器/运行时可配）======

	/** 要拾取的物品 ID（如 "HP_Potion"）*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FName ItemID;

	/** 掉落数量（默认1）*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	int32 ItemQuantity = 1;

	/** 自动拾取模式：true = 进入重叠范围即自动捡起；false = 需要手动交互按键 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bAutoPickup = true;

	// ====== 子组件声明 ======

	/** 外观网格体（作为 RootComponent，承载显示和物理）*/
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* StaticMesh;

	/** 拾取检测球体碰撞（附着到 StaticMesh，仅用于 Overlap 检测）*/
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	class USphereComponent* SphereCollision;

public:

	// ====== 访问器（供外部查询当前状态）======

	FORCEINLINE FName GetItemID() const { return ItemID; }
	FORCEINLINE int32 GetItemQuantity() const { return ItemQuantity; }
	FORCEINLINE bool IsAutoPickup() const { return bAutoPickup; }

	// ====== 拾取事件（BlueprintNativeEvent 允许蓝图覆写扩展）======

	/**
	 * 拾取成功时的回调。
	 * 默认实现：Destroy() 销毁此 Actor。
	 * 蓝图子类可覆写以添加特效、音效、动画等额外表现。
	 *
	 * @param OtherActor 触发拾取的 Actor（通常是玩家角色）
	 */
	UFUNCTION(BlueprintNativeEvent, Category = "Pickup")
	void OnPickup(AActor* OtherActor);
	virtual void OnPickup_Implementation(AActor* OtherActor);

	/** 调试用日志接口 */
	void OnPickup_Log(FString Message);

	// ====== 重叠回调（SphereCollision 的 OnComponentBeginOverlap 绑定目标）======

	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
	                    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
	                    bool bFromSweep, const FHitResult& SweepResult);

private:
	/** 配置碰撞组件的通用拾取检测参数（QueryOnly + PawnOnly）*/
	void SetupCollisionComponent(UPrimitiveComponent* CollisionComp);
};
