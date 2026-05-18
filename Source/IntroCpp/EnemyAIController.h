// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "AIController.h"
#include "EEnemyTypes.h"
#include "Perception/AIPerceptionTypes.h"
#include "EnemyAIController.generated.h"

class AEnemyBase;
class UEnemyData;

/**
 * 敌人 AI 控制器
 *
 * 使用简单的有限状态机（FSM）驱动敌人行为。
 * 状态: Patrol → Chase → Attack → Dead
 *
 * 扩展方向:
 *   - 当前: 简单 FSM（适合初学者/小规模敌人）
 *   - 未来: 升级为 BehaviorTree（替换 UpdateState 为 BT 任务）
 */
UCLASS()
class INTROCPP_API AEnemyAIController : public AAIController
{
	GENERATED_BODY()

public:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;
	virtual void OnPossess(APawn* InPawn) override;

	/** 当控制的敌人死亡时调用（停止 AI 行为） */
	UFUNCTION(BlueprintCallable, Category = "AI")
	void OnOwnerDied();

protected:

	// ====== 当前状态 ======

	/** 当前 AI 状态 */
	EAIState CurrentState = EAIState::Patrol;


	// ====== 状态更新入口 ======

	/** 每一帧根据条件决定是否转换状态 */
	void UpdateState(float DeltaTime);

	/** 切换到新状态 */
	void TransitionToState(EAIState NewState);


	// ====== 各状态的行为逻辑 ======

	void State_Patrol(float DeltaTime);
	void State_Chase(float DeltaTime);
	void State_Attack(float DeltaTime);
	void State_Dead(float DeltaTime);


	// ====== 巡逻相关 ======

	FVector PatrolCenter;               // 巡逻中心点（出生位置）
	FVector CurrentPatrolTarget;        // 当前巡逻目标点
	float WaitTimer = 0.f;              // 到达目标点的等待计时
	bool bWaitingAtPatrolPoint = false; // 是否正在等待
	int32 PatrolIndex = 0;              // 巡逻点索引（Circular/BackAndForth 模式使用）
	bool bPatrolForward = true;         // 来回巡逻的方向标志
	bool bIsPlayingIdleMontage = false; // 是否正在播放待机动画

	/** 根据 PatrolType 选择下一个巡逻点 */
	FVector ChooseNextPatrolPoint();


	// ====== 感知辅助 ======

	/**
	 * 检测能否看到目标（视线检测 + 距离检测）
	 * 包含 LineOfSight 检测，防止隔墙追击
	 */
	bool CanSeeTarget() const;

	/** 获取一个随机巡逻点（在 PatrolRadius 内） */
	FVector GetRandomPatrolPoint() const;


	// ====== AIPerception 目标发现 ======

	/** AIPerception 组件 — 用于自动发现/丢失目标 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "AI|Perception")
	class UAIPerceptionComponent* PerceptionComp;

	/** 视觉感知配置 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "AI|Perception")
	class UAISenseConfig_Sight* SightConfig;

	/** 感知回调：当检测到/丢失目标时由 AIPerception 自动调用 */
	UFUNCTION()
	void OnPerceptionUpdated(AActor* Actor, FAIStimulus Stimulus);


	// ====== 追击丢失防抖动 ======

	float LostTargetTimer = 0.f;    // 丢失目标的累计时间

	// ====== 攻击范围容差（防止边缘抖动）======

	float AttackGraceTimer = 0.f;   // 脱离攻击范围的容差计时
	bool bAttackGraceActive = false; // 是否正在容差倒计时


	// ====== 辅助获取 ======

	/** 获取控制的敌人（安全转换） */
	AEnemyBase* GetEnemyPawn() const;
};
