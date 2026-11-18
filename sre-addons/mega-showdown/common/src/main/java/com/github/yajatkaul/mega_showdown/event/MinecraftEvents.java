package com.github.yajatkaul.mega_showdown.event;

import com.github.yajatkaul.mega_showdown.config.MegaShowdownConfig;
import com.github.yajatkaul.mega_showdown.datapack.MegaShowdownDatapackRegister;
import com.github.yajatkaul.mega_showdown.gimmick.MaxGimmick;
import com.github.yajatkaul.mega_showdown.networking.client.packet.ConfigSyncPacket;
import com.github.yajatkaul.mega_showdown.networking.client.packet.EffectivenessSyncPacket;
import com.github.yajatkaul.mega_showdown.utils.ShowdownItemsLoad;
import com.github.yajatkaul.mega_showdown.utils.TypeEffectivenessUtils;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerPlayer;

public class MinecraftEvents {
    public static void register() {
        ServerLifecycleEvents.SERVER_STARTING.register(minecraftServer -> {
            MegaShowdownDatapackRegister.registerShowdownDatapackItems(minecraftServer);
            ShowdownItemsLoad.load();
        });

        ServerTickEvents.START_SERVER_TICK.register(MaxGimmick::updateScalingAnimations);

        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayer player = handler.player;
            ServerPlayNetworking.send(player, new ConfigSyncPacket(MegaShowdownConfig.outSideMega, MegaShowdownConfig.outSideUltraBurst));
            ServerPlayNetworking.send(player, new EffectivenessSyncPacket(TypeEffectivenessUtils.typeChartMap));
        });
    }
}
