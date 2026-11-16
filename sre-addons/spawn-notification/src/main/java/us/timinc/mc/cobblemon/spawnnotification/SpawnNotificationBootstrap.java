package us.timinc.mc.cobblemon.spawnnotification;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.metadata.CustomValue;

/** 只在完整 Cobblemon 环境中加载玩法实现；本类不得引用 Minecraft 或 Cobblemon 类型。 */
public final class SpawnNotificationBootstrap implements ModInitializer {
    @Override
    public void onInitialize() {
        var container = FabricLoader.getInstance().getModContainer("cobblemon");
        if (container.isEmpty()) {
            throw new IllegalStateException("Spawn Notification requires Cobblemon 1.8.4");
        }
        var variant = container.get().getMetadata().getCustomValue("train:variant");
        if (variant != null && variant.getType() == CustomValue.CvType.STRING
                && "registry-only-shell".equals(variant.getAsString())) {
            System.getLogger("spawn_notification").log(System.Logger.Level.INFO,
                    "Registry-only Cobblemon shell: Spawn Notification gameplay is disabled.");
            return;
        }
        // 使用字符串隔离类加载：空壳不会解析 Kotlin 实现，也不会读取配置、创建音效或订阅事件。
        try {
            Class<?> implementation = Class.forName(
                    "us.timinc.mc.cobblemon.spawnnotification.SpawnNotification",
                    true, SpawnNotificationBootstrap.class.getClassLoader());
            ((ModInitializer) implementation.getField("INSTANCE").get(null)).onInitialize();
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Unable to initialize Spawn Notification for Cobblemon 1.8.4", e);
        }
    }
}
