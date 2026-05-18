#pragma once
#include "CoreMinimal.h"

/**
 * 全局事件名称常量定义
 *
 * 集中管理所有跨模块通信的事件标识符字符串，
 * 避免在各文件中硬编码魔法字符串导致拼写不一致。
 *
 * 【使用方式】
 * 通过 EventBus (UMyEventBusGameInstance) 发布/订阅：
 *   // 发布事件
 *   EventBus->Publish_StringParam(GlobalEvents::Item_Pickup, "HP_Potion");
 *
 *   // 订阅事件（通常在 BeginPlay 中）
 *   EventBus->Subscribe_StringParam(GlobalEvents::Item_Pickup, this, &MyClass::OnItemPickup);
 *
 * 【当前已定义的事件】
 * - Item_Pickup: 物品被拾取到背包时发布（PickupItem.OnOverlapBegin 中触发）
 * - Player_Jump: 玩家跳跃时发布（预留）
 *
 * @note 使用 namespace 而非 static const 避免 ODR(One Definition Rule) 问题，
 *       且调用时更语义化：GlobalEvents::Item_Pickup vs GLOBAL_ITEM_PICKUP
 */
namespace GlobalEvents
{
    /** 物品拾取事件 — 参数为 ItemID 字符串（如 "HP_Potion"）*/
    inline const FName Item_Pickup = TEXT("Item_Pickup");

    /** 玩家跳跃事件 — 预留，当前未使用 */
    inline const FName Player_Jump = TEXT("Player_Jump");
}
