package com.github.yajatkaul.mega_showdown.registry;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ItemLike;
import org.jetbrains.annotations.NotNull;

import java.util.function.Supplier;

public interface RegistrySupplier<T> extends Supplier<T>, ItemLike {
    ResourceLocation getId();

    @Override
    default @NotNull Item asItem() {
        T value = get();
        if (value instanceof ItemLike itemLike) {
            return itemLike.asItem();
        }
        return Items.AIR;
    }
}
