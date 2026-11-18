package com.github.yajatkaul.mega_showdown.registry;

import com.github.yajatkaul.mega_showdown.creative.MegaShowdownTabs;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

public final class FabricDeferredRegister<T> {
    private final String modId;
    private final ResourceKey<? extends Registry<T>> registryKey;
    private final List<Entry<? extends T>> entries = new ArrayList<>();
    private boolean registered = false;

    private FabricDeferredRegister(String modId, ResourceKey<? extends Registry<T>> registryKey) {
        this.modId = modId;
        this.registryKey = registryKey;
    }

    public static <T> FabricDeferredRegister<T> create(String modId, ResourceKey<? extends Registry<T>> registryKey) {
        return new FabricDeferredRegister<>(modId, registryKey);
    }

    public <R extends T> RegistrySupplier<R> register(String name, Supplier<R> factory) {
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath(modId, name);
        Entry<R> entry = new Entry<>(id, factory);
        entries.add(entry);
        return entry;
    }

    @SuppressWarnings("unchecked")
    public void register() {
        if (registered) {
            return;
        }
        registered = true;
        Registry<T> registry = (Registry<T>) BuiltInRegistries.REGISTRY.get(registryKey.location());
        if (registry == null) {
            throw new IllegalStateException("Missing built-in registry for " + registryKey.location());
        }
        for (Entry<? extends T> entry : entries) {
            registerEntry(registry, entry);
        }
    }

    private <R extends T> void registerEntry(Registry<T> registry, Entry<R> entry) {
        MegaShowdownTabs.clearPendingTab();
        try {
            R value = entry.factory.get();
            R registeredValue = Registry.register(registry, entry.id, value);
            entry.value = registeredValue;
            if (registeredValue instanceof Item item) {
                MegaShowdownTabs.attachPendingTab(item);
            }
        } finally {
            MegaShowdownTabs.clearPendingTab();
        }
    }

    private static final class Entry<R> implements RegistrySupplier<R> {
        private final ResourceLocation id;
        private final Supplier<R> factory;
        private R value;

        private Entry(ResourceLocation id, Supplier<R> factory) {
            this.id = id;
            this.factory = factory;
        }

        @Override
        public ResourceLocation getId() {
            return id;
        }

        @Override
        public R get() {
            if (value == null) {
                throw new IllegalStateException("Registry entry accessed before registration: " + id);
            }
            return value;
        }
    }
}
