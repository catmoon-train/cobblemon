package com.github.yajatkaul.mega_showdown.utils;

import com.cobblemon.mod.common.entity.pokemon.PokemonEntity;
import com.cobblemon.mod.common.net.messages.client.animation.PlayPosableAnimationPacket;
import com.cobblemon.mod.common.net.messages.client.effect.SpawnSnowstormEntityParticlePacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Set;

public final class PokemonBehaviourHelper {
    public static final Companion Companion = new Companion();

    private PokemonBehaviourHelper() {
    }

    public static final class Companion {
        private Companion() {
        }

        public void playAnimation(Entity pokemon, Set<String> animations, List<String> expressions) {
            PlayPosableAnimationPacket packet = new PlayPosableAnimationPacket(pokemon.getId(), animations, expressions);
            packet.sendToPlayersAround(
                    pokemon.getX(),
                    pokemon.getY(),
                    pokemon.getZ(),
                    128.0,
                    pokemon.level().dimension(),
                    player -> false
            );
        }

        public void playAnimation(Entity pokemon, Set<String> animations) {
            playAnimation(pokemon, animations, List.of());
        }

        public void snowStormPartileSpawner(
                PokemonEntity entity,
                ResourceLocation particleId,
                @Nullable List<String> source,
                @Nullable PokemonEntity targetEntity,
                @Nullable List<String> target
        ) {
            SpawnSnowstormEntityParticlePacket packet = new SpawnSnowstormEntityParticlePacket(
                    particleId,
                    entity.getId(),
                    source != null ? source : List.of(),
                    targetEntity != null ? targetEntity.getId() : null,
                    target
            );
            packet.sendToPlayersAround(
                    entity.getX(),
                    entity.getY(),
                    entity.getZ(),
                    64.0,
                    entity.level().dimension(),
                    player -> false
            );
        }
    }
}
