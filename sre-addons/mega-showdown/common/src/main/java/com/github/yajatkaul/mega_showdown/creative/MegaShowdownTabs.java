package com.github.yajatkaul.mega_showdown.creative;

import com.github.yajatkaul.mega_showdown.MegaShowdown;
import com.github.yajatkaul.mega_showdown.item.MegaShowdownItems;
import com.github.yajatkaul.mega_showdown.registry.FabricDeferredRegister;
import com.github.yajatkaul.mega_showdown.registry.RegistrySupplier;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

public class MegaShowdownTabs {
    public static final FabricDeferredRegister<CreativeModeTab> CREATIVE_TABS =
            FabricDeferredRegister.create(MegaShowdown.MOD_ID, Registries.CREATIVE_MODE_TAB);

    private static final Map<Supplier<CreativeModeTab>, List<Item>> TAB_ITEMS = new LinkedHashMap<>();
    private static final ThreadLocal<Supplier<CreativeModeTab>> PENDING_TAB = new ThreadLocal<>();

    public static Item.Properties tab(Item.Properties properties, Supplier<CreativeModeTab> tab) {
        PENDING_TAB.set(tab);
        return properties;
    }

    public static void clearPendingTab() {
        PENDING_TAB.remove();
    }

    public static void attachPendingTab(Item item) {
        Supplier<CreativeModeTab> tab = PENDING_TAB.get();
        if (tab != null) {
            TAB_ITEMS.computeIfAbsent(tab, k -> new ArrayList<>()).add(item);
        }
    }

    private static RegistrySupplier<CreativeModeTab> registerTab(String id, String translationKey, Supplier<Item> iconSupplier) {
        final java.util.concurrent.atomic.AtomicReference<RegistrySupplier<CreativeModeTab>> holder = new java.util.concurrent.atomic.AtomicReference<>();
        RegistrySupplier<CreativeModeTab> tab = CREATIVE_TABS.register(
                id,
                () -> FabricItemGroup.builder()
                        .title(Component.translatable(translationKey))
                        .icon(() -> new ItemStack(iconSupplier.get()))
                        .displayItems((params, output) -> {
                            List<Item> items = TAB_ITEMS.get(holder.get());
                            if (items != null) {
                                for (Item item : items) {
                                    output.accept(item);
                                }
                            }
                        })
                        .build()
        );
        holder.set(tab);
        return tab;
    }

    public static final RegistrySupplier<CreativeModeTab> MEGA_TAB =
            registerTab("mega_tab", "creativeTab.mega_showdown.mega_tab", MegaShowdownItems.MEGA_BRACELET);

    public static final RegistrySupplier<CreativeModeTab> COMPI_TAB =
            registerTab("compi_tab", "creativeTab.mega_showdown.compi_tab", MegaShowdownItems.BOOSTER_ENERGY);

    public static final RegistrySupplier<CreativeModeTab> TERA_TAB =
            registerTab("tera_tab", "creativeTab.mega_showdown.tera_tab", MegaShowdownItems.TERA_ORB);

    public static final RegistrySupplier<CreativeModeTab> KEY_TAB =
            registerTab("key_tab", "creativeTab.mega_showdown.key_tab", MegaShowdownItems.OMNI_RING);

    public static final RegistrySupplier<CreativeModeTab> Z_TAB =
            registerTab("z_tab", "creativeTab.mega_showdown.z_tab", MegaShowdownItems.Z_RING);

    public static final RegistrySupplier<CreativeModeTab> DYNAMAX_TAB =
            registerTab("dynamax_tab", "creativeTab.mega_showdown.dynamax_tab", MegaShowdownItems.DYNAMAX_BAND);

    public static final RegistrySupplier<CreativeModeTab> FORM_TAB =
            registerTab("form_tab", "creativeTab.mega_showdown.form_tab", MegaShowdownItems.BLUE_ORB);

    public static void register() {
        CREATIVE_TABS.register();
    }
}
