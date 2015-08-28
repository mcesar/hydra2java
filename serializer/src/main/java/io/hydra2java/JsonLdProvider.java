package io.hydra2java;

import java.io.IOException;
import java.io.OutputStream;
import java.lang.annotation.Annotation;
import java.lang.reflect.Type;

import javax.ws.rs.Consumes;
import javax.ws.rs.Produces;
import javax.ws.rs.WebApplicationException;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.MultivaluedMap;
import javax.ws.rs.ext.Provider;

import org.eclipse.persistence.jaxb.rs.MOXyJsonProvider;

import com.fasterxml.jackson.databind.ObjectMapper;

@Provider
@Produces("application/ld+json")
@Consumes("application/ld+json")
public class JsonLdProvider extends MOXyJsonProvider {

    @Override
    public void writeTo(Object object, Class<?> type, Type genericType, Annotation[] annotations,
            MediaType mediaType, MultivaluedMap<String, Object> httpHeaders,
            OutputStream entityStream) throws IOException, WebApplicationException {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JacksonHydraModule());
        mapper.writeValue(entityStream, object);
    }
}

