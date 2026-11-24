## Projet 3 — Passerelle de provisionnement IAM intelligente

Ce dépôt contient l’ensemble des artefacts produits pour le projet SAE de développement d’une gateway de provisionnement multi-cibles pilotée par des règles dynamiques et assistée par IA.

### Structure du dépôt

- `docs/` — livrables textuels (plans de sprint, backlog, rapports, etc.).
- `gateway/` — code source de la passerelle (API, moteur de règles, connecteurs).
- `infrastructure/` — scripts d’installation, docker-compose, automatisation MidPoint/ApacheDS.
- `datasets/` — exports fictifs (CSV/Excel) RH et systèmes cibles.
- `presentations/` — supports marketing, techniques et soutenance.
- `media/` — captures d’écran, schémas d’architecture, vidéos (liens).

Chaque dossier possède un fichier `README.md` décrivant son contenu et la façon de générer ou mettre à jour les artefacts.

### Prochaines étapes

1. Élaborer les livrables de cadrage (état de l’art, backlog, politique IAM).
2. Prototyper l’architecture gateway (API REST, moteur de règles, connecteurs mock).
3. Mettre en place l’environnement MidPoint/ApacheDS/Odoo via Docker.
4. Produire les guides utilisateurs, rapports d’implémentation et supports de présentation.

Tous les documents devront référencer l’adresse `achibani@gmail.com` comme co-auteur dans les métadonnées ou en-têtes.

### Licence

Le code source (`gateway/`, `infrastructure/`, `scripts/` et les fichiers de configuration à la racine) est publié sous [licence MIT](LICENSE).

La licence ne couvre **pas** :

- les documents et supports de présentation (`docs/`, `presentations/`, `media/`), qui restent soumis aux règles du projet universitaire et à leurs auteurs ;
- les logos du laboratoire LISSI et de l'IUT (`Lissi-cmjn.png`, `cropped-Logo-INFO-FOND-BLANC.jpg`), qui appartiennent à leurs propriétaires.

