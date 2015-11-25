package io.hydra2java;

import java.io.IOException;
import java.io.OutputStream;
import java.lang.annotation.Annotation;
import java.lang.reflect.Type;

import javax.ws.rs.Consumes;
import javax.ws.rs.Produces;
import javax.ws.rs.WebApplicationException;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.MultivaluedMap;
import javax.ws.rs.core.UriInfo;
import javax.ws.rs.ext.MessageBodyWriter;
import javax.ws.rs.ext.Provider;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonInclude.Include;

@Provider
@Produces("application/ld+json")
@Consumes("application/ld+json")
public class JsonLdProvider implements MessageBodyWriter<Object> {

    @Context
    UriInfo uriInfo;

    public boolean isWriteable(java.lang.Class<?> type,
                    java.lang.reflect.Type genericType,
                    java.lang.annotation.Annotation[] annotations,
                    MediaType mediaType) {
        return true;
    }

    public long getSize(Object t,
             java.lang.Class<?> type,
             java.lang.reflect.Type genericType,
             java.lang.annotation.Annotation[] annotations,
             MediaType mediaType){
        return -1;
    }

    @Override
    public void writeTo(Object object, Class<?> type, Type genericType, Annotation[] annotations,
            MediaType mediaType, MultivaluedMap<String, Object> httpHeaders,
            OutputStream entityStream) throws IOException, WebApplicationException {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JacksonHydraModule(uriInfo));
        mapper.setSerializationInclusion(Include.NON_NULL);
        mapper.writeValue(entityStream, object);
    }
}

