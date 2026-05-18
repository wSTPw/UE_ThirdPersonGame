// Fill out your copyright notice in the Description page of Project Settings.

#include "AnimNotify_MeleeHit.h"
#include "MyPlayerCharacter.h"

void UAnimNotify_MeleeHit::Notify(
	USkeletalMeshComponent* MeshComp,
	UAnimSequenceBase* Animation,
	const FAnimNotifyEventReference& EventReference)
{
	Super::Notify(MeshComp, Animation, EventReference);

	// 安全检查：确保 MeshComp 有效
	if (!MeshComp) return;

	// 从 SkeletalMeshComponent 获取其所属的 Actor（通常是角色本身）
	AActor* OwnerActor = MeshComp->GetOwner();
	if (!OwnerActor) return;

	// 尝试转换为玩家角色 — 只有 AMyPlayerCharacter 才有连击系统的 OnMeleeHitNotify
	if (AMyPlayerCharacter* PlayerChar = Cast<AMyPlayerCharacter>(OwnerActor))
	{
		PlayerChar->OnMeleeHitNotify();
	}
	// 如果 Cast 失败（例如敌人也用了这个 Notify），静默忽略不做任何事
}
