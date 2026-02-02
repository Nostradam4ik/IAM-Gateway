/**
 * Odoo CreateScript.groovy
 * Creates a new contact in Odoo res_partner table
 */
import groovy.sql.Sql
import org.identityconnectors.framework.common.objects.*
import org.identityconnectors.framework.common.exceptions.AlreadyExistsException

// Get the connection
def sql = new Sql(connection)

log.info("Creating Odoo contact with attributes: {0}", attributes)

// Extract attributes
def name = null
def email = null
def phone = null
def function = null
def comment = "Synced from MidPoint IAM"
def employee = true
def active = true
def company_id = 1

attributes.each { attr ->
    switch (attr.name) {
        case "__NAME__":
            email = attr.value?.get(0)
            break
        case "name":
            name = attr.value?.get(0)
            break
        case "email":
            email = attr.value?.get(0)
            break
        case "phone":
            phone = attr.value?.get(0)
            break
        case "function":
            function = attr.value?.get(0)
            break
        case "comment":
            comment = attr.value?.get(0)
            break
        case "employee":
            employee = attr.value?.get(0) ?: true
            break
        case "active":
            active = attr.value?.get(0) ?: true
            break
        case "company_id":
            company_id = attr.value?.get(0) ?: 1
            break
    }
}

// Validate required fields
if (name == null || name.isEmpty()) {
    name = email?.split("@")?.get(0) ?: "Unknown"
}

log.info("Creating contact: name={0}, email={1}", name, email)

// Check if contact already exists by email
def existing = sql.firstRow("SELECT id FROM res_partner WHERE email = ?", [email])
if (existing != null) {
    throw new AlreadyExistsException("Contact with email ${email} already exists with id ${existing.id}")
}

// Insert the new contact
def insertQuery = """
    INSERT INTO res_partner (name, email, phone, function, comment, employee, active, company_id, create_date, write_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
    RETURNING id
"""

def result = sql.firstRow(insertQuery, [name, email, phone, function, comment, employee, active, company_id])
def newId = result.id

log.info("Created Odoo contact with id: {0}", newId)

// Return the UID of the created object
return new Uid(newId.toString())
