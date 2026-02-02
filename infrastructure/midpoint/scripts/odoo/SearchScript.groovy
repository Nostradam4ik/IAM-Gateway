/**
 * Odoo SearchScript.groovy
 * Searches for contacts in Odoo res_partner table
 */
import groovy.sql.Sql
import org.identityconnectors.framework.common.objects.*

// Get the connection
def sql = new Sql(connection)

// Build the query
def query = "SELECT id, name, email, phone, function, comment, employee, active, company_id FROM res_partner WHERE 1=1"
def params = []

// Handle search filters
if (filter != null) {
    // Filter by UID (id)
    if (filter.byUid != null) {
        query += " AND id = ?"
        params << Integer.parseInt(filter.byUid)
    }
    // Filter by Name (email)
    if (filter.byName != null) {
        query += " AND email = ?"
        params << filter.byName
    }
}

// Add ordering
query += " ORDER BY id"

// Execute query
log.info("Executing search: {0}", query)

sql.eachRow(query, params) { row ->
    def connectorObject = new ConnectorObjectBuilder()
    connectorObject.setObjectClass(ObjectClass.ACCOUNT)

    // Set UID (database id as string)
    connectorObject.setUid(row.id.toString())

    // Set Name (email)
    connectorObject.setName(row.email ?: "user_${row.id}@unknown.com")

    // Add attributes
    if (row.name != null) {
        connectorObject.addAttribute("name", row.name)
    }
    if (row.email != null) {
        connectorObject.addAttribute("email", row.email)
    }
    if (row.phone != null) {
        connectorObject.addAttribute("phone", row.phone)
    }
    if (row.function != null) {
        connectorObject.addAttribute("function", row.function)
    }
    if (row.comment != null) {
        connectorObject.addAttribute("comment", row.comment)
    }
    connectorObject.addAttribute("employee", row.employee ?: false)
    connectorObject.addAttribute("active", row.active ?: true)
    if (row.company_id != null) {
        connectorObject.addAttribute("company_id", row.company_id)
    }

    // Return the object to handler
    handler.handle(connectorObject.build())
}

return new SearchResult()
