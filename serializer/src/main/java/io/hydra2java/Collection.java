package io.hydra2java;

public interface Collection<T> {
    java.util.Collection<T> getMembers();
    String getTemplate();
    java.util.Map<String, String> getMapping();
}
