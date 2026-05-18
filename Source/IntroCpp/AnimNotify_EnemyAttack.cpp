// Fill out your copyright notice in the Description page of Project Settings.

#include "AnimNotify_EnemyAttack.h"
#include "EnemyBase.h"

void UAnimNotify_EnemyAttack::Notify(
	USkeletalMeshComponent* MeshComp,
	UAnimSequenceBase* Animation,
	const FAnimNotifyEventReference& EventReference)
{
	Super::Notify(MeshComp, Animation, EventReference);

	// 安全检查
	if (!MeshComp) return;

	// 获取 owning Actor
	AActor* Owner = MeshComp->GetOwner();
	if (!Owner) return;

	// 尝试转换为 AEnemyBase 并调用攻击通知
	// （和 AnimNotify_UseItemComplete 完全相同的模式）
	if (AEnemyBase* Enemy = Cast<AEnemyBase>(Owner))
	{
		Enemy->OnAttackAnimNotify();
	}
}
