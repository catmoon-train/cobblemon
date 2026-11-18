package com.github.yajatkaul.mega_showdown.cobblemon.status;

import com.cobblemon.mod.common.pokemon.Pokemon;
import com.cobblemon.mod.common.pokemon.status.PersistentStatus;
import kotlin.random.Random;
import kotlin.ranges.IntRange;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import org.jetbrains.annotations.NotNull;

public class DamageStatus extends PersistentStatus {
    private final int chance;
    private final double damagePercent;
    private final String healingAbility;

    public DamageStatus(
            @NotNull ResourceLocation name,
            @NotNull String showdownName,
            @NotNull String applyMessage,
            @NotNull String removeMessage,
            @NotNull IntRange defaultDuration,
            int chance,
            double damagePercent,
            @NotNull String healingAbility
    ) {
        super(name, showdownName, applyMessage, removeMessage, defaultDuration);
        this.chance = chance;
        this.damagePercent = damagePercent;
        this.healingAbility = healingAbility;
    }

    @Override
    public void onSecondPassed(@NotNull ServerPlayer player, @NotNull Pokemon pokemon, @NotNull Random random) {
        // 1 in x chance to damage y% of their HP with a minimum of 1
        if (!pokemon.isFainted() && random.nextInt(chance) == 0) {
            int delta = Math.max(1, (int) Math.round(pokemon.getMaxHealth() * damagePercent));
            int sign = pokemon.getAbility().getTemplate().getName().equals(healingAbility) ? -1 : 1;
            pokemon.setCurrentHealth(pokemon.getCurrentHealth() - delta * sign);
            // Only way that's happened is if the Pokémon has z heal
            if (pokemon.getCurrentHealth() == pokemon.getMaxHealth()) {
                pokemon.setStatus(null);
            }
        }
    }
}
