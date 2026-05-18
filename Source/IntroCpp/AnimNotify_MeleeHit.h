// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"  // UAnimNotify 基类
#include "AnimNotify_MeleeHit.generated.h"

// 前向声明（避免在头文件中包含沉重的 Character 头文件）
class AMyPlayerCharacter;

/**
 * 近战命中帧通知 (UAnimNotify_MeleeHit)
 *
 * 【用途】
 * 放在连击 Montage 每段攻击 Section 的"武器接触敌人瞬间"帧。
 * 当动画播放到此 Notify 帧时，引擎自动调用 Notify() → 回调玩家角色的
 * OnMeleeHitNotify() → MeleeHitCheck() → SphereTrace + ApplyDamage。
 *
 * 【设计模式】
 * 与项目中已有的以下 Notify 采用完全相同的模式：
 *   - AnimNotify_UseItemComplete  （物品使用完成回调）
 *   - AnimNotify_EnemyAttack      （敌人攻击命中回调）
 *
 * 统一模式：Notify() → GetOwner() → Cast<目标类型> → 回调方法()
 *
 * 【使用方式】
 * 1. 在 Montage 编辑器的 Notify Track 中找到对应 Section
 * 2. 在武器即将接触敌人的那一帧位置（手臂伸直/武器过身体中心时刻）
 * 3. 拖入一个 AnimNotify_MeleeHit 实例
 * 4. 同一 Section 可放置多个（配合 FComboHitEntry.SubHits 实现多段判定）
 *
 * 【调用链路】
 * Montage 播放到 Notify 帧
 *   → 引擎自动调用 UAnimNotify_MeleeHit::Notify()
 *     → MeshComp.GetOwner() 获取拥有者 Actor
 *       → Cast<AMyPlayerCharacter>(Owner)
 *         → PlayerChar->OnMeleeHitNotify()
 *           → PlayerChar->MeleeHitCheck()
 *             → SphereTrace → ApplyDamage → 击退 → BP_OnMeleeAttackHit(蓝图扩展)
 *
 * @note 如果 Owner 不是 AMyPlayerCharacter（如敌人误用了此 Notify），静默忽略不报错
 */
UCLASS()
class INTROCPP_API UAnimNotify_MeleeHit : public UAnimNotify
{
	GENERATED_BODY()

public:

	/**
	 * 动画播放到此 Notify 帧时由引擎自动调用
	 *
	 * @param MeshComp       播放此动画的骨骼网格组件（通常是角色的 SkeletalMeshComponent）
	 * @param Animation      正在播放的动画序列
	 * @param EventReference Notify 事件引用（含时间、轨迹等信息）
	 */
	virtual void Notify(
		USkeletalMeshComponent* MeshComp,
		UAnimSequenceBase* Animation,
		const FAnimNotifyEventReference& EventReference) override;
};
