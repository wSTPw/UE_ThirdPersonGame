// Fill out your copyright notice in the Description page of Project Settings.

#include "ItemDataBase.h"

/**
 * UItemDataBase 构造函数
 *
 * 设置所有字段的安全默认值。
 * 子类（UConsumableData / UWeaponData）的构造函数会覆盖 ItemType 等特定字段。
 */
UItemDataBase::UItemDataBase()
	: ItemID(NAME_None)                    // 无效 ID，等待编辑器填写
	, ItemType(EItemType::Miscellaneous)   // 默认杂物类型，子类会覆盖
	, ItemRarity(EItemRarity::Common)       // 默认普通稀有度
	, MaxStackSize(1)                       // 默认不可堆叠（最安全的默认值）
	, Weight(0.0f)                          // 默认无重量
	, Value(0)                              // 默认无价值
	, bCanSell(true)                        // 默认可出售
	, bCanUse(false)                        // 默认不可使用（消耗品子类会改为 true）
	, bCanDrop(true)                        // 默认可丢弃
{
}
