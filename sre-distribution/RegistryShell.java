package train.cobblemon.shell;

import com.google.common.collect.ImmutableSet;
import com.google.gson.*;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Stream;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.advancements.critereon.EntitySubPredicate;
import net.minecraft.advancements.critereon.ImpossibleTrigger;
import net.minecraft.commands.synchronization.SingletonArgumentInfo;
import net.minecraft.core.*;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.*;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.sensing.*;
import net.minecraft.world.entity.ai.village.poi.PoiType;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.schedule.Activity;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.*;
import net.minecraft.world.item.crafting.*;
import net.minecraft.world.level.*;
import net.minecraft.world.level.block.*;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.*;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.levelgen.blockpredicates.*;
import net.minecraft.world.level.levelgen.feature.*;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraft.world.level.levelgen.placement.*;
import net.minecraft.world.level.levelgen.structure.templatesystem.*;
import net.minecraft.world.phys.Vec3;

/** 仅保留发行版的静态注册身份和方块状态，完全不加载 Cobblemon 玩法与运行库。 */
@SuppressWarnings({"rawtypes", "unchecked"})
public final class RegistryShell implements ModInitializer {
    private static final ThreadLocal<List<Property<?>>> CONSTRUCTING = new ThreadLocal<>();
    private static final Set<String> SUPPORTED = Set.of("sound_event", "mob_effect", "block", "entity_type", "item", "particle_type", "block_entity_type", "custom_stat", "recipe_type", "recipe_serializer", "command_argument_type", "villager_profession", "point_of_interest_type", "memory_module_type", "sensor_type", "activity", "block_predicate_type", "worldgen/feature", "worldgen/placement_modifier_type", "worldgen/structure_processor", "decorated_pot_pattern", "creative_mode_tab", "trigger_type", "data_component_type", "entity_sub_predicate_type", "menu");

    @Override public void onInitialize() {
        JsonObject snapshot;
        try (var stream = Objects.requireNonNull(getClass().getResourceAsStream("/train-shell-registries.json"));
             var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            snapshot = JsonParser.parseReader(reader).getAsJsonObject();
        } catch (IOException error) { throw new IllegalStateException("Cannot load exact 1.8.4 registry snapshot", error); }
        int count = 0;
        for (var registryEntry : snapshot.entrySet()) {
            ResourceLocation registryId = ResourceLocation.parse(registryEntry.getKey());
            if (!SUPPORTED.contains(registryId.getPath())) throw new IllegalStateException("Unknown registry: " + registryId);
            Registry registry = (Registry) BuiltInRegistries.REGISTRY.get(registryId);
            if (registry == null) throw new IllegalStateException("Missing vanilla registry: " + registryId);
            for (JsonElement raw : registryEntry.getValue().getAsJsonArray()) {
                JsonObject spec = raw.getAsJsonObject(); ResourceLocation id = ResourceLocation.parse(spec.get("id").getAsString());
                if (registry.containsKey(id)) throw new IllegalStateException("Refusing registry collision: " + id);
                Registry.register(registry, id, placeholder(registryId.getPath(), id, spec));
                count++;
            }
        }
        System.out.println("COBBLEMON_REGISTRY_SHELL_READY entries=" + count + "; gameplay disabled; fresh non-Cobblemon worlds only");
    }

