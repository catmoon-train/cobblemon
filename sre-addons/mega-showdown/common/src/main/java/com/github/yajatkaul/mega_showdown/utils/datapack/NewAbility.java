package com.github.yajatkaul.mega_showdown.utils.datapack;

import com.cobblemon.mod.common.api.abilities.Ability;
import com.cobblemon.mod.common.api.abilities.AbilityTemplate;

public final class NewAbility {
    public static final NewAbility INSTANCE = new NewAbility();

    private NewAbility() {
    }

    public AbilityTemplate getAbility(String name) {
        return new AbilityTemplate(
                name,
                Ability::new,
                "cobblemon.ability." + name,
                "cobblemon.ability." + name + ".desc"
        );
    }
}
