package com.github.yajatkaul.mega_showdown.networking.client.handler;

import com.github.yajatkaul.mega_showdown.config.MegaShowdownConfig;
import com.github.yajatkaul.mega_showdown.networking.client.packet.ConfigSyncPacket;

public class ConfigSyncHandler {
    public static void handle(ConfigSyncPacket packet) {
        MegaShowdownConfig.outSideMega = packet.outSideMega();
        MegaShowdownConfig.outSideUltraBurst = packet.outSideUltraBurst();
    }
}
