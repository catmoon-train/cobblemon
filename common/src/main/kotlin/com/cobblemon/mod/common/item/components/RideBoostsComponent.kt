/*
 * Copyright (C) 2023 Cobblemon Contributors
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

package com.cobblemon.mod.common.item.components

import com.cobblemon.mod.common.CobblemonMechanics
import com.cobblemon.mod.common.api.riding.stats.RidingStat
import com.cobblemon.mod.common.client.pot.CookingQuality
import com.mojang.serialization.Codec
import com.mojang.serialization.codecs.RecordCodecBuilder
import io.netty.buffer.ByteBuf
import net.minecraft.network.codec.ByteBufCodecs
import net.minecraft.network.codec.StreamCodec

/**
 * Put on aprijuice after cooking, gives boosts to riding stats when used on a Pokémon.
 *
 * @author Hiroku
 * @since November 7th, 2025
 */
class RideBoostsComponent(
    val boosts: Map<RidingStat, Int>
) {
    companion object {
        val CODEC: Codec<RideBoostsComponent> = RecordCodecBuilder.create { builder ->
            builder.group(
                Codec.unboundedMap(Codec.STRING, Codec.INT).fieldOf("boosts").forGetter { it.boosts.mapKeys { it.key.name } }
            ).apply(builder) { map -> RideBoostsComponent(map.mapKeys { RidingStat.valueOf(it.key) }) }
        }

        val PACKET_CODEC: StreamCodec<ByteBuf, RideBoostsComponent> = ByteBufCodecs.fromCodec(CODEC)

        private val DEFAULT_QUALITY_THRESHOLDS = mapOf(
            -999 to CookingQuality.LOW,
            4 to CookingQuality.MEDIUM,
            8 to CookingQuality.HIGH
        )
    }

    fun getQuality(): CookingQuality {
        val thresholds = CobblemonMechanics.aprijuices.cookingQualityPointThresholds
            .ifEmpty { DEFAULT_QUALITY_THRESHOLDS }
        val totalPoints = boosts.values.sum()
        return thresholds.filter { totalPoints >= it.key }.maxOfOrNull { it.value } ?: CookingQuality.LOW
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is RideBoostsComponent) return false
        return boosts == other.boosts
    }

    override fun hashCode(): Int {
        return boosts.hashCode()
    }
}