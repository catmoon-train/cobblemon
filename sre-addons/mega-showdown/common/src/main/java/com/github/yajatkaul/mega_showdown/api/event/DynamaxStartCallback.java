package com.github.yajatkaul.mega_showdown.api.event;

import com.cobblemon.mod.common.api.battles.model.PokemonBattle;
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.EventFactory;

public interface DynamaxStartCallback {
    Event<DynamaxStartCallback> EVENT = EventFactory.createArrayBacked(
            DynamaxStartCallback.class,
            listeners -> (battle, pokemon, gmax) -> {
                for (DynamaxStartCallback listener : listeners) {
                    listener.onDynamaxStart(battle, pokemon, gmax);
                }
            }
    );

    void onDynamaxStart(PokemonBattle battle, BattlePokemon pokemon, Boolean gmax);
}
