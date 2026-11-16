package net.fabricmc.loader.api;

import java.lang.reflect.Proxy;
import java.util.Optional;
import net.fabricmc.loader.api.metadata.CustomValue;
import net.fabricmc.loader.api.metadata.ModMetadata;

// 仅测试使用的 FabricLoader 替身；生产 JAR 不打包 tests/。
public interface FabricLoader {
    static FabricLoader getInstance() { return State.INSTANCE; }
    Optional<ModContainer> getModContainer(String id);

    final class State {
        public static String variant = "registry-only-shell";
        public static boolean stringType = true;
        private static final FabricLoader INSTANCE = id -> Optional.of(
            proxy(ModContainer.class, (p, m, a) -> {
                if (m.getName().equals("getMetadata")) return proxy(ModMetadata.class, (p2, m2, a2) -> {
                    if (!m2.getName().equals("getCustomValue")) throw new AssertionError(m2);
                    if (!a2[0].equals("train:variant")) throw new AssertionError(a2[0]);
                    if (variant == null) return null;
                    return proxy(CustomValue.class, (p3, m3, a3) -> switch (m3.getName()) {
                        case "getType" -> stringType ? CustomValue.CvType.STRING : CustomValue.CvType.OBJECT;
                        case "getAsString" -> {
                            if (!stringType) throw new AssertionError("Non-string metadata read as string");
                            yield variant;
                        }
                        default -> throw new AssertionError(m3);
                    });
                });
                throw new AssertionError(m);
            }));
        private static <T> T proxy(Class<T> type, java.lang.reflect.InvocationHandler handler) {
            return type.cast(Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, handler));
        }
    }
}
