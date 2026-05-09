// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "UW_MainHUD.generated.h"

class UButton;

/**
 * 
 */
UCLASS()
class INTROCPP_API UUW_MainHUD : public UUserWidget
{
	GENERATED_BODY()
	
protected:
	UPROPERTY(meta = (BindWidget))
	UButton* Button_StartGame;
	UPROPERTY(meta = (BindWidget))
	UButton* Button_1;
	UPROPERTY(meta = (BindWidget))
	UButton* Button_2;

	virtual void NativeConstruct() override; // 对应 Start：初始化、绑定事件
	virtual void NativeDestruct() override;  // 对应 OnDestroy：解绑事件、清理

private:
	UFUNCTION()
	void OnButton_StartGameClicked();
	UFUNCTION()
	void OnButton_1Clicked();
	UFUNCTION()
	void OnButton_2Clicked();

	// 在第38行之前添加
public:
	// ==========================================
	// 要跳转的关卡名（在蓝图中设置）
	// ==========================================
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Level")
		FString GameLevelName = "MyLevel";  // 设置默认值

//public:
//	// ==========================================
//	// 【7】给外部调用的公共接口（比如GameMode/PlayerController）
//	// ==========================================
//	UFUNCTION(BlueprintCallable, Category = "PickupTip")
//	void ShowTip(const FString& Message); // 显示提示
//
//	UFUNCTION(BlueprintCallable, Category = "PickupTip")
//	void HideTip(); // 隐藏提示
};
