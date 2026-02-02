/**
 * Odoo TestScript.groovy
 * Tests the connection to Odoo PostgreSQL database
 */
import groovy.sql.Sql

// Get the connection
def sql = new Sql(connection)

log.info("Testing connection to Odoo database...")

try {
    // Test query - check if res_partner table exists and is accessible
    def result = sql.firstRow("SELECT COUNT(*) as cnt FROM res_partner WHERE 1=1")
    log.info("Connection test successful. Found {0} contacts in res_partner table.", result.cnt)
} catch (Exception e) {
    log.error("Connection test failed: {0}", e.message)
    throw e
}

return
