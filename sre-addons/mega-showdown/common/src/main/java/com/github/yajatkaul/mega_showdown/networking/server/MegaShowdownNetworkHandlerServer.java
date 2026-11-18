package com.github.yajatkaul.mega_showdown.networking.server;

import com.github.yajatkaul.mega_showdown.api.lilycobble.networking.battle.BattleStatePacketS2C;
import com.github.yajatkaul.mega_showdown.networking.client.packet.ConfigSyncPacket;
import com.github.yajatkaul.mega_showdown.networking.client.packet.EffectivenessSyncPacket;
import com.github.yajatkaul.mega_showdown.networking.client.packet.InteractionWheelPacket;
import com.github.yajatkaul.mega_showdown.networking.server.handler.*;
import com.github.yajatkaul.mega_showdown.networking.server.packet.*;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

public class MegaShowdownNetworkHandlerServer {
    public static void register() {
        registerPayloads();
        registerCommon();
    }

    public static void registerPayloads() {
        PayloadTypeRegistry.playS2C().register(InteractionWheelPacket.TYPE, InteractionWheelPacket.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(ConfigSyncPacket.TYPE, ConfigSyncPacket.STREAM_CODEC);
        PayloadTypeRegistry.playS2C().register(BattleStatePacketS2C.ID, BattleStatePacketS2C.PACKET_CODEC);
        PayloadTypeRegistry.playS2C().register(EffectivenessSyncPacket.TYPE, EffectivenessSyncPacket.STREAM_CODEC);

        PayloadTypeRegistry.playC2S().register(MegaEvoPacket.TYPE, MegaEvoPacket.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(PrimalEvoPacket.TYPE, PrimalEvoPacket.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(CrownPacket.TYPE, CrownPacket.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(UltraBurstPacket.TYPE, UltraBurstPacket.STREAM_CODEC);
        PayloadTypeRegistry.playC2S().register(SecretSwordMoveSwapPacket.TYPE, SecretSwordMoveSwapPacket.STREAM_CODEC);
    }

    public static void registerCommon() {
        ServerPlayNetworking.registerGlobalReceiver(MegaEvoPacket.TYPE, (packet, context) -> MegaEvoHandler.handle(packet, context.player()));
        ServerPlayNetworking.registerGlobalReceiver(PrimalEvoPacket.TYPE, (packet, context) -> PrimalEvoHandler.handle(packet, context.player()));
        ServerPlayNetworking.registerGlobalReceiver(CrownPacket.TYPE, (packet, context) -> CrownHandler.handle(packet, context.player()));
        ServerPlayNetworking.registerGlobalReceiver(UltraBurstPacket.TYPE, (packet, context) -> UltraBurstHandler.handle(packet, context.player()));
        ServerPlayNetworking.registerGlobalReceiver(SecretSwordMoveSwapPacket.TYPE, (packet, context) -> SecretSwordMoveSwapHandler.handle(packet, context.player()));
    }
}
