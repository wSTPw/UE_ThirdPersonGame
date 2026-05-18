// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "EEnemyTypes.generated.h"

/** 巡逻行为类型 — 决定敌人在闲置时的移动模式 */
UENUM(BlueprintType)
enum class EPatrolType : uint8
{
	Random			UMETA(DisplayName = "随机巡逻"),
	Circular		UMETA(DisplayName = "环形巡逻"),
	BackAndForth	UMETA(DisplayName = "来回巡逻")
};

/** AI 行为状态 — 敌人 AI 状态机的状态枚举 */
UENUM(BlueprintType)
enum class EAIState : uint8
{
	Patrol		UMETA(DisplayName = "巡逻"),
	Chase		UMETA(DisplayName = "追击"),
	Attack		UMETA(DisplayName = "攻击"),
	Dead		UMETA(DisplayName = "死亡")
};
