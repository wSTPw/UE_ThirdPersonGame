#include "Tests/InventoryActionTestTypes.h"
#include "InventoryComponent.h"

void UInventoryActionTestProbe::OnAttributeChanged(float CurrentValue, float MaxValue)
{
    ++ChangedCount;
    if (!Inventory)
    {
        bObservedCommittedQuantity = false;
        return;
    }
    const FItemInstance Source = bQuickSlot ? Inventory->GetQuickSlot(SlotIndex) : Inventory->GetItemAt(SlotIndex);
    bObservedCommittedQuantity &= Source.Quantity == ExpectedQuantity;
    bRejectedReentrantMutation &= !Inventory->SetQuickSlot(0, FItemInstance(TEXT("ReentrantReplacement"), 99));
}

#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Actions/CharacterActionTypes.h"
#include "AttributeComponent.h"
#include "ConsumableData.h"
#include "Engine/World.h"
#include "ItemAction_Heal.h"
#include "ItemAction_RestoreMana.h"
#include "MyPlayerCharacter.h"
#include "UObject/StrongObjectPtr.h"

struct FInventoryActionTestAccess
{
    static bool Reserve(const UInventoryComponent& Inventory, bool bQuickSlot, int32 SlotIndex, FActionItemReservation& Out)
    {
        return Inventory.ReserveActionItem(bQuickSlot, SlotIndex, Out);
    }
    static FActionItemCommitResult Commit(UInventoryComponent& Inventory, const FActionItemReservation& Source, UItemDataBase* Data)
    {
        return Inventory.CommitActionItem(Source, Data);
    }
};

namespace InventoryActionTests
{
    struct FFixture
    {
        UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
        AMyPlayerCharacter* Character = nullptr;
        TStrongObjectPtr<UConsumableData> Data;

