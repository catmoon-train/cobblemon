package train.cobblemon.probe;

import io.netty.buffer.Unpooled;
import java.lang.reflect.*;
import java.util.*;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;

/** 仅限独立验证运行：检查实际数据加载、原生骑乘同步以及通知内容。 */
public final class AddonRuntimeProbe implements ModInitializer {
    @Override public void onInitialize() {
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            try { check(server); }
            catch (Exception e) { throw new IllegalStateException("TRAIN_ADDON_RUNTIME_FAILED", e); }
        });
    }
    private static Object singleton(Class<?> c) throws Exception { return c.getField("INSTANCE").get(null); }
    private static Object call(Object o, String name) throws Exception { return o.getClass().getMethod(name).invoke(o); }
    private static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
    private static void check(MinecraftServer server) throws Exception {
        Class<?> speciesRegistry=Class.forName("com.cobblemon.mod.common.api.pokemon.PokemonSpecies");
        Object registry=singleton(speciesRegistry);
        Method byName=speciesRegistry.getMethod("getByName",String.class);
        String[] speciesNames=("charizard blastoise pidgeot fearow nidoking ninetales arcanine tentacruel rapidash magnezone dodrio dewgong exeggutor tauros gyarados lapras aerodactyl dragonite meganium feraligatr steelix stantler swampert mightyena sharpedo wailmer camerupt relicanth metagross staraptor luxray garchomp yanmega mamoswine samurott stoutland scolipede sawsbuck golurk bouffalant avalugg mudsdale corviknight wyrdeer ursaluna skeledirge espathra").split(" ");
        for (String name:speciesNames) {
            Object species=byName.invoke(registry,name);
            require(species!=null,"Missing species "+name);
            Object riding=call(call(species,"getStandardForm"),"getRiding");
            require(riding!=null,"Missing riding "+name);
            List<?> seats=(List<?>)call(riding,"getSeats");
            require(seats.size()>=2,"Missing passenger seat "+name);
            Map<?,?> behaviours=(Map<?,?>)call(riding,"getBehaviours");
            require(behaviours!=null && !behaviours.isEmpty(),"Missing native behaviour "+name);
            var buffer=new RegistryFriendlyByteBuf(Unpooled.buffer(),server.registryAccess());
            try {
                riding.getClass().getMethod("encode",RegistryFriendlyByteBuf.class).invoke(riding,buffer);
                Object companion=riding.getClass().getField("Companion").get(null);
                Object decoded=companion.getClass().getMethod("decode",RegistryFriendlyByteBuf.class).invoke(companion,buffer);
                require(((List<?>)call(decoded,"getSeats")).size()==seats.size() && buffer.readableBytes()==0,"Riding sync roundtrip "+name);
            } finally {buffer.release();}
        }
        if (Boolean.getBoolean("train.legacy.fixture")) {
            Class<?> importer=Class.forName("com.cobblemon.mod.common.api.riding.LegacyRidingConfig");
            Method apply=Arrays.stream(importer.getMethods()).filter(m->m.getName().startsWith("applyToSpecies") && m.getParameterCount()==0).findFirst().orElseThrow();
            for (int repeat=0;repeat<2;repeat++) {
                apply.invoke(singleton(importer));
                Object riding=call(call(byName.invoke(registry,"nidoking"),"getStandardForm"),"getRiding");
                Object settings=((Map<?,?>)call(riding,"getBehaviours")).entrySet().stream().filter(e->e.getKey().toString().equals("LAND")).findFirst().orElseThrow().getValue();
                require(((Number)call(settings,"getWalkSpeedMultiplier")).doubleValue()==1.25,"Legacy speed import compounded");
                Object offset=call(((List<?>)call(riding,"getSeats")).getFirst(),"getOffset");
                require(((Number)call(offset,"getX")).doubleValue()==0.3 && ((Number)call(offset,"getY")).doubleValue()==1.4 && ((Number)call(offset,"getZ")).doubleValue()==0.2,"Legacy offset axis order");
            }
            System.out.println("TRAIN_LEGACY_CONFIG_PASS repeats=2 speed=1.25 offsetXYZ=0.3,1.4,0.2");
        }
        long navItems=BuiltInRegistries.ITEM.keySet().stream().filter(id->id.getNamespace().equals("cobblenav")).count();
        require(navItems==29,"Nav items "+navItems);
        Class<?> pokemon=Class.forName("com.cobblemon.mod.common.pokemon.Pokemon");
        Object mon=pokemon.getConstructor().newInstance();
        Object pikachu=byName.invoke(registry,"pikachu");
        pokemon.getMethod("setSpecies",pikachu.getClass()).invoke(mon,pikachu);
        Class<?> poolClass=Class.forName("com.cobblemon.mod.common.api.spawning.detail.SpawnPool");
        Object pool=poolClass.getConstructor(String.class).newInstance("train-runtime-probe");
        Class<?> broadcaster=Class.forName("us.timinc.mc.cobblemon.spawnnotification.broadcasters.SpawnBroadcaster");
        Constructor<?> ctor=Arrays.stream(broadcaster.getConstructors()).filter(c->c.getParameterCount()==6).findFirst().orElseThrow();
        Object message=ctor.newInstance(mon,pool,new BlockPos(12,64,34),ResourceLocation.parse("minecraft:plains"),ResourceLocation.parse("minecraft:overworld"),null);
        require(call(message,"getBroadcast")==null,"Ordinary Pokemon should not broadcast");
        pokemon.getMethod("setShiny",boolean.class).invoke(mon,true);
        require(call(message,"getBroadcast")!=null,"Missing shiny notification");
        pokemon.getMethod("setShiny",boolean.class).invoke(mon,false);
        Object legendary=byName.invoke(registry,"mewtwo");
        pokemon.getMethod("setSpecies",legendary.getClass()).invoke(mon,legendary);
        require(call(message,"getBroadcast")!=null,"Missing legendary notification");
        System.out.println("TRAIN_ADDON_RUNTIME_PASS ridingSpecies="+speciesNames.length+" nativeSyncRoundtrips="+speciesNames.length+" navItems="+navItems+" notificationCases=3");
    }
}
