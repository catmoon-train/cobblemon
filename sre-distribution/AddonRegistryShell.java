package train.addons.shell.mega_showdown;

import net.fabricmc.api.ModInitializer;
import train.cobblemon.shell.RegistryReplayEngine;

/** 整合附属（Mega Showdown + Cobblenav + Spawn Notification）列车服务端空壳入口。 */
public final class AddonRegistryShell implements ModInitializer {
    @Override
    public void onInitialize() {
        RegistryReplayEngine.replayResource(
                AddonRegistryShell.class,
                "/train-shell-mega_showdown-registries.json",
                "MEGA_SHOWDOWN_REGISTRY_SHELL_READY"
        );
    }
}
