package com.github.yajatkaul.mega_showdown.networking.client;

import com.github.yajatkaul.mega_showdown.api.lilycobble.networking.battle.BattleStatePacketS2C;
import com.github.yajatkaul.mega_showdown.client.battle.hud.BattleHUD;
import com.github.yajatkaul.mega_showdown.networking.client.handler.ConfigSyncHandler;
import com.github.yajatkaul.mega_showdown.networking.client.handler.EffectivenessSyncHandler;
import com.github.yajatkaul.mega_showdown.networking.client.handler.InteractionWheelHandler;
import com.github.yajatkaul.mega_showdown.networking.client.packet.ConfigSyncPacket;
import com.github.yajatkaul.mega_showdown.networking.client.packet.EffectivenessSyncPacket;
import com.github.yajatkaul.mega_showdown.networking.client.packet.InteractionWheelPacket;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

public class MegaShowdownNetworkHandlerClient {
    public static void register() {
        ClientPlayNetworking.registerGlobalReceiver(InteractionWheelPacket.TYPE, (packet, context) -> InteractionWheelHandler.handle(packet));
        ClientPlayNetworking.registerGlobalReceiver(ConfigSyncPacket.TYPE, (packet, context) -> ConfigSyncHandler.handle(packet));
        ClientPlayNetworking.registerGlobalReceiver(BattleStatePacketS2C.ID, BattleHUD::receivePacket);
        ClientPlayNetworking.registerGlobalReceiver(EffectivenessSyncPacket.TYPE, (packet, context) -> EffectivenessSyncHandler.handle(packet));
    }
}
