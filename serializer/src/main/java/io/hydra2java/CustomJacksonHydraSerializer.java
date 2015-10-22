package io.hydra2java;

import static de.escalon.hypermedia.AnnotationUtils.getAnnotation;

import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
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
        if (resource != null) {
            for (Method m : resource.value().getMethods()) {
                Property p = m.getAnnotation(Property.class);
                if (p != null && m.getAnnotation(Path.class) != null) {
                    ub = uriInfo.getRequestUriBuilder();
                    if (m.getAnnotation(Id.class) != null && 
                            m.getReturnType().equals(bean.getClass())) {
                        jgen.writeStringField(p.value(), ub.build().toString());
                    } else {
                        jgen.writeStringField(p.value(), ub.path(m).build().toString());
                    }
                }
                Id id= m.getAnnotation(Id.class);
                if (id != null && bean.getClass().equals(m.getReturnType())) {
                    if (bean.getClass().equals(resource.value())) {
                        jgen.writeStringField(JsonLdKeywords.AT_ID, ub.build().toString());
                    } else {
                        Object idValue = "";
                        for (Method mb : bean.getClass().getMethods()) {
                            if (mb.getAnnotation(Id.class) != null && 
                                    !bean.getClass().equals(mb.getReturnType())) {
                                try {
                                    idValue = mb.invoke(bean);
                                } catch (IllegalAccessException e) {
                                    throw new IOException(e);
                                } catch(InvocationTargetException e) {
                                    throw new IOException(e);
                                }
                            }
                        }
                        UriBuilder path = ub;
                        if (m.getAnnotation(Path.class) != null) {
                            path = ub.path(m);
                        }
                        jgen.writeStringField(JsonLdKeywords.AT_ID, 
                            path.path(idValue.toString()).build().toString());
                        }
                }
            }
        }
        super.serializeFields(bean, jgen, provider);
    }
}
