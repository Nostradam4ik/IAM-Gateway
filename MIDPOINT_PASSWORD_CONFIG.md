# Configuration du Mot de Passe MidPoint Permanent

## Mot de passe configuré
- **Username**: `administrator`
- **Password**: `Holimolly1`

## Comment cela fonctionne

Le mot de passe est défini de manière permanente grâce au fichier:
- **Chemin dans le conteneur**: `/opt/midpoint/var/post-initial-objects/100-admin-password.xml`

Ce fichier est automatiquement chargé par MidPoint lors du démarrage et applique le mot de passe configuré.

## Que se passe-t-il lors d'un redémarrage?

1. **Redémarrage du conteneur**: Le mot de passe reste `Holimolly1` ✅
2. **Recréation du conteneur**: Le mot de passe reste `Holimolly1` ✅ (car le volume est persistant)
3. **Suppression complète du volume**: Le fichier sera rechargé depuis post-initial-objects ✅

## URLs de connexion

- **Interface Web**: http://localhost:8080/midpoint
- **Gateway IAM**: http://localhost:8000
- **Frontend Gateway**: http://localhost:3000

## Fichier de configuration

Le fichier XML contient:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<objects xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
         xmlns:c="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
         xmlns:t="http://prism.evolveum.com/xml/ns/public/types-3">
    <user oid="00000000-0000-0000-0000-000000000002">
        <name>administrator</name>
        <credentials>
            <password>
                <value>
                    <t:clearValue>Holimolly1</t:clearValue>
                </value>
            </password>
        </credentials>
    </user>
</objects>
```

## Note importante

- Le fichier est marqué `.done` après import par MidPoint
- Une copie sans `.done` est conservée pour les réinitialisations futures
- Le mot de passe est aussi configuré dans docker-compose.yml pour la Gateway IAM

## Vérification

Pour vérifier que le mot de passe fonctionne:
```bash
curl -s -u "administrator:Holimolly1" http://localhost:8080/midpoint/ -I | grep -E "HTTP/|Location"
```

Résultat attendu:
```
HTTP/1.1 302 
Location: ./self/dashboard
```
