package com.github.yajatkaul.mega_showdown.utils.datapack;

import com.cobblemon.mod.common.api.moves.MoveTemplate;
import com.cobblemon.mod.common.api.moves.categories.DamageCategory;
import com.cobblemon.mod.common.api.moves.categories.DamageCategories;
import com.cobblemon.mod.common.api.types.ElementalType;
import com.cobblemon.mod.common.api.types.ElementalTypes;
import com.cobblemon.mod.common.battles.MoveTarget;
import com.github.yajatkaul.mega_showdown.mixin.MovesAccessor;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

import java.util.ArrayList;
import java.util.List;

public final class NewMove {
    public static final NewMove INSTANCE = new NewMove();

    private NewMove() {
    }

    public MoveTemplate createMoveTemplate(JsonObject moveData, String id) {
        int num = moveData.get("num").getAsInt();
        ElementalType elementalType = ElementalTypes.getOrException(moveData.get("type").getAsString());
        DamageCategory damageCategory = DamageCategories.INSTANCE.getOrException(moveData.get("category").getAsString());
        double power = moveData.get("basePower").getAsDouble();
        MoveTarget target = MoveTarget.Companion.fromShowdownId(moveData.get("target").getAsString());
        JsonPrimitive accuracyJson = moveData.get("accuracy").getAsJsonPrimitive();
        double accuracy = accuracyJson.isNumber() ? accuracyJson.getAsDouble() : -1.0;
        int pp = moveData.get("pp").getAsInt();
        int priority = moveData.get("priority").getAsInt();
        JsonElement critElement = moveData.get("critRatio");
        double critRatio = (critElement != null && !critElement.isJsonNull()) ? critElement.getAsDouble() : 1.0;

        List<Double> effectChances = new ArrayList<>();
        JsonElement secondariesMember = moveData.get("secondaries");
        JsonElement secondaryMember = moveData.get("secondary");
        if (secondariesMember instanceof JsonArray arr) {
            for (int j = 0; j < arr.size(); j++) {
                JsonObject element = arr.get(j).getAsJsonObject();
                if (element.has("chance")) {
                    effectChances.add(element.get("chance").getAsDouble());
                }
            }
        } else if (secondaryMember instanceof JsonObject obj) {
            if (obj.has("chance")) {
                effectChances.add(obj.get("chance").getAsDouble());
            }
        }

        JsonElement weightMember = moveData.get("weight");
        float weight = (weightMember != null && !weightMember.isJsonNull()) ? weightMember.getAsFloat() : 0f;

        return new MoveTemplate(
                id,
                num,
                elementalType,
                damageCategory,
                power,
                target,
                accuracy,
                pp,
                priority,
                critRatio,
                effectChances.toArray(Double[]::new),
                weight
        );
    }

    public void register(MoveTemplate move) {
        MovesAccessor.getIdMapping().put(move.getNum(), move);
        MovesAccessor.getAllMoves().put(move.getName(), move);
    }
}
