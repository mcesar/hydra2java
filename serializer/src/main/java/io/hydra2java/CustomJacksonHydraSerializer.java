package io.hydra2java;

import static de.escalon.hypermedia.AnnotationUtils.getAnnotation;

import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.URI;

import javax.ws.rs.Path;
import javax.ws.rs.core.UriBuilder;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.std.BeanSerializerBase;

import de.escalon.hypermedia.hydra.serialize.JacksonHydraSerializer;
import de.escalon.hypermedia.hydra.serialize.JsonLdKeywords;

public class CustomJacksonHydraSerializer extends JacksonHydraSerializer {
    
    public CustomJacksonHydraSerializer(BeanSerializerBase source) {
        super(source);
        try {
            for (Field f : JacksonHydraSerializer.class.getDeclaredFields()) {
                if (f.getName().equals("ldContextFactory")) {
                    f.setAccessible(true);
                    f.set(this, new CustomLdContextFactory());
                }
            }
        } catch (IllegalStateException | IllegalAccessException e) {
            throw new RuntimeException(e);
        }
    }
    
    protected void serializeFields(Object bean, JsonGenerator jgen, SerializerProvider provider) 
        throws IOException {
        final Id classId = getAnnotation(bean.getClass(), Id.class);
        if (classId != null) {
            jgen.writeStringField(JsonLdKeywords.AT_ID, classId.value());
        }
        final Resource resource = getAnnotation(bean.getClass(), Resource.class);
        if (resource != null) {
            for (Method m : resource.value().getMethods()) {
                Property p = m.getAnnotation(Property.class);
                if (p != null && m.getAnnotation(Path.class) != null) {
                    URI uri = UriBuilder.fromMethod(resource.value(), m.getName()).build();
                    jgen.writeStringField(p.value(), uri.toString());
                }
            }
        }
        super.serializeFields(bean, jgen, provider);
    }
}
