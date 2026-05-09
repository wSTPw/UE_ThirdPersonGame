// Fill out your copyright notice in the Description page of Project Settings.


#include "MovingPlatform.h"

// Sets default values
AMovingPlatform::AMovingPlatform()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AMovingPlatform::BeginPlay()
{
	Super::BeginPlay();

	SetActorLocation(OriginPoint);

	TestFunction();

}

void AMovingPlatform::TestFunction()
{
	//测试函数
	UE_LOG(LogTemp, Warning, TEXT("It just a TestFunction!!!"));
}

// Called every frame
void AMovingPlatform::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	MovePlatform(DeltaTime);
	RotatePlatform(DeltaTime);
}

/// <summary>
/// 移动平台的函数
/// </summary>
/// <param name="DeltaTime">DeltaTime</param>
void AMovingPlatform::MovePlatform(float DeltaTime)
{
	Progress += DeltaTime * MoveSpeed;
	FVector CurrentLocation = GetActorLocation();

	//如果不是返回，则向目标点移动
	if (!Backing)
	{
		//移动到插值计算的新位置
		FVector NewLocation = FMath::Lerp(OriginPoint, TargetPoint, Progress);
		SetActorLocation(NewLocation);
		//如果进度达到或超过1，则切换到返回
		if (Progress >= 1)
		{
			Backing = !Backing;
			Progress = 0.0f;
		}
	}
	//如果返回，则向起始点移动
	else
	{
		//移动到插值计算的新位置
		FVector NewLocation = FMath::Lerp(TargetPoint, OriginPoint, Progress);
		SetActorLocation(NewLocation);
		//如果进度达到或超过1，则切换到非返回
		if (Progress >= 1)
		{
			Backing = !Backing;
			Progress = 0.0f;
		}
	}
}

void AMovingPlatform::RotatePlatform(float DeltaTime)
{
	//旋转平台的函数
	FRotator CurrentRotation = GetActorRotation();
	CurrentRotation.Yaw += DeltaTime * RotateSpeed * 20; //旋转速度可以根据需要调整
	SetActorRotation(CurrentRotation);
}