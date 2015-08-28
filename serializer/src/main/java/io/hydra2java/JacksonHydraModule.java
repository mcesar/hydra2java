package io.hydra2java;

import com.fasterxml.jackson.core.Version;
import com.fasterxml.jackson.databind.BeanDescription;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializationConfig;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.databind.ser.BeanSerializerModifier;
import com.fasterxml.jackson.databind.ser.std.BeanSerializerBase;

import de.escalon.hypermedia.hydra.serialize.JacksonHydraSerializer;

public class JacksonHydraModule extends SimpleModule {

	static final long serialVersionUID = 0;

    public JacksonHydraModule() {
        super("json-hydra-module", 
				new Version(1, 0, 0, null, "de.escalon.hypermedia", "hydra-spring"));
        //setMixInAnnotation(ResourceSupport.class, ResourceSupportMixin.class);
        //setMixInAnnotation(Resources.class, ResourcesMixin.class);
        //setMixInAnnotation(Resource.class, ResourceMixin.class);
        //addSerializer(Resource.class, new ResourceSerializer());
    }

    public void setupModule(SetupContext context) {
        super.setupModule(context);

        context.addBeanSerializerModifier(new BeanSerializerModifier() {

            public JsonSerializer<?> modifySerializer(
                    SerializationConfig config,
                    BeanDescription beanDesc,
                    JsonSerializer<?> serializer) {

                if (serializer instanceof BeanSerializerBase) {
                    return new JacksonHydraSerializer(
                            (BeanSerializerBase) serializer);
                } else {
                    return serializer;
                }
            }
        });
    }

}
