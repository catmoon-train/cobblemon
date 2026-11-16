import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Path;

public final class BootstrapIsolationTest {
    private static final String PREFIX = "us.timinc.mc.cobblemon.spawnnotification.";
    private static final class Isolated extends URLClassLoader {
        boolean forbidImplementation;
        Isolated(URL[] urls, boolean forbid) { super(urls, ClassLoader.getPlatformClassLoader()); forbidImplementation = forbid; }
        @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
            if (name.startsWith("com.cobblemon.") || name.startsWith("net.minecraft.")
                    || name.startsWith("kotlin.") || name.startsWith("net.fabricmc.fabric.")
                    || (forbidImplementation && name.equals(PREFIX + "SpawnNotification"))) {
                throw new AssertionError("Forbidden gameplay class load: " + name);
            }
            return super.loadClass(name, resolve);
        }
    }
    public static void main(String[] args) throws Exception {
        URL[] urls = {Path.of(args[0]).toUri().toURL(), Path.of(args[1]).toUri().toURL(), Path.of(args[2]).toUri().toURL()};
        // 使用真实的生产入口字节码；故意拒绝所有游戏、Kotlin 和玩法实现类。
        try (var cl = new Isolated(urls, true)) {
            Object entry = cl.loadClass(PREFIX + "SpawnNotificationBootstrap").getConstructor().newInstance();
            entry.getClass().getMethod("onInitialize").invoke(entry);
        }
        // 缺省、其他变体及非字符串值都必须走完整实现，且错误不能被吞掉。
        for (String variant : new String[]{null, "full", "registry-only-shell"}) {
            try (var cl = new Isolated(urls, false)) {
                Class<?> state = cl.loadClass("net.fabricmc.loader.api.FabricLoader$State");
                state.getField("variant").set(null, variant);
                state.getField("stringType").setBoolean(null, !"registry-only-shell".equals(variant));
                Object entry = cl.loadClass(PREFIX + "SpawnNotificationBootstrap").getConstructor().newInstance();
                entry.getClass().getMethod("onInitialize").invoke(entry);
                Class<?> implementation = cl.loadClass(PREFIX + "SpawnNotification");
                if (implementation.getField("calls").getInt(null) != 1) throw new AssertionError("No full initialization");
                implementation.getField("fail").setBoolean(null, true);
                try {
                    entry.getClass().getMethod("onInitialize").invoke(entry);
                    throw new AssertionError("Full implementation failure was ignored");
                } catch (InvocationTargetException expected) {
                    if (!(expected.getCause() instanceof IllegalStateException)) throw expected;
                }
            }
        }
        System.out.println("BOOTSTRAP_ISOLATION_PASS (no Cobblemon/Minecraft/Kotlin/Fabric API classes available)");
    }
}