    private static Object placeholder(String registry, ResourceLocation id, JsonObject spec) {
        return switch (registry) {
            case "sound_event" -> SoundEvent.createVariableRangeEvent(id);
            case "mob_effect" -> new MobEffect(MobEffectCategory.NEUTRAL, 0) { };
            case "block" -> block(spec);
            case "item" -> new Item(new Item.Properties().stacksTo(Math.max(1, Math.min(99, spec.get("maxStackSize").getAsInt()))));
            // 工厂永远返回 null，同时禁止 summon 和保存，避免产生与官方客户端元数据不兼容的实体。
            case "entity_type" -> EntityType.Builder.of((type, level) -> null, MobCategory.MISC).noSave().noSummon()
                    .sized(spec.get("width").getAsFloat(), spec.get("height").getAsFloat()).build(id.toString());
            case "particle_type" -> FabricParticleTypes.simple();
            case "block_entity_type" -> BlockEntityType.Builder.of((pos, state) -> null, new Block[0]).build(null);
            case "custom_stat" -> id;
            case "recipe_type" -> new RecipeType() { @Override public String toString() { return id.toString(); } };
            case "recipe_serializer" -> new DisabledRecipeSerializer();
            case "command_argument_type" -> SingletonArgumentInfo.contextFree(StringArgumentType::word);
            case "villager_profession" -> new VillagerProfession(id.toString(), holder -> false, holder -> false, ImmutableSet.of(), ImmutableSet.of(), null);
            case "point_of_interest_type" -> new PoiType(Set.of(), 0, 1);
            case "memory_module_type" -> new MemoryModuleType(Optional.empty());
            case "sensor_type" -> new SensorType<>(EmptySensor::new);
            case "activity" -> new Activity(id.toString());
            case "block_predicate_type" -> (BlockPredicateType<EmptyPredicate>) () -> MapCodec.unit(new EmptyPredicate(id));
            case "worldgen/feature" -> new Feature<NoneFeatureConfiguration>(NoneFeatureConfiguration.CODEC) {
                @Override public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> context) { return false; }
            };
            case "worldgen/placement_modifier_type" -> (PlacementModifierType<EmptyPlacement>) () -> MapCodec.unit(new EmptyPlacement(id));
            case "worldgen/structure_processor" -> (StructureProcessorType<EmptyProcessor>) () -> MapCodec.unit(new EmptyProcessor(id));
            case "decorated_pot_pattern" -> id.toString();
            case "creative_mode_tab" -> FabricItemGroup.builder().title(Component.literal(id.toString())).icon(() -> new ItemStack(Items.BARRIER)).displayItems((parameters, output) -> { }).build();
            case "trigger_type" -> new ImpossibleTrigger();
            // 注册 ID 供 Fabric 同步，但不制造或接收任何宝可梦业务组件值。
            case "data_component_type" -> DataComponentType.builder().networkSynchronized(rejectedStream()).build();
            case "entity_sub_predicate_type" -> MapCodec.unit(new EmptyEntityPredicate());
            case "menu" -> new MenuType<>((syncId, inventory) -> { throw unsupported(); }, FeatureFlags.VANILLA_SET);
            default -> throw new IllegalStateException("Unhandled registry " + registry);
        };
    }

    private static UnsupportedOperationException unsupported() { return new UnsupportedOperationException("Cobblemon gameplay data is unavailable in the registry-only server shell"); }
    private static StreamCodec rejectedStream() { return StreamCodec.of((buffer, value) -> { throw unsupported(); }, buffer -> { throw unsupported(); }); }

    private static Block block(JsonObject spec) {
        List<Property<?>> properties = new ArrayList<>();
        for (var property : spec.getAsJsonObject("properties").entrySet()) {
            List<String> values = new ArrayList<>(); for (JsonElement value : property.getValue().getAsJsonArray()) values.add(value.getAsString());
            properties.add(new TextProperty(property.getKey(), values));
        }
        CONSTRUCTING.set(properties);
        ShellBlock block;
        try { block = new ShellBlock(spec.get("defaultState").getAsString()); }
        finally { CONSTRUCTING.remove(); }
        List<String> expected = new ArrayList<>(); for (JsonElement state : spec.getAsJsonArray("states")) expected.add(state.getAsString());
        List<String> actual = block.getStateDefinition().getPossibleStates().stream().map(RegistryShell::describe).toList();
        if (!actual.equals(expected)) throw new IllegalStateException("State ordering mismatch: " + spec.get("id"));
        return block;
    }
    private static String describe(BlockState state) {
        StringJoiner text = new StringJoiner(",");
        for (Property property : state.getProperties()) text.add(property.getName() + "=" + property.getName(state.getValue(property)));
        return text.toString();
    }
    private static final class TextProperty extends Property<String> {
        private final List<String> values;
        TextProperty(String name, List<String> values) { super(name, String.class); this.values = List.copyOf(values); }
        @Override public Collection<String> getPossibleValues() { return values; }
        @Override public String getName(String value) { return value; }
        @Override public Optional<String> getValue(String name) { return values.contains(name) ? Optional.of(name) : Optional.empty(); }
        @Override public boolean equals(Object other) { return super.equals(other) && other instanceof TextProperty property && values.equals(property.values); }
        @Override public int generateHashCode() { return 31 * super.generateHashCode() + values.hashCode(); }
    }
    private static final class ShellBlock extends Block {
        ShellBlock(String defaults) {
            super(BlockBehaviour.Properties.of().strength(1));
            BlockState state = defaultBlockState();
            if (!defaults.isEmpty()) for (String assignment : defaults.split(",")) {
                String[] pair = assignment.split("=", 2);
                Property<String> property = (Property<String>) getStateDefinition().getProperty(pair[0]);
                state = state.setValue(property, pair[1]);
            }
            registerDefaultState(state);
        }
        @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            for (Property<?> property : CONSTRUCTING.get()) builder.add(property);
        }
    }
    private static final class DisabledRecipeSerializer implements RecipeSerializer {
        @Override public MapCodec codec() { return MapCodec.unit(() -> { throw unsupported(); }); }
        @Override public StreamCodec streamCodec() { return rejectedStream(); }
    }
    private static final class EmptySensor extends Sensor<LivingEntity> {
        @Override protected void doTick(ServerLevel level, LivingEntity entity) { }
        @Override public Set<MemoryModuleType<?>> requires() { return Set.of(); }
    }
    private record EmptyPredicate(ResourceLocation id) implements BlockPredicate {
        @Override public BlockPredicateType<?> type() { return BuiltInRegistries.BLOCK_PREDICATE_TYPE.get(id); }
        @Override public boolean test(WorldGenLevel level, BlockPos pos) { return false; }
    }
    private static final class EmptyPlacement extends PlacementModifier {
        private final ResourceLocation id;
        EmptyPlacement(ResourceLocation id) { this.id = id; }
        @Override public Stream<BlockPos> getPositions(PlacementContext context, RandomSource random, BlockPos pos) { return Stream.empty(); }
        @Override public PlacementModifierType<?> type() { return BuiltInRegistries.PLACEMENT_MODIFIER_TYPE.get(id); }
    }
    private static final class EmptyProcessor extends StructureProcessor {
        private final ResourceLocation id;
        EmptyProcessor(ResourceLocation id) { this.id = id; }
        @Override protected StructureProcessorType<?> getType() { return BuiltInRegistries.STRUCTURE_PROCESSOR.get(id); }
    }
    private static final class EmptyEntityPredicate implements EntitySubPredicate {
        @Override public MapCodec<? extends EntitySubPredicate> codec() { return BuiltInRegistries.ENTITY_SUB_PREDICATE_TYPE.get(ResourceLocation.parse("cobblemon:poke_bobber")); }
        @Override public boolean matches(Entity entity, ServerLevel level, Vec3 position) { return false; }
    }
}
