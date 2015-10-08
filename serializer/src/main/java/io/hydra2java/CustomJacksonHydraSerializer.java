package io.hydra2java;

import static de.escalon.hypermedia.AnnotationUtils.getAnnotation;

import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

import javax.ws.rs.Path;
import javax.ws.rs.core.UriBuilder;
import javax.ws.rs.core.UriInfo;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.std.BeanSerializerBase;

import de.escalon.hypermedia.hydra.serialize.JacksonHydraSerializer;
import de.escalon.hypermedia.hydra.serialize.JsonLdKeywords;

public class CustomJacksonHydraSerializer extends JacksonHydraSerializer {

    private UriInfo uriInfo;

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

    public void setUriInfo(UriInfo uriInfo) {
        this.uriInfo = uriInfo;
    }
    
    protected void serializeFields(Object bean, JsonGenerator jgen, SerializerProvider provider) 
        throws IOException {
        UriBuilder ub = uriInfo.getRequestUriBuilder();
        final Resource resource = getAnnotation(bean.getClass(), Resource.class);
        //final Id classId = getAnnotation(bean.getClass(), Id.class);
        if (resource != null) {
            //if (classId != null) {
                jgen.writeStringField(JsonLdKeywords.AT_ID, ub.path("").build().toString());
            //}
            for (Method m : resource.value().getMethods()) {
                Property p = m.getAnnotation(Property.class);
                if (p != null && m.getAnnotation(Path.class) != null) {
                    ub = uriInfo.getRequestUriBuilder();
                    jgen.writeStringField(p.value(), ub.path(m).build().toString());
                }
            }
        }
        super.serializeFields(bean, jgen, provider);
    }
}
