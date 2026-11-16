package us.timinc.mc.cobblemon.spawnnotification.events

import com.cobblemon.mod.common.api.events.entity.SpawnEvent
import com.cobblemon.mod.common.api.spawning.spawner.PlayerSpawner
import com.cobblemon.mod.common.entity.pokemon.PokemonEntity
import net.minecraft.server.level.ServerPlayer
import us.timinc.mc.cobblemon.spawnnotification.SpawnNotification.config
import us.timinc.mc.cobblemon.spawnnotification.broadcasters.SpawnBroadcaster
import us.timinc.mc.cobblemon.spawnnotification.util.Broadcast
import us.timinc.mc.cobblemon.spawnnotification.util.PlayerUtil.getValidPlayers

object BroadcastSpawn {
    fun handle(evt: SpawnEvent<PokemonEntity>) {
        val world = evt.spawnablePosition.world
        val pos = evt.spawnablePosition.position
        val pokemon = evt.entity.pokemon

        if (evt.isCanceled || world.isClientSide) return
        if (pokemon.isPlayerOwned()) return

        SpawnBroadcaster(
            evt.entity.pokemon,
            evt.spawner.spawnPool,
            evt.spawnablePosition.position,
            evt.spawnablePosition.biomeName,
            evt.spawnablePosition.world.dimension().location(),
            if (evt.spawnablePosition.spawner is PlayerSpawner) evt.cause.entity as? ServerPlayer else null
        ).getBroadcast()?.let { message ->
            if (config.announceCrossDimensions) {
                Broadcast.broadcastMessage(message)
            } else if (config.broadcastRangeEnabled) {
                Broadcast.broadcastMessage(getValidPlayers(world.dimension(), pos), message)
            } else {
                Broadcast.broadcastMessage(world, message)
            }
        }
    }
}