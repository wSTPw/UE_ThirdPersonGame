// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MovingPlatform.generated.h"

UCLASS()
class INTROCPP_API AMovingPlatform : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AMovingPlatform();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

	void TestFunction();
	void MovePlatform(float DeltaTime);
	void RotatePlatform(float DeltaTime);

	UPROPERTY(EditAnywhere)
	float MoveSpeed = 2.0f;
	UPROPERTY(EditAnywhere)
	float RotateSpeed = 2.0f;

	UPROPERTY(EditAnywhere)
	FVector OriginPoint = FVector(0.0,0.0,0.0);

	UPROPERTY(EditAnywhere)
	FVector TargetPoint = FVector(0.0,0.0,0.0);

	UPROPERTY(VisibleAnywhere)
	float Progress = 0.0f;
	UPROPERTY(VisibleAnywhere)
	bool Backing = false;
};
