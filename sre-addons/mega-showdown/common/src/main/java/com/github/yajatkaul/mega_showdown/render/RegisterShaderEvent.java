package com.github.yajatkaul.mega_showdown.render;

import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.EventFactory;

import java.io.IOException;

public interface RegisterShaderEvent {
    Event<RegisterShaderEvent> EVENT = EventFactory.createArrayBacked(
            RegisterShaderEvent.class,
            listeners -> register -> {
                for (RegisterShaderEvent listener : listeners) {
                    listener.registerShaders(register);
                }
            }
    );

    void registerShaders(ShaderRegister register) throws IOException;
}