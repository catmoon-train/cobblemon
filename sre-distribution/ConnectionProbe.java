package train.cobblemon.probe;

import java.nio.file.Path;
import java.util.Map;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.gui.screens.DisconnectedScreen;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.resolver.ServerAddress;

/** 验证真实生产客户端连接、区块接收和完整外置模型加载。 */
public final class ConnectionProbe implements ClientModInitializer {
    private boolean started;
    private int inWorldTicks;
    @Override public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (!started) {
                if (client.getOverlay() != null || client.screen == null) return;
                started = true;
                String address = System.getProperty("train.connect");
                var server = new ServerData("Distribution verification", address, ServerData.Type.OTHER);
                ConnectScreen.startConnecting(client.screen, client, ServerAddress.parseString(address), server, false, null);
                System.out.println("TRAIN_CLIENT_CONNECTING " + address);
                return;
            }
            if (client.screen instanceof DisconnectedScreen) throw new IllegalStateException("TRAIN_CLIENT_DISCONNECTED");
            if (client.level == null || client.player == null || client.getConnection() == null) return;
            if (++inWorldTicks < 120) return;
            try {
                DistributionProbe.dump(Path.of(System.getProperty("train.client.registry.output")));
                var repositoryClass = Class.forName("com.cobblemon.mod.common.client.render.models.blockbench.repository.VaryingModelRepository");
                Object repository = repositoryClass.getField("INSTANCE").get(null);
                Map<?, ?> models = (Map<?, ?>) repositoryClass.getMethod("getVariations").invoke(repository);
                if (models.size() < 985) throw new IllegalStateException("Complete resource pack not loaded: " + models.size());
                System.out.println("TRAIN_CLIENT_JOIN_PASS ticks=" + inWorldTicks + " models=" + models.size() + " player=" + client.player.getGameProfile().getName());
                client.stop();
            } catch (Exception error) { throw new IllegalStateException("TRAIN_CLIENT_JOIN_FAILED", error); }
        });
    }
}
