// Fill out your copyright notice in the Description page of Project Settings.

#include "ItemDataBase.h"

UItemDataBase::UItemDataBase()
	: ItemID(NAME_None)
	, ItemType(EItemType::Miscellaneous)
	, ItemRarity(EItemRarity::Common)
	, MaxStackSize(1)
	, Weight(0.0f)
	, Value(0)
	, bCanSell(true)
	, bCanUse(false)
	, bCanDrop(true)
{
}