        FFixture() : Data(NewObject<UConsumableData>())
        {
            // No map, controller, BeginPlay, asset loading or ItemDataSubsystem.
            if (World) Character = World->SpawnActor<AMyPlayerCharacter>();
            Data->ItemID = TEXT("TransactionTestPotion");
            Data->ItemType = EItemType::Consumable;
            Data->bCanUse = true;
            Data->HealthRestore = 25;
            Data->ManaRestore = 12;
            Data->ItemActionClasses.Add(UItemAction_Heal::StaticClass());
            if (Character)
            {
                Character->AttributeComp->SetHealth(30.f);
                Character->AttributeComp->SetMana(10.f);
            }
        }
        ~FFixture()
        {
            if (World) World->DestroyWorld(false);
        }
        UInventoryComponent& Inventory() const { return *Character->InventoryComponent; }
        UAttributeComponent& Attributes() const { return *Character->AttributeComp; }
        bool Reserve(bool bQuickSlot, int32 Quantity, FActionItemReservation& Out)
        {
            const FItemInstance Item(Data->ItemID, Quantity);
            if (bQuickSlot) Inventory().SetQuickSlot(0, Item);
            else Inventory().SetItemAt(0, Item);
            return FInventoryActionTestAccess::Reserve(Inventory(), bQuickSlot, 0, Out);
        }
        FActionItemCommitResult Commit(const FActionItemReservation& Source)
        {
            return FInventoryActionTestAccess::Commit(Inventory(), Source, Data.Get());
        }
    };
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryActionIndependentSourceTest, "IntroCpp.Actions.Inventory.IndependentSourceAndDuplicate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FInventoryActionIndependentSourceTest::RunTest(const FString& Parameters)
{
    InventoryActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native player fixture"), Fixture.Character)) return false;
    Fixture.Inventory().SetItemAt(0, FItemInstance(Fixture.Data->ItemID, 7));
    FActionItemReservation Source;
    if (!TestTrue(TEXT("Reserve original quickslot"), Fixture.Reserve(true, 2, Source))) return false;
    const auto Result = Fixture.Commit(Source);
    TestTrue(TEXT("Heal reported applied"), Result.bApplied);
    TestTrue(TEXT("Consumption committed"), Result.IsCommitted());
    TestEqual(TEXT("Exactly one item consumed"), Result.ConsumedQuantity, 1);
    TestEqual(TEXT("Quickslot source decreased"), Fixture.Inventory().GetQuickSlot(0).Quantity, 1);
    TestEqual(TEXT("Same ID in backpack untouched"), Fixture.Inventory().GetItemAt(0).Quantity, 7);
    TestEqual(TEXT("Real heal effect applied"), Fixture.Attributes().GetCurrentHealth(), 55.f);
    TestFalse(TEXT("Duplicate reservation cannot commit again"), Fixture.Commit(Source).IsCommitted());
    TestEqual(TEXT("Duplicate has no additional heal"), Fixture.Attributes().GetCurrentHealth(), 55.f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryActionLastItemEventsTest, "IntroCpp.Actions.Inventory.LastItemAndConsistentEvents",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FInventoryActionLastItemEventsTest::RunTest(const FString& Parameters)
{
    InventoryActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native player fixture"), Fixture.Character)) return false;
    FActionItemReservation Source;
    if (!TestTrue(TEXT("Reserve last backpack item"), Fixture.Reserve(false, 1, Source))) return false;
    TStrongObjectPtr<UInventoryActionTestProbe> Probe(NewObject<UInventoryActionTestProbe>());
    Probe->Inventory = &Fixture.Inventory();
    Probe->bQuickSlot = false;
    Probe->ExpectedQuantity = 0;
    Fixture.Attributes().OnHealthChanged.AddDynamic(Probe.Get(), &UInventoryActionTestProbe::OnAttributeChanged);
    FName RemovedID;
    FName UsedID;
    int32 UsedCount = 0;
    Fixture.Inventory().OnItemRemoved.AddLambda([&](const FItemInstance& Item) { RemovedID = Item.ItemID; });
    Fixture.Inventory().OnItemUsed.AddLambda([&](const FItemInstance& Item) { UsedID = Item.ItemID; UsedCount += Item.Quantity; });
    const auto Result = Fixture.Commit(Source);
    TestTrue(TEXT("Last item committed"), Result.IsCommitted());
    TestTrue(TEXT("Last source slot is empty"), Fixture.Inventory().GetItemAt(0).IsEmpty());
    TestEqual(TEXT("Removed payload keeps original ID"), RemovedID, Fixture.Data->ItemID);
    TestEqual(TEXT("Used payload keeps original ID"), UsedID, Fixture.Data->ItemID);
    TestEqual(TEXT("Used event emitted for one item"), UsedCount, 1);
    TestEqual(TEXT("One deferred health notification"), Probe->ChangedCount, 1);
    TestTrue(TEXT("Health listener sees committed source quantity"), Probe->bObservedCommittedQuantity);
    TestTrue(TEXT("Health listener cannot reenter inventory write"), Probe->bRejectedReentrantMutation);
    Fixture.Attributes().OnHealthChanged.RemoveDynamic(Probe.Get(), &UInventoryActionTestProbe::OnAttributeChanged);
    Fixture.Inventory().OnItemRemoved.Clear();
    Fixture.Inventory().OnItemUsed.Clear();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryActionFailureTest, "IntroCpp.Actions.Inventory.FailureDoesNotConsume",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FInventoryActionFailureTest::RunTest(const FString& Parameters)
{
    InventoryActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native player fixture"), Fixture.Character)) return false;
    FActionItemReservation Source;
    if (!TestTrue(TEXT("Reserve original source"), Fixture.Reserve(true, 2, Source))) return false;
    // Preflight must load all effects before the valid first heal runs.
    Fixture.Data->ItemActionClasses.Add(TSoftClassPtr<UItemAction>());
    TestFalse(TEXT("Missing effect fails preflight"), Fixture.Commit(Source).IsCommitted());
    TestEqual(TEXT("Preflight failure preserves HP"), Fixture.Attributes().GetCurrentHealth(), 30.f);
    TestEqual(TEXT("Preflight failure preserves quantity"), Fixture.Inventory().GetQuickSlot(0).Quantity, 2);
    Fixture.Data->ItemActionClasses.Reset();
    Fixture.Data->ItemActionClasses.Add(UInventoryActionTestNoEffect::StaticClass());
    const auto NoEffect = Fixture.Commit(Source);
    TestFalse(TEXT("All effects false reports no application"), NoEffect.bApplied);
    TestFalse(TEXT("All effects false does not consume"), NoEffect.IsCommitted());
    TestEqual(TEXT("No-effect failure preserves quantity"), Fixture.Inventory().GetQuickSlot(0).Quantity, 2);
    Fixture.Data->ItemActionClasses.Reset();
    Fixture.Data->ItemActionClasses.Add(UItemAction_Heal::StaticClass());
    Fixture.Inventory().SetQuickSlot(0, FItemInstance(Fixture.Data->ItemID, 4));
    TestFalse(TEXT("Changed source invalidates reservation"), Fixture.Commit(Source).IsCommitted());
    TestEqual(TEXT("Stale source has no effect"), Fixture.Attributes().GetCurrentHealth(), 30.f);
    TestEqual(TEXT("Stale source preserves replacement stack"), Fixture.Inventory().GetQuickSlot(0).Quantity, 4);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryActionPartialEffectsTest, "IntroCpp.Actions.Inventory.PartialEffectsConsumeOnce",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FInventoryActionPartialEffectsTest::RunTest(const FString& Parameters)
{
    InventoryActionTests::FFixture Fixture;
    if (!TestNotNull(TEXT("Native player fixture"), Fixture.Character)) return false;
    Fixture.Data->ItemActionClasses.Add(UInventoryActionTestNoEffect::StaticClass());
    Fixture.Data->ItemActionClasses.Add(UItemAction_RestoreMana::StaticClass());
    FActionItemReservation Source;
    if (!TestTrue(TEXT("Reserve mixed-effect potion"), Fixture.Reserve(true, 3, Source))) return false;
    const auto Result = Fixture.Commit(Source);
    TestTrue(TEXT("Successful effects reported"), Result.bApplied);
    TestTrue(TEXT("Mixed success and failure reported partial"), Result.bPartial);
    TestEqual(TEXT("Two effects consume only once"), Result.ConsumedQuantity, 1);
    TestEqual(TEXT("Source reduced by one"), Fixture.Inventory().GetQuickSlot(0).Quantity, 2);
    TestEqual(TEXT("Real health effect applied"), Fixture.Attributes().GetCurrentHealth(), 55.f);
    TestEqual(TEXT("Real mana effect applied"), Fixture.Attributes().GetCurrentMana(), 22.f);
    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
