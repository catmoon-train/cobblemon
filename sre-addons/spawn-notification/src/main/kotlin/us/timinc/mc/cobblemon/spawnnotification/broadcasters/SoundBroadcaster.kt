package us.timinc.mc.cobblemon.spawnnotification.broadcasters

import net.minecraft.core.BlockPos
import net.minecraft.server.level.ServerLevel
import net.minecraft.server.level.ServerPlayer
import net.minecraft.sounds.SoundEvent
import net.minecraft.sounds.SoundSource
import net.minecraft.world.level.Level

class SoundBroadcaster(
    val level: Level,
    val pos: BlockPos,
    val sound: SoundEvent
) {
    fun playShinySound() {
        if (level !is ServerLevel) return
        val center = pos.center
        level.playSound(null, center.x, center.y, center.z, sound, SoundSource.NEUTRAL, 10f, 1f)
    }

    fun playShinySoundClient(player: ServerPlayer) {
        // ServerPlayer.playNotifySound 才会向指定玩家发包；Entity.playSound 会再次广播到世界。
        player.playNotifySound(sound, SoundSource.NEUTRAL, 10f, 1f)
    }
}
