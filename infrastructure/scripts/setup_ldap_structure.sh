#!/bin/bash

# Script pour créer la structure LDAP de base dans ApacheDS

echo "=========================================="
echo "Configuration de la structure LDAP"
echo "=========================================="

# Copier le fichier LDIF dans le conteneur ApacheDS
echo ""
echo "Étape 1: Copie du fichier LDIF dans le conteneur ApacheDS..."
docker cp infrastructure/scripts/setup_ldap_structure.ldif apacheds:/tmp/setup_ldap_structure.ldif

if [ $? -eq 0 ]; then
    echo "✓ Fichier LDIF copié avec succès"
else
    echo "✗ Erreur lors de la copie du fichier LDIF"
    exit 1
fi

# Importer la structure LDAP
echo ""
echo "Étape 2: Import de la structure LDAP..."
docker exec apacheds ldapadd -x -D "uid=admin,ou=system" -w "secret" -f /tmp/setup_ldap_structure.ldif

if [ $? -eq 0 ]; then
    echo "✓ Structure LDAP créée avec succès"
else
    echo "⚠ Note: Si vous voyez 'Already exists', c'est normal - la structure existe déjà"
fi

# Vérifier la création
echo ""
echo "Étape 3: Vérification de la structure LDAP..."
docker exec apacheds ldapsearch -x -D "uid=admin,ou=system" -w "secret" -b "dc=example,dc=com" "(ou=people)" dn

echo ""
echo "=========================================="
echo "Configuration terminée !"
echo "=========================================="
echo ""
echo "Vous pouvez maintenant assigner le rôle LDAP Basic User à Alice (u1001)"
