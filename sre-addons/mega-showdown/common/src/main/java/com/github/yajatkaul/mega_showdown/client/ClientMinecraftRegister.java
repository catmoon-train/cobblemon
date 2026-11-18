package com.github.yajatkaul.mega_showdown.client;

import com.github.yajatkaul.mega_showdown.client.battle.hud.BattleHUD;
import com.github.yajatkaul.mega_showdown.config.MegaShowdownConfig;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;

public class ClientMinecraftRegister {
    public static void register() {
        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> MegaShowdownConfig.load());
        HudRenderCallback.EVENT.register(BattleHUD::hudCallback);
    }
}
