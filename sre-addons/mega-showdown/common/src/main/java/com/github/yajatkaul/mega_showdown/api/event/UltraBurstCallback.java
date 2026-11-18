package com.github.yajatkaul.mega_showdown.api.event;

import com.cobblemon.mod.common.api.battles.model.PokemonBattle;
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.EventFactory;

public interface UltraBurstCallback {
    Event<UltraBurstCallback> EVENT = EventFactory.createArrayBacked(
            UltraBurstCallback.class,
            listeners -> (battle, pokemon) -> {
                for (UltraBurstCallback listener : listeners) {
                    listener.onUltraBurst(battle, pokemon);
                }
            }
    );

    void onUltraBurst(PokemonBattle battle, BattlePokemon pokemon);
}
