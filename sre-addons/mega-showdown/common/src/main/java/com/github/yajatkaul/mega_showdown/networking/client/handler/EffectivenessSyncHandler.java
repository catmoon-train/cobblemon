package com.github.yajatkaul.mega_showdown.networking.client.handler;

import com.github.yajatkaul.mega_showdown.networking.client.packet.EffectivenessSyncPacket;
import com.github.yajatkaul.mega_showdown.utils.TypeEffectivenessUtils;

public class EffectivenessSyncHandler {
    public static void handle(EffectivenessSyncPacket packet) {
        TypeEffectivenessUtils.typeChartMap = packet.typeChart();
    }
}
