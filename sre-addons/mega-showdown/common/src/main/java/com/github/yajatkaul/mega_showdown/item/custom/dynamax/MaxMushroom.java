package com.github.yajatkaul.mega_showdown.item.custom.dynamax;

import com.cobblemon.mod.common.api.battles.model.PokemonBattle;
import com.cobblemon.mod.common.api.battles.model.actor.BattleActor;
import com.cobblemon.mod.common.api.item.HealingSource;
import com.cobblemon.mod.common.api.pokemon.stats.Stats;
import com.cobblemon.mod.common.battles.BattleRegistry;
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon;
import com.cobblemon.mod.common.item.battle.BagItem;
import com.github.yajatkaul.mega_showdown.item.custom.ToolTipBlockItem;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public class MaxMushroom extends ToolTipBlockItem implements HealingSource {
    private final BagItem bagItem = new BagItem() {
        @Override
        public @NotNull String getItemName() {
            return "item.mega_showdown.max_mushroom";
        }

        @Override
        public @NotNull Item getReturnItem() {
            return Items.AIR;
        }

        @Override
        public boolean canUse(@NotNull ItemStack stack, @NotNull PokemonBattle battle, @NotNull BattlePokemon target) {
            return target.getHealth() > 0;
        }

        @Override
        public @NotNull String getShowdownInput(@NotNull BattleActor actor, @NotNull BattlePokemon battlePokemon, @Nullable String data) {
            battlePokemon.getEffectedPokemon().incrementFriendship(1, false);
            return "max_mushroom " + Stats.ATTACK.getShowdownId() + " " + Stats.DEFENCE.getShowdownId()
                    + " " + Stats.SPECIAL_ATTACK.getShowdownId() + " " + Stats.SPECIAL_DEFENCE.getShowdownId()
                    + " " + Stats.SPEED.getShowdownId() + " 1";
        }
    };

    public MaxMushroom(Block block, Properties settings) {
        super(block, settings);
    }

    @Override
    public @NotNull InteractionResultHolder<ItemStack> use(@NotNull Level world, @NotNull Player user, @NotNull InteractionHand hand) {
        if (!(world instanceof ServerLevel)) {
            return InteractionResultHolder.pass(user.getItemInHand(hand));
        }

        ServerPlayer player = (ServerPlayer) user;
        ItemStack stack = user.getItemInHand(hand);
        PokemonBattle battle = BattleRegistry.getBattleByParticipatingPlayer(player);
        if (battle != null) {
            if (!DynamaxBagItemHelper.tryUseInBattle(player, stack, battle, bagItem, bp -> bp.getHealth() > 0, true)) {
                return InteractionResultHolder.consume(stack);
            }
            return InteractionResultHolder.success(stack);
        }
        return super.use(world, user, hand);
    }

    @Override
    public @NotNull InteractionResult useOn(@NotNull UseOnContext context) {
        Player player = context.getPlayer();
        ItemStack stack = context.getItemInHand();

        if (player instanceof ServerPlayer serverPlayer) {
            PokemonBattle battle = BattleRegistry.getBattleByParticipatingPlayer(serverPlayer);
            if (battle != null) {
                if (!DynamaxBagItemHelper.tryUseInBattle(serverPlayer, stack, battle, bagItem, bp -> bp.getHealth() > 0, false)) {
                    return InteractionResult.PASS;
                }
                return InteractionResult.SUCCESS;
            }
        }
        return super.useOn(context);
    }
}
