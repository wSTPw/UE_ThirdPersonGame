// Fill out your copyright notice in the Description page of Project Settings.

#include "AnimNotify_UseItemComplete.h"
#include "MyPlayerCharacter.h"                    // 目标角色类（调用 OnUseItemAnimFinished）
#include "Components/SkeletalMeshComponent.h"    // USkeletalMeshComponent（参数类型）

/**
 * Notify 实现 — 动画帧通知的执行入口
 *
 * 职责链：
 * 1. 从 SkeletalMeshComponent 获取拥有者 Actor
 * 2. 安全检查 Owner 有效性
 * 3. 尝试转型为玩家角色 (AMyPlayerCharacter)
 * 4. 转型成功 → 调用角色的 OnUseItemAnimFinished() 方法
 *
 * @note 此 Notify 只对玩家角色有意义。
 *       如果敌人或其他 Actor 也使用了带此 Notify 的 Montage，
 *       Cast 会失败并安全跳过（不会 Crash）。
 */
void UAnimNotify_UseItemComplete::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
	const FAnimNotifyEventReference& EventReference)
{
	// 调用基类 Notify（引擎标准流程，不要遗漏）
	Super::Notify(MeshComp, Animation, EventReference);

	// 安全检查：骨骼网格组件必须有效
	if (!MeshComp) return;

	// 从组件获取其所属 Actor（即播放动画的角色/生物）
	AActor* Owner = MeshComp->GetOwner();
	if (!Owner) return;

	// 尝试转换为玩家角色类型
	// 只有玩家角色实现了 OnUseItemAnimFinished() 方法
	if (AMyPlayerCharacter* PlayerChar = Cast<AMyPlayerCharacter>(Owner))
	{
		// ★ 调用玩家的物品使用完成方法
		// 该方法内部会执行：ItemAction 效果 + RemoveItemAt 扣减 + UI 刷新
		PlayerChar->OnUseItemAnimFinished();
	}
	// 如果 Cast 失败（Owner 不是 AMyPlayerCharacter），静默忽略
	 // 这保证了此 Notify 放在任何 Montage 中都是安全的
}
