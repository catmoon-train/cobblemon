package com.github.yajatkaul.mega_showdown.cobblemon.battle.button;

import com.cobblemon.mod.common.api.gui.GuiUtilsKt;
import com.cobblemon.mod.common.client.battle.SingleActionRequest;
import com.cobblemon.mod.common.util.MiscUtilsKt;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.resources.ResourceLocation;

public class BattleShiftButton {
    public static final int WIDTH = 72;
    public static final int HEIGHT = 34;
    public static final float SCALE = 0.5F;
    private static final ResourceLocation BASE_TEXTURE =
            MiscUtilsKt.cobblemonResource("textures/gui/battle/triple_battle_shift.png");

    private final float x;
    private final float y;
    private final SingleActionRequest request;

    public BattleShiftButton(float x, float y, SingleActionRequest request) {
        this.x = x;
        this.y = y;
        this.request = request;
    }

    public float getX() {
        return x;
    }

    public float getY() {
        return y;
    }

    public SingleActionRequest getRequest() {
        return request;
    }

    public boolean getEnabled() {
        char slot = request.getActivePokemon().getPNX().charAt(2);
        return request.getActivePokemon().getFormat().getBattleType().getSlotsPerActor() == 3
                && (slot == 'a' || slot == 'c');
    }

    public void render(GuiGraphics context, int mouseX, int mouseY, float delta) {
        if (!getEnabled()) {
            return;
        }
        GuiUtilsKt.blitk(
                context.pose(),
                BASE_TEXTURE,
                x * 6,
                y * 2,
                HEIGHT,
                WIDTH,
                0,
                isHovered(mouseX, mouseY) ? HEIGHT : 0,
                WIDTH,
                HEIGHT * 2,
                0,
                1,
                1,
                1,
                1F,
                true,
                SCALE
        );
    }

    public boolean isHovered(double mouseX, double mouseY) {
        float scaledX = x * 3;
        float scaledY = y;
        float scaledWidth = WIDTH * SCALE;
        float scaledHeight = HEIGHT * SCALE;
        return mouseX >= scaledX && mouseX <= (scaledX + scaledWidth)
                && mouseY >= scaledY && mouseY <= (scaledY + scaledHeight);
    }
}
