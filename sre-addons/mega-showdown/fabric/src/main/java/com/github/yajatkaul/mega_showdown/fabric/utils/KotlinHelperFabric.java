package com.github.yajatkaul.mega_showdown.fabric.utils;

import com.bedrockk.molang.runtime.MoLangRuntime;
import com.cobblemon.mod.common.util.MoLangExtensionsKt;

import java.util.Map;

public final class KotlinHelperFabric {
    public static final KotlinHelperFabric INSTANCE = new KotlinHelperFabric();

    private KotlinHelperFabric() {
    }

    public void playParticleEffect(String particleId, String locator, MoLangRuntime runtime) {
        MoLangExtensionsKt.resolve(
                runtime,
                MoLangExtensionsKt.asExpressionLike("q.particle('" + particleId + "', '" + locator + "')"),
                Map.of()
        );
    }
}
