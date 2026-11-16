import com.google.gson.Gson;
import com.google.gson.JsonObject;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.contents.TranslatableContents;
import us.timinc.mc.cobblemon.spawnnotification.config.ConfigBuilder;
import us.timinc.mc.cobblemon.spawnnotification.config.SpawnNotificationConfig;

public final class ConfigCompatibilityTest {
    private static void check(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] args) throws Exception {
        Gson gson = new Gson();
        var defaults = new SpawnNotificationConfig();
        JsonObject fields = gson.toJsonTree(defaults).getAsJsonObject();
        check(fields.size() == 15);
        check(defaults.getBroadcastShiny() && defaults.getBroadcastCoords() && !defaults.getBroadcastBiome());
        check(defaults.getPlayShinySound() && !defaults.getPlayShinySoundPlayer());
        check(!defaults.getAnnounceCrossDimensions() && !defaults.getBroadcastDespawns());
        check(!defaults.getBroadcastVolatileDespawns() && defaults.getBroadcastSpeciesName());
        check(!defaults.getBroadcastPlayerSpawnedOn() && !defaults.getBroadcastRangeEnabled() && !defaults.getPlayerLimitEnabled());
        check(defaults.getLabelsForBroadcast().equals(java.util.Set.of("legendary")) && defaults.getBucketsForBroadcast().isEmpty());
        check(defaults.getComponent("shiny").getStyle().getColor().equals(net.minecraft.network.chat.TextColor.fromLegacyFormat(ChatFormatting.GOLD)));
        check(((TranslatableContents) defaults.getComponent("notification.coords", 1, 2, 3).getContents()).getArgs().length == 3);
        check(((TranslatableContents) defaults.getRawComponent("biome.minecraft.plains").getContents()).getKey().equals("biome.minecraft.plains"));
        var custom = gson.fromJson("""
            {"broadcastShiny":false,"broadcastCoords":false,"broadcastBiome":true,
             "playShinySound":false,"playShinySoundPlayer":true,"announceCrossDimensions":true,
             "broadcastDespawns":true,"broadcastVolatileDespawns":true,"broadcastSpeciesName":false,
             "broadcastPlayerSpawnedOn":true,"broadcastRange":128,"playerLimit":2,
             "labelsForBroadcast":["mythical"],"bucketsForBroadcast":["ultra-rare"],"formatting":{"shiny":"RED"}}
            """, SpawnNotificationConfig.class);
        check(!custom.getBroadcastShiny() && !custom.getBroadcastCoords() && custom.getBroadcastBiome());
        check(!custom.getPlayShinySound() && custom.getPlayShinySoundPlayer());
        check(custom.getAnnounceCrossDimensions() && custom.getBroadcastDespawns() && custom.getBroadcastVolatileDespawns());
        check(!custom.getBroadcastSpeciesName() && custom.getBroadcastPlayerSpawnedOn());
        check(custom.getBroadcastRange() == 128 && custom.getPlayerLimit() == 2 && custom.getBroadcastRangeEnabled() && custom.getPlayerLimitEnabled());
        check(custom.getLabelsForBroadcast().contains("mythical") && custom.getBucketsForBroadcast().contains("ultra-rare"));
        check(custom.getComponent("shiny").getStyle().getColor().equals(net.minecraft.network.chat.TextColor.fromLegacyFormat(ChatFormatting.RED)));
        var loaded = ConfigBuilder.Companion.load(SpawnNotificationConfig.class, "spawn_notification_test");
        check(loaded.getPlayShinySound() && java.nio.file.Files.isRegularFile(java.nio.file.Path.of("config/spawn_notification_test.json")));
        var reloaded = ConfigBuilder.Companion.load(SpawnNotificationConfig.class, "spawn_notification_test");
        check(reloaded.getLabelsForBroadcast().equals(defaults.getLabelsForBroadcast()));
        System.out.println("CONFIG_COMPATIBILITY_PASS (all 15 upstream fields/defaults, overrides, formatting, JSON file roundtrip)");
    }
}
