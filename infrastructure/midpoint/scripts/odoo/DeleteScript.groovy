/**
 * Odoo DeleteScript.groovy
 * Deletes a contact from Odoo res_partner table
 * Note: In Odoo, it's better to deactivate than delete to preserve data integrity
 */
import groovy.sql.Sql
import org.identityconnectors.framework.common.objects.*

// Get the connection
def sql = new Sql(connection)

log.info("Deleting/Deactivating Odoo contact uid={0}", uid)

// Extract the ID from UID
def id = Integer.parseInt(uid.uidValue)

// Option 1: Soft delete (deactivate) - safer for Odoo
def deactivateQuery = "UPDATE res_partner SET active = false, write_date = NOW() WHERE id = ?"
def rowsUpdated = sql.executeUpdate(deactivateQuery, [id])

log.info("Deactivated {0} rows for contact id={1}", rowsUpdated, id)

// Option 2: Hard delete (uncomment if you really want to delete)
// def deleteQuery = "DELETE FROM res_partner WHERE id = ?"
// def rowsDeleted = sql.executeUpdate(deleteQuery, [id])
// log.info("Deleted {0} rows for contact id={1}", rowsDeleted, id)

return
