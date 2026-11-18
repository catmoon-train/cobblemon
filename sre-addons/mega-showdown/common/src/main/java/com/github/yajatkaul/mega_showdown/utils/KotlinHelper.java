package com.github.yajatkaul.mega_showdown.utils;

import com.cobblemon.mod.common.api.gui.GuiUtilsKt;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.resources.ResourceLocation;

public final class KotlinHelper {
    public static final KotlinHelper INSTANCE = new KotlinHelper();

    private KotlinHelper() {
    }

    public void gimmikInfo(
            PoseStack matrices,
            ResourceLocation texture,
            Number x,
            Number y,
            Number width,
            Number height,
            float scale
    ) {
        GuiUtilsKt.blitk(
                matrices,
                texture,
                x,
                y,
                height,
                width,
                0,
                0,
                width,
                height,
                0,
                1,
                1,
                1,
                1F,
                true,
                scale
        );
    }
}
