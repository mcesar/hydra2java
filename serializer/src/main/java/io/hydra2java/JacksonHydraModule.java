package io.hydra2java;

import javax.ws.rs.core.UriInfo;

import com.fasterxml.jackson.core.Version;
import com.fasterxml.jackson.databind.BeanDescription;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializationConfig;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.databind.ser.BeanSerializerModifier;
import com.fasterxml.jackson.databind.ser.std.BeanSerializerBase;

public class JacksonHydraModule extends SimpleModule {

    static final long serialVersionUID = 0;

    private UriInfo uriInfo;

    public JacksonHydraModule(UriInfo uriInfo) {
        super("json-hydra-module", 
                new Version(1, 0, 0, null, "de.escalon.hypermedia", "hydra-spring"));
        //setMixInAnnotation(ResourceSupport.class, ResourceSupportMixin.class);
        //setMixInAnnotation(Resources.class, ResourcesMixin.class);
        //setMixInAnnotation(Resource.class, ResourceMixin.class);
        //addSerializer(Resource.class, new ResourceSerializer());
        this.uriInfo = uriInfo;
    }

    public void setupModule(SetupContext context) {
        super.setupModule(context);

        context.addBeanSerializerModifier(new BeanSerializerModifier() {

            public JsonSerializer<?> modifySerializer(
                    SerializationConfig config,
                    BeanDescription beanDesc,
                    JsonSerializer<?> serializer) {

                if (serializer instanceof BeanSerializerBase) {
                    CustomJacksonHydraSerializer result = 
                        new CustomJacksonHydraSerializer((BeanSerializerBase) serializer);
                    result.setUriInfo(uriInfo);
                    return result;
                } else {
                    return serializer;
                }
            }
        });
    }

}
