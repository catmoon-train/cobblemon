package train.cobblemon.shell;

import net.fabricmc.api.ModInitializer;

/** Cobblemon 列车服务端空壳入口：委托中间注册层回放 Cobblemon 静态注册表。 */
public final class RegistryShell implements ModInitializer {
    @Override
    public void onInitialize() {
        RegistryReplayEngine.replayResource(RegistryShell.class, "/train-shell-registries.json", "COBBLEMON_REGISTRY_SHELL_READY");
    }
}
