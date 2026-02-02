/**
 * Odoo SchemaScript.groovy
 * Defines the schema for Odoo res_partner table
 */
import org.identityconnectors.framework.common.objects.AttributeInfoBuilder
import org.identityconnectors.framework.common.objects.ObjectClassInfoBuilder

// Define ACCOUNT schema (res_partner)
def accountBuilder = new ObjectClassInfoBuilder()
accountBuilder.setType("__ACCOUNT__")

// Primary identifier - database ID (read-only, auto-generated)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("__UID__", String.class, [] as Set)
)

// Name attribute - email (used for lookups)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("__NAME__", String.class, [] as Set)
)

// Odoo res_partner attributes
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("name", String.class, [] as Set)
)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("email", String.class, [] as Set)
)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("phone", String.class, [] as Set)
)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("function", String.class, [] as Set)
)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("comment", String.class, [] as Set)
)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("employee", Boolean.class, [] as Set)
)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("active", Boolean.class, [] as Set)
)
accountBuilder.addAttributeInfo(
    AttributeInfoBuilder.build("company_id", Integer.class, [] as Set)
)

return [accountBuilder.build()]
