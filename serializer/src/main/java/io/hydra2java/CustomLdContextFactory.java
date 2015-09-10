package io.hydra2java;

import static de.escalon.hypermedia.AnnotationUtils.getAnnotation;

import java.util.LinkedHashMap;
import java.util.Map;

import de.escalon.hypermedia.hydra.serialize.LdContextFactory;
import de.escalon.hypermedia.hydra.serialize.MixinSource;

public class CustomLdContextFactory extends LdContextFactory {
    public Map<String, Object> getTerms(MixinSource mixinSource, Object bean, Class<?> mixInClass) {
        Map<String, Object> result = super.getTerms(mixinSource, bean, mixInClass);
        final TermTypes annotatedTerms = getAnnotation(bean.getClass(), TermTypes.class);
        if (annotatedTerms != null) {
            final TermType[] terms = annotatedTerms.value();
            for (TermType term : terms) {
                for (Map.Entry<String, Object> e : result.entrySet()) {
                    if (e.getKey().equals(term.define())) {
                        Map<String, String> m = new LinkedHashMap<String, String>();
                        m.put("@id", e.getValue().toString());
                        m.put("@type", term.type());
                        result.put(e.getKey(), m);
                    }
                }
            }
        }
        return result;
    } 
}
