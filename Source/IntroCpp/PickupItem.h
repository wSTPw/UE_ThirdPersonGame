// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PickupItem.generated.h"

UCLASS()
class INTROCPP_API APickupItem : public AActor
{
	GENERATED_BODY()

public:
	APickupItem();

	// 在运行时初始化拾取数据（Spawn 时调用）
	UFUNCTION(BlueprintCallable, Category = "Pickup")
	void InitializePickup(FName InItemID, int32 InQuantity);

protected:
	virtual void BeginPlay() override;
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:
	virtual void Tick(float DeltaTime) override;

protected:
	// 物品数据，可在编辑器配置
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	FName ItemID;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	int32 ItemQuantity = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item")
	bool bAutoPickup = true;

	// 可视网格（用于显示与物理）
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* StaticMesh;

	// 仅保留 SphereCollision 用作拾取检测（附着到 StaticMesh）
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	class USphereComponent* SphereCollision;

public:
	FORCEINLINE FName GetItemID() const { return ItemID; }
	FORCEINLINE int32 GetItemQuantity() const { return ItemQuantity; }
	FORCEINLINE bool IsAutoPickup() const { return bAutoPickup; }

	// 拾取事件（Blueprint 可实现）
	UFUNCTION(BlueprintNativeEvent, Category = "Pickup")
	void OnPickup(AActor* OtherActor);
	virtual void OnPickup_Implementation(AActor* OtherActor);

	void OnPickup_Log(FString Message);

	// 重叠回调
	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
	                    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
	                    bool bFromSweep, const FHitResult& SweepResult);

private:
	// 初始化碰撞组件的通用设置（仅用于拾取检测）
	void SetupCollisionComponent(UPrimitiveComponent* CollisionComp);

	// 运行时初始化/配置（保留以便未来扩展）
};
