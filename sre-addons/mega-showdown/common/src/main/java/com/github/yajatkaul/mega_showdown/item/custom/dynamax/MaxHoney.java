package com.github.yajatkaul.mega_showdown.item.custom.dynamax;

import com.cobblemon.mod.common.advancement.CobblemonCriteria;
import com.cobblemon.mod.common.advancement.criterion.PokemonInteractContext;
import com.cobblemon.mod.common.api.battles.model.PokemonBattle;
import com.cobblemon.mod.common.api.battles.model.actor.BattleActor;
import com.cobblemon.mod.common.api.callback.PartySelectCallbacks;
import com.cobblemon.mod.common.api.events.CobblemonEvents;
import com.cobblemon.mod.common.api.events.pokemon.healing.PokemonHealedEvent;
import com.cobblemon.mod.common.api.item.HealingSource;
import com.cobblemon.mod.common.battles.BattleRegistry;
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon;
import com.cobblemon.mod.common.item.battle.BagItem;
import com.cobblemon.mod.common.pokemon.Pokemon;
import com.cobblemon.mod.common.util.ItemStackExtensionsKt;
import com.cobblemon.mod.common.util.PlayerExtensionsKt;
import com.github.yajatkaul.mega_showdown.item.custom.ToolTipItem;
import kotlin.Unit;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

public class MaxHoney extends ToolTipItem implements HealingSource {
    private final BagItem bagItem = new BagItem() {
        @Override
        public @NotNull String getItemName() {
            return "item.mega_showdown.max_honey";
        }

        @Override
        public @NotNull Item getReturnItem() {
            return Items.AIR;
        }

        @Override
        public boolean canUse(@NotNull ItemStack stack, @NotNull PokemonBattle battle, @NotNull BattlePokemon target) {
            return target.getHealth() <= 0;
        }

        @Override
        public @NotNull String getShowdownInput(@NotNull BattleActor actor, @NotNull BattlePokemon battlePokemon, @Nullable String data) {
            return "max_honey";
        }
    };

    public MaxHoney(Properties properties) {
        super(properties);
    }

    public BagItem getBagItem() {
        return bagItem;
    }

    @Override
    public @NotNull InteractionResultHolder<ItemStack> use(@NotNull Level world, @NotNull Player user, @NotNull InteractionHand hand) {
        ItemStack stack = user.getItemInHand(hand);
        if (!(world instanceof ServerLevel)) {
            return InteractionResultHolder.success(stack);
        }

        ServerPlayer player = (ServerPlayer) user;
        PokemonBattle battle = BattleRegistry.getBattleByParticipatingPlayer(player);
        if (battle != null) {
            if (!DynamaxBagItemHelper.tryUseInBattle(player, stack, battle, bagItem, bp -> bp.getHealth() <= 0, true)) {
                return InteractionResultHolder.consume(stack);
            }
            return InteractionResultHolder.success(stack);
        }

        List<Pokemon> pokemonList = new ArrayList<>();
        PlayerExtensionsKt.party(player).forEach(pokemonList::add);
        PartySelectCallbacks.INSTANCE.createFromPokemon(
                player,
                pokemonList,
                Pokemon::isFainted,
                pk -> {
                    if (pk.isFainted() && !PlayerExtensionsKt.isInBattle(player) && ItemStackExtensionsKt.isHeld(stack, player)) {
                        int amount = pk.getMaxHealth();
                        CobblemonEvents.POKEMON_HEALED.postThen(
                                new PokemonHealedEvent(pk, amount, this),
                                canceled -> Unit.INSTANCE,
                                event -> {
                                    pk.setCurrentHealth(event.getAmount());
                                    ResourceLocation stackName = BuiltInRegistries.ITEM.getKey(stack.getItem());
                                    if (!player.isCreative()) {
                                        stack.shrink(1);
                                    }
                                    CobblemonCriteria.POKEMON_INTERACT.trigger(
                                            player,
                                            new PokemonInteractContext(pk.getSpecies().resourceIdentifier, stackName)
                                    );
                                    return Unit.INSTANCE;
                                }
                        );
                    }
                    return Unit.INSTANCE;
                }
        );
        return InteractionResultHolder.success(stack);
    }
}
