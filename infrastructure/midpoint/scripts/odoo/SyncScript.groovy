/**
 * Odoo SyncScript.groovy
 * Synchronization script for LiveSync - detects changes in Odoo
 */
import groovy.sql.Sql
import org.identityconnectors.framework.common.objects.*
import org.identityconnectors.framework.common.objects.filter.*

// Get the connection
def sql = new Sql(connection)

log.info("Starting Odoo sync with token: {0}", token)

// Parse the sync token (timestamp of last sync)
def lastSyncTimestamp = null
if (token != null) {
    lastSyncTimestamp = token
}

// Query for changes since last sync
def query = """
    SELECT id, name, email, phone, function, comment, employee, active, company_id, write_date
    FROM res_partner
    WHERE write_date > ?::timestamp
    ORDER BY write_date ASC
"""

def newToken = null

sql.eachRow(query, [lastSyncTimestamp ?: '1970-01-01 00:00:00']) { row ->
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

    // Determine sync delta type
    def deltaType = row.active ? SyncDeltaType.CREATE_OR_UPDATE : SyncDeltaType.DELETE

    // Build sync delta
    def syncDelta = new SyncDeltaBuilder()
    syncDelta.setDeltaType(deltaType)
    syncDelta.setToken(new SyncToken(row.write_date.toString()))
    syncDelta.setObject(connectorObject.build())

    handler.handle(syncDelta.build())

    // Update token
    newToken = row.write_date.toString()
}

// Return the new sync token
return newToken != null ? new SyncToken(newToken) : (token != null ? new SyncToken(token) : new SyncToken("1970-01-01 00:00:00"))
