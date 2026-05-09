// Fill out your copyright notice in the Description page of Project Settings.


#include "UW_MainHUD.h"
#include "Components/Button.h"
#include "Kismet/GameplayStatics.h"
#include "HAL/IConsoleManager.h"

void UUW_MainHUD::NativeConstruct()
{
	Super::NativeConstruct();
	if (Button_StartGame)
	{
		Button_StartGame->OnClicked.AddDynamic(this, &UUW_MainHUD::OnButton_StartGameClicked);
	}
	if (Button_1)
	{
		Button_1->OnClicked.AddDynamic(this, &UUW_MainHUD::OnButton_1Clicked);
	}
	if (Button_2)
	{
		Button_2->OnClicked.AddDynamic(this, &UUW_MainHUD::OnButton_2Clicked);
	}

	IConsoleManager& ConsoleManager = IConsoleManager::Get();

	// 开启自定义宽高比
	if (IConsoleVariable* CVar_CustomAspectRatio = ConsoleManager.FindConsoleVariable(TEXT("r.CustomAspectRatio")))
	{
		CVar_CustomAspectRatio->Set(1);
	}

	// 设置 16:9 比例
	if (IConsoleVariable* CVar_AspectRatio = ConsoleManager.FindConsoleVariable(TEXT("r.AspectRatio")))
	{
		CVar_AspectRatio->Set(16.0f / 9.0f);
	}

	// 设置约束方向：0=宽优先，1=高优先
	if (IConsoleVariable* CVar_AspectRatioAxis = ConsoleManager.FindConsoleVariable(TEXT("r.AspectRatioAxisConstraint")))
	{
		CVar_AspectRatioAxis->Set(0);
	}

		UE_LOG(LogTemp, Warning, TEXT("已通过控制台命令锁定视口比例为 16:9"));
}

void UUW_MainHUD::NativeDestruct()
{
	Super::NativeDestruct();
	if (Button_StartGame)
	{
		Button_StartGame->OnClicked.RemoveDynamic(this, &UUW_MainHUD::OnButton_StartGameClicked);
	}
	if (Button_1)
	{
		Button_1->OnClicked.RemoveDynamic(this, &UUW_MainHUD::OnButton_1Clicked);
	}
	if (Button_2)
	{
		Button_2->OnClicked.RemoveDynamic(this, &UUW_MainHUD::OnButton_2Clicked);
	}
}

void UUW_MainHUD::OnButton_StartGameClicked()
{
	UE_LOG(LogTemp, Warning, TEXT("Button_StartGame Clicked!")); 
	if (!GameLevelName.IsEmpty())
	{
		UGameplayStatics::OpenLevel(this, FName(*GameLevelName));
	}

	// 获取玩家控制器
	if (APlayerController* PC = GetOwningPlayer())
	{
		// 隐藏鼠标
		PC->bShowMouseCursor = false;

		// 禁用UI点击事件
		PC->bEnableClickEvents = false;
		PC->bEnableMouseOverEvents = false;

		// 设置仅游戏输入模式（关键！）
		FInputModeGameOnly InputMode;
		PC->SetInputMode(InputMode);
	}

}

void UUW_MainHUD::OnButton_1Clicked()
{
	UE_LOG(LogTemp, Warning, TEXT("Button_1 Clicked!"));
}

void UUW_MainHUD::OnButton_2Clicked()
{
	UE_LOG(LogTemp, Warning, TEXT("Button_2 Clicked!"));
}