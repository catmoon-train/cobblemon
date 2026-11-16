/*
 * Copyright (C) 2026 Cobblemon Contributors
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
package com.cobblemon.mod.common.api.riding

import com.bedrockk.molang.Expression
import com.cobblemon.mod.common.Cobblemon
import com.cobblemon.mod.common.CobblemonRideSettings
import com.cobblemon.mod.common.api.pokemon.PokemonSpecies
import com.cobblemon.mod.common.api.riding.behaviour.RidingBehaviourSettings
import com.cobblemon.mod.common.api.riding.sound.RideSoundSettingsList
import com.cobblemon.mod.common.platform.events.PlatformEvents
import com.cobblemon.mod.common.pokemon.FormData
import com.cobblemon.mod.common.util.getString
import com.google.gson.JsonElement
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.google.gson.JsonPrimitive
import com.google.gson.JsonSerializer
import net.minecraft.world.level.storage.LevelResource
import java.nio.file.Files
import java.nio.file.Path
import java.util.Locale

/** Read-only, server-authoritative conversion into the existing species/seat/settings sync. */
object LegacyRidingConfig {
    private var worldRoot: Path? = null
    private val originals = mutableMapOf<FormData, RidingProperties?>()

    // The native species Gson has read-only adapters for these two types. Supply serializers only;
    // deserialization still delegates to its original adapters. Never serialize MoLang implementation fields.
    private val gson by lazy {
        PokemonSpecies.gson.newBuilder()
            .registerTypeHierarchyAdapter(Expression::class.java, JsonSerializer<Expression> { value, _, _ ->
                JsonPrimitive(value.getString())
            })
            .registerTypeAdapter(RideSoundSettingsList::class.java, JsonSerializer<RideSoundSettingsList> { value, _, context ->
                context.serialize(value.sounds)
            })
            .create()
    }

    internal fun initialize() {
        PlatformEvents.SERVER_STARTING.subscribe {
            worldRoot = it.server.getWorldPath(LevelResource.ROOT)
            applyToSpecies()
        }
        PlatformEvents.SERVER_STOPPED.subscribe {
            restoreOriginals()
            worldRoot = null
        }
    }

    private fun restoreOriginals() {
        originals.forEach { (form, properties) -> form.ridingOverride = properties }
        originals.clear()
    }

    /** Also called after fresh species additions on /reload, before native registry synchronization. */
    internal fun applyToSpecies() {
        val file = worldRoot?.resolve("pokemonRideConfig.json") ?: return
        restoreOriginals()
        if (!Files.isRegularFile(file)) return // No generated file, no overwrite, no implicit legacy whitelist.
        try {
            require(Files.size(file) <= 1024 * 1024) { "file exceeds 1 MiB" }
            val root = Files.newBufferedReader(file, Charsets.UTF_8).use { JsonParser.parseReader(it).asJsonObject }
            root.get("mustAllowEntityRiding")?.let {
                require(it.isJsonPrimitive && it.asJsonPrimitive.isBoolean) { "mustAllowEntityRiding must be boolean" }
                if (it.asBoolean) Cobblemon.LOGGER.warn("pokemonRideConfig.json: mustAllowEntityRiding is not enabled; native player seats remain available")
            }
            val entries = root.get("pokemonTypes")
            require(entries != null && entries.isJsonObject) { "pokemonTypes must be an object" }
            require(entries.asJsonObject.size() <= 1024) { "more than 1024 species entries" }
            val targets = mutableSetOf<FormData>()
            entries.asJsonObject.entrySet().forEach { (name, value) ->
                try {
                    val config = parseEntry(value)
                    val canonical = name.lowercase(Locale.ROOT).let { if (it == "espahtla") "espathra" else it }
                    val species = PokemonSpecies.species.firstOrNull {
                        it.name.equals(canonical, ignoreCase = true) || it.resourceIdentifier.toString().equals(canonical, ignoreCase = true) ||
                            (it.resourceIdentifier.namespace == Cobblemon.MODID && it.resourceIdentifier.path == canonical)
                    } ?: error("unknown species")
                    val form = if (config.formName in setOf("none", "normal", "base")) species.standardForm
                        else species.forms.firstOrNull { it.name.equals(config.formName, ignoreCase = true) }
                            ?: error("unknown form '${config.formName}'")
                    require(form !in targets) { "duplicate species/form target (including aliases)" }
                    // Construct everything first: malformed entries never partially replace seats or settings.
                    val converted = convert(form.riding, config)
                    originals[form] = form.ridingOverride
                    form.ridingOverride = converted
                    targets.add(form)
                } catch (e: Exception) {
                    Cobblemon.LOGGER.warn("pokemonRideConfig.json: skipping '{}': {}", name, e.message)
                }
            }
            Cobblemon.LOGGER.info("Imported {} native riding form overrides from {} (original file unchanged)", targets.size, file)
        } catch (e: Exception) {
            Cobblemon.LOGGER.warn("Cannot import {}: {}. Native riding data retained.", file, e.message)
        }
    }

    internal data class Entry(
        val formName: String,
        val mountTypes: Set<String>,
        val speed: Double,
        val stamina: Int,
        val driverOffset: SeatOffset?,
        val passengerOffsets: List<SeatOffset>?
    )

    internal fun parseEntry(value: JsonElement): Entry {
        require(value.isJsonObject) { "entry must be an object" }
        val data = value.asJsonObject
        val types = data.get("mountType")
        require(types != null && types.isJsonArray && types.asJsonArray.size() in 1..4) { "mountType must contain 1..4 types" }
        val mountTypes = types.asJsonArray.map {
            require(it.isJsonPrimitive && it.asJsonPrimitive.isString) { "mountType must contain strings" }
            it.asString.uppercase(Locale.ROOT).also { name ->
                require(name in setOf("WALK", "FLY", "SWIM", "LAVA_SWIM")) { "unknown mountType '$name'" }
            }
        }.toSet()
        val form = data.get("formName")?.takeUnless { it.isJsonNull }?.let {
            require(it.isJsonPrimitive && it.asJsonPrimitive.isString) { "formName must be a string or null" }
            it.asString.lowercase(Locale.ROOT)
        } ?: "none"
        val speed = data.get("speedModifier")?.let { number(it, 0.05, 4.0, "speedModifier") } ?: 1.0
        val stamina = data.get("stamina")?.let {
            val n = number(it, 0.0, 72000.0, "stamina")
            require(n % 1.0 == 0.0) { "stamina must be an integer" }
            n.toInt()
        } ?: 0
        val driver = data.get("ridingOffSet")?.let { offset(it) }
        val passengers = data.get("passengersOffSet")?.let {
            require(it.isJsonArray && it.asJsonArray.size() <= 7) { "at most 7 passenger offsets are allowed" }
            it.asJsonArray.map(::offset)
        }
        return Entry(form, mountTypes, speed, stamina, driver, passengers)
    }

    private fun number(value: JsonElement, min: Double, max: Double, field: String): Double {
        require(value.isJsonPrimitive && value.asJsonPrimitive.isNumber) { "$field must be a number" }
        val n = value.asDouble
        require(n.isFinite() && n in min..max) { "$field must be finite and within $min..$max" }
        return n
    }

    private fun offset(value: JsonElement): SeatOffset {
        require(value.isJsonArray && value.asJsonArray.size() == 3) { "offset must have exactly 3 coordinates" }
        val xyz = value.asJsonArray.map { number(it, -16.0, 16.0, "offset") }
        // Legacy order is [Z, Y, X] in world-block units, NOT model pixels. Convert exactly once.
        return SeatOffset(xyz[2], xyz[1], xyz[0])
    }

    private fun nativeDefaults(settings: RidingBehaviourSettings): RidingBehaviourSettings? = with(CobblemonRideSettings) {
        listOf(horse, bird, hover, boat, submarine, dolphin, rocket, jet, minekart, vehicle, glider, helicopter, burst)
            .firstOrNull { it.key == settings.key }
    }

    internal fun convert(original: RidingProperties, config: Entry): RidingProperties {
        val behaviours = original.behaviours.orEmpty().toMutableMap()
        val requested = mutableMapOf<RidingStyle, String>()
        if ("WALK" in config.mountTypes) requested[RidingStyle.LAND] = "cobblemon:land/horse"
        if ("FLY" in config.mountTypes) requested[RidingStyle.AIR] = "cobblemon:air/hover"
        if ("SWIM" in config.mountTypes || "LAVA_SWIM" in config.mountTypes) requested[RidingStyle.LIQUID] = "cobblemon:liquid/submarine"
        requested.forEach { (style, key) ->
            // Keep native flight styles and additional modes; explicit old SWIM gets real diving, not a surface boat.
            if (style !in behaviours || style == RidingStyle.LIQUID) {
                val current = behaviours[style]
                // An existing submarine already has compatible units: preserve all its per-species settings.
                val json = (if (current?.key?.toString() == key) gson.toJsonTree(current).asJsonObject else JsonObject()).apply {
                    addProperty("key", key)
                    add("stats", gson.toJsonTree(behaviours[style]?.stats ?: mapOf(
                        com.cobblemon.mod.common.api.riding.stats.RidingStat.SPEED to 20..60,
                        com.cobblemon.mod.common.api.riding.stats.RidingStat.ACCELERATION to 20..60,
                        com.cobblemon.mod.common.api.riding.stats.RidingStat.SKILL to 20..60,
                        com.cobblemon.mod.common.api.riding.stats.RidingStat.JUMP to 20..60,
                        com.cobblemon.mod.common.api.riding.stats.RidingStat.STAMINA to 20..60
                    )))
                    behaviours[style]?.let { add("rideSounds", gson.toJsonTree(it).asJsonObject.get("rideSounds")) }
                    if (style == RidingStyle.LIQUID) addProperty("legacyFluid", when {
                        "SWIM" in config.mountTypes && "LAVA_SWIM" in config.mountTypes -> "both"
                        "LAVA_SWIM" in config.mountTypes -> "lava"
                        else -> "water"
                    })
                }
                behaviours[style] = gson.fromJson(json, RidingBehaviourSettings::class.java)
            }
        }
        val converted = behaviours.mapValues { (_, settings) ->
            // Default old speed=1 and stamina=0/200 are compatibility sentinels: keep native balance.
            if (config.speed == 1.0 && config.stamina in setOf(0, 200)) return@mapValues settings
            val json = gson.toJsonTree(settings).asJsonObject
            val defaults = nativeDefaults(settings)?.let { gson.toJsonTree(it).asJsonObject }
            if (config.speed != 1.0) {
                val expression = json.get("speedExpr") ?: defaults?.get("speedExpr")
                    ?: error("custom speed unsupported for native style ${settings.key}")
                json.addProperty("speedExpr", "(${expression.asString}) * ${config.speed}")
                if (settings.key.toString() == "cobblemon:land/horse") {
                    val oldMultiplier = json.get("walkSpeedMultiplier")?.asDouble ?: 1.0
                    json.addProperty("walkSpeedMultiplier", oldMultiplier * config.speed)
                }
            }
            if (config.stamina !in setOf(0, 200)) {
                require(json.has("staminaExpr") || defaults?.has("staminaExpr") == true) {
                    "custom stamina unsupported for native style ${settings.key}"
                }
                // This is native duration, NOT the old sprint-only policy or a 0..100 riding stat.
                json.addProperty("staminaExpr", (config.stamina / 20.0).toString())
            }
            gson.fromJson(json, RidingBehaviourSettings::class.java)
        }
        val seats = if (config.driverOffset != null || config.passengerOffsets != null) {
            listOf(config.driverOffset?.let { Seat(offset = it) } ?: original.seats.firstOrNull() ?: Seat(offset = SeatOffset(0.0, 1.0, 0.0))) +
                (config.passengerOffsets?.map { Seat(offset = it) } ?: original.seats.drop(1))
        } else original.seats.ifEmpty {
            listOf(Seat(offset = SeatOffset(0.0, 1.0, 0.0)), Seat(offset = SeatOffset(0.0, 1.0, -0.75)))
        }
        return RidingProperties(seats, original.conditions, converted)
    }
}
