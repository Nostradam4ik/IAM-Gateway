# Guide d'import des ressources dans MidPoint

## Problèmes corrigés

Les fichiers XML ont été corrigés pour être compatibles avec MidPoint 4.8 :
- ✅ Namespace XML correct (`common/common-3`)
- ✅ ConnectorRef avec filtre dynamique (pas de OID placeholder)
- ✅ Structure complète avec `schemaHandling`, `capabilities`, et `synchronization`
- ✅ Configuration LDAP et CSV complètes

## Étapes d'import

### 1. Préparer le fichier CSV

Le fichier CSV doit être copié dans le conteneur MidPoint avant l'import :

**Linux/macOS :**
```bash
bash infrastructure/scripts/copy_csv_to_midpoint.sh
```

**Windows (PowerShell) :**
```powershell
powershell -ExecutionPolicy Bypass -File infrastructure/scripts/copy_csv_to_midpoint.ps1
```

**Ou manuellement :**
```bash
docker exec midpoint-core mkdir -p /opt/midpoint/var/import
docker cp datasets/hr_sample.csv midpoint-core:/opt/midpoint/var/import/hr_sample.csv
```

### 2. Importer les ressources dans MidPoint

1. Connectez-vous à MidPoint : http://localhost:8080/midpoint
   - Username : `administrator`
   - Password : Le mot de passe que vous avez défini

2. **Importer la ressource LDAP :**
   - Aller dans : **Configuration** → **Import object**
   - Cliquer sur **Choose File**
   - Sélectionner : `infrastructure/midpoint/resources/ldap-resource.xml`
   - Cliquer sur **Import object**
   - Vérifier qu'il n'y a pas d'erreurs

3. **Tester la connexion LDAP :**
   - Aller dans : **Resources** → **All resources**
   - Cliquer sur "ApacheDS LDAP Resource"
   - Onglet **Configuration** → **Test connection**
   - Devrait afficher "Success"

4. **Importer la ressource CSV :**
   - Aller dans : **Configuration** → **Import object**
   - Cliquer sur **Choose File**
   - Sélectionner : `infrastructure/midpoint/resources/hr-csv.xml`
   - Cliquer sur **Import object**
   - Vérifier qu'il n'y a pas d'erreurs

5. **Tester la ressource CSV :**
   - Aller dans : **Resources** → **All resources**
   - Cliquer sur "HR CSV Resource"
   - Onglet **Configuration** → **Test connection**
   - Devrait afficher "Success"

### 3. Créer une tâche d'import CSV

1. Aller dans : **Server tasks** → **New task**
2. Configuration :
   - **Name** : `Import HR CSV`
   - **Task category** : `ImportFromResource`
   - **Resource** : Sélectionner "HR CSV Resource"
   - **Object class** : `AccountObjectClass`
3. Sauvegarder et exécuter : **Run now**
4. Vérifier dans **Users** que les utilisateurs ont été créés

### 4. Vérifier les utilisateurs importés

- Aller dans : **Users** → **All users**
- Vous devriez voir les utilisateurs du CSV :
  - Alice Dupont (u1001)
  - Bob Martin (u1002)
  - Carla Nguyen (u1003)

## Dépannage

### Erreur : "Cannot find connector"
- Le connecteur CSV ou LDAP n'est pas disponible dans votre version de MidPoint
- Vérifier dans **Configuration** → **Repository objects** → **Connectors**

### Erreur : "File not found" pour CSV
- Le fichier CSV n'a pas été copié dans le conteneur
- Exécuter le script `copy_csv_to_midpoint.sh` ou `.ps1`
- Vérifier avec : `docker exec midpoint-core ls -lh /opt/midpoint/var/import/`

### Erreur : "Cannot connect to LDAP"
- Vérifier que le conteneur apacheds est en cours d'exécution : `docker ps`
- Vérifier les logs : `docker logs apacheds`
- Le mot de passe LDAP par défaut est `secret`

### Erreur : "Invalid XML structure"
- Assurez-vous d'utiliser les fichiers XML corrigés dans `infrastructure/midpoint/resources/`
- Ne pas modifier les namespaces XML

