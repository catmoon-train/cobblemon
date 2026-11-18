package com.github.yajatkaul.mega_showdown.networking.server.handler;

import com.cobblemon.mod.common.pokemon.Pokemon;
import com.github.yajatkaul.mega_showdown.gimmick.PrimalGimmick;
import com.github.yajatkaul.mega_showdown.networking.server.packet.PrimalEvoPacket;
import com.github.yajatkaul.mega_showdown.utils.PlayerUtils;
import net.minecraft.server.level.ServerPlayer;

public class PrimalEvoHandler {
    public static void handle(PrimalEvoPacket packet, ServerPlayer player) {
        Pokemon pokemon = PlayerUtils.getPartyPokemonFromUUID(player, packet.pokemonId());

        if (pokemon != null) {
            PrimalGimmick.primalToggle(pokemon);
        }
    }
}
