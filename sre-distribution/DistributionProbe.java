package train.cobblemon.probe;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.item.Item;
import net.minecraft.world.entity.EntityType;

/** 仅在隔离验证进程中导出发行版注册结果，不进入交付 JAR。 */
public final class DistributionProbe implements ModInitializer {
    @Override public void onInitialize() {
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            String output = System.getProperty("train.registry.output");
            if (output != null) {
                try { dump(Path.of(output)); }
                catch (Exception error) { throw new IllegalStateException("REGISTRY_DUMP_FAILED", error); }
            }
            System.out.println("TRAIN_SERVER_READY port=" + server.getPort());
            if (Boolean.getBoolean("train.probe.stop")) server.halt(false);
        });
    }
    @SuppressWarnings({"rawtypes", "unchecked"})
    public static void dump(Path target) throws Exception {
        JsonObject root = new JsonObject();
        for (Object raw : BuiltInRegistries.REGISTRY) {
            Registry registry = (Registry) raw;
            String key = registry.key().location().toString();
            JsonArray entries = new JsonArray();
            for (Object value : registry) {
                var id = registry.getKey(value);
                if (!id.getNamespace().equals("cobblemon") && !(key.equals("minecraft:menu") && Set.of("cooking_pot_menu", "tm_machine_menu").contains(id.getPath()))) continue;
                JsonObject entry = new JsonObject();
                entry.addProperty("id", id.toString());
                entry.addProperty("rawId", registry.getId(value));
                entry.addProperty("class", value.getClass().getName());
                if (value instanceof Block block) {
                    JsonObject properties = new JsonObject();
                    for (Property property : block.getStateDefinition().getProperties()) {
                        JsonArray values = new JsonArray();
                        for (Object allowed : property.getPossibleValues()) values.add(property.getName((Comparable) allowed));
                        properties.add(property.getName(), values);
                    }
                    entry.add("properties", properties);
                    entry.addProperty("defaultState", describe(block.defaultBlockState()));
                    JsonArray states = new JsonArray();
                    for (BlockState state : block.getStateDefinition().getPossibleStates()) states.add(describe(state));
                    entry.add("states", states);
                }
                if (value instanceof Item item) entry.addProperty("maxStackSize", item.getDefaultInstance().getMaxStackSize());
                if (value instanceof EntityType<?> entity) {
                    entry.addProperty("width", entity.getWidth()); entry.addProperty("height", entity.getHeight());
                    entry.addProperty("category", entity.getCategory().getName());
                }
                entries.add(entry);
            }
            if (!entries.isEmpty()) root.add(key, entries);
        }
        Files.createDirectories(target.toAbsolutePath().getParent());
        Files.writeString(target, new GsonBuilder().setPrettyPrinting().create().toJson(root));
        System.out.println("TRAIN_REGISTRY_DUMP_PASS registries=" + root.size() + " path=" + target);
    }
    @SuppressWarnings({"rawtypes", "unchecked"})
    private static String describe(BlockState state) {
        StringJoiner description = new StringJoiner(",");
        for (Property property : state.getProperties()) description.add(property.getName() + "=" + property.getName(state.getValue(property)));
        return description.toString();
    }
}
