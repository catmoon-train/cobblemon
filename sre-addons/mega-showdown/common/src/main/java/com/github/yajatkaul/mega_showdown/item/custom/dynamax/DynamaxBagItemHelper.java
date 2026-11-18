package com.github.yajatkaul.mega_showdown.item.custom.dynamax;

import com.cobblemon.mod.common.CobblemonSounds;
import com.cobblemon.mod.common.advancement.CobblemonCriteria;
import com.cobblemon.mod.common.advancement.criterion.PokemonInteractContext;
import com.cobblemon.mod.common.api.battles.model.PokemonBattle;
import com.cobblemon.mod.common.api.battles.model.actor.BattleActor;
import com.cobblemon.mod.common.api.callback.PartySelectCallbacks;
import com.cobblemon.mod.common.api.text.TextKt;
import com.cobblemon.mod.common.battles.BagItemActionResponse;
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon;
import com.cobblemon.mod.common.item.battle.BagItem;
import com.cobblemon.mod.common.util.ItemStackExtensionsKt;
import com.cobblemon.mod.common.util.LocalizationUtilsKt;
import kotlin.Unit;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import java.util.function.Predicate;

final class DynamaxBagItemHelper {
    private DynamaxBagItemHelper() {
    }

    static boolean tryUseInBattle(
            ServerPlayer player,
            ItemStack stack,
            PokemonBattle battle,
            BagItem bagItem,
            Predicate<BattlePokemon> targetStillValid,
            boolean actionBarWarning
    ) {
        BattleActor actor = battle.getActor(player);
        if (actor == null) {
            return false;
        }
        if (!actor.canFitForcedAction()) {
            player.sendSystemMessage(TextKt.red(LocalizationUtilsKt.battleLang("bagitem.cannot")), actionBarWarning);
            return false;
        }
        int turn = battle.getTurn();
        PartySelectCallbacks.INSTANCE.createBattleSelect(
                player,
                actor.getPokemonList(),
                bp -> bagItem.canUse(stack, battle, bp),
                bp -> {
                    if (actor.canFitForcedAction()
                            && targetStillValid.test(bp)
                            && battle.getTurn() == turn
                            && ItemStackExtensionsKt.isHeld(stack, player)) {
                        player.playSound(CobblemonSounds.ITEM_USE, 1F, 1F);
                        actor.forceChoose(new BagItemActionResponse(bagItem, bp, bp.getUuid().toString()));
                        ResourceLocation stackName = BuiltInRegistries.ITEM.getKey(stack.getItem());
                        stack.consume(1, player);
                        CobblemonCriteria.POKEMON_INTERACT.trigger(
                                player,
                                new PokemonInteractContext(bp.getEffectedPokemon().getSpecies().resourceIdentifier, stackName)
                        );
                    }
                    return Unit.INSTANCE;
                }
        );
        return true;
    }
}
