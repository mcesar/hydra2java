package io.hydra2java;

import java.lang.annotation.*;

@Documented
@Target({ElementType.PACKAGE, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface TermType {
    String define();
    String type();
}

