import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.PUT;
import javax.ws.rs.DELETE;
import javax.ws.rs.Consumes;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.UriInfo;
import de.escalon.hypermedia.hydra.mapping.*;
import io.hydra2java.*;

@Vocab("http://example.com/basic/vocab")
@Terms({
@Term(define="name",as="http://example.com/basic/vocab#EntryPoint/name")
})
@TermTypes({

})
@Expose("EntryPoint")
@Path("EntryPoint")
public interface EntryPoint {

    String getName();

    void setName(String name);
}
