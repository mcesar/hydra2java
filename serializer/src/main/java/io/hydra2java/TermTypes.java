package io.hydra2java;

import java.lang.annotation.*;

/**
 * Allows to define multiple <code>&#64;Term</code>s in a type or package.
 */
@Documented
@Target({ElementType.PACKAGE, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface TermTypes {

    TermType[] value();
}
