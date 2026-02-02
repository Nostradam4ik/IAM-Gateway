/**
 * Odoo UpdateScript.groovy
 * Updates a contact in Odoo res_partner table
 */
import groovy.sql.Sql
import org.identityconnectors.framework.common.objects.*

// Get the connection
def sql = new Sql(connection)

log.info("Updating Odoo contact uid={0} with attributes: {1}", uid, attributes)

// Extract the ID from UID
def id = Integer.parseInt(uid.uidValue)

// Build update query dynamically
def updates = []
def params = []

attributes.each { attr ->
    switch (attr.name) {
        case "name":
            updates << "name = ?"
            params << attr.value?.get(0)
            break
        case "email":
        case "__NAME__":
            updates << "email = ?"
            params << attr.value?.get(0)
            break
        case "phone":
            updates << "phone = ?"
            params << attr.value?.get(0)
            break
        case "function":
            updates << "function = ?"
            params << attr.value?.get(0)
            break
        case "comment":
            updates << "comment = ?"
            params << attr.value?.get(0)
            break
        case "employee":
            updates << "employee = ?"
            params << (attr.value?.get(0) ?: true)
            break
        case "active":
            updates << "active = ?"
            params << (attr.value?.get(0) ?: true)
            break
        case "company_id":
            updates << "company_id = ?"
            params << (attr.value?.get(0) ?: 1)
            break
    }
}

if (updates.isEmpty()) {
    log.info("No attributes to update for contact id={0}", id)
    return uid
}

// Add write_date update
updates << "write_date = NOW()"

// Add ID to params
params << id

def updateQuery = "UPDATE res_partner SET ${updates.join(', ')} WHERE id = ?"
log.info("Executing update: {0}", updateQuery)

def rowsUpdated = sql.executeUpdate(updateQuery, params)
log.info("Updated {0} rows for contact id={1}", rowsUpdated, id)

return uid
