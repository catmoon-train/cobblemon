package com.github.yajatkaul.mega_showdown.api.event;

import com.cobblemon.mod.common.api.battles.model.PokemonBattle;
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.EventFactory;

public interface DynamaxEndCallback {
    Event<DynamaxEndCallback> EVENT = EventFactory.createArrayBacked(
            DynamaxEndCallback.class,
            listeners -> (battle, pokemon) -> {
                for (DynamaxEndCallback listener : listeners) {
                    listener.onDynamaxEnd(battle, pokemon);
                }
            }
    );

    void onDynamaxEnd(PokemonBattle battle, BattlePokemon pokemon);
}
