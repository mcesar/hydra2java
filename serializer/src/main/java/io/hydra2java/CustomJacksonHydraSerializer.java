package io.hydra2java;

import static de.escalon.hypermedia.AnnotationUtils.getAnnotation;

import java.io.IOException;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.std.BeanSerializerBase;

import de.escalon.hypermedia.hydra.serialize.JacksonHydraSerializer;
import de.escalon.hypermedia.hydra.serialize.JsonLdKeywords;

public class CustomJacksonHydraSerializer extends JacksonHydraSerializer {
    
    public CustomJacksonHydraSerializer(BeanSerializerBase source) {
        super(source);
    }
    
    protected void serializeFields(Object bean, JsonGenerator jgen, SerializerProvider provider) 
        throws IOException {
        final Id classId = getAnnotation(bean.getClass(), Id.class);
        if (classId != null) {
            jgen.writeStringField(JsonLdKeywords.AT_ID, classId.value());
        }
        super.serializeFields(bean, jgen, provider);
    }
}
