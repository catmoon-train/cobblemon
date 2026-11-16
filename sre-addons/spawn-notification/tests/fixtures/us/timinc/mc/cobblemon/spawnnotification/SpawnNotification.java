package us.timinc.mc.cobblemon.spawnnotification;
import net.fabricmc.api.ModInitializer;

// 验证完整环境确实调用实现入口，而不是静默跳过。这里不模拟 Cobblemon 玩法。
public final class SpawnNotification implements ModInitializer {
    public static final SpawnNotification INSTANCE = new SpawnNotification();
    public static int calls;
    public static boolean fail;
    @Override public void onInitialize() {
        calls++;
        if (fail) throw new IllegalStateException("expected test failure");
    }
}