## Structure des fichiers

```
infrastructure/midpoint/
├── resources/
│   ├── hr-csv.xml          # Ressource CSV corrigée
│   └── ldap-resource.xml   # Ressource LDAP corrigée
└── IMPORT_GUIDE.md         # Ce guide

infrastructure/scripts/
├── copy_csv_to_midpoint.sh   # Script Linux/macOS
└── copy_csv_to_midpoint.ps1  # Script Windows

datasets/
└── hr_sample.csv           # Données RH à importer
```

## Notes importantes

- Les fichiers XML utilisent des OIDs fixes :
  - LDAP : `8a8b9c1d-0001-0000-0000-000000000001`
  - CSV : `8a8b9c1d-0002-0000-0000-000000000001`
- Le délimiteur CSV est le point-virgule (`;`)
- Les utilisateurs importés sont créés avec le statut "enabled"
- La corrélation se fait sur le champ `uid`/`name`

## Créer une nouvelle ressource dans l'UI MidPoint (New resource)

Lorsque vous cliquez sur Resources → New resource, MidPoint vous demande comment vous voulez créer la ressource :

- **Inherit template** : utilisez cette option si vous avez un *template* (objet ResourceType) sous votre contrôle dans le repository. La nouvelle ressource héritera des propriétés du template (utile si vous voulez propager des changements depuis le template). C'est recommandé quand le template est maintenu par votre équipe.
- **From scratch** : créez la ressource complètement depuis zéro. À choisir si vous avez des besoins très spécifiques ou si vous préférez définir manuellement le `connectorRef` et la `connectorConfiguration`.
- **Copy from template** : effectue une copie indépendante d'un template existant (par exemple un template fourni par midPoint). Utilisez cela pour commencer rapidement depuis un modèle sans créer une dépendance d'héritage.

Conseils pratiques avant de créer/importer une ressource :

1. Assurez-vous que le *connecteur* (bundle) est disponible dans MidPoint : `Configuration` → `Repository objects` → `Connectors`. Si le connecteur (CSV/LDAP, etc.) n'apparaît pas, MidPoint ne pourra pas l'utiliser et vous verrez des erreurs comme "Cannot find connector".
   - Si le connecteur manque, installez le bundle de connecteur fourni par Evolveum (ou celui qui correspond à votre service) dans le dossier `connectors` du serveur midPoint ou importez l'objet ConnectorType via l'UI (Import object).
   - Pour le CSV, le type attendu dans nos templates est : `com.evolveum.polygon.connector.csv.CsvConnector`
   - Pour LDAP (ApacheDS) : `com.evolveum.polygon.connector.ldap.LdapConnector`

2. Si vous importez un XML depuis ce dépôt (ex. `hr-csv.xml`, `ldap-resource.xml`) et que midPoint se plaint du connecteur introuvable, vérifiez le `connectorType` dans la section ConnectorRef et comparez-le aux Connectors listés dans la configuration.

3. Avec une ressource CSV : copiez le fichier CSV dans le conteneur (voir la section "Préparer le fichier CSV" plus haut) — la plupart des erreurs d'import sont dues à un fichier manquant ou à un mauvais `filePath` dans la configuration du connector.

Exemple rapide de démarche pour créer une ressource à partir d'un modèle local (recommandé si vous avez nos fichiers) :

1. Aller dans `Resources` → `New resource` → **Copy from template**
2. Choisir `Import from repository` (ou `Choose template`) et sélectionner le template déjà présent (ou importer `hr-csv.xml` puis utiliser **Inherit template**)
3. Sauvegarder et aller dans la ressource nouvellement créée → `Configuration` → `Test connection`

Si vous voulez, je peux ajouter un court 1) script d'import automatique (pour uploader les XML dans midPoint via REST API) ou 2) un exemple d'objet ConnectorType exporté pour les connecteurs CSV/LDAP pour faciliter l'installation côté midPoint. Dites-moi ce que vous préférez.
