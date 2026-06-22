# Rapport de réalisation
## Plateforme IAM Gateway — Passerelle de provisionnement IAM intelligente avec interface No-Code et assistant IA intégré

> **Projet** : SAE S5/S6 — BUT Informatique, UPEC / Laboratoire LISSI
> **Dépôt GitHub** : <https://github.com/Nostradam4ik/IAM-Gateway>
> **Révision documentée** : commit `50d2bc6` (branche `main`)
> **Date de rédaction** : juin 2026
> **Co-auteur référencé** (conformément au `README.md`) : `achibani@gmail.com` (Abdelghani Chibani)
> **Volume** : ~40 pages

---

## Table des matières

| Section | Titre | Pages (est.) |
|---|---|---|
| 1 | Introduction et contexte général | 4–5 |
| 1.1 | Contexte académique et institutionnel | 1 |
| 1.2 | Problématique métier — La gestion des identités numériques | 1,5 |
| 1.3 | Objectifs du projet | 0,5 |
| 1.4 | Périmètre et contraintes | 0,5 |
| 2 | Architecture technique | 5–6 |
| 2.1 | Principes directeurs d'architecture | 1 |
| 2.2 | Vue d'ensemble et diagramme | 1 |
| 2.3 | Description détaillée de chaque composant | 2,5 |
| 2.4 | Architecture interne du service gateway | 1,5 |
| 3 | Fonctionnalités réalisées | 8–10 |
| 4 | Audit de sécurité complet | 4–5 |
| 5 | Qualité logicielle et DevOps | 3–4 |
| 6 | Modèle de données et persistance | 3–4 |
| 7 | Infrastructure Docker et déploiement | 2–3 |
| 8 | Difficultés rencontrées et solutions | 2–3 |
| 9 | Limites actuelles et perspectives | 2 |
| 10 | Conclusion | 1 |
| Annexes | A (endpoints), B (env), C (dépendances), D (commandes), E (glossaire) | 5–6 |

**Chiffres-clés du projet** (mesurés sur la révision `50d2bc6`) : **149 endpoints** REST répartis sur **14 routeurs**, **14 services** Docker, **82 fichiers Python** totalisant **27 406 lignes**, **25 fichiers** TypeScript/TSX (frontend), **13 fonctions de test** automatisées, **54 commits**, **13 vulnérabilités de sécurité** corrigées et tracées.

---

## 1. Introduction et contexte général

### 1.1 Contexte académique et institutionnel

Le présent rapport documente la réalisation de la plateforme **IAM Gateway**, développée dans le cadre d'une **SAE (Situation d'Apprentissage et d'Évaluation)** des semestres S5 et S6 du **BUT Informatique** de l'**UPEC (Université Paris-Est Créteil)**, en lien avec le **laboratoire LISSI**. Dans le référentiel du BUT (Bachelor Universitaire de Technologie), une SAE n'est pas un simple exercice : il s'agit d'une mise en situation professionnelle d'envergure, conçue pour que les compétences visées par le diplôme soient mobilisées de manière intégrée sur un livrable réaliste. Là où les ressources (cours, TD, TP) apportent des savoirs disciplinaires isolés, la SAE demande à l'étudiant de les **combiner** pour résoudre un problème complexe, depuis l'analyse du besoin jusqu'à la livraison d'un produit fonctionnel et documenté. La plateforme IAM Gateway s'inscrit pleinement dans cette logique : elle exige la maîtrise simultanée de l'architecture logicielle, de la sécurité applicative, de l'intégration de systèmes hétérogènes, du DevOps et de la communication technique.

Le rattachement au laboratoire **LISSI** (Laboratoire Images, Signaux et Systèmes Intelligents) confère au projet une dimension applicative ancrée dans des problématiques réelles d'ingénierie des systèmes d'information. La gestion des identités et des accès (IAM) constitue un domaine transversal critique : toute organisation, qu'elle soit académique, industrielle ou administrative, doit gouverner le cycle de vie de centaines, voire de milliers d'identités numériques réparties sur des dizaines de systèmes. Le choix de ce sujet pour une SAE de fin de cursus n'est donc pas anodin : il confronte l'étudiant à un domaine où l'erreur n'est pas tolérée (une mauvaise gestion des accès se traduit directement par des incidents de sécurité ou des manquements réglementaires), et où la qualité de l'ingénierie se mesure à l'aune de la robustesse, de l'auditabilité et de la maintenabilité.

L'**équipe projet** se compose des contributeurs identifiables dans l'historique Git du dépôt. Les deux identités d'auteur Git principales sont **Nostradam4ik / Andrii Zhmuryk** et la référence **`achibani@gmail.com` / Abdelghani Chibani**, ce dernier étant systématiquement crédité comme co-auteur dans les métadonnées des livrables conformément à la consigne inscrite dans le `README.md` du dépôt. L'analyse des statistiques de contribution montre une activité concentrée et soutenue : sur les **54 commits** que compte la branche `main`, la majorité relève d'un travail d'ingénierie incrémental (durcissement de sécurité commit par commit, fiabilisation des connecteurs, documentation). Les contributions Git se répartissent comme suit :

| Contributeur (Git) | Commits | Rôle |
|---|---|---|
| Nostradam4ik / Andrii Zhmuryk | 33 | Développement, architecture, sécurité |
| Andrii Zhmuryk (2ᵉ identité) | 21 | Développement, connecteurs, documentation |
| Co-auteur référencé : `achibani@gmail.com` (Abdelghani Chibani) | — | Crédité dans les livrables (consigne `README.md`) |

La méthodologie de collaboration s'appuie sur **Git et GitHub** avec un modèle de branches de fonctionnalités et de **Pull Requests** revues avant fusion, complété par une intégration continue (GitHub Actions) qui sert de garde-fou automatique à chaque poussée de code. Cette organisation reflète des pratiques professionnelles : aucune fonctionnalité n'est intégrée directement sur la branche principale ; chaque chantier vit sur sa propre branche, est soumis à revue via une Pull Request, et n'est fusionné qu'une fois les vérifications automatiques passées. La convention de nommage des commits, inspirée des *Conventional Commits* (`type(scope): description`), et la granularité fine des commits — particulièrement visible dans le chantier de sécurité, où chaque vulnérabilité a son commit dédié — témoignent d'une discipline de traçabilité qui dépasse le cadre d'un simple projet étudiant. Cette rigueur méthodologique est, en soi, l'une des compétences que la SAE vise à développer : savoir non seulement produire du code, mais le produire de manière **collaborative, tracée et vérifiable**.

Sur le plan **temporel**, le projet s'étend sur environ **sept mois**. Le premier commit (« Initial import ») est daté du **24 novembre 2025** ; il marque la mise en place des livrables de cadrage et de la structure documentaire. S'ensuit une phase de prototypage de l'architecture (API REST, moteur de règles, connecteurs), puis deux chantiers d'ingénierie majeurs menés sur des branches dédiées : un chantier de **durcissement de sécurité** (`security-hardening`, 13 commits de correction) et un chantier d'**amélioration des connecteurs** (`iam-connector-improvements`, fiabilisation TLS/timeout/retry, modèles IAM typés, durcissement Docker). La fusion finale de la seconde Pull Request dans `main` date du **21 juin 2026** (commit de merge `50d2bc6`). Cette chronologie illustre une démarche **itérative et incrémentale** : la fonctionnalité d'abord, puis la sécurisation, puis la fiabilisation et la documentation — chaque phase capitalisant sur la précédente. Le tableau ci-dessous synthétise les grandes phases du projet :

| Phase | Période indicative | Livrables et chantiers |
|---|---|---|
| Cadrage | nov. 2025 | Import initial, structure documentaire, livrables de cadrage |
| Prototypage | hiver 2025–2026 | API REST, moteur de règles, connecteurs initiaux, stack Docker |
| Durcissement sécurité | printemps 2026 | Branche `security-hardening` : 13 corrections de sécurité tracées |
| Fiabilisation connecteurs | printemps 2026 | Branche `iam-connector-improvements` : TLS/timeouts/retry, modèles IAM typés, durcissement Docker |
| Documentation & clôture | juin 2026 | Fiches techniques, ARCHITECTURE.md, fusion finale (`50d2bc6`, 21 juin 2026) |

Les **objectifs pédagogiques** servis par ce projet sont multiples et couvrent l'essentiel des compétences attendues d'un diplômé en informatique orienté systèmes et réseaux. On y trouve d'abord l'**architecture micro-services** : décomposer un système complexe en services autonomes, conteneurisés, communiquant par API. Ensuite la **sécurité applicative** : authentification, autorisation, protection contre les injections, gestion des secrets — abordée non comme un vernis final mais comme un audit structuré ayant produit treize corrections traçables. Vient également l'**intégration de systèmes** : faire dialoguer des technologies hétérogènes (REST, LDAP, XML-RPC, SQL) derrière une abstraction uniforme. Le **DevOps** est représenté par la conteneurisation Docker, l'orchestration Compose et le pipeline CI/CD. Enfin, la **gestion de projet agile** (branches, PR, revue, intégration continue) et la **communication technique** (ce rapport, l'`ARCHITECTURE.md`, les fiches techniques) parachèvent le panorama des compétences mobilisées.

### 1.2 Problématique métier — La gestion des identités numériques

La **gestion des identités et des accès** (*Identity and Access Management*, IAM) désigne l'ensemble des politiques, processus et technologies qui permettent à une organisation de garantir que **les bonnes personnes** disposent du **bon niveau d'accès** aux **bonnes ressources**, au **bon moment**, et pour les **bonnes raisons**. Cette discipline repose sur quelques concepts fondateurs qu'il convient de distinguer rigoureusement. Le **cycle de vie de l'identité** décrit la trajectoire d'un compte depuis sa création jusqu'à sa suppression, en passant par toutes ses évolutions. La **gouvernance des accès** (IGA, *Identity Governance and Administration*) ajoute à la simple administration la dimension de contrôle : revues périodiques, certification des droits, séparation des tâches. L'**authentification** répond à la question « qui êtes-vous ? » (vérification de l'identité, par mot de passe, jeton, biométrie), tandis que l'**autorisation** répond à « qu'avez-vous le droit de faire ? » (attribution et vérification des permissions) — deux mécanismes distincts qu'une architecture saine ne confond jamais. Enfin, le **principe du moindre privilège** stipule qu'une identité ne doit détenir que les droits strictement nécessaires à sa fonction, ni plus, ni pour plus longtemps que nécessaire.

Concrètement, dans une entreprise, ces concepts se matérialisent par des situations quotidiennes. Lorsqu'un commercial est recruté, il lui faut un compte dans l'annuaire d'entreprise (pour ouvrir sa session Windows), une boîte e-mail, un accès au CRM, un accès à l'ERP pour consulter les stocks, parfois un badge physique et un accès VPN pour le télétravail. Chacun de ces accès est géré par un système différent, avec sa propre console d'administration. Multipliée par le nombre d'embauches, de mutations et de départs annuels, cette charge devient ingérable manuellement et, surtout, **dangereuse**.

C'est précisément ce que capture le **problème JML (Joiner / Mover / Leaver)**, qui structure toute réflexion IAM. Le moment **Joiner** (l'arrivée) exige de créer **simultanément** et de manière cohérente l'ensemble des comptes d'un nouvel employé : compte Active Directory ou LDAP, messagerie, accès ERP, badge, VPN. La difficulté n'est pas seulement la multiplicité des cibles, mais la **synchronisation** : un nouvel arrivant qui attend une semaine son accès à l'ERP est improductif, et chaque création manuelle est une occasion d'erreur. Le moment **Mover** (la mobilité) — promotion, changement de service, mutation géographique — est le plus subtil et le plus souvent mal géré : il faut **accorder** les nouveaux droits **et retirer** les anciens. Or, dans la pratique, on ajoute volontiers les nouveaux accès mais on oublie de révoquer les anciens, ce qui produit une **accumulation de privilèges** (*privilege creep*) : au fil de sa carrière, un employé finit par cumuler des accès qu'il ne devrait plus avoir, créant un risque majeur. Le moment **Leaver** (le départ) est le plus critique en matière de sécurité : à la fin d'un contrat, **tous** les accès doivent être désactivés en **quelques minutes**, pas en quelques semaines. Un compte resté actif après un départ — un **compte orphelin** — est une porte d'entrée idéale pour un ancien employé malveillant ou pour un attaquant ayant compromis des identifiants oubliés. Le tableau suivant synthétise les trois moments JML et la réponse qu'y apporte IAM Gateway :

| Moment | Besoin métier | Risque si mal géré | Réponse d'IAM Gateway |
|---|---|---|---|
| **Joiner** | Créer tous les comptes le premier jour | Improductivité, erreurs de saisie | Provisionnement multi-cibles via rôles MidPoint, en une requête |
| **Mover** | Ajuster les droits, retirer les anciens | Accumulation de privilèges (*privilege creep*) | Comparaison temps réel + réconciliation pour détecter les écarts |
| **Leaver** | Désactiver partout en minutes | Comptes orphelins, accès résiduels | Désactivation multi-systèmes + job automatique sur contrats expirés |

Les chiffres connus du secteur soulignent la gravité de l'enjeu. Les études récurrentes sur les violations de données (notamment les rapports annuels de référence du secteur) attribuent une part majoritaire des compromissions à un facteur humain ou à des identifiants volés/mal gérés. Les comptes orphelins et les droits dormants figurent systématiquement parmi les premières causes de mouvement latéral lors d'une attaque : un attaquant qui obtient un accès initial cherche à rebondir, et un compte sur-privilégié oublié lui en donne les moyens. Le coût d'une mauvaise IAM ne se limite donc pas à l'incident technique : il englobe les amendes réglementaires, la perte de confiance, l'interruption d'activité et le coût de remédiation, souvent chiffré en centaines de milliers d'euros pour une violation significative.

L'**enjeu réglementaire** renforce encore cette nécessité. Le **RGPD** (Règlement Général sur la Protection des Données), en son **article 25** relatif à la *protection des données dès la conception et par défaut* (*privacy by design and by default*), impose que les systèmes limitent par construction l'accès aux données personnelles aux seules personnes habilitées : une IAM défaillante est de facto une non-conformité. La norme **ISO/IEC 27001**, dans son domaine **A.9** consacré au *contrôle d'accès*, exige des procédures formelles de gestion des droits, de revue périodique et de révocation. Dans le contexte d'un ERP manipulant des données financières, les exigences de type **SOX** (Sarbanes-Oxley) imposent une traçabilité et une séparation des tâches strictes sur les accès. Dans tous ces cadres, l'absence d'une piste d'audit fiable et d'un processus maîtrisé de provisionnement constitue un **risque de conformité** directement opposable à l'organisation.

Concrètement, un auditeur de conformité posera des questions auxquelles une IAM défaillante ne sait pas répondre : « Qui a eu accès à cette donnée personnelle, et sur quelle base ? », « Cet ancien employé a-t-il bien perdu tous ses accès le jour de son départ ? », « Qui a approuvé l'octroi de ce droit, et quand ? ». Sans piste d'audit horodatée et sans processus d'approbation tracé, ces questions restent sans réponse, et l'organisation s'expose à des sanctions. Le RGPD prévoit des amendes pouvant atteindre 4 % du chiffre d'affaires mondial ; au-delà du montant, c'est l'**incapacité à démontrer la maîtrise** qui est sanctionnée. IAM Gateway répond précisément à cette exigence par sa piste d'audit systématique (chaque opération journalisée, horodatée, attribuée à un acteur) et par ses workflows d'approbation qui matérialisent et conservent la trace de chaque validation — transformant la conformité d'une promesse en une propriété démontrable du système.

Face à ces enjeux, les **solutions existantes** présentent chacune des limites qui justifient une approche nouvelle. Les **suites IGA d'entreprise** (SailPoint, Saviynt, One Identity) sont fonctionnellement très riches mais leur **coût est prohibitif** — souvent supérieur à 100 000 € par an en licences et intégration — ce qui les réserve aux grandes organisations. **MidPoint**, la solution IGA open-source d'Evolveum, est techniquement puissante (elle gère identités, rôles, ressources, réconciliation) mais sa **complexité de configuration** est réelle : elle suppose une expertise pointue en Java et en XML pour modéliser les ressources, les rôles et les mappings, ce qui la rend difficile d'accès aux équipes non spécialisées. Les **scripts personnalisés** (Python, PowerShell) que beaucoup d'organisations bricolent sont **fragiles, non maintenables et non auditables** : ils dérivent au fil du temps, ne survivent pas au départ de leur auteur, et n'offrent ni interface ni traçabilité. Enfin, **Keycloak** seul ne résout qu'une partie du problème : c'est un excellent fournisseur d'**authentification** (SSO, OIDC), mais il n'assure pas la **gouvernance** des identités ni le provisionnement multi-cibles.

Le tableau suivant synthétise ces limites et la réponse du projet :

| Solution | Forces | Limites | Réponse d'IAM Gateway |
|---|---|---|---|
| SailPoint / Saviynt | IGA complet | Coût > 100 k€/an | Pile open-source gratuite |
| MidPoint seul | Moteur IGA puissant | Complexité Java/XML | Interface no-code par-dessus |
| Scripts custom | Souplesse initiale | Fragiles, non auditables | API tracée + tests + CI |
| Keycloak seul | SSO/OIDC excellent | Pas de gouvernance IGA | Provisionnement multi-cibles |

C'est dans cet espace que se positionne la **proposition de valeur d'IAM Gateway**. Le projet ne prétend pas remplacer MidPoint, mais le **rendre exploitable** : il offre un **plan de contrôle unique** au-dessus de MidPoint et des systèmes cibles, doublé d'une **interface no-code** (moteur de règles éditable, workflows configurables) qui démocratise l'usage de l'IGA pour des équipes non expertes en Java/XML. La plateforme repose intégralement sur une **pile open-source** (FastAPI, React, PostgreSQL, Redis, Qdrant, MidPoint, Keycloak, OpenLDAP, Odoo), ce qui élimine le coût de licence prohibitif des suites commerciales. Enfin, elle est **déployable en une seule commande** (`docker compose up`), abaissant radicalement la barrière à l'entrée. En synthèse, IAM Gateway vise à conjuguer la puissance d'un hub IGA mature, l'accessibilité d'une interface moderne et l'économie d'une pile libre — répondant ainsi point par point aux limites des approches existantes.

### 1.3 Objectifs du projet

L'**objectif principal** du projet est de concevoir et réaliser une **passerelle d'API intelligente, multi-cibles**, qui centralise et automatise le provisionnement des identités vers un ensemble de systèmes hétérogènes, tout en restant pilotable par des équipes non spécialistes. Cette passerelle doit s'interposer entre un hub IGA (MidPoint) et les systèmes cibles (annuaire LDAP, ERP Odoo, base SQL « intranet », fournisseur d'identité Keycloak), en ajoutant la valeur que le hub seul n'apporte pas : une API REST documentée, une interface web d'administration, un moteur de règles éditable, des workflows d'approbation et une piste d'audit consultable.

Les **objectifs fonctionnels** se déclinent en cinq grands domaines, qui structureront d'ailleurs la section 3 de ce rapport. Le premier domaine est le **provisionnement multi-cibles** lui-même, décliné selon deux paradigmes (mode hub via MidPoint et mode direct avec rollback). Le deuxième domaine regroupe l'**authentification et l'autorisation** : connexion par jeton JWT, contrôle d'accès basé sur les rôles, révocation de session. Le troisième domaine est l'**automatisation pilotée par règles** : un moteur de calcul d'attributs et un ordonnanceur de tâches périodiques. Le quatrième domaine couvre la **gouvernance** : workflows d'approbation multi-niveaux et réconciliation entre systèmes. Le cinquième domaine, plus innovant, rassemble l'**assistant IA** et la **recherche sémantique d'audit**, qui apportent une couche d'intelligence à l'exploitation.

Les **objectifs non-fonctionnels** sont tout aussi structurants, car ils déterminent la qualité d'ingénierie du livrable. La **sécurité** est un objectif de premier rang : l'application doit refuser de démarrer avec des secrets faibles, authentifier toute requête, autoriser finement, se prémunir des injections et tracer chaque action. La **performance** impose une architecture asynchrone qui ne bloque pas la boucle d'événements et qui sert les lectures depuis un cache mémoire. L'**observabilité** exige des journaux structurés et corrélés permettant de reconstituer le parcours d'une requête. La **maintenabilité**, enfin, s'appuie sur une architecture en couches strictes, une validation déclarative des entrées et une couverture de test du cœur sécurité.

Les **critères de succès** retenus sont mesurables. Sur le plan fonctionnel, la plateforme expose effectivement **149 endpoints** opérationnels couvrant les cinq domaines, et orchestre **14 services** conteneurisés. Sur le plan de la sécurité, **13 vulnérabilités** ont été identifiées et corrigées, chacune dans un commit dédié et tracé. Sur le plan de la qualité, une **suite de tests** automatisés couvre le cœur sécurité (JWT, RBAC, validation des secrets, anti-injection) et un **pipeline CI/CD** bloque toute régression à la racine. Sur le plan du déploiement, la stack complète se lève par une commande unique et se documente exhaustivement (quatre fiches techniques et ce rapport).

Le tableau ci-dessous met en regard les objectifs et leurs indicateurs de réalisation :

| Objectif | Indicateur de succès | Réalisation |
|---|---|---|
| Plan de contrôle unique | Endpoints REST exposés | 149 endpoints / 14 routeurs |
| Orchestration multi-cibles | Services intégrés | 14 services (LDAP, Odoo, SQL, Keycloak, MidPoint…) |
| Sécurité applicative | Vulnérabilités corrigées et tracées | 13 commits de sécurité |
| Qualité logicielle | Tests automatisés + CI bloquante | 13 tests, pipeline 2 jobs |
| Déploiement reproductible | Commande unique + documentation | `docker compose up` + 5 documents |
| Interface no-code | Moteur de règles + workflows éditables | Règles Jinja2 sandboxées, workflows configurables |

Ces critères, tous atteints ou substantiellement atteints, fournissent une grille d'évaluation objective de la réussite du projet, indépendante de toute appréciation subjective.

### 1.4 Périmètre et contraintes

Le **périmètre couvert** par le projet comprend l'intégralité de la passerelle applicative — backend FastAPI et frontend React — ainsi que l'orchestration de l'écosystème IAM qui l'entoure. Sont inclus : le provisionnement vers OpenLDAP, Odoo, la base SQL « intranet » et Keycloak (via webhook) ; le moteur de règles d'attributs ; les workflows d'approbation multi-niveaux ; la réconciliation et la comparaison inter-systèmes ; les synchronisations planifiées depuis Odoo ; l'assistant IA optionnel et la recherche d'audit sémantique ; ainsi que l'ensemble du socle de sécurité (JWT, RBAC, rate-limiting, HMAC, anti-injection) et de la chaîne DevOps (Docker, Compose, CI/CD).

Le **hors-périmètre** est tout aussi explicite, car le reconnaître est une marque de maturité d'ingénierie. Ne sont pas réalisés (et sont documentés comme tels) : les connecteurs GLPI et Firebase, volontairement laissés en `NotImplementedError` en mode statique et destinés à être ajoutés dynamiquement ; la terminaison TLS et le reverse-proxy de production ; la gestion des secrets par un coffre externe (Vault) ; l'immuabilité cryptographique de la piste d'audit ; et l'outillage de sauvegarde/restauration automatisé. Certaines méthodes de persistance du moteur de règles renvoient encore des données par défaut (mocks), ce qui est assumé et inscrit à la feuille de route. Le tableau suivant clarifie la frontière du périmètre :

| Domaine | Dans le périmètre | Hors périmètre |
|---|---|---|
| Cibles | OpenLDAP, Odoo, SQL intranet, Keycloak (webhook) | GLPI, Firebase (dynamiques, non implémentés) |
| Provisionnement | Mode hub + mode direct avec rollback | — |
| Gouvernance | Workflows, réconciliation, comparaison | Recertification, SCIM/SAML |
| Sécurité | JWT, RBAC, rate-limit, HMAC, anti-injection | TLS production, coffre de secrets, WAF |
| IA | Assistant + recherche d'audit (optionnels) | Embeddings sémantiques réels |
| Exploitation | Docker Compose, CI/CD, logs JSON | Kubernetes, supervision Prometheus/Grafana |

Ces choix de périmètre traduisent une priorisation lucide : livrer un cœur fonctionnel, sûr et démontrable plutôt qu'un ensemble plus large mais inégalement abouti.

Les **contraintes techniques** ont encadré l'ensemble des décisions. La première contrainte est l'usage exclusif de **technologies open-source**, pour des raisons de coût (cf. §1.2) et de reproductibilité académique. La deuxième est le **déploiement par Docker** : l'ensemble du système doit se lever dans des conteneurs orchestrés par Docker Compose, sans installation manuelle de dépendances sur la machine hôte. La troisième contrainte impose un **backend Python** (FastAPI, asynchrone) et un **frontend React** (Vite, TypeScript), choix justifiés en §2 et §5. Ces contraintes, loin d'être des limitations arbitraires, structurent positivement le projet : elles imposent une discipline de portabilité, de reproductibilité et de séparation nette entre la logique applicative (conteneur gateway) et son environnement.

---

## 2. Architecture technique

### 2.1 Principes directeurs d'architecture

Le premier principe directeur de l'architecture est la **séparation des préoccupations** (*separation of concerns*), matérialisée par un découpage en couches strictes au sein du service gateway : la couche **API** (routeurs), la couche **services** (logique métier), la couche **connecteurs** (adaptateurs vers les systèmes externes) et la couche **données/transverse** (`core` et `models`). Chaque couche n'a connaissance que de la couche immédiatement inférieure : un routeur ne parle jamais directement à un connecteur sans passer par un service, et un service n'écrit jamais dans la base sans passer par les abstractions de `core`. Cette discipline présente un double bénéfice. D'une part, elle rend chaque couche **substituable** : ajouter un système cible se résume à écrire un nouveau connecteur, sans toucher à l'API ni aux services ; changer de moteur de stockage de cache n'affecte que `core`. D'autre part, elle **concentre les responsabilités transversales** au bon endroit : l'authentification et l'autorisation vivent dans la couche API (via l'injection de dépendances de FastAPI), la persistance dans `core`, la connaissance des protocoles externes dans les connecteurs.

Le deuxième principe est celui de l'**API sans état avec état externalisé** (*stateless API with external state*). Le service gateway lui-même ne conserve aucun état de session en mémoire de processus : tout l'état partagé est déporté dans des magasins externes dédiés. Les jetons révoqués et les compteurs de limitation de débit vivent dans **Redis** ; les opérations, l'audit, les workflows et les utilisateurs vivent dans **PostgreSQL** ; les vecteurs d'audit dans **Qdrant**. Ce choix est ce qui rendrait la gateway **horizontalement scalable** : on pourrait lancer plusieurs instances derrière un répartiteur de charge, chacune partageant le même état externe, sans collision. Il améliore aussi la **résilience** : le redémarrage d'une instance ne perd aucune donnée, puisque l'état n'y réside pas. Le seul élément de cache local (le `MemoryStore`) est explicitement un cache de **lecture** reconstruit au démarrage depuis PostgreSQL, jamais une source de vérité.

Le troisième principe est la **dégradation gracieuse** (*graceful degradation*) : la défaillance d'un composant non critique ne doit pas provoquer l'effondrement du système, mais une dégradation maîtrisée et journalisée. Plusieurs mécanismes l'incarnent dans le code. Si **Redis** est indisponible, la vérification de limitation de débit retourne « autorisé » (*fail-open*) plutôt que de bloquer toutes les connexions : on privilégie la disponibilité du service sur la défense en profondeur, choix assumé et tracé dans le code (`check_rate_limit`). Si **Qdrant** est indisponible, l'indexation et la recherche sémantique sont désactivées mais l'audit relationnel continue d'être écrit dans PostgreSQL ; aucune opération de provisionnement n'échoue à cause de Qdrant. Au démarrage (`main.py`), les connexions à Redis et Qdrant sont tentées et leur échec est simplement journalisé (`status="unavailable"`) sans interrompre le boot. Cette philosophie distingue clairement les composants **critiques** (PostgreSQL, sans lequel rien ne peut être persisté) des composants **d'amélioration** (Redis, Qdrant) dont l'absence dégrade l'expérience sans la rompre. Cette classification n'est pas qu'un principe théorique : elle se traduit par des choix de code précis. Pour Redis, le repli est différencié selon l'opération — `False` pour une écriture de blacklist (l'opération n'a pas eu lieu, mais on ne lève pas d'exception), `True` pour la limitation de débit (on autorise plutôt que de bloquer tout le monde). Pour Qdrant, les méthodes d'indexation et de recherche retournent silencieusement `False`/`[]` si le client n'est pas connecté, de sorte qu'un audit continue d'être écrit en base même si son indexation vectorielle échoue. Ce traitement explicite de chaque mode de défaillance — plutôt qu'une propagation aveugle d'exceptions — est la marque d'une conception qui a anticipé les pannes partielles plutôt que de les subir.

Le quatrième principe est l'**infrastructure as code**, incarnée par le fichier `docker-compose.yml`. L'intégralité de l'écosystème — les 14 services, leurs images et versions, leurs ports, leurs volumes, leurs réseaux, leurs dépendances et leurs sondes de santé — est décrite déclarativement dans un unique fichier versionné. Il n'existe aucune étape d'installation manuelle, aucune configuration implicite reposant sur l'état de la machine hôte. Cette approche garantit la **reproductibilité** (le même fichier produit le même environnement sur n'importe quelle machine dotée de Docker), la **traçabilité** (toute modification de l'infrastructure passe par un commit) et la **documentation par le code** (le fichier sert lui-même de spécification de l'environnement). Conjuguée au principe d'API sans état, cette infrastructure déclarative pose les fondations d'une exploitation moderne, où l'environnement est un artefact versionné au même titre que le code applicatif. Ce principe se prolonge dans les `Dockerfile` (la recette de construction des images est, elle aussi, du code versionné), dans le script de migration `migrations.py` (le schéma de base est du code), et dans le pipeline CI (`ci.yml`, le processus de qualité est du code). L'ensemble forme une chaîne où **chaque maillon de l'environnement et du processus est décrit, versionné et reproductible** — par opposition à une exploitation artisanale reposant sur des actions manuelles non tracées. Cette discipline a une vertu pédagogique directe : elle force à expliciter ce qui, dans une approche manuelle, resterait implicite et fragile, et constitue le socle sur lequel s'appuieraient les évolutions de production (Helm/Kubernetes, cf. §9.3).

### 2.2 Vue d'ensemble et diagramme

L'architecture globale du système peut être représentée par le diagramme suivant, qui fait apparaître les points d'entrée externes, le plan de contrôle (la gateway), les systèmes cibles et les magasins de données, ainsi que les protocoles de communication entre eux.

```
                          ┌───────────────────────────────────────────┐
                          │  React Admin UI (Vite → nginx)             │
                          │  http://localhost:3000                     │
                          └───────────────────────┬────────────────────┘
                                                  │ REST/HTTPS + JWT Bearer
                                                  │ (proxy nginx /api → :8000)
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Gateway  ·  http://localhost:8000                    │
│   api/ (149 endpoints) → services/ (logique) → connectors/ (adaptateurs)          │
│   JWT · RBAC · moteur de règles · workflows · scheduler · audit                   │
└───┬───────────┬───────────┬───────────┬────────────┬───────────┬──────────────────┘
    │ SQL       │ RESP       │ REST      │ REST       │ LDAP       │ XML-RPC
    │ (asyncpg) │            │ (Qdrant)  │ (httpx)    │ (ldap3)    │
    ▼           ▼            ▼           ▼            ▼            ▼
┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────────────┐ ┌──────────┐ ┌──────────┐
│gateway- │ │ Redis  │ │ Qdrant   │ │ MidPoint 4.4     │ │ OpenLDAP │ │ Odoo 17  │
│  db     │ │ :6379  │ │ :6333/4  │ │ :8080  (HUB)     │ │ :10389   │ │ :8069    │
│ :5434   │ │ JWT    │ │ semantic │ │ /ws/rest/*       │ │ inetOrg  │ │ res.users│
│ Postgres│ │ block- │ │ audit    │ │ Basic Auth       │ │ Person   │ │ hr.*     │
│ (cache) │ │ list   │ └──────────┘ └───┬─────────┬────┘ └──────────┘ └──────────┘
└─────────┘ │ +rate  │                  │ propage (connecteurs MidPoint)
            │ limit  │   ┌──────────────┼───────────────┬──────────────┐
            └────────┘   ▼              ▼               ▼              ▼
                     ┌──────────┐ ┌──────────┐   ┌──────────────┐ ┌──────────┐
                     │ OpenLDAP │ │ Odoo DB  │   │ intranet-db  │ │midpoint- │
                     │          │ │          │   │ :55432 (SQL) │ │ postgres │
                     └──────────┘ └──────────┘   └──────────────┘ │ :5433    │
                                                                  └──────────┘
   ┌──────────────────────────────────────────────────────────────────────────┐
   │  MidPoint  ──(webhook, HMAC-SHA256)──►  Gateway /api/v1/webhooks/...        │
   │            user-change  ──►  KeycloakProvisioner (REST admin API)  ──►      │
   │            Keycloak :8081  (keycloak-db Postgres, interne)                  │
   └──────────────────────────────────────────────────────────────────────────┘
```

Le **parcours d'une requête** illustre la circulation des données à travers ces couches. Lorsqu'un opérateur agit dans l'interface React (par exemple, pour provisionner un compte), le navigateur émet une requête HTTP vers nginx, qui la relaie via son proxy `/api` vers la gateway FastAPI sur le port 8000, en transportant le jeton JWT dans l'en-tête `Authorization`. La gateway commence par **authentifier** la requête (décodage et validation du JWT, vérification de la liste de révocation Redis), puis **autorise** l'action via la dépendance `require_role`. Le routeur concerné délègue alors au service métier approprié, qui, en mode hub, appelle le `MidPointConnector` ; celui-ci émet une requête REST authentifiée en Basic Auth vers MidPoint. MidPoint, à son tour, **propage** la création vers les systèmes cibles via ses propres connecteurs (LDAP, Odoo, SQL). Enfin, MidPoint notifie la gateway par un webhook signé HMAC pour répliquer le changement vers Keycloak. À chaque étape, une entrée d'audit est écrite et, si Qdrant est disponible, indexée pour la recherche sémantique.

Le système peut fonctionner selon **deux modes mutuellement exclusifs**, commutés par le paramètre `settings.MIDPOINT_ENABLED` (vrai par défaut), comme le montre le code du routeur `provision.py` qui aiguille vers `_provision_via_midpoint` ou `_provision_direct`. En **mode hub**, la gateway ne dialogue qu'avec MidPoint, qui détient la vérité des identités et orchestre la propagation via ses **rôles** (assigner le rôle `ldap-user` déclenche la création d'un compte LDAP, `odoo-user` un compte Odoo, `intranet-user` une ligne SQL). C'est le mode privilégié, car il délègue à un moteur IGA mature la complexité de la réconciliation et des projections (*shadows*). En **mode direct** (*legacy*), la gateway écrit elle-même chaque connecteur via la `ConnectorFactory` et suit chaque opération avec des **actions de rollback** afin d'annuler un succès partiel. Cette dualité, détaillée en §3.3, constitue la décision d'architecture la plus structurante du projet : elle permet à la fois de démontrer l'orchestration par un hub et de conserver un chemin autonome lorsque le hub est absent.

La **stratégie d'isolation réseau** mérite une attention particulière, car elle constitue la principale frontière de sécurité de l'infrastructure. Tous les conteneurs partagent un unique réseau bridge `iam-network`, sur lequel ils se joignent par leur nom de service. La protection ne provient donc pas d'une segmentation inter-services, mais du **binding des ports côté hôte** : les magasins de données (PostgreSQL `gateway-db`/`midpoint-postgres`/`intranet-db`, Redis, Qdrant, OpenLDAP) sont publiés exclusivement sur `127.0.0.1`, donc inaccessibles depuis le réseau local ou Internet, tandis que `odoo-db` et `keycloak-db` ne publient aucun port. Seuls les services applicatifs destinés à être consultés (gateway `:8000`, frontend `:3000`, MidPoint `:8080`, Keycloak `:8081`, Odoo `:8069`, phpLDAPadmin `:8088`) sont exposés plus largement. Cette approche, simple mais efficace dans un contexte de démonstration mono-hôte, est analysée et nuancée en §7.2.

Les protocoles employés entre la gateway et chaque système sont récapitulés ci-dessous, illustrant l'hétérogénéité que l'abstraction de connecteurs masque :

| Cible | Protocole | Bibliothèque | Authentification |
|---|---|---|---|
| MidPoint | REST HTTP/JSON (+ XML pour les rôles) | httpx | HTTP Basic |
| OpenLDAP | LDAP (389) / LDAPS (636) | ldap3 | bind DN + mot de passe |
| Odoo | XML-RPC (sur HTTP :8069) | xmlrpc.client | authenticate (uid) |
| SQL « intranet » | PostgreSQL (asyncpg) | asyncpg | utilisateur/mot de passe |
| Keycloak | REST admin API | httpx | token `admin-cli` |
| Redis | RESP | redis.asyncio | — (réseau interne) |
| Qdrant | REST / gRPC | qdrant-client | — (réseau interne) |

Cette diversité de protocoles (REST, LDAP, XML-RPC, SQL natif, RESP) au sein d'un même système est précisément ce qui justifie l'investissement dans une couche d'abstraction de connecteurs : sans elle, chaque service métier devrait connaître les particularités de chaque protocole, rendant le code inmaintenable.

### 2.3 Description détaillée de chaque composant

L'écosystème compte **14 services** orchestrés par Docker Compose. Cette sous-section décrit chacun d'eux en explicitant son rôle, le choix de son image et de sa version, ses interactions et la justification de ses ressources.

**`gateway` — Le plan de contrôle.** Cœur du système, ce service est l'application FastAPI construite localement à partir de l'image `python:3.11-slim`. Il expose les 149 endpoints REST, applique l'authentification et le RBAC, exécute le moteur de règles, les workflows et l'ordonnanceur, et pilote tous les connecteurs. Sa limite mémoire de **768 Mio** reflète une empreinte modérée, propre à une API asynchrone qui délègue le gros du travail aux systèmes externes. Il déclare une sonde de santé applicative interrogeant `/health` (intervalle 15 s, 40 s de grâce au démarrage) et dépend de `gateway-db`, `redis` et `qdrant`. Son exécution en utilisateur non privilégié (UID 10001) et le montage de son code en *bind mount* (`./gateway/app`) pour le rechargement à chaud complètent sa configuration.

**`gateway-frontend` — L'interface d'administration.** Ce service sert l'application React compilée. Il est construit en deux étapes (build Node puis service nginx) et n'embarque, dans son image finale, que **nginx:alpine** et les fichiers statiques compilés. Il publie le port `3000 → 80` et relaie les appels `/api` vers la gateway via un proxy nginx. Il dépend explicitement de `gateway` avec la condition `service_healthy`, garantissant que l'interface n'est servie qu'une fois l'API réellement opérationnelle. Il ne déclare ni limite mémoire ni volume, car son contenu est statique et reconstruit à chaque build d'image.

**`gateway-db` — Le magasin applicatif.** Instance **PostgreSQL 15** dédiée à la gateway, elle persiste les opérations de provisionnement, les journaux d'audit, les jobs de réconciliation, les workflows, les configurations de connecteurs et les utilisateurs. Publiée sur `127.0.0.1:5434` (jamais exposée au-delà de l'hôte), elle dispose d'une sonde `pg_isready -U gateway` (intervalle 10 s, 5 essais) qui conditionne le démarrage de la gateway, et d'un volume nommé `gateway_db_data` assurant la persistance des données entre redémarrages.

**`midpoint` — Le hub IGA central.** Ce service exécute **MidPoint 4.4** (image officielle `evolveum/midpoint:4.4`), pilier de l'architecture en mode hub. Il détient le référentiel des identités, gère les rôles et les ressources, et propage les changements vers les systèmes cibles via ses propres connecteurs. C'est le service le plus gourmand en mémoire : sa limite est fixée à **3 Gio** (avec `MP_MEM_MAX=2048m` et `MP_MEM_INIT=1024m` pour la JVM), car MidPoint repose sur une machine virtuelle Java dont l'empreinte est intrinsèquement élevée. Il dépend de `midpoint-postgres` (sain) et conserve sa configuration et son keystore dans le volume `midpoint_home`.

**`midpoint-postgres` — Le dépôt de MidPoint.** Instance **PostgreSQL 15** distincte dédiée au référentiel propre de MidPoint, publiée sur `127.0.0.1:5433`. La séparation de cette base de celle de la gateway relève d'un principe d'**autonomie de service** : chaque produit gère son schéma, ses montées de version et ses sauvegardes indépendamment. Elle dispose de sa propre sonde `pg_isready -U midpoint` et du volume `midpoint_postgres_data`.

**`keycloak` — Le fournisseur d'identité OIDC.** Ce service exécute **Keycloak 23.0** (image `quay.io/keycloak/keycloak:23.0`) et assure l'authentification SSO/OIDC des utilisateurs finaux. Il est provisionné **depuis MidPoint** : lorsqu'une identité change, MidPoint notifie la gateway par webhook, qui répercute la création/modification/suppression dans Keycloak via son API d'administration. Sa limite mémoire est de **1 Gio** (JVM). Il est lancé en `command: start-dev`, mode de développement non destiné à la production, et dépend de `keycloak-db`.

**`keycloak-db` — Le dépôt de Keycloak.** Instance **PostgreSQL 15** backing de Keycloak, **strictement interne** (aucun port publié sur l'hôte), dotée d'une sonde `pg_isready -U keycloak` et du volume `keycloak_db_data`. Son isolation totale du réseau hôte illustre le principe selon lequel un magasin de données qui n'a pas besoin d'être consulté de l'extérieur ne doit pas l'être.

**`openldap` — L'annuaire cible.** Ce service exécute **OpenLDAP** (image `osixia/openldap:1.5.0`) et constitue un système cible de provisionnement : il héberge les entrées `inetOrgPerson` et les groupes sous `dc=example,dc=com`. Il publie ses ports sur `127.0.0.1` uniquement (`10389` pour LDAP en clair, `10636` pour LDAPS) et conserve son annuaire et sa configuration dans deux volumes (`openldap_data`, `openldap_config`). C'est la cible privilégiée pour démontrer la gestion des comptes et des appartenances de groupe.

**`phpldapadmin` — L'inspecteur d'annuaire.** Interface web (image `osixia/phpldapadmin:0.9.0`) permettant de visualiser et d'administrer manuellement le contenu de l'annuaire LDAP. Publiée sur le port `8088`, elle dépend d'`openldap`. Sa présence est un confort de développement et de démonstration : elle permet de vérifier de visu que les comptes provisionnés par la gateway apparaissent bien dans l'annuaire.

**`odoo` — L'ERP, source RH et cible.** Ce service exécute **Odoo 17** (image `odoo:17`) et joue un double rôle : il est la **source de vérité RH** (employés, départements, contrats), d'où la gateway synchronise les identités vers MidPoint, et il est simultanément un **système cible** de provisionnement. Piloté en XML-RPC, il publie le port `8069` et dispose d'une limite mémoire de **1 Gio**, justifiée par son architecture à *workers* Python et son ORM. Il dépend d'`odoo-db` et conserve ses données dans les volumes `odoo_data` et `odoo_addons`.

**`odoo-db` — Le dépôt d'Odoo.** Instance **PostgreSQL 15** backing d'Odoo, **strictement interne**, avec sonde `pg_isready -U odoo` et volume `odoo_db_data`. Comme `keycloak-db`, elle n'expose aucun port à l'hôte.

**`intranet-db` — La cible SQL « intranet ».** Instance **PostgreSQL 15** représentant une application métier « intranet » fictive, cible du provisionnement SQL direct. Publiée sur `127.0.0.1:55432`, elle monte en plus un script d'initialisation (`infrastructure/sql/init-intranet.sql`) en lecture seule, exécuté au premier démarrage, et conserve ses données dans `intranet_db_data`. Elle illustre la capacité de la plateforme à écrire dans une base applicative arbitraire via le connecteur SQL.

**`redis` — Le cache atomique.** Ce service exécute **Redis 7** (image `redis:7-alpine`) et remplit trois fonctions de sécurité et de performance : la **liste noire des jetons JWT révoqués** (`blacklist:{jti}`), le **comptage atomique** de la limitation de débit du login (`rate:{key}`), et le cache de sessions et de tokens de workflow. Publié sur `127.0.0.1:6379`, il dispose d'une sonde `redis-cli ping` et du volume `redis_data`. Son choix s'impose par l'atomicité de ses opérations (scripts Lua) et sa latence sub-milliseconde.

**`qdrant` — La base vectorielle.** Ce service exécute **Qdrant v1.12.4** (image épinglée `qdrant/qdrant:v1.12.4`) et indexe les journaux d'audit sous forme de vecteurs pour permettre une recherche par similarité. Publié sur `127.0.0.1:6333` (REST) et `6334` (gRPC), il dispose d'une limite mémoire de **1 Gio** (l'index vectoriel résidant en mémoire) et du volume `qdrant_data`. Composant d'amélioration et non critique, son indisponibilité dégrade la recherche sémantique sans interrompre l'audit relationnel.

En synthèse, la somme des limites mémoire explicitement déclarées atteint **6 912 Mio (≈ 6,75 Gio)**, répartis sur cinq services (MidPoint 3 g, gateway 768 m, Keycloak/Odoo/Qdrant 1 g chacun) ; les neuf autres services, principalement les instances PostgreSQL, Redis et les interfaces, ne portent pas de limite explicite — un point d'amélioration discuté en §7.2 et §9.

Le tableau de synthèse suivant offre une vue d'ensemble des quatorze services et de leurs caractéristiques principales :

| Service | Image | Port hôte | Mem limit | Healthcheck |
|---|---|---|---|---|
| `gateway` | build (`python:3.11-slim`) | 8000 | 768m | `/health` |
| `gateway-frontend` | build (`nginx:alpine`) | 3000→80 | — | — |
| `gateway-db` | `postgres:15` | 127.0.0.1:5434 | — | `pg_isready` |
| `midpoint` | `evolveum/midpoint:4.4` | 8080 | 3g | — |
| `midpoint-postgres` | `postgres:15` | 127.0.0.1:5433 | — | `pg_isready` |
| `keycloak` | `quay.io/keycloak/keycloak:23.0` | 8081→8080 | 1g | — |
| `keycloak-db` | `postgres:15` | interne | — | `pg_isready` |
| `openldap` | `osixia/openldap:1.5.0` | 127.0.0.1:10389/10636 | — | — |
| `phpldapadmin` | `osixia/phpldapadmin:0.9.0` | 8088→80 | — | — |
| `odoo` | `odoo:17` | 8069 | 1g | — |
| `odoo-db` | `postgres:15` | interne | — | `pg_isready` |
| `intranet-db` | `postgres:15` | 127.0.0.1:55432 | — | `pg_isready` |
| `redis` | `redis:7-alpine` | 127.0.0.1:6379 | — | `redis-cli ping` |
| `qdrant` | `qdrant/qdrant:v1.12.4` | 127.0.0.1:6333/6334 | 1g | — |

### 2.4 Architecture interne du service gateway

**La couche API — 14 routeurs, 149 endpoints.** La couche API, sous `gateway/app/api/`, organise les endpoints en quatorze routeurs thématiques, chacun monté sous un préfixe `/api/v1/...` dans `main.py`. Cette organisation thématique (administration, provisionnement, MidPoint, règles, workflows, réconciliation, connecteurs, ordonnanceur, utilisateurs, permissions, comparaison temps réel, groupes LDAP, assistant IA, webhooks) rend la base de code navigable : un développeur sait immédiatement où chercher. Le mécanisme central qui irrigue toute la couche est l'**injection de dépendances** de FastAPI. L'authentification et l'autorisation ne sont pas codées en dur dans chaque handler ; elles sont déclarées comme dépendances : `current_user: dict = Depends(get_current_user)` impose un JWT valide, et `Depends(require_role(["admin", "iam_engineer"]))` impose un rôle. Ce style déclaratif est à la fois lisible (la signature de la fonction documente ses exigences de sécurité), testable (les dépendances s'invoquent isolément, cf. §5.2) et infalsifiable (il n'existe pas de chemin qui contourne la dépendance). La configuration **CORS**, posée en amont dans `main.py` via `CORSMiddleware`, restreint les origines à `settings.CORS_ORIGINS` et énumère explicitement les méthodes (`GET/POST/PUT/PATCH/DELETE/OPTIONS`) et les en-têtes autorisés (`Authorization`, `Content-Type`, `X-Request-ID`).

**La couche services — la logique métier.** Sous `gateway/app/services/`, cette couche concentre la logique applicative, isolée des détails de transport (API) et de protocole (connecteurs). Le `MidPointProvisionService` implémente le **mode hub** : il enregistre une opération dans le `MemoryStore`, traduit les systèmes cibles en rôles MidPoint via `_map_targets_to_roles`, et pilote le `MidPointConnector` pour créer l'utilisateur puis lui assigner les rôles déclencheurs. Le `ProvisionService` implémente le **mode direct** *legacy* : il résout les connecteurs via la `ConnectorFactory`, exécute le provisionnement cible par cible et **empile une action de rollback par succès** afin de pouvoir annuler un échec partiel ; il porte aussi la méthode `continue_after_approval` qui reprend le provisionnement après validation d'un workflow. Le `ConnectorManagementService` gère le CRUD des connecteurs dynamiques et leur synchronisation vers des *Resources* MidPoint. Le `SchedulerService` (APScheduler) pilote les synchronisations Odoo→MidPoint, l'attribution de rôles par département et le contrôle des contrats expirés. Le `UserService`, enfin, gère les utilisateurs de la gateway (table `gateway_users`) et résout les chaînes d'approbation par rôle pour les workflows. D'autres services complètent l'ensemble. Le tableau suivant récapitule la couche services :

| Service | Responsabilité |
|---|---|
| `MidPointProvisionService` | Provisionnement mode hub |
| `ProvisionService` | Provisionnement mode direct + rollback |
| `MidPointClient` / `MidPointResourceService` | Client REST bas niveau / gestion des Resources |
| `RuleEngine` | Calcul d'attributs (Jinja2 sandboxé) |
| `WorkflowService` | Workflows d'approbation multi-niveaux |
| `ReconciliationService` | Réconciliation et divergences |
| `SchedulerService` | Jobs planifiés (sync, contrats, rôles) |
| `AuditService` | Journalisation, métriques, état système |
| `ConnectorManagementService` | CRUD des connecteurs dynamiques |
| `UserService` | Utilisateurs gateway, chaînes d'approbation |
| `EmailService` | Notifications d'approbation (SMTP / DEV_MODE) |
| `AIAgent` | Appels au fournisseur LLM |

**La couche connecteurs — l'abstraction des systèmes externes.** Sous `gateway/app/connectors/`, cette couche masque l'hétérogénéité des protocoles derrière un contrat uniforme. La classe abstraite `BaseConnector` définit l'interface CRUD asynchrone que tout connecteur statique implémente : `test_connection`, `create_account`, `update_account`, `delete_account`, `disable_account`, `enable_account`, `get_account`, `list_accounts`, complétée par la gestion des appartenances (groupes pour LDAP/Odoo, rôles pour MidPoint). La `ConnectorFactory` résout un nom de cible en une instance : elle tente d'abord un **connecteur dynamique** dont la configuration est chargée depuis la table `connector_configurations`, puis retombe sur un **connecteur statique** (`MidPointConnector`, `LDAPConnector`, `SQLConnector`, `OdooConnector`). Les cibles `GLPI`, `KEYCLOAK` et `FIREBASE` lèvent volontairement `NotImplementedError` en statique, signalant qu'elles doivent être ajoutées dynamiquement, comme le montre la résolution statique :

```python
def _create_static_connector(self, target: str) -> BaseConnector:
    if target == "MIDPOINT":              return MidPointConnector()
    elif target in ("LDAP", "AD"):        return LDAPConnector()
    elif target == "SQL":                 return SQLConnector()
    elif target == "ODOO":                return OdooConnector()
    elif target == "GLPI":
        raise NotImplementedError("GLPI connector not configured. Add it via the Connectors page.")
    elif target == "KEYCLOAK":
        raise NotImplementedError("Keycloak connector not configured. Add it via the Connectors page.")
    elif target == "FIREBASE":
        raise NotImplementedError("Firebase connector not configured. Add it via the Connectors page.")
    else:
        raise ValueError(f"Unknown target system: {target}. Configure it via the Connectors page.")
```

Le message d'erreur lui-même guide l'utilisateur vers la solution (« Add it via the Connectors page »). C'est cette abstraction qui permet l'**architecture double-mode** : les services manipulent des `BaseConnector` interchangeables, sans savoir s'ils écrivent en direct ou si MidPoint orchestrera. La fabrique met par ailleurs en cache les instances résolues et expose `invalidate_cache()` pour forcer un rechargement après modification d'une configuration de connecteur.

Le schéma suivant résume la circulation verticale entre les couches internes de la gateway :

```
┌──────────────────────────────────────────────────────────────────┐
│ Couche API (app/api/) — 14 routeurs, 149 endpoints                 │
│   parse/valide (Pydantic) · auth (get_current_user) · RBAC         │
│   (require_role) · délègue au service                              │
└───────────────────────────────┬────────────────────────────────────┘
                                 ▼  appelle
┌──────────────────────────────────────────────────────────────────┐
│ Couche services (app/services/) — logique métier                  │
│   MidPointProvisionService · ProvisionService · WorkflowService    │
│   SchedulerService · ConnectorManagementService · UserService …    │
└───────────────────────────────┬────────────────────────────────────┘
                                 ▼  utilise
┌──────────────────────────────────────────────────────────────────┐
│ Couche connecteurs (app/connectors/) — BaseConnector (ABC)         │
│   ConnectorFactory → MidPoint / LDAP / SQL / Odoo / Dynamic        │
└───────────────────────────────┬────────────────────────────────────┘
                                 ▼  s'appuie sur
┌──────────────────────────────────────────────────────────────────┐
│ Couches transverses : core/ (config, security, db, redis, qdrant, │
│   logging, memory_store) · models/ (Pydantic / SQLModel / IAM)     │
└──────────────────────────────────────────────────────────────────┘
```

**La couche données — cache hybride et accès asynchrone.** Sous `gateway/app/core/`, cette couche transverse gère la persistance et les ressources partagées. Le `MemoryStore` est un **cache hybride** singleton, thread-safe, qui constitue le chemin de lecture rapide : au démarrage, il charge en mémoire les lignes récentes de PostgreSQL (jusqu'à 500 opérations, 1 000 logs d'audit, 100 jobs de réconciliation, 200 workflows) ; les lectures d'API sont servies depuis ce cache sans requête SQL, tandis que les écritures mettent à jour le cache **immédiatement** puis sont persistées de façon **asynchrone** (*fire-and-forget*). Le moteur SQLAlchemy asynchrone (`database.py`), reposant sur le pilote **asyncpg**, est configuré avec un pool dimensionné (`pool_size=10`, `max_overflow=20`), un recyclage anti-coupures (`pool_recycle=1800`) et une vérification pré-emploi des connexions (`pool_pre_ping=True`) :

```python
engine = create_async_engine(
    settings.DATABASE_URL, echo=settings.DEBUG, future=True,
    pool_pre_ping=True,   # détecte/remplace une connexion morte (après redémarrage PG)
    pool_recycle=1800,    # recycle toutes les 30 min (coupures idle des proxys)
    pool_size=10, max_overflow=20,
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

La fonction `get_session`, utilisée comme dépendance FastAPI, garantit un `rollback` automatique sur toute exception non gérée — aucune transaction partielle ne peut donc fuir vers la base. Le client Redis (`redis_client.py`), enfin, est lui aussi un singleton, exposant les opérations de liste noire, de cache et de limitation de débit atomique. Ensemble, ces composants réalisent le principe d'**état externalisé** énoncé en §2.1 tout en préservant des temps de réponse faibles.

### 2.5 Démarrage, middleware et cycle de vie (détail technique)

Le point d'entrée de l'application, `main.py`, mérite une analyse approfondie car il orchestre l'initialisation ordonnée de tous les sous-systèmes et installe les mécanismes transverses qui encadrent chaque requête. L'initialisation s'appuie sur le patron `asynccontextmanager` de FastAPI (le *lifespan*), qui sépare nettement le code de démarrage (avant le `yield`) du code d'arrêt (après) :

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Gateway IAM", version=app.version)
    await init_db()                              # 1. PostgreSQL (création des tables)
    await memory_store.ensure_cache_loaded()     # 2. Cache mémoire depuis Postgres
    redis_ok = await redis_client.connect()      # 3. Redis (dégrade si indisponible)
    qdrant_ok = await qdrant_store.connect()     # 4. Qdrant (dégrade si indisponible)
    init_scheduler()                             # 5. APScheduler
    yield                                        # l'application tourne ici
    shutdown_scheduler()                         # arrêt : scheduler puis Redis
    await redis_client.close()
```

L'**ordre de démarrage** n'est pas arbitraire : il reflète les dépendances entre sous-systèmes. La journalisation est configurée en premier, afin que toutes les étapes suivantes soient tracées. PostgreSQL vient ensuite, car le `MemoryStore` charge son cache depuis cette base : tenter de charger le cache avant l'initialisation de la base échouerait. Redis et Qdrant suivent, mais leur échec est **non fatal** — la valeur de retour booléenne (`redis_ok`, `qdrant_ok`) est journalisée (`status="connected"` ou `"unavailable"`) sans interrompre le démarrage, conformément au principe de dégradation gracieuse. L'ordonnanceur est démarré en dernier, une fois tous les services dont il dépend disponibles. À l'arrêt, l'ordre est **inversé** : on arrête d'abord le scheduler (pour qu'aucune nouvelle tâche ne démarre) avant de fermer Redis. La séquence de démarrage et les conséquences d'un échec se résument ainsi :

| Ordre | Étape | Critique ? | Sur échec |
|---|---|---|---|
| 1 | Configuration des logs | oui | arrêt |
| 2 | `init_db()` (PostgreSQL) | oui | arrêt |
| 3 | Chargement du cache `MemoryStore` | oui | dictionnaires vides (journalisé) |
| 4 | Connexion Redis | non | `unavailable` (dégradation) |
| 5 | Connexion Qdrant | non | `unavailable` (dégradation) |
| 6 | Démarrage APScheduler | oui | arrêt |

L'enregistrement des routeurs, à la fin de `main.py`, matérialise la cartographie entre les modules fonctionnels et leurs préfixes d'URL :

```python
app.include_router(provision.router, prefix="/api/v1/provision", tags=["Provisionnement"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["Regles"])
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["Workflow"])
app.include_router(reconcile.router, prefix="/api/v1/reconcile", tags=["Reconciliation"])
app.include_router(ai_assistant.router, prefix="/api/v1/ai", tags=["Agent IA"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])
app.include_router(live_comparison.router, prefix="/api/v1/live", tags=["Comparaison Temps Reel"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Niveaux de Droits"])
app.include_router(connectors.router, prefix="/api/v1/connectors", tags=["Connecteurs"])
app.include_router(webhooks.router, tags=["Webhooks MidPoint"])         # préfixe porté par le routeur
app.include_router(midpoint.router, prefix="/api/v1", tags=["MidPoint Orchestration"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["Planification Sync"])
app.include_router(ldap_groups.router, prefix="/api/v1", tags=["Groupes LDAP"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Gestion Utilisateurs"])
```

Chaque routeur reçoit un préfixe et des *tags* (qui structurent la documentation Swagger), à l'exception de `webhooks` (qui porte son préfixe `/api/v1/webhooks` en interne) et de `midpoint`/`ldap_groups` (montés sous `/api/v1` car leurs chemins internes incluent déjà `/midpoint` et `/ldap/groups`).

Le **middleware de contexte de requête** est le pivot de l'observabilité. À chaque requête, il génère ou propage un identifiant de corrélation, le lie au contexte de journalisation, mesure la latence et capture les exceptions non gérées :

```python
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    _request_id_ctx.set(request_id)
    clear_contextvars()
    bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("Unhandled exception", error=str(exc), duration_ms=duration_ms, exc_info=True)
        response = JSONResponse(status_code=500,
            content={"detail": "Internal server error", "request_id": request_id})
    response.headers["X-Request-ID"] = request_id
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info("request", status_code=response.status_code, duration_ms=duration_ms)
    return response
```

Ce middleware combine trois responsabilités. D'abord la **corrélation** : le `request_id`, lié au contexte structlog via `bind_contextvars`, est automatiquement présent dans **toutes** les lignes de log émises pendant la requête, et il est aussi renvoyé au client dans l'en-tête `X-Request-ID` — ce qui permet à un utilisateur signalant un problème de fournir un identifiant directement traçable côté serveur. Ensuite la **mesure de latence** : `time.perf_counter()` encadre le traitement et la durée est journalisée systématiquement. Enfin la **sécurité** : toute exception non interceptée est transformée en réponse 500 générique, sans jamais exposer de trace interne (cf. §4.2 V9). Deux gestionnaires d'exception complémentaires (`StarletteHTTPException` et `RequestValidationError`) assurent des réponses cohérentes pour les erreurs HTTP attendues et les erreurs de validation (422), toutes deux incluant le `request_id`.

Le **MemoryStore**, déjà introduit, mérite un examen de son fonctionnement interne car il incarne le compromis entre performance et durabilité. C'est un singleton thread-safe (verrou `threading.Lock` dans `__new__`). Au démarrage, `_load_from_database` charge en mémoire les lignes récentes par des requêtes SQL bornées, par exemple pour les opérations :

```python
result = await session.execute(text("""
    SELECT id, correlation_id, operation_type, status, target_systems,
           account_id, input_attributes, calculated_attributes,
           error_message, created_at, updated_at
    FROM provisioning_operations
    ORDER BY created_at DESC
    LIMIT 500
"""))
```

Les autres catégories sont chargées avec leurs propres bornes, dimensionnées selon leur volumétrie attendue et leur fréquence de consultation :

```python
# audit_logs : les 1000 entrées les plus récentes
"SELECT id, created_at, event_type, target_system, account_id, action, severity, actor, details "
"FROM audit_logs ORDER BY created_at DESC LIMIT 1000"
# reconciliation_jobs : 100 derniers ; workflows : 200 derniers
```

Ces limites (500 opérations, 1000 logs d'audit, 100 jobs, 200 workflows) traduisent un compromis : charger assez de données récentes pour servir l'écrasante majorité des lectures depuis la mémoire, sans saturer celle-ci avec un historique ancien rarement consulté. Les données plus anciennes restent accessibles en base, mais ne sont pas pré-chargées.

Le **chemin d'écriture** illustre le modèle *write-through cache + persistance asynchrone*. La méthode `save_operation` met d'abord à jour le dictionnaire en mémoire (lecture immédiate garantie), puis délègue la persistance à une coroutine lancée par `_run_async`. Cette dernière, étudiée en §8.4, conserve une **référence forte** à la tâche pour empêcher sa collecte prématurée par le ramasse-miettes, et journalise toute exception via un *callback* de complétion. L'écriture SQL elle-même emploie un `INSERT ... ON CONFLICT ... DO UPDATE` avec des `CAST` explicites vers les énumérations PostgreSQL (en majuscules), témoignant de la gestion manuelle de la dérive entre les énumérations Python (minuscules) et la DDL :

```python
await session.execute(text("""
    INSERT INTO provisioning_operations
      (id, correlation_id, operation_type, status, target_systems, account_id,
       input_attributes, calculated_attributes, error_message, created_at, updated_at)
    VALUES (:id, :correlation_id, CAST(:op_type AS operationtype), CAST(:status AS operationstatus),
            :target, :account_id, :attrs, :calc, :msg, :created, :created)
    ON CONFLICT (id) DO UPDATE SET
        status = CAST(EXCLUDED.status AS operationstatus),
        calculated_attributes = EXCLUDED.calculated_attributes,
        error_message = EXCLUDED.error_message,
        updated_at = CURRENT_TIMESTAMP
"""), {"id": operation_id, "op_type": op_type, "status": status_db, ...})
```

L'`ON CONFLICT (id) DO UPDATE` réalise un *upsert* idempotent : une même opération peut être enregistrée (création) puis ré-enregistrée (mise à jour de statut) sans collision de clé. Les `CAST(:x AS operationtype/operationstatus)` sont la conséquence directe de la dérive de casse entre les énumérations : la valeur, mise en majuscules par un `status.upper()` préalable, est explicitement convertie vers le type énuméré PostgreSQL. Ce mécanisme garantit des lectures instantanées au prix d'une cohérence *eventually consistent* : une écriture asynchrone ayant échoué laisserait temporairement le cache en avance sur la base, situation tracée par les journaux d'erreur.

---

## 3. Fonctionnalités réalisées

Cette section décrit en détail l'ensemble des fonctionnalités implémentées, en s'appuyant systématiquement sur le code réel du projet. Chaque sous-section développe le besoin auquel répond la fonctionnalité, son fonctionnement interne et ses points d'attention.

### 3.1 Authentification et gestion des sessions

L'authentification constitue le point d'entrée sécuritaire de toute la plateforme et a fait l'objet d'un soin particulier. Le flux commence par l'endpoint `POST /api/v1/admin/token`, qui reçoit un identifiant et un mot de passe selon le standard OAuth2 (`OAuth2PasswordRequestForm`). La vérification se déroule en plusieurs étapes ordonnées : limitation de débit, résolution de l'utilisateur, vérification du mot de passe, émission du jeton. À l'issue de cette chaîne, le code produit un **jeton JWT** signé en HS256 et porteur de plusieurs revendications de sécurité, comme le montre la fonction `create_access_token` de `core/security.py` :

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid.uuid4())  # ID unique pour la révocation via Redis
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
```

Trois revendications méritent une attention particulière. L'**émetteur** (`iss`) et l'**audience** (`aud`) sont systématiquement posés et **revérifiés** au décodage (`decode_token` passe `audience=` et `issuer=` à `jwt.decode`) : un jeton émis pour un autre service, ou par un autre émetteur, est rejeté, ce qui neutralise les attaques de confusion d'audience. L'identifiant unique **`jti`** (un UUID v4) est la clé de voûte de la révocation : il permet d'inscrire un jeton précis dans une liste noire. Enfin, la durée de vie est bornée à `JWT_EXPIRE_MINUTES` (60 minutes par défaut), limitant la fenêtre d'exploitation d'un jeton volé. Les revendications portées par le jeton sont récapitulées ci-dessous :

| Claim | Contenu | Vérifié au décodage ? | Rôle |
|---|---|---|---|
| `sub` | nom d'utilisateur | présence | identité du porteur |
| `roles` | liste des rôles | — | base du RBAC |
| `exp` | expiration (now + 60 min) | ✅ | borne la fenêtre d'exploitation |
| `iss` | `iam-gateway` | ✅ | émetteur attendu |
| `aud` | `iam-gateway` | ✅ | audience attendue |
| `jti` | UUID v4 unique | présence | clé de révocation (blacklist Redis) |

Le **hachage des mots de passe** repose sur **bcrypt**, mais avec une subtilité essentielle au bon fonctionnement asynchrone. bcrypt est un algorithme volontairement coûteux en CPU et **bloquant** : l'appeler directement dans un *handler* asynchrone figerait la boucle d'événements pendant toute la durée du calcul, empêchant le serveur de traiter d'autres requêtes. La solution adoptée déporte le calcul dans un *thread* via `asyncio.to_thread`, comme on le voit dans `security.py` :

```python
async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe hors de la boucle d'événements (bcrypt est bloquant et CPU-intensif)."""
    return await asyncio.to_thread(verify_password, plain_password, hashed_password)
```

Ce choix illustre une compréhension fine du modèle d'exécution ASGI : la boucle d'événements ne doit jamais être bloquée par du travail CPU synchrone ; `asyncio.to_thread` exécute la fonction dans le pool de *threads* par défaut, libérant la boucle pour d'autres requêtes pendant le calcul. Ce point a d'ailleurs fait l'objet d'une correction de sécurité dédiée (cf. §4.2, V6).

La **révocation des jetons** s'opère à la déconnexion. L'endpoint `POST /api/v1/admin/logout` extrait le `jti` du jeton courant et l'inscrit dans Redis avec une durée de vie égale à la durée de vie résiduelle du jeton (`JWT_EXPIRE_MINUTES × 60` secondes). À chaque requête authentifiée ultérieure, `get_current_user` interroge cette liste noire : si le `jti` y figure, la requête est rejetée avec un code 401 « Token has been revoked ». Ce mécanisme offre une révocation **immédiate** sans nécessiter d'état serveur lourd : la liste noire est auto-purgeante (les entrées expirent avec le jeton), et son interrogation est une simple opération Redis en O(1). La vérification complète, à chaque requête authentifiée, combine le décodage validant et le contrôle de révocation dans `get_current_user` :

```python
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
                          audience=settings.JWT_AUDIENCE, issuer=settings.JWT_ISSUER)
    except JWTError as e:
        logger.error("JWT decode error", error=str(e))
        raise HTTPException(status_code=401, detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"})

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    jti = payload.get("jti")
    if jti and await redis_client.is_token_blacklisted(jti):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    return {"username": username, "roles": payload.get("roles", []), "jti": jti}
```

L'enchaînement est rigoureux : on décode et valide (signature, expiration, `iss`, `aud` — l'algorithme étant explicitement borné à `[settings.JWT_ALGORITHM]`, l'attaque `alg=none` est neutralisée), on vérifie la présence du sujet, puis on consulte la liste noire. Ce n'est qu'au terme de ces trois contrôles que l'utilisateur est considéré comme authentifié, et le dictionnaire retourné (`username`, `roles`, `jti`) alimente ensuite la vérification de rôle.

Une **fixture de développement** (`TEMP_USERS`) coexiste dans `admin.py` avec la source d'authentification principale (la table `gateway_users`). Cette fixture définit deux comptes (`admin`/`admin123`, `operator`/`operator123`) dont les mots de passe sont hachés paresseusement à la première utilisation. Le point crucial est qu'elle est **strictement conditionnée au mode DEBUG** : le code ne l'active que `elif settings.DEBUG and username in TEMP_USERS`. En production (`DEBUG=false`), seule la table `gateway_users` est consultée ; la fixture est inerte. Ce verrou évite qu'un compte de test codé en dur ne devienne une porte dérobée en production — un risque que la §9 identifie néanmoins comme dépendant de la rigueur de configuration.

Enfin, la **limitation de débit** protège l'endpoint de connexion contre les attaques par force brute. Avant toute vérification de mot de passe, `admin.py` appelle `redis_client.check_rate_limit(f"login:{client_ip}:{form_data.username}", max_requests=10, window_seconds=300)` : au-delà de **10 tentatives en 5 minutes** pour un couple IP+identifiant donné, l'endpoint répond 429. Le compteur est incrémenté par un **script Lua atomique** dont la logique et la justification sont détaillées en §3.1 du point de vue données (§6.4) et en §8.2 du point de vue difficultés rencontrées ; retenons ici que l'atomicité garantit qu'aucun compteur ne reste sans expiration, et que le mécanisme dégrade en mode ouvert si Redis est indisponible.

L'enchaînement complet de l'endpoint de connexion, dans `admin.py`, met clairement en évidence cet ordre des contrôles :

```python
@router.post("/token", response_model=Token)
async def login_for_access_token(request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)):
    # 1. Rate limiting anti-brute-force (par IP + username)
    client_ip = request.client.host if request.client else "unknown"
    allowed = await redis_client.check_rate_limit(
        f"login:{client_ip}:{form_data.username}", max_requests=10, window_seconds=300)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts, please try again later")

    # 2. Source d'authentification principale : la table gateway_users
    db_user = await UserService(session).get_user_by_username(form_data.username)
    if db_user and db_user.get("is_active") and db_user.get("password_hash"):
        password_hash = db_user["password_hash"]
        roles = db_user.get("roles") or ([db_user["role"]] if db_user.get("role") else [])
    elif settings.DEBUG and form_data.username in TEMP_USERS:   # fixture dev uniquement
        _ensure_password_hashed(form_data.username)
        password_hash = TEMP_USERS[form_data.username]["password_hash"]
        roles = TEMP_USERS[form_data.username]["roles"]

    # 3. Vérification du mot de passe (bcrypt hors de la boucle d'événements)
    if not password_hash or not await verify_password_async(form_data.password, password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # 4. Émission du JWT
    access_token = create_access_token(data={"sub": form_data.username, "roles": roles},
                                       expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}
```

On y lit la priorité de la table `gateway_users` sur la fixture, le conditionnement strict de cette dernière à `settings.DEBUG`, et le déport asynchrone de la vérification bcrypt — soit la synthèse des protections V1, V6, V10 et V13 dans un unique flux.

Le routeur d'administration offre par ailleurs un mécanisme d'**arrêt d'urgence** (le « bouton rouge »), réservé au rôle `admin`, qui désactive instantanément tout provisionnement en basculant un état système persistant :

```python
@router.post("/emergency-stop")
async def emergency_stop(current_user: dict = Depends(require_role(["admin"])), session=Depends(get_session)):
    audit_service = AuditService(session)
    await audit_service.set_system_state(key="provisioning_enabled", value="false",
                                         updated_by=current_user["username"])
    await audit_service.log_config_change(action="emergency_stop", user=current_user,
                                          details={"reason": "Emergency stop activated"})
    logger.warning("EMERGENCY STOP ACTIVATED", user=current_user["username"])
    return {"status": "stopped", "message": "Provisioning system disabled. All operations suspended."}
```

Ce dispositif, complété par son endpoint symétrique `/resume`, permet à un administrateur de **figer immédiatement** le système en cas d'incident (par exemple, une synchronisation défaillante en cours de propagation), pendant qu'il diagnostique la situation. L'état est persisté dans la table `system_states` (clé `provisioning_enabled`), de sorte qu'il survit à un redémarrage, et chaque activation est journalisée en `WARNING` et auditée. L'endpoint `/status`, lui, effectue des **vérifications de santé réelles** (tentative de *bind* LDAP, appel REST `/ws/rest/self` à MidPoint, *ping* Redis) plutôt que de retourner un état mis en cache, offrant à l'exploitant une vue fiable de la connectivité des systèmes externes.

### 3.2 Contrôle d'accès basé sur les rôles (RBAC)

Le contrôle d'accès basé sur les rôles est le second pilier de la sécurité applicative. Il repose sur une **hiérarchie de rôles** stockée par utilisateur (colonne `roles` de type JSONB dans `gateway_users`) et vérifiée de manière déclarative. Le projet distingue deux familles de rôles, définies dans `user_service.py` : les **rôles d'accès** (`admin`, `iam_engineer`, `director`, `viewer`), qui gouvernent ce qu'un utilisateur peut faire dans la gateway, et les **rôles d'approbation** (`manager`, `rh_manager`, `it_admin`, `security_officer`), qui déterminent sa place dans les chaînes de validation des workflows. À cela s'ajoute un rôle `operator` *legacy*, réservé à la fixture de développement.

Le mécanisme d'application est la dépendance `require_role`, dont le code dans `security.py` est d'une concision révélatrice :

```python
def require_role(required_roles: list):
    """Décorateur RBAC — exige au moins un des rôles spécifiés."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_checker
```

La sémantique retenue est celle du **« au moins un rôle »** (logique OU) : un utilisateur est autorisé dès lors qu'il possède l'un des rôles requis. Cette dépendance s'attache à un endpoint par `Depends(require_role([...]))`, et compose naturellement avec `get_current_user` (dont elle dépend), si bien que l'authentification est garantie avant même l'évaluation de l'autorisation. L'usage, lisible et déclaratif, se retrouve à l'identique sur toute la surface mutante de l'API :

```python
@router.delete("/{operation_id}")                                        # suppression : admin seul
async def delete_operation(operation_id: str,
        current_user: dict = Depends(require_role(["admin"]))): ...

@router.post("/")                                                        # provisionnement : admin ou ingénieur IAM
async def provision_account(request: ProvisioningRequest,
        current_user: dict = Depends(require_role(["admin", "iam_engineer"]))): ...

@router.get("/{operation_id}")                                           # lecture : tout authentifié
async def get_operation_status(operation_id: str,
        current_user: dict = Depends(get_current_user)): ...
```

La signature de chaque fonction **documente sa propre politique de sécurité** : un relecteur voit immédiatement, sans lire le corps, qui peut appeler l'endpoint. Cette homogénéité — lecture en `get_current_user`, écriture en `require_role` — est ce qui rend l'audit d'autorisation (§4.2 V3) fiable et exhaustif. La règle générale appliquée dans toute la base de code est limpide : les **lectures** exigent un JWT valide (`get_current_user`), tandis que les endpoints **mutants** exigent un rôle — `admin` pour les opérations les plus sensibles (suppressions, gestion des rôles, configuration, arrêt d'urgence), `admin,iam_engineer` pour la majorité des autres écritures (provisionnement, règles, ordonnanceur, groupes LDAP). Cette granularité, généralisée à tous les endpoints mutants lors de l'audit de sécurité (cf. §4.2, V3), constitue une défense robuste contre l'élévation de privilèges.

Au-delà des rôles RBAC stricts, le routeur `permissions.py` introduit un **système de niveaux de droits hiérarchiques de 1 à 5** (Visiteur, Utilisateur, Opérateur, Manager, Chef de Département), persistés dans la colonne `permission_level` de `gateway_users`. Chaque niveau agrège un ensemble de permissions fonctionnelles (de `view_dashboard` au niveau 1 jusqu'à `strategic_decisions` au niveau 5) et sert notamment à modéliser la profondeur d'approbation dans les workflows. Ce double système — rôles nominatifs pour le RBAC technique, niveaux numériques pour la gouvernance fonctionnelle — offre une flexibilité appréciable, au prix d'une certaine redondance conceptuelle qu'une évolution future pourrait unifier.

Le tableau ci-dessous récapitule la hiérarchie des rôles RBAC (définie dans `user_service.py`) :

| Catégorie | Rôle | Libellé | Capacité type |
|---|---|---|---|
| Accès | `admin` | Administrateur | Contrôle total (users, connecteurs, règles, arrêt d'urgence, suppressions, rôles) |
| Accès | `iam_engineer` | Ingénieur IAM | Provisionnement, règles, scheduler, groupes LDAP, synchronisations |
| Accès | `director` | Directeur | Vision stratégique et supervision (lecture étendue) |
| Accès | `viewer` | Lecteur | Consultation uniquement, aucune modification |
| Approbation | `manager` | Manager | Approbation de niveau 1 |
| Approbation | `rh_manager` | Responsable RH | Approbation de niveau 2 |
| Approbation | `it_admin` | Administrateur IT | Approbation de niveau 3 (final) |
| Approbation | `security_officer` | Responsable Sécurité | Approbation des comptes à privilège élevé |
| Legacy/dev | `operator` | Opérateur | Fixture de code, réservée au mode DEBUG |

Et le tableau suivant détaille les cinq niveaux de droits fonctionnels (définis dans `permissions.py`) :

| Niveau | Nom | Description | Exemples de profils |
|---|---|---|---|
| 1 | Visiteur | Consultation minimale (`view_dashboard`, `view_own_profile`) | Stagiaire, visiteur externe |
| 2 | Utilisateur | Actions basiques (+ `create_request`, `view_own_requests`) | Employé, technicien |
| 3 | Opérateur | Gestion courante (+ `approve_level1`, `view_reports`, `export_data`) | Chef d'équipe, superviseur |
| 4 | Manager | Validation et gestion d'équipe (+ `approve_level2`, `manage_team`, `view_audit_logs`, `configure_rules`) | Manager, responsable RH |
| 5 | Chef de Département | Accès maximum non-admin (+ `approve_level3`, `manage_department`, `approve_budget`, `strategic_decisions`) | Directeur, VP |

Cette double granularité permet d'exprimer aussi bien des autorisations **techniques** (qui peut appeler tel endpoint) que des prérogatives **organisationnelles** (qui peut approuver à quel niveau), couvrant ainsi le spectre complet de la gouvernance des accès.

### 3.3 Provisionnement multi-cibles

Le provisionnement multi-cibles est **la fonctionnalité centrale** de la plateforme, celle qui justifie son existence. Elle est réalisée selon deux paradigmes complémentaires, commutés par `settings.MIDPOINT_ENABLED`, comme l'illustre l'aiguillage en tête de l'endpoint `POST /api/v1/provision/` :

```python
if settings.MIDPOINT_ENABLED:
    return await _provision_via_midpoint(request, current_user, session)
# Legacy : provisionnement direct vers les cibles
return await _provision_direct(request, background_tasks, current_user, session)
```

Les deux paradigmes se distinguent sur plusieurs axes :

| Aspect | Mode hub (`MIDPOINT_ENABLED=True`) | Mode direct (`False`) |
|---|---|---|
| Service | `MidPointProvisionService` | `ProvisionService` |
| Écritures de la gateway | une seule (vers MidPoint) | une par cible (LDAP, Odoo, SQL) |
| Propagation | par MidPoint (rôles → ressources) | par la gateway elle-même |
| Atomicité | assurée par MidPoint | actions de rollback (compensation) |
| Réconciliation / shadows | natifs MidPoint | cache d'état des comptes |
| Dépendance | MidPoint requis | autonome (sans MidPoint) |

#### 3.3.1 Mode hub via MidPoint

En mode hub, la gateway délègue à MidPoint la responsabilité d'orchestrer la propagation. Le `MidPointProvisionService.provision()` reçoit une `ProvisioningRequest`, structure Pydantic dont la définition (dans `models/provision.py`) typographie précisément le contrat d'entrée :

```python
class ProvisioningRequest(SQLModel):
    operation: OperationType                     # create / update / delete / enable / disable
    target_systems: List[TargetSystem]           # LDAP, AD, SQL, ODOO, GLPI, KEYCLOAK, FIREBASE
    account_id: str
    attributes: Dict[str, Any]
    policy_id: Optional[str] = None
    correlation_id: Optional[str] = None
    require_approval: Optional[bool] = False
```

Les énumérations `OperationType` (cinq valeurs : `create`, `update`, `delete`, `disable`, `enable`) et `TargetSystem` (sept cibles) garantissent par construction que seules des opérations et des cibles valides peuvent être demandées — toute valeur hors énumération est rejetée par Pydantic avec un 422 avant même d'atteindre le service. Le champ `require_approval`, couplé au `manager_email` présent dans les attributs, est ce qui aiguille vers le flux d'approbation décrit en §3.6. La première action du service est d'**enregistrer une opération** dans le `MemoryStore` avec un identifiant horodaté (`op_<AAAAMMJJHHMMSS>_<account_id>`) et un statut `IN_PROGRESS`, garantissant la traçabilité dès le début du traitement. Le statut de l'opération évolue ensuite parmi les valeurs de l'énumération `OperationStatus` : `pending` (créée), `awaiting_approval` (en attente de workflow), `in_progress` (en cours d'exécution), `success` (terminée), `failed` (échouée), `rolled_back` (annulée par compensation), `approved`/`rejected` (issues de workflow). Ce suivi fin permet à l'opérateur de connaître à tout instant l'état exact d'une demande, et alimente les métriques d'exploitation (`GET /admin/metrics`). En cas de provisionnement avec approbation, l'opération est d'abord enregistrée avec le statut `awaiting_approval` et un drapeau `midpoint_pending=True`, signalant que la création MidPoint est différée jusqu'à la validation complète du workflow — séparation nette entre la demande et l'exécution.

Le cœur de la mécanique réside dans la **traduction des systèmes cibles en rôles MidPoint**. MidPoint ne provisionne pas directement « vers LDAP » ; il assigne des **rôles**, et ce sont les rôles qui, par leurs *constructions*, déclenchent la création de comptes dans les ressources. Le service réalise cette traduction via `_map_targets_to_roles` :

```python
role_mapping = {
    TargetSystem.LDAP: "ldap-user",
    TargetSystem.AD: "ad-user",
    TargetSystem.SQL: "intranet-user",
    TargetSystem.ODOO: "odoo-user",
    TargetSystem.KEYCLOAK: "keycloak-user",
    TargetSystem.GLPI: "glpi-user",
    TargetSystem.FIREBASE: "firebase-user",
}
```

La séquence complète, depuis l'appel d'API jusqu'à la création du compte, se déroule ainsi : le service appelle `MidPointConnector.create_account()`, qui construit un objet `UserType` MidPoint et l'envoie par `POST /ws/rest/users`. La construction de cet objet repose sur une **table de correspondance** entre les noms d'attributs source (variés) et les noms canoniques MidPoint :

```python
attr_mapping = {
    "firstname": "givenName", "first_name": "givenName", "givenName": "givenName",
    "lastname": "familyName", "last_name": "familyName", "familyName": "familyName",
    "email": "emailAddress", "emailAddress": "emailAddress",
    "employeeNumber": "employeeNumber", "employee_id": "employeeNumber",
    "department": "organizationalUnit", "title": "title",
    "telephoneNumber": "telephoneNumber", "phone": "telephoneNumber",
}
```

Cette tolérance aux variantes de nommage (`firstname`, `first_name`, `givenName` mènent tous à `givenName`) rend le connecteur robuste face à des sources de données hétérogènes — une qualité essentielle quand les attributs proviennent de systèmes aussi différents qu'Odoo, un CSV RH ou un appel d'API direct. Le `fullName` est composé automatiquement si absent, et le mot de passe, s'il est fourni, est encapsulé dans la structure `credentials/password/value/clearValue` attendue par MidPoint. MidPoint retourne l'**OID** (identifiant unique au format UUID) du nouvel utilisateur, extrait soit du corps de la réponse, soit de l'en-tête `Location`. Le service assigne alors chaque rôle cartographié via `assign_role(oid, role_name)`, opération qui, en MidPoint 4.4, requiert l'envoi d'une modification au **format XML** (`objectModification` ajoutant un `assignment` avec un `targetRef` de type `RoleType`). C'est l'assignation de ce rôle qui déclenche, côté MidPoint, la création effective du compte dans la ressource correspondante.

Le parcours complet d'un provisionnement d'arrivée (*Joiner*) en mode hub peut se résumer en huit étapes ordonnées :

1. **Réception** — `POST /api/v1/provision/` reçoit la `ProvisioningRequest`, après authentification JWT et vérification du rôle `admin`/`iam_engineer`.
2. **Enregistrement** — le service crée une opération `op_<horodatage>_<account_id>` au statut `IN_PROGRESS` dans le `MemoryStore` (lecture immédiate, persistance asynchrone).
3. **Cartographie** — `_map_targets_to_roles` traduit les systèmes cibles demandés en noms de rôles MidPoint (`LDAP`→`ldap-user`, etc.).
4. **Création de l'identité** — `MidPointConnector.create_account` construit le `UserType` et l'envoie par `POST /ws/rest/users` ; l'OID est récupéré.
5. **Assignation des rôles** — pour chaque rôle cartographié, `assign_role(oid, role)` envoie un `objectModification` XML ; MidPoint crée alors les projections.
6. **Propagation** — les connecteurs propres à MidPoint créent les comptes réels dans LDAP, Odoo et SQL ; les *shadows* deviennent visibles.
7. **Réplication Keycloak** — MidPoint émet une notification `user-change` ; la gateway, après vérification HMAC, déclenche le `KeycloakProvisioner`.
8. **Clôture** — l'opération passe à `SUCCESS`, une entrée d'audit est écrite et indexée dans Qdrant.

Ce déroulé illustre la valeur du mode hub : la gateway n'écrit qu'**une seule fois** (vers MidPoint), et c'est le hub qui assume la complexité de la propagation cohérente vers quatre systèmes hétérogènes. Le code de `_create_user` matérialise les étapes 3 à 5 :

```python
async def _create_user(self, request: ProvisioningRequest) -> Dict[str, Any]:
    attributes = request.attributes.copy()
    roles_to_assign = self._map_targets_to_roles(request.target_systems)
    if roles_to_assign:
        attributes["_roles"] = roles_to_assign
    result = await self.midpoint.create_account(account_id=request.account_id, attributes=attributes)
    if roles_to_assign and result.get("oid"):
        for role_name in roles_to_assign:
            try:
                await self.midpoint.assign_role(result["oid"], role_name)
                logger.info("Role assigned", user=request.account_id, role=role_name)
            except Exception as e:
                logger.warning("Failed to assign role", role=role_name, error=str(e))
    return result
```

On notera la **gestion résiliente des erreurs d'assignation** : si l'assignation d'un rôle échoue, l'erreur est journalisée mais n'interrompt pas la boucle — les autres rôles sont tout de même tentés. Ce choix évite qu'une défaillance sur une seule cible (par exemple Odoo momentanément indisponible) ne compromette la totalité du provisionnement multi-cibles.

Une fois les comptes propagés, l'utilisateur dispose de **comptes shadow** dans MidPoint. Un *shadow* est la **projection** d'une identité dans une ressource cible : c'est la représentation, dans le référentiel MidPoint, du compte réel existant côté LDAP, Odoo ou SQL. La gateway expose ces shadows via `GET /api/v1/midpoint/users/{id}/shadows`, ce qui permet à un opérateur de visualiser **où** une identité a été effectivement provisionnée. La **gestion des erreurs et le suivi de statut** sont assurés tout au long : en cas de succès, l'opération passe à `SUCCESS` dans le `MemoryStore` ; en cas d'échec, à `FAILED` avec le message d'erreur, et une entrée d'audit est systématiquement écrite. Le `MidPointConnector` enrichit même les messages d'erreur bruts de MidPoint pour les rendre intelligibles (par exemple, transformer « Name attribute cannot be null » en « L'utilisateur n'a pas de nom/prénom valide pour créer un compte LDAP »).

#### 3.3.2 Mode direct avec rollback

Lorsque `MIDPOINT_ENABLED=False`, la gateway prend en charge elle-même l'orchestration via le `ProvisionService`. Ce mode, qualifié de *legacy*, conserve un intérêt majeur : il permet de fonctionner **sans MidPoint**, en écrivant directement dans chaque système cible. Sa difficulté propre est d'assurer l'**atomicité** d'une opération multi-cibles : si la création réussit dans LDAP mais échoue dans Odoo, il faut pouvoir **annuler** la création LDAP pour ne pas laisser le système dans un état incohérent.

La résolution des connecteurs passe par la `ConnectorFactory`, qui tente d'abord un connecteur dynamique (configuré en base) puis retombe sur un connecteur statique. Le `ProvisionService.execute_provisioning()` itère sur les systèmes cibles, et **pour chaque succès, empile une action de rollback** dans une liste `rollback_actions`. Le mécanisme est conceptuellement le suivant :

```python
for target in target_systems:
    connector = self.connector_factory.get_connector(target)
    attrs = calculated_attributes.get(target, {})
    if operation.operation_type == OperationType.CREATE:
        result = await connector.create_account(account_id=operation.account_id, attributes=attrs)
        rollback_actions.append(RollbackAction(
            operation_id=operation.id, target_system=target, action_type="delete", ...
        ))
```

En cas d'échec en cours de route, le service rejoue les actions de rollback empilées (par exemple, supprimer les comptes déjà créés), restaurant la cohérence. Au niveau de l'endpoint, ce rollback est même déclenché en **tâche d'arrière-plan** lorsqu'une opération échoue, afin de ne pas faire attendre l'appelant pendant la compensation :

```python
except Exception as e:
    logger.error("Provisioning failed", error=str(e), operation_id=operation.id if operation else None)
    if operation:
        background_tasks.add_task(provision_service.rollback_operation, operation.id)
        await audit_service.log_provision_failure(operation, str(e))
    raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")
```

Le rollback est donc à la fois **automatique** (déclenché par l'exception) et **asynchrone** (exécuté en arrière-plan), et il est tracé par une entrée d'audit `provision_failure`. La suppression elle-même (`DELETE /provision/{operation_id}`) illustre le même esprit de robustesse : elle itère sur chaque système cible, accumule les éventuelles erreurs sans interrompre les suppressions suivantes, et retourne un statut `partial` si certaines cibles ont échoué — préférant une suppression incomplète mais maximale à un échec total. Ce mécanisme de **compensation** est l'équivalent applicatif d'une transaction distribuée : faute de pouvoir verrouiller des systèmes hétérogènes dans une transaction ACID unique, on enregistre de quoi défaire chaque action réussie. Le modèle `RollbackAction` (table `rollback_actions`) capture précisément l'information nécessaire à l'annulation :

```python
class RollbackAction(SQLModel, table=True):
    __tablename__ = "rollback_actions"
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    operation_id: str = Field(index=True)
    target_system: TargetSystem
    action_type: str           # ex. "delete" pour annuler un "create"
    action_data: str           # JSON : données nécessaires à la compensation
    executed: bool = False
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

Chaque action porte le système cible, le type d'action inverse (un `delete` compense un `create`), les données nécessaires et un drapeau `executed` indiquant si la compensation a déjà été appliquée. Ce modèle transforme le rollback d'une intention abstraite en un enregistrement persistant et auditable — on peut ainsi savoir, après coup, quelles compensations ont été tentées et lesquelles ont réussi. L'**orchestration multi-cibles** couvre ainsi LDAP, Odoo, SQL et MidPoint de manière homogène, grâce au contrat uniforme `BaseConnector`.

Le `ProvisionService` maintient par ailleurs un **cache d'état des comptes** (table `account_state_cache`), reflétant l'état connu de chaque identité dans chaque cible, support de la réconciliation ultérieure. Enfin, la méthode `continue_after_approval` réalise le **flux double-mode après approbation** : lorsqu'un workflow d'approbation est validé, cette méthode reprend le provisionnement suspendu — elle tente d'abord MidPoint puis, le cas échéant, bascule sur les écritures directes. Cette articulation entre les deux modes au sein d'une même méthode est l'expression la plus aboutie de la décision d'architecture double-paradigme.

### 3.4 Connecteurs d'intégration

Les connecteurs sont les adaptateurs qui traduisent les opérations abstraites de la gateway en dialogues concrets avec chaque système cible. Tous dérivent de `BaseConnector` et ont été spécifiquement fiabilisés (TLS, timeouts, retry) lors du chantier `iam-connector-improvements`. Les mesures de fiabilité de chaque connecteur sont récapitulées ci-dessous :

| Connecteur | Timeout | Retry | TLS |
|---|---|---|---|
| MidPoint (httpx) | 60 s | `AsyncHTTPTransport(retries=2)` | vérifié si `MIDPOINT_VERIFY_SSL` |
| LDAP (ldap3) | 10 s (connect + receive) | bind ×2 | LDAPS (636) disponible |
| Odoo (xmlrpc) | 15 s (socket) | ré-auth ×2 | selon URL |
| Keycloak (httpx) | 10 s/appel | re-token par opération | selon URL |

**Le connecteur MidPoint (REST/JSON + XML).** Le `MidPointConnector` dialogue avec MidPoint via son API REST `/ws/rest/*`, en authentification **HTTP Basic**. Il réutilise un client `httpx.AsyncClient` configuré avec un **timeout de 60 secondes**, une **vérification TLS** conditionnée par `settings.MIDPOINT_VERIFY_SSL`, et surtout un transport résilient `httpx.AsyncHTTPTransport(retries=2)` qui **retente deux fois** les échecs de connexion transitoires — typiquement lorsque MidPoint redémarre tout en propageant vers ses ressources. Le connecteur couvre l'ensemble du CRUD (`create_account`, `update_account`, `delete_account`, `disable_account`, `enable_account`, `get_account`, `list_accounts`), la gestion des rôles (`assign_role`, `remove_role` en format XML pour 4.4), la gestion des shadows (`get_user_shadows`) et la consultation des ressources (`get_resources`). Une attention particulière est portée au parsing des réponses MidPoint, dont la structure JSON imbriquée (`data["object"]["object"]`) est gérée défensivement pour tolérer les variations de forme.

**Le connecteur LDAP.** Le `LDAPConnector` s'appuie sur la bibliothèque **ldap3** (synchrone). Comme bcrypt, ldap3 est bloquant ; le connecteur borne donc rigoureusement les temps : un `connect_timeout` de **10 secondes** sur le `Server` et un `receive_timeout` de 10 secondes sur la `Connection`. Sa méthode `_get_connection` implémente en outre une **reconnexion** : elle retente le *bind* **deux fois** en cas d'échec transitoire (annuaire qui redémarre, coupure réseau brève), suivant le motif *connect-use-unbind* qui ouvre une connexion fraîche par opération pour éviter les connexions périmées. Sur le plan de la sécurité, ce connecteur intègre le correctif anti-injection majeur de l'audit : tous les filtres de recherche et les composants de DN sont échappés via `escape_filter_chars()` et `escape_rdn()` de ldap3 (cf. §4.2, V5). Il gère la création de comptes `inetOrgPerson`, leur modification (`MODIFY_REPLACE`), leur suppression, ainsi que l'appartenance aux groupes (`add_to_group`/`remove_from_group` via `MODIFY_ADD`/`MODIFY_DELETE`). La création construit le DN et les attributs avec un échappement systématique :

```python
dn = f"uid={escape_rdn(attributes.get('uid', account_id))},{self.users_ou}"
ldap_attrs = {
    'objectClass': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
    'uid': attributes.get('uid', account_id),
    'cn': cn,
    'sn': lastname,
}
if firstname:                          # LDAP n'accepte pas les chaînes vides
    ldap_attrs['givenName'] = firstname
email = attributes.get('mail') or attributes.get('email')
if email:
    ldap_attrs['mail'] = email
result = conn.add(dn, attributes=ldap_attrs)
```

On notera deux détails révélateurs d'une connaissance pratique de LDAP : l'usage d'`escape_rdn` sur le composant `uid` du DN (correctif d'injection V5), et la garde `if firstname` — car un annuaire LDAP rejette les attributs à valeur vide, contrairement à ce qu'on pourrait naïvement supposer. La liste d'`objectClass` (`inetOrgPerson` et ses parents `organizationalPerson`, `person`, `top`) respecte la hiérarchie de schéma LDAP standard.

**Le connecteur Odoo.** Le `OdooConnector` communique avec Odoo via le protocole **XML-RPC**, selon le motif classique en deux temps : authentification sur `/xmlrpc/2/common` (méthode `authenticate`) puis exécution d'opérations sur `/xmlrpc/2/object` (méthode `execute_kw`). Pour borner les appels réseau, le connecteur définit une classe `_TimeoutTransport` personnalisée imposant un **timeout de 15 secondes** sur le socket. L'`uid` retourné par l'authentification est **mis en cache** ; et la méthode `_execute` implémente une **ré-authentification sur expiration** : elle retente l'appel deux fois, en réinitialisant l'`uid` mis en cache entre les tentatives, de sorte qu'une session expirée ne provoque pas un échec définitif. Le connecteur réalise le **mapping employé → utilisateur IAM** en orchestrant la création coordonnée de trois objets Odoo liés :

```python
# 1. Contact (res.partner)
partner_result = self._execute('res.partner', 'create', [[partner_data]])
partner_id = partner_result[0] if isinstance(partner_result, list) else partner_result
# 2. Utilisateur (res.users) lié au contact
user_data = {'name': partner_data['name'], 'login': login, 'partner_id': partner_id, 'active': True}
user_result = self._execute('res.users', 'create', [[user_data]])
user_id = user_result[0] if isinstance(user_result, list) else user_result
# 3. Employé (hr.employee) lié à l'utilisateur
employee_id = await self._create_employee(user_id, partner_id, attributes)
```

Cet enchaînement reflète le modèle de données d'Odoo, où un utilisateur (`res.users`) est rattaché à un contact (`res.partner`) et où la dimension RH passe par un employé (`hr.employee`). Le connecteur normalise par ailleurs les noms de départements pour le mapping automatique de rôles, et sait détecter les contrats expirés ou expirants (`get_expired_contracts`, `get_expiring_contracts`) — fonctions clés du traitement automatisé des départs.

**Les connecteurs dynamiques via la ConnectorFactory.** Au-delà des connecteurs statiques, le `DynamicConnector` permet d'ajouter des cibles **sans redéploiement** : sa configuration est chargée depuis la table `connector_configurations`, et il dispatche son comportement selon le `connector_type` (`sql`, `ldap`, `rest`, `erp`). Le connecteur SQL générique illustre une préoccupation de sécurité majeure : les noms de colonnes, qui ne peuvent pas être paramétrés comme des valeurs en SQL, sont validés contre une **liste blanche stricte** par la fonction `_safe_sql_identifier` (expression régulière `^[A-Za-z_][A-Za-z0-9_]*$`) avant toute interpolation dans une requête — neutralisant l'injection SQL via les clés JSON (cf. §4.2, V5). Le code de provisionnement SQL distingue clairement les **valeurs** (paramétrées) des **identifiants** (validés par allowlist) :

```python
async def _provision_sql(self, operation_type: str, user_data: dict) -> dict:
    conn = await self._get_sql_connection()
    try:
        if operation_type == "create":
            # noms de colonnes validés contre l'allowlist ; valeurs paramétrées ($1, $2, …)
            columns = ", ".join(_safe_sql_identifier(k) for k in user_data.keys())
            placeholders = ", ".join(f"${i+1}" for i in range(len(user_data)))
            query = f"INSERT INTO users ({columns}) VALUES ({placeholders}) RETURNING id"
            result = await conn.fetchval(query, *user_data.values())
            return {"success": True, "id": result}
    finally:
        await conn.close()
```

La distinction est cruciale : les **valeurs** transitent par les paramètres `$1, $2, …` d'asyncpg (jamais interpolées dans la chaîne, donc immunisées contre l'injection par construction), tandis que les **noms de colonnes** — qui ne peuvent pas être paramétrés en SQL — sont systématiquement passés par `_safe_sql_identifier` qui rejette tout ce qui n'est pas un identifiant strict. Cette défense en deux temps couvre les deux seules surfaces d'injection possibles d'une requête dynamique. Le connecteur REST générique, lui, supporte plusieurs schémas d'authentification (aucun, basique, bearer, clé d'API) configurables dynamiquement.

Pour documenter précisément la surface fonctionnelle des connecteurs, le tableau suivant récapitule, pour chaque connecteur statique, les méthodes principales du contrat `BaseConnector` et leur réalisation concrète.

| Méthode | MidPoint (REST) | LDAP (ldap3) | Odoo (XML-RPC) |
|---|---|---|---|
| `test_connection` | `GET /ws/rest/self` | `bind()` puis `unbind()` | `common.version()` |
| `create_account` | `POST /ws/rest/users` (UserType) | `add()` (inetOrgPerson) | `res.partner` + `res.users` + `hr.employee` |
| `update_account` | `POST /ws/rest/users/{oid}` (delta) | `modify()` (MODIFY_REPLACE) | `write()` sur users/partner/employee |
| `delete_account` | `DELETE /ws/rest/users/{oid}` | `delete()` (DN) | `write({'active': False})` (désactivation) |
| `disable_account` | `administrativeStatus=disabled` | `employeeType=disabled` | `write({'active': False})` |
| `enable_account` | `administrativeStatus=enabled` | `employeeType=active` | `write({'active': True})` |
| `get_account` | `GET /ws/rest/users/{oid}` | `search()` (uid/cn/mail) | `search_read()` (login/name/email) |
| `list_accounts` | `GET /ws/rest/users` | `search()` (inetOrgPerson) | `search_read()` res.users |
| gestion groupes/rôles | `assign_role`/`remove_role` (XML) | `add_to_group`/`remove_from_group` | `groups_id` (4=add, 3=remove) |

Le **connecteur MidPoint** illustre la subtilité du dialogue avec un hub IGA. La création d'un utilisateur passe par la construction d'un objet `UserType`, où les attributs source sont cartographiés vers les attributs canoniques de MidPoint (`firstname`→`givenName`, `email`→`emailAddress`, `department`→`organizationalUnit`, etc.), comme le montre `_build_user_object`. L'assignation d'un rôle, en revanche, ne peut se faire en JSON sous MidPoint 4.4 : elle exige une modification au format XML, ce que le connecteur génère explicitement :

```python
modify_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<objectModification xmlns="...api-types-3" xmlns:c="...common-3" xmlns:t="...types-3">
    <itemDelta>
        <t:modificationType>add</t:modificationType>
        <t:path>c:assignment</t:path>
        <t:value xsi:type="c:AssignmentType" ...>
            <c:targetRef oid="{role_oid}" type="c:RoleType"/>
        </t:value>
    </itemDelta>
</objectModification>'''
response = await client.post(f"/ws/rest/users/{user_oid}", content=modify_xml.encode('utf-8'),
                            headers={"Content-Type": "application/xml"})
```

La réponse de MidPoint, à l'inverse, est normalisée par `_parse_user`, qui extrait les attributs canoniques et reconstitue la liste des rôles à partir des assignations :

```python
def _parse_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
    props = user_data.get("user", user_data)
    roles = []
    assignments = props.get("assignment", [])
    if not isinstance(assignments, list):
        assignments = [assignments]
    for a in assignments:
        target_ref = a.get("targetRef", {})
        if "RoleType" in target_ref.get("type", ""):       # filtre les assignations de rôle
            roles.append(target_ref.get("oid"))
    activation = props.get("activation", {})
    return {
        "oid": props.get("oid"), "name": props.get("name"), "fullName": props.get("fullName"),
        "firstname": props.get("givenName"), "lastname": props.get("familyName"),
        "email": props.get("emailAddress"), "department": props.get("organizationalUnit"),
        "active": activation.get("administrativeStatus") == "enabled",
        "roles": roles,
    }
```

Cette gestion du format XML pour les modifications, combinée au parsing défensif des réponses JSON imbriquées de MidPoint, constitue l'essentiel de la complexité du connecteur — complexité que l'abstraction `BaseConnector` masque entièrement aux couches supérieures. La transformation bidirectionnelle (attributs source → `UserType`, puis réponse MidPoint → `MidpointUser`) est précisément ce qui découple le reste de l'application des idiosyncrasies du hub.

Le **connecteur LDAP** illustre, lui, la conjugaison de la robustesse et de la sécurité. Sa méthode de connexion borne les *timeouts* et retente le *bind* deux fois :

```python
def _get_connection(self) -> Connection:
    last_error = None
    for attempt in range(2):
        try:
            return Connection(self.server, user=self.bind_dn, password=self.bind_password,
                              auto_bind=True, receive_timeout=self.timeout)
        except Exception as e:
            last_error = e
            logger.warning("LDAP bind failed, retrying", attempt=attempt + 1, error=str(e))
    raise last_error
```

Sur le plan de la sécurité, chaque recherche échappe ses entrées : `f"(uid={escape_filter_chars(account_id)})"` pour les filtres, `f"uid={escape_rdn(...)},{self.users_ou}"` pour les DN — la correction d'injection détaillée en §4.2 V5. Le connecteur supporte en outre trois types de groupes LDAP (`groupOfNames` via `member`, `groupOfUniqueNames` via `uniqueMember`, `posixGroup` via `memberUid`), détectés dynamiquement à partir des `objectClass` du groupe avant toute modification d'appartenance — preuve d'une compréhension fine du modèle d'annuaire.

Le **connecteur Odoo** illustre la résilience face aux sessions expirées. Sa méthode `_execute` retente l'appel en réinitialisant l'`uid` mis en cache :

```python
def _execute(self, model, method, args_list, kwargs_dict=None):
    last_error = None
    for attempt in range(2):
        try:
            uid = self._authenticate()
            models = self._get_models()
            return models.execute_kw(self.db, uid, self.password, model, method, args_list, kwargs_dict or {})
        except Exception as e:
            last_error = e
            self._uid = None  # forcer une ré-authentification au prochain essai
    raise last_error
```

Au-delà du CRUD, ce connecteur porte une logique métier RH précieuse : la **normalisation des départements** et la **détection des contrats** (`get_expired_contracts`, `get_expiring_contracts`) qui interrogent le modèle `hr.contract` d'Odoo pour identifier les départs à traiter. La normalisation des départements mérite un examen, car elle conditionne le mapping automatique de rôles : un dictionnaire associe les nombreuses variantes d'un même département à un libellé canonique.

```python
def _normalize_department(self, department: str) -> str:
    dept_lower = department.lower().strip()
    mappings = {
        "it": "it", "informatique": "it", "systemes d'information": "it", "dsi": "it",
        "hr": "hr", "rh": "hr", "ressources humaines": "hr",
        "finance": "finance", "comptabilite": "finance", "accounting": "finance",
        "sales": "sales", "ventes": "sales", "commercial": "sales",
        # ... marketing, management, r&d, support, juridique, production, qualité, logistique, achats ...
    }
    for key, value in mappings.items():
        if key in dept_lower:
            return value
    return dept_lower.replace(" ", "-")
```

Cette normalisation résout un problème concret d'intégration : un même département peut être saisi de multiples façons dans Odoo (« Informatique », « IT », « DSI », « Systèmes d'Information »), et sans normalisation, le mapping automatique de rôles échouerait sur ces variantes. En ramenant toutes les formes à un libellé canonique (« it »), le connecteur permet à l'ordonnanceur d'attribuer de manière fiable le rôle correspondant. Cette richesse fonctionnelle fait de l'Odoo le connecteur le plus élaboré du projet, à la hauteur de son double rôle de source RH et de cible.

Le modèle `connector.py` définit par ailleurs une **taxonomie riche** de types et de sous-types de connecteurs, accompagnée de schémas JSON de configuration qui pilotent la génération dynamique des formulaires côté frontend. Le tableau suivant récapitule les sous-types prévus et leurs champs requis :

| Type | Sous-types | Champs requis (exemples) |
|---|---|---|
| `sql` | PostgreSQL, MySQL, Oracle, SQL Server, MariaDB | host, port, database, username, password |
| `ldap` | OpenLDAP, Active Directory, FreeIPA | host, port, bind_dn, bind_password, base_dn |
| `rest` | Keycloak, Firebase, GLPI, REST générique | base_url, auth_type (ou server_url/realm/client) |
| `erp` | Odoo, SAP | url, database, username, password |
| `iga` | MidPoint, IGA générique, SailPoint, Saviynt | url, username, password |

Chaque sous-type est associé à un schéma JSON déclarant ses propriétés, leurs types, leurs valeurs par défaut et le marquage `format: "password"` pour les champs sensibles (masqués dans les réponses API). Cette taxonomie montre que l'architecture des connecteurs a été pensée pour l'**extensibilité** bien au-delà des quatre connecteurs statiques implémentés : ajouter le support effectif d'un nouveau sous-type ne demanderait que d'implémenter sa logique de provisionnement dans le `DynamicConnector`, le schéma de configuration et l'interface étant déjà prévus.

### 3.5 Moteur de règles no-code

Le moteur de règles est ce qui confère à la plateforme sa dimension **no-code** : il permet à un opérateur non programmeur de définir, depuis l'interface, comment les attributs d'une identité sont calculés pour chaque système cible. Une **règle** est un objet comportant un nom, un système cible, une expression, une priorité, un type (`mapping`, `calculation`, `validation`, `aggregation`) et d'éventuelles conditions. L'expression est un **template Jinja2** : par exemple, la règle d'exemple semée en base calcule un login LDAP par `{{ first_name }} {{ last_name }}` et un identifiant par `{{ employee_id }}`. Les types de règles, définis par l'énumération `RuleType`, couvrent les principaux besoins de transformation :

| Type | Finalité | Exemple |
|---|---|---|
| `mapping` | Correspondance directe source→cible | `mail` ← `email` |
| `calculation` | Calcul d'une valeur dérivée | login ← `firstname` + `lastname` |
| `validation` | Vérification d'une contrainte | email conforme à un motif |
| `aggregation` | Agrégation de plusieurs sources | nom complet ← prénom + nom |
| `transformation` | Transformation de format | normalisation, slug |

La sécurité de l'exécution des règles est assurée par un **environnement Jinja2 restreint** (`SafeJinjaEnvironment`, un `SandboxedEnvironment`), enrichi de filtres métier sur mesure tels que `normalize_name`, `generate_login` et `slugify`. Le bac à sable (*sandbox*) est essentiel : il empêche qu'une expression de règle, saisie depuis l'interface, ne puisse exécuter du code arbitraire ou accéder à des attributs Python dangereux. C'est la condition sine qua non pour offrir une édition de règles à des utilisateurs non développeurs sans ouvrir une faille d'exécution de code.

L'**ordre d'exécution** obéit à la **priorité décroissante** : les règles d'un même système cible sont triées par priorité, et la sortie de chaque règle est injectée dans le contexte des règles suivantes (**chaînage**). Ce mécanisme permet de construire des calculs en cascade — par exemple, calculer d'abord un login normalisé, puis l'utiliser pour composer une adresse e-mail. À titre illustratif, la règle LDAP semée par les migrations associe des attributs source à des attributs d'annuaire via des expressions Jinja2 :

```json
{
  "uid": "{{ employee_id }}",
  "cn": "{{ first_name }} {{ last_name }}",
  "sn": "{{ last_name }}",
  "givenName": "{{ first_name }}",
  "mail": "{{ email }}",
  "displayName": "{{ first_name }} {{ last_name }}"
}
```

Les filtres personnalisés enrichissent l'expressivité : `generate_login` pourrait composer `{{ first_name | generate_login(last_name) }}` pour produire un identifiant normalisé (par exemple `jdupont`), `normalize_name` retirerait les accents et la casse, et `slugify` produirait une forme URL-compatible. Le bac à sable garantit que ces expressions, bien que saisies depuis l'interface, ne peuvent ni importer de modules, ni accéder à des attributs Python internes, ni exécuter de code arbitraire — seules les opérations de template et les filtres explicitement autorisés sont disponibles. L'API expose un CRUD complet (`rules.py` : lister, créer, lire, mettre à jour, supprimer), un endpoint de **test** (`POST /rules/test`) qui évalue une règle sur des données d'exemple sans l'appliquer, un **historique de versions** (`GET /rules/{id}/versions`) et une **restauration** de version (`POST /rules/{id}/restore/{version}`). Le versionnement est une fonctionnalité de gouvernance importante : il permet de tracer qui a modifié quelle règle et de revenir en arrière en cas d'erreur.

Il convient toutefois d'être **honnête sur une limite actuelle**, documentée également en §9 : plusieurs méthodes de persistance du `RuleEngine` renvoient encore des données par défaut (mocks) plutôt que d'interroger réellement la table `rules`. La table existe pourtant, et est correctement semée par les migrations. Le câblage complet du moteur à sa persistance figure donc à la feuille de route. Cette transparence sur l'état d'avancement est volontaire : un rapport d'ingénierie sérieux distingue ce qui est pleinement opérationnel de ce qui reste à finaliser.

### 3.6 Workflows d'approbation

Les workflows d'approbation répondent à un besoin de **gouvernance** : certaines opérations de provisionnement, en raison de leur sensibilité, ne doivent pas être exécutées sans validation humaine préalable. Le `WorkflowService` implémente une **chaîne d'approbation multi-niveaux** dont la configuration par défaut comporte trois niveaux : **Manager** (niveau 1, délai 48 h), **RH Manager** (niveau 2, délai 48 h) et **IT Admin** (niveau 3, délai 24 h avec auto-approbation sur expiration). Cette configuration est définie explicitement dans `workflow_service.py` :

```python
DEFAULT_APPROVAL_LEVELS = [
    {"level": 1, "name": "Manager", "approver_type": "manager",
     "role_required": "manager", "timeout_hours": 48, "auto_approve_on_timeout": False},
    {"level": 2, "name": "RH Manager", "approver_type": "role",
     "role_required": "rh_manager", "timeout_hours": 48, "auto_approve_on_timeout": False},
    {"level": 3, "name": "IT Admin", "approver_type": "role",
     "role_required": "it_admin", "timeout_hours": 24, "auto_approve_on_timeout": True},
]
```

On notera que le dernier niveau (IT Admin) porte `auto_approve_on_timeout: True` : passé son délai de 24 h sans décision, il s'approuve automatiquement, évitant qu'une demande ne reste indéfiniment bloquée au niveau final — un compromis pragmatique entre rigueur et fluidité opérationnelle. Trois variantes de chaîne sont prévues, sélectionnables selon la sensibilité de l'opération :

| Variante | Chaîne d'approbation | Usage typique |
|---|---|---|
| `full` | Manager → RH → IT Admin | Création de compte standard (3 validations) |
| `manager_only` | Manager seul | Opération à faible risque (validation rapide) |
| `rh_it` | RH → IT Admin | Opération sans hiérarchie directe (ex. prestataire) |

Les instances de workflow transitent par un ensemble d'états bien défini, modélisé par l'énumération `ApprovalStatus` : `pending` (en attente d'une décision au niveau courant), `approved` (toutes les approbations obtenues), `rejected` (refusé à un niveau), `expired` (délai dépassé sans décision ni auto-approbation) et `cancelled` (annulé par un administrateur). Cette modélisation explicite des états rend le cycle de vie d'une demande entièrement traçable et auditable.

Le flux s'articule avec le provisionnement de la manière suivante. Lorsqu'une `ProvisioningRequest` porte `require_approval=true` et un `manager_email`, le routeur `provision.py` **ne provisionne pas immédiatement** : il crée un workflow via `create_approval_workflow`, enregistre l'opération avec le statut `awaiting_approval` et un drapeau `midpoint_pending=True`, puis retourne une réponse `AWAITING_APPROVAL`. Aucune écriture n'atteint MidPoint ni les cibles tant que l'approbation finale n'est pas obtenue. Cette séparation stricte entre la **demande** et l'**exécution** est la garantie que la validation précède réellement l'action. Le code de l'aiguillage, dans `_provision_via_midpoint`, le montre clairement :

```python
if request.require_approval:
    manager_email = request.attributes.get("manager_email", "")
    operation_id = f"op_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{request.account_id}"
    if manager_email:
        workflow_result = await workflow_service.create_approval_workflow(
            operation_id=operation_id, user_data={**request.attributes, "account_id": request.account_id},
            manager_email=manager_email, requester=current_user["username"])
        memory_store.save_operation(operation_id, {
            "status": "awaiting_approval", "midpoint_pending": True,   # MidPoint différé
            "workflow_id": workflow_result.get("workflow_id"), ...})
        return ProvisioningResponse(status=OperationStatus.AWAITING_APPROVAL, ...)
# sinon : provisionnement immédiat
midpoint_service = await get_midpoint_provision_service(session)
result = await midpoint_service.provision(request=request, created_by=current_user["username"])
```

Le drapeau `midpoint_pending=True` est central : il marque explicitement qu'aucune écriture n'a encore atteint MidPoint, et c'est l'approbation finale du workflow qui, via `continue_after_approval`, lèvera ce drapeau et déclenchera la création effective. Tant que ce drapeau est positionné, l'opération reste une simple intention enregistrée.

La **notification par e-mail** est assurée par l'`EmailService`. Pour chaque niveau, le service génère des **jetons d'approbation et de rejet** uniques et envoie à l'approbateur un e-mail contenant des liens vers `GET /api/v1/workflow/approve-by-email?token=...&action=approve|reject`. En mode `DEV_MODE`, l'e-mail est journalisé plutôt qu'envoyé, ce qui facilite le développement. L'endpoint d'approbation par e-mail retourne une **page HTML de confirmation** élégante, qui affiche la progression du workflow (les niveaux franchis, le niveau courant) — un soin d'expérience utilisateur notable pour une fonctionnalité d'arrière-plan.

L'**API des approbations en attente** (`GET /api/v1/workflow/instances/pending`) permet à un approbateur de lister les demandes qui requièrent son intervention, filtrées selon son rôle et le niveau courant de chaque workflow. Les **instances de workflow** transitent par plusieurs états (`pending`, `approved`, `rejected`, `expired`, `cancelled`), et le service journalise chaque décision dans un historique complet. Le contrôle d'autorisation à l'approbation est de niveau objet : avant d'enregistrer une décision, le routeur vérifie via `can_approve(instance_id, username)` que l'utilisateur est bien légitime pour approuver ce niveau précis. La logique d'avancement, dans `approve_level`, illustre le passage de niveau en niveau jusqu'à complétion :

```python
if current_level >= total_levels:
    workflow["status"] = "approved"            # tous les niveaux franchis
    # notifie le demandeur, déclenche la création du compte (_execute_odoo_sync si source Odoo)
else:
    next_level = current_level + 1
    workflow["current_level"] = next_level     # passe au niveau suivant
    # détermine le prochain approbateur (manager_email ou emails par rôle depuis la DB),
    # génère ses tokens approve/reject et lui envoie la notification email
```

Cette mécanique en escalier garantit qu'**aucun niveau ne peut être sauté** : la demande progresse strictement du niveau 1 vers le niveau final, chaque approbation déclenchant la notification du niveau suivant, et seule l'approbation du dernier niveau déclenche l'exécution effective du provisionnement. Un rejet à n'importe quel niveau, à l'inverse, clôt immédiatement le workflow et annule l'opération. À l'approbation complète, le provisionnement reprend automatiquement (appel à `continue_after_approval` ou `_execute_odoo_sync` selon la source) ; au rejet, l'opération est annulée. Cette intégration fluide entre workflow et provisionnement fait du système d'approbation un véritable point de contrôle opérationnel, et non un simple registre déclaratif.

### 3.7 Ordonnanceur de tâches

L'ordonnanceur automatise les tâches récurrentes de gouvernance des identités. Il s'appuie sur **APScheduler** (`AsyncIOScheduler`), avec un magasin de jobs en mémoire, et est exposé par le routeur `scheduler.py`. Trois types de planification sont offerts, récapitulés ci-dessous :

| Type | Endpoint | Configuration | Exemple |
|---|---|---|---|
| Quotidienne | `POST /scheduler/jobs/daily` | heure + minute | tous les jours à 2 h 00 |
| Intervalle | `POST /scheduler/jobs/interval` | heures + minutes | toutes les 2 heures |
| Cron | `POST /scheduler/jobs/cron` | expression cron | `0 9 * * 1-5` (jours ouvrés 9 h) |
| Preset workday | `POST /scheduler/presets/workday` | — | 8 h, 12 h, 18 h (lun.–ven.) |
| Preset nightly | `POST /scheduler/presets/nightly` | heure | nocturne quotidien |
| Preset hourly | `POST /scheduler/presets/hourly` | — | toutes les heures |
| Contrôle contrats | `POST /scheduler/jobs/contract-check` | heure + minute | désactivation des contrats expirés | Des **presets** facilitent la configuration : `workday` crée trois synchronisations aux heures ouvrées (8 h, 12 h, 18 h du lundi au vendredi), `nightly` une synchronisation nocturne, `hourly` une synchronisation horaire. Le preset jours ouvrés, par exemple, se traduit par trois expressions cron créées d'un coup :

```python
sync_scheduler.add_cron_sync(job_id="workday-morning", cron_expression="0 8 * * 1-5", enabled=True)
sync_scheduler.add_cron_sync(job_id="workday-noon",    cron_expression="0 12 * * 1-5", enabled=True)
sync_scheduler.add_cron_sync(job_id="workday-evening", cron_expression="0 18 * * 1-5", enabled=True)
```

Les expressions cron (`0 8 * * 1-5` = à 8 h 00 du lundi au vendredi) offrent une expressivité complète, validée à la création par un contrôle du nombre de champs. Chaque création de job retourne une description lisible de la planification, et l'endpoint `POST /jobs/{job_id}/run` permet de **forcer une exécution immédiate** — précieux pour tester une synchronisation sans attendre l'échéance planifiée.

Trois jobs automatiques portent la valeur métier de l'ordonnanceur. Le premier est la **synchronisation Odoo→MidPoint**, qui importe périodiquement les employés depuis l'ERP vers le hub IAM ; il automatise le moment *Joiner* en garantissant qu'un nouvel employé saisi dans le système RH se voit provisionner ses comptes sans intervention manuelle. Le deuxième est l'**attribution de rôles par département** (`DEPARTMENT_ROLE_MAPPING`), qui aligne automatiquement les droits sur l'organisation : un employé du département « Finance » se voit attribuer le rôle correspondant, et donc les accès associés, par simple lecture de son département Odoo (préalablement normalisé par le connecteur, cf. §3.4). Le troisième, particulièrement aligné sur le problème JML, est le **traitement des contrats expirés** : le job `contract-check` (configurable à une heure précise, par défaut 6 h du matin) interroge Odoo via `get_expired_contracts` pour détecter les contrats échus et **désactive automatiquement** les comptes correspondants — automatisant ainsi le moment *Leaver* le plus critique. Ces trois jobs couvrent donc, à eux seuls, l'essentiel du cycle JML de manière automatisée, l'historique de chaque exécution étant consultable via `GET /scheduler/history` et `GET /scheduler/contracts/history`. Chaque job peut être activé/désactivé, exécuté manuellement à la demande (`POST /jobs/{id}/run`) et son historique est consultable, offrant à l'exploitant un contrôle complet sur l'automatisation.

### 3.8 Webhooks bidirectionnels

Les webhooks réalisent la communication **entrante** depuis MidPoint vers la gateway, complétant la communication sortante (gateway → MidPoint). Lorsqu'une identité change dans MidPoint, celui-ci notifie la gateway sur `POST /api/v1/webhooks/midpoint/user-change`, ce qui déclenche la réplication du changement vers Keycloak. La sécurité de ce point d'entrée est critique : un appelant non authentifié pouvant le solliciter pourrait créer ou supprimer des comptes Keycloak. La protection repose sur une **vérification de signature HMAC-SHA256**, implémentée dans la dépendance `verify_midpoint_signature` :

```python
expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
if not hmac.compare_digest(expected, signature):
    raise HTTPException(status_code=401, detail="Invalid webhook signature")
```

Trois propriétés de cette vérification sont remarquables. D'abord, elle s'exécute **avant tout traitement** (en dépendance), de sorte qu'une requête non signée est rejetée sans effet. Ensuite, la comparaison utilise `hmac.compare_digest`, qui s'effectue en **temps constant** pour ne pas fuiter d'information par analyse temporelle. Enfin, elle est **fail-closed en production** : si le secret n'est pas configuré, le webhook renvoie 503 (sauf en mode DEBUG, où la vérification est contournée pour le développement). Cette gestion du secret manquant est explicite :

```python
async def verify_midpoint_signature(request: Request) -> None:
    body = await request.body()
    secret = settings.MIDPOINT_WEBHOOK_SECRET
    if not secret:
        if settings.DEBUG:
            logger.warning("MIDPOINT_WEBHOOK_SECRET non configuré - vérification ignorée (DEBUG)")
            return
        logger.error("MIDPOINT_WEBHOOK_SECRET non configuré - webhook rejeté")
        raise HTTPException(status_code=503, detail="Webhook authentication not configured")
    signature = request.headers.get("X-MidPoint-Signature", "")
    if signature.startswith("sha256="):
        signature = signature.split("=", 1)[1]
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
```

On y observe la lecture du corps brut (nécessaire car la signature porte sur les octets exacts, et non sur le JSON re-sérialisé), le support du préfixe `sha256=` (convention courante) et la distinction nette entre l'absence de secret (503 en production, contournement en DEBUG) et la signature invalide (401). C'est cette dépendance, déclarée via `dependencies=[Depends(verify_midpoint_signature)]` sur l'endpoint, qui garantit l'exécution de la vérification **avant** toute logique métier. Une fois la signature validée, le traitement est délégué à une **tâche d'arrière-plan** (`BackgroundTasks`) afin de répondre immédiatement à MidPoint, et le `KeycloakProvisioner` crée/met à jour/supprime l'utilisateur Keycloak selon l'opération — en générant un **mot de passe temporaire aléatoire** (`secrets.token_urlsafe(24)`) à la création (cf. §4.2, V4). Le `KeycloakProvisioner` (défini dans `webhooks.py`) encapsule le dialogue avec l'API d'administration de Keycloak. Il obtient d'abord un jeton d'administration via le *grant* `password` du client `admin-cli`, puis dispatche selon l'opération. La création illustre la génération du mot de passe temporaire aléatoire et le forçage de sa réinitialisation :

```python
keycloak_user = {
    "username": username,
    "email": user_data.get("email") or f"{username}@example.com",
    "firstName": user_data.get("givenName") or "",
    "lastName": user_data.get("familyName") or "",
    "enabled": True, "emailVerified": True,
    "credentials": [{"type": "password", "value": _secrets.token_urlsafe(24), "temporary": True}],
}
response = await client.post(f"{self.base_url}/admin/realms/{self.realm}/users",
                            json=keycloak_user, headers={"Authorization": f"Bearer {token}"}, timeout=10.0)
```

La méthode `provision_user` réalise un aiguillage idempotent selon l'opération et l'existence préalable du compte :

| Opération MidPoint | Compte Keycloak existant ? | Action |
|---|---|---|
| `add` / `create` | oui | mise à jour (au lieu d'échouer) |
| `add` / `create` | non | création (mot de passe temporaire aléatoire) |
| `modify` / `update` | oui | mise à jour |
| `modify` / `update` | non | création |
| `delete` | oui | suppression |
| `delete` | non | succès (déjà absent) |

Cet aiguillage tolère donc aussi bien les re-livraisons de webhook que les états initiaux incohérents, sans jamais produire d'erreur évitable. Les comptes système (`administrator`, `midpoint`) sont explicitement ignorés. Chaque appel HTTP est borné par un *timeout* de 10 secondes. Cette idempotence est essentielle dans un contexte de webhook, où une même notification peut être reçue plusieurs fois (re-livraison) sans devoir produire d'erreur ou de duplication.

Un endpoint administratif `POST /webhooks/midpoint/sync-all` permet par ailleurs de déclencher une synchronisation complète manuelle.

### 3.9 Assistant IA intégré

L'assistant IA est la fonctionnalité la plus innovante de la plateforme, bien qu'optionnelle. Il s'appuie sur la base vectorielle **Qdrant**, qui indexe les journaux d'audit pour permettre une recherche par similarité, et sur un agent (`ai_agent.py`) interrogeant un fournisseur de modèle de langage configurable (OpenAI, Anthropic, Mistral, DeepSeek, Azure). Le routeur `ai_assistant.py` expose plusieurs outils : `POST /ai/query` (questions en langage naturel sur le provisionnement), `POST /ai/suggest-mappings` (suggestions automatiques de correspondances d'attributs source→cible), `POST /ai/generate-connector` (génération de squelette de connecteur), `POST /ai/analyze-error` (diagnostic d'erreurs) et `POST /ai/explain-rule` (explication d'une règle en langage naturel). La **clé d'API** du fournisseur est stockée en base (table `ai_configuration`) et **n'est jamais renvoyée au frontend** : l'endpoint `GET /ai/config` n'indique que si une configuration existe. Les fournisseurs pris en charge et les outils exposés sont récapitulés ci-dessous :

| Fournisseur | Identifiant | Outils de l'assistant | Endpoint |
|---|---|---|---|
| OpenAI | `openai` | Question libre | `POST /ai/query` |
| Anthropic | `anthropic` | Suggestion de mappings | `POST /ai/suggest-mappings` |
| Mistral AI | `mistral` | Génération de connecteur | `POST /ai/generate-connector` |
| DeepSeek | `deepseek` | Analyse d'erreur | `POST /ai/analyze-error` |
| Azure OpenAI | `azure` | Explication de règle | `POST /ai/explain-rule` |

La protection de la clé d'API est exemplaire : l'endpoint de lecture `GET /ai/config` retourne un booléen `is_configured` et le nom du fournisseur, mais **jamais la clé**, même tronquée — l'écriture de configuration (`POST /ai/config`, réservée à `admin`) la stocke en base sans la réexposer.

Le caractère **optionnel** de l'assistant est important : Qdrant dégrade gracieusement (cf. §2.1), si bien que son absence n'empêche pas le fonctionnement de la plateforme. La recherche d'audit s'effectue par vectorisation du texte de requête et recherche des plus proches voisins par distance cosinus. Il faut noter — par souci d'exactitude — que la vectorisation actuelle (`qdrant_store.py`) repose sur un encodage **déterministe par hachage** de dimension 128, présenté dans le code comme un substitut destiné à être remplacé par un véritable modèle d'embedding (ex. `all-MiniLM-L6-v2`) ; l'infrastructure vectorielle est donc en place, mais la qualité sémantique réelle reste à enrichir, comme détaillé en §6.5.

### 3.10 Comparaison en temps réel

Le routeur `live_comparison.py` offre une **vue transversale** de l'état de synchronisation des identités à travers les systèmes. Son endpoint `GET /api/v1/live/compare` interroge en parallèle LDAP, SQL et Odoo, croise les identités par e-mail ou identifiant, et calcule pour chacune un statut de synchronisation :

| Statut | Condition | Interprétation |
|---|---|---|
| `synced` | présente dans les 3 systèmes | identité cohérente |
| `partial` | présente dans 2 systèmes | désynchronisation (liste des systèmes manquants fournie) |
| `isolated` | présente dans 1 seul système | identité orpheline ou non propagée |

Ces statuts, agrégés, produisent un **taux de synchronisation** global et une liste de divergences exploitables. Il en déduit des statistiques agrégées, dont un **taux de synchronisation** global. L'endpoint `GET /live/user/{identifier}` permet, lui, de retrouver une identité précise dans tous les systèmes et de diagnostiquer où elle manque. L'algorithme de comparaison récupère les comptes des trois systèmes, les indexe par e-mail (ou identifiant à défaut), calcule l'union des clés et, pour chacune, compte sa présence : trois présences donnent le statut `synced`, deux donnent `partial` (avec la liste des systèmes manquants), une seule donne `isolated`. Le taux de synchronisation est dérivé du ratio d'identités présentes dans les trois systèmes sur le total des identités uniques :

```python
present_count = sum([ref["in_ldap"], ref["in_sql"], ref["in_odoo"]])
if present_count == 3:    ref["sync_status"] = "synced"
elif present_count == 2:  ref["sync_status"] = "partial"   # + liste des systèmes manquants
else:                     ref["sync_status"] = "isolated"
# ...
"sync_rate": f"{(len(in_all_systems) / max(len(all_keys), 1)) * 100:.1f}%"
```

Ce diagnostic outillé répond directement au problème du *Mover* (§1.2) : il rend visibles les incohérences inter-systèmes — un compte présent dans LDAP mais absent d'Odoo, par exemple — qui sont précisément les symptômes d'un cycle de vie mal géré.

Au-delà du diagnostic, ce routeur réalise la **synchronisation Odoo→MidPoint**, avec ou sans approbation. L'endpoint `POST /live/sync/odoo-to-midpoint` crée directement les utilisateurs MidPoint manquants (en générant un nom d'utilisateur depuis le nom de l'employé et en évitant les doublons par e-mail et identifiant), tandis que `POST /live/sync/odoo-to-midpoint/with-approval` enclenche pour chaque employé un workflow d'approbation multi-niveaux, ne créant le compte qu'après validation complète. La génération du nom d'utilisateur et la détection des doublons illustrent le soin porté à l'idempotence de la synchronisation :

```python
name_parts = emp_name.split()
if len(name_parts) >= 2:
    firstname, lastname = name_parts[0], " ".join(name_parts[1:])
    username = f"{firstname.lower()}{lastname.lower().replace(' ', '')}"
else:
    firstname, lastname, username = emp_name, "", emp_name.lower().replace(" ", "")

if emp_email and emp_email.lower() in existing_emails:   # doublon par email
    results.append({"name": emp_name, "status": "skipped", "reason": "Email already exists"})
    continue
if username.lower() in existing_usernames:               # doublon par username
    results.append({"name": emp_name, "status": "skipped", "reason": "Username already exists"})
    continue
```

Cette double vérification (par e-mail **et** par identifiant), conjuguée à la mise à jour des ensembles `existing_emails`/`existing_usernames` au fil de la boucle, garantit qu'aucun doublon n'est créé, **même au sein d'un même lot de synchronisation** — un détail qui distingue une synchronisation robuste d'une synchronisation naïve. Le routeur expose également la **détection des contrats** expirés (`/contracts/expired`) et expirants (`/contracts/expiring`), ainsi que la **désactivation/réactivation multi-systèmes** d'un compte (`/account/{username}/disable` et `/enable`), qui agit simultanément sur MidPoint, LDAP et Odoo. Cet ensemble fait de la comparaison temps réel un véritable tableau de bord opérationnel de la cohérence inter-systèmes.

### 3.11 Interface React

L'interface d'administration est une application monopage (*SPA*) construite avec **Vite + React 18 + TypeScript**, totalisant 25 fichiers TypeScript/TSX. Son architecture, décrite dans les fiches techniques, repose sur une instance **Axios unique** (`src/lib/api.ts`) qui injecte automatiquement le jeton JWT dans l'en-tête `Authorization` de chaque requête et redirige vers `/login` en cas de réponse 401 — centralisant ainsi la logique d'authentification côté client. L'état applicatif est géré par **Zustand** (état d'authentification) et **TanStack Query** (état serveur, cache des requêtes), et l'interface est internationalisée (`en`/`fr`/`uk`). L'édition des règles bénéficie de l'éditeur **Monaco** (le moteur de VS Code).

En production, l'interface est servie en **statique par nginx** après compilation, via une construction Docker multi-étapes : l'image finale ne contient ni Node ni `node_modules`, seulement les fichiers compilés et la configuration nginx.

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build                 # produit dist/

FROM nginx:alpine                 # image finale : pas de Node
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

La configuration nginx assure le proxy de l'API, le routage SPA et des **en-têtes de sécurité** :

```nginx
location /api {
    proxy_pass http://gateway:8000;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
location / {
    try_files $uri $uri/ /index.html;       # routage SPA
}
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

Ces en-têtes (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`) ajoutent une couche de défense côté navigateur contre le *clickjacking*, le *MIME sniffing* et certaines attaques XSS, complétant la sécurité applicative du backend. Un point connu, sans gravité fonctionnelle, mérite d'être signalé : le build Vite émet un **avertissement de taille de chunk** (supérieure à 500 ko), attendu en raison de l'embarquement de l'éditeur Monaco ; cet avertissement est non bloquant et pourrait être traité par un découpage de code (*code splitting*) ultérieur. L'absence de `package-lock.json` versionné (cf. §9) affecte par ailleurs la reproductibilité exacte des builds frontend, point inscrit à la feuille de route.

L'interface est organisée autour de **seize pages** (sous `src/pages/`), chacune correspondant à un domaine fonctionnel du backend : `Landing` (page d'accueil publique), `Login` (authentification), `Dashboard` (tableau de bord), `Operations` (opérations de provisionnement), `Rules` (édition des règles avec Monaco), `Workflows` (approbations), `Reconciliation` (réconciliation), `Connectors` (connecteurs dynamiques), `MidpointUsers` (utilisateurs MidPoint), `LiveComparison` (comparaison temps réel), `LDAPGroups` (groupes LDAP), `Permissions` (niveaux de droits), `Users` (utilisateurs gateway), `AuditLogs` (journaux d'audit), `AIAssistant` (assistant IA) et `Settings` (configuration). Cette correspondance page↔domaine reflète la cohérence d'ensemble entre le backend et le frontend. Les composants transverses (`Layout`, `LanguageSelector`) et le découpage `lib/api.ts` (instance Axios), `store/auth.ts` (Zustand) et `i18n/` (traductions `en`/`fr`/`uk`) complètent une architecture frontend claire et maintenable. Le routage (`App.tsx`) distingue les routes publiques (`/`, `/login`) des routes protégées (`/dashboard/*`) derrière un garde `PrivateRoute`, garantissant qu'aucune vue d'administration n'est accessible sans authentification.

### 3.12 Réconciliation et gestion des divergences

La réconciliation est la fonctionnalité de gouvernance qui garantit, dans la durée, la **cohérence** entre l'état attendu des identités (côté hub) et leur état réel (côté systèmes cibles). Sans elle, des dérives s'accumulent inévitablement : un compte modifié manuellement dans LDAP, un employé désactivé dans Odoo mais resté actif ailleurs, une projection orpheline. Le routeur `reconcile.py` expose le cycle complet : démarrer un job (`POST /reconcile/start`), suivre son statut (`GET /reconcile/status/{job_id}`), lister les jobs (`GET /reconcile/jobs`), consulter les divergences détectées (`GET /reconcile/{job_id}/discrepancies`) et les résoudre (`POST /reconcile/{job_id}/resolve`).

Les jobs de réconciliation sont persistés dans la table `reconciliation_jobs` (statut, horodatages de début et de fin, nombre total d'utilisateurs, nombre traité, nombre de divergences trouvées, systèmes cibles), et les divergences elles-mêmes dans la table `discrepancies` (identité, système, type de divergence, valeur côté gateway, valeur côté cible, statut de résolution). Cette persistance structurée permet de **tracer** chaque campagne de réconciliation et de produire des indicateurs de qualité de synchronisation. L'endpoint `POST /reconcile/sync-cache` rafraîchit par ailleurs le cache d'état des comptes (`account_state_cache`), support de la détection ultérieure des écarts. En mode hub, la réconciliation profonde est largement déléguée à MidPoint (dont c'est l'une des fonctions natives), la gateway offrant la vue de pilotage ; en mode direct, elle s'appuie sur le cache d'état maintenu par le `ProvisionService`. Couplée à la comparaison temps réel (§3.10), cette fonctionnalité ferme la boucle de gouvernance : détecter, qualifier, puis corriger les incohérences inter-systèmes.

---

## 4. Audit de sécurité complet

### 4.1 Méthodologie d'audit

L'audit de sécurité de la plateforme a suivi une **méthodologie structurée**, combinant une revue de code manuelle systématique et une cartographie des risques inspirée de l'OWASP Top 10. L'approche n'a pas consisté à passer un outil automatique et à corriger ses alertes, mais à **relire le code couche par couche** en se posant, pour chaque point d'entrée et chaque interaction externe, la question de l'attaquant : « que pourrais-je exploiter ici ? ». Cette démarche, plus exigeante, permet de détecter des failles logiques (un contrôle d'autorisation manquant, une comparaison non constante) qu'aucun scanner ne signale. Le tableau suivant met en correspondance les vulnérabilités traitées avec les catégories de l'OWASP Top 10, illustrant la couverture de l'audit.

| Catégorie OWASP | Vulnérabilités du projet concernées |
|---|---|
| A01 — Broken Access Control | V3 (RBAC incomplet), V13 (SSRF / test-preview) |
| A02 — Cryptographic Failures | V1 (secret JWT faible), V4 (mot de passe temporaire prévisible) |
| A03 — Injection | V5 (injection LDAP et SQL) |
| A05 — Security Misconfiguration | V2 (secrets en dur), V11 (durcissement Docker) |
| A07 — Identification & Auth Failures | V1 (forge JWT), V6 (audience JWT), V10 (force brute) |
| A08 — Software & Data Integrity | V4 (HMAC webhook), V8 (perte d'écritures d'audit) |
| A09 — Security Logging & Monitoring | V9 (fuite par les erreurs, corrélation), V12 (tests/CI) |
| A06 — Vulnerable Components | analyse `pip-audit` en CI (§4.3) |
| Disponibilité (hors OWASP strict) | V7 (I/O bloquantes) |



Le **périmètre** de l'audit a couvert sept catégories de risques : l'**authentification** (gestion des jetons, des mots de passe, des sessions), l'**autorisation** (complétude du RBAC, élévation de privilèges), l'**injection** (LDAP, SQL), la **cryptographie** (secrets de signature, hachage), la **configuration** (secrets par défaut, mode debug), l'**infrastructure** (durcissement des conteneurs, exposition réseau) et le **logging** (fuite d'informations, traçabilité). Chaque catégorie a été examinée à la lumière du code réel, en remontant les chemins d'exécution depuis les points d'entrée publics.

La **priorisation** des vulnérabilités a suivi une logique de type CVSS, croisant la probabilité d'exploitation et l'impact. Une faille permettant la **forge de jetons** (compromission totale de l'authentification) ou une **injection** (exécution de requêtes arbitraires) est classée CRITIQUE. Une faille permettant une **élévation de privilèges**, une **usurpation de webhook** ou un **SSRF** est classée HAUTE. Les problèmes de **disponibilité** (blocage de la boucle d'événements), d'**intégrité d'audit** ou de **fuite d'informations par les erreurs** sont classés MOYENNE. Cette hiérarchisation a guidé l'ordre des corrections.

La **stratégie de branche** mérite d'être soulignée comme une bonne pratique d'ingénierie de sécurité. L'ensemble des corrections a été isolé sur une branche dédiée `security-hardening`, et **chaque vulnérabilité a fait l'objet d'un commit distinct**. Cette granularité offre une **traçabilité** exemplaire : chaque correction est documentée par son message de commit, peut être revue indépendamment, et pourrait être annulée isolément si elle introduisait une régression. Les treize commits de sécurité forment ainsi un registre auditable des décisions prises, ce que la sous-section suivante détaille un par un.

### 4.2 Vulnérabilités identifiées et corrections détaillées

Les treize vulnérabilités ci-dessous correspondent aux treize commits de la branche `security-hardening`, présentés dans leur ordre chronologique de correction. Les extraits « avant » reconstituent le motif vulnérable à partir de la correction observée et sont fournis à titre illustratif ; les extraits « après » reflètent le code réellement présent dans le dépôt. Le tableau suivant offre une vue d'ensemble des treize corrections :

| # | Vulnérabilité | Commit | Sévérité |
|---|---|---|---|
| V1 | Secret de signature JWT faible | `d68adfb` | CRITIQUE |
| V2 | Identifiants admin codés en dur | `8d3ac36` | HAUTE |
| V3 | RBAC incomplet (élévation de privilèges) | `0483e05` | HAUTE |
| V4 | Webhook MidPoint non authentifié | `7b834c0` | HAUTE |
| V5 | Injection LDAP et SQL | `2876c1d` | CRITIQUE |
| V6 | bcrypt bloquant / JWT sans audience | `65b2e6d` | MOYENNE |
| V7 | I/O bloquantes (connecteurs, SMTP) | `9296a3b` | MOYENNE |
| V8 | Tâches d'arrière-plan perdues (GC) | `6cf898d` | MOYENNE |
| V9 | Fuite d'informations par les erreurs | `e2fb262` | MOYENNE |
| V10 | Absence de limitation force brute | `5a46ddf` | HAUTE |
| V11 | Durcissement Docker | `97d284c` | HAUTE |
| V12 | Absence de filet de sécurité (tests/CI) | `8f93b6b` | PROCESSUS |
| V13 | SSRF + intégrité d'authentification | `088de77` | HAUTE |

#### V1 — Secret de signature JWT faible ou par défaut (Commit : `d68adfb`, Sévérité : CRITIQUE)

**Description de la vulnérabilité.** En l'absence de validation, l'application pouvait démarrer avec un `SECRET_KEY`/`JWT_SECRET_KEY` vide, par défaut ou trop court. Or la signature des JWT en HS256 repose entièrement sur le secret de l'émetteur : si ce secret est connu, prévisible ou faible, un attaquant peut **forger des jetons valides** pour n'importe quel utilisateur, y compris `admin`, et compromettre l'intégralité de l'authentification. Le scénario d'attaque est direct : récupérer le secret par défaut (présent dans le code source public), forger un JWT avec `roles: ["admin"]`, et accéder à toutes les fonctions.

**Code vulnérable (avant).**
```python
class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production"
    JWT_SECRET_KEY: str = "jwt-secret-change-in-production"
    # ... aucune validation : l'app démarre avec ces valeurs
```

**Correction appliquée.** Un validateur Pydantic *fail-fast* refuse désormais tout secret faible hors mode DEBUG, et génère un secret éphémère en DEBUG :
```python
@model_validator(mode="after")
def _enforce_secret_strength(self) -> "Settings":
    for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = getattr(self, name) or ""
        if value not in _INSECURE_SECRETS and len(value) >= 32:
            continue
        if self.DEBUG:
            setattr(self, name, _secrets.token_urlsafe(48))
            warnings.warn(f"{name} was unset/weak; generated an ephemeral DEBUG secret.")
        else:
            raise RuntimeError(f"{name} must be set to a strong random value (>= 32 chars) when DEBUG is false.")
    return self
```

**Impact de la correction.** Il devient impossible de déployer en production avec un secret prévisible : l'application refuse de démarrer, fermant la voie à la forge de jetons.

#### V2 — Identifiants administrateur codés en dur (Commit : `8d3ac36`, Sévérité : HAUTE)

**Description de la vulnérabilité.** Des identifiants d'administration (MidPoint) étaient présents en clair dans le code source, et un bug autour de la variable `MIDPOINT_USERNAME` faisait silencieusement échouer toutes les opérations sur les ressources MidPoint. Des secrets dans le code source sont exposés à quiconque accède au dépôt, et survivent dans l'historique Git même après suppression.

**Code vulnérable (avant).**
```python
MIDPOINT_USER = "administrator"
MIDPOINT_PASSWORD = "5ecr3t"   # en dur dans le module
# usage incohérent de MIDPOINT_USERNAME (inexistant) → opérations cassées
```

**Correction appliquée.** Les identifiants passent par la configuration typée (variables d'environnement, valeurs par défaut de dev uniquement), et l'incohérence de nommage est corrigée :
```python
MIDPOINT_USER: str = Field(default="administrator")
MIDPOINT_PASSWORD: str = Field(default="5ecr3t")  # surchargé par .env en prod
```

**Impact de la correction.** Les secrets quittent le code applicatif au profit de l'environnement, et les opérations sur les ressources MidPoint redeviennent fonctionnelles.

#### V3 — Contrôle d'accès (RBAC) incomplet (Commit : `0483e05`, Sévérité : HAUTE)

**Description de la vulnérabilité.** Certains endpoints modifiant des identités n'imposaient qu'une authentification (`get_current_user`) sans contrôle de rôle, permettant à tout utilisateur authentifié — fût-il un simple `viewer` — d'exécuter des opérations sensibles (création, suppression, attribution de rôle). C'est une faille d'**élévation de privilèges horizontale et verticale**.

**Code vulnérable (avant).**
```python
@router.delete("/{operation_id}")
async def delete_operation(operation_id: str, current_user: dict = Depends(get_current_user)):
    # tout utilisateur authentifié pouvait supprimer
```

**Correction appliquée.** Tous les endpoints mutants imposent désormais un rôle, les suppressions et la gestion des rôles étant réservées à `admin` :
```python
@router.delete("/{operation_id}")
async def delete_operation(operation_id: str, current_user: dict = Depends(require_role(["admin"]))):
    ...
```

**Impact de la correction.** Un `viewer` ne peut plus muter d'état ; la séparation des privilèges est effective sur toute la surface d'API.

#### V4 — Webhook MidPoint non authentifié (Commit : `7b834c0`, Sévérité : HAUTE)

**Description de la vulnérabilité.** L'endpoint de webhook `POST /webhooks/midpoint/user-change` acceptait toute requête, sans vérifier qu'elle provenait bien de MidPoint. Un attaquant pouvait donc **usurper MidPoint** et déclencher la création, la modification ou la suppression de comptes Keycloak arbitraires. De plus, les comptes Keycloak étaient créés avec un mot de passe temporaire prévisible.

**Code vulnérable (avant).**
```python
@router.post("/midpoint/user-change")
async def midpoint_user_change_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()  # aucune vérification de provenance
```

**Correction appliquée.** Une dépendance vérifie une signature **HMAC-SHA256** en temps constant avant tout traitement, et le mot de passe temporaire devient aléatoire :
```python
expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
if not hmac.compare_digest(expected, signature):
    raise HTTPException(status_code=401, detail="Invalid webhook signature")
# ... création Keycloak :
"credentials": [{"type": "password", "value": _secrets.token_urlsafe(24), "temporary": True}]
```

**Impact de la correction.** Seul un appelant détenant le secret partagé peut solliciter le webhook ; l'usurpation est neutralisée et les mots de passe temporaires sont imprévisibles.

#### V5 — Injection LDAP et SQL (Commit : `2876c1d`, Sévérité : CRITIQUE)

**Description de la vulnérabilité.** Les filtres de recherche LDAP et les composants de DN étaient construits par concaténation de chaînes non échappées, et les noms de colonnes des requêtes SQL dynamiques provenaient directement des clés de dictionnaires JSON. Un attaquant pouvait **injecter** des métacaractères LDAP (pour contourner un filtre d'authentification ou exfiltrer des entrées) ou des fragments SQL (pour détourner une requête).

**Code vulnérable (avant).**
```python
search_filter = f"(uid={account_id})"             # injection LDAP
columns = ", ".join(user_data.keys())             # injection SQL via clés JSON
query = f"INSERT INTO users ({columns}) VALUES (...)"
```

**Correction appliquée.** Échappement systématique LDAP et liste blanche stricte des identifiants SQL :
```python
search_filter = f"(uid={escape_filter_chars(account_id)})"
dn = f"uid={escape_rdn(uid)},{self.users_ou}"
# SQL :
_SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
def _safe_sql_identifier(name: str) -> str:
    if not isinstance(name, str) or not _SQL_IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name
```

**Impact de la correction.** Les métacaractères sont neutralisés (LDAP) et toute colonne non conforme est rejetée avant exécution (SQL), fermant les deux vecteurs d'injection.

#### V6 — bcrypt bloquant et JWT sans audience (Commit : `65b2e6d`, Sévérité : MOYENNE)

**Description de la vulnérabilité.** Le hachage bcrypt était appelé de manière synchrone dans des *handlers* asynchrones, **bloquant la boucle d'événements** à chaque connexion et exposant à un déni de service par saturation. Par ailleurs, les JWT ne portaient pas de revendications `iss`/`aud`, autorisant une confusion d'audience.

**Code vulnérable (avant).**
```python
# dans un handler async :
if not verify_password(form_data.password, password_hash):  # bloque l'event loop
```

**Correction appliquée.** Déport du bcrypt hors boucle et ajout/vérification des claims `iss`/`aud` :
```python
if not await verify_password_async(form_data.password, password_hash):
    ...
# decode_token vérifie désormais audience= et issuer=
```

**Impact de la correction.** La boucle d'événements reste réactive sous charge, et les jetons sont liés à un émetteur et une audience précis.

#### V7 — I/O bloquantes (tests de connecteurs, SMTP) (Commit : `9296a3b`, Sévérité : MOYENNE)

**Description de la vulnérabilité.** À l'instar de bcrypt, les tests de connexion synchrones (ldap3, xmlrpc) et l'envoi d'e-mails SMTP s'exécutaient dans le fil principal, bloquant la boucle d'événements et dégradant la disponibilité de l'ensemble de l'API pendant ces opérations potentiellement lentes.

**Code vulnérable (avant).**
```python
conn = Connection(server, ..., auto_bind=True)  # bind synchrone bloquant
smtp.send_message(msg)                           # envoi SMTP bloquant
```

**Correction appliquée.** Déport systématique des I/O bloquantes hors de la boucle (via `asyncio.to_thread` et bornage des timeouts), de sorte qu'un connecteur lent ou un serveur SMTP injoignable ne fige plus le service.

**Impact de la correction.** La disponibilité de l'API est préservée même lorsqu'un système externe est lent ou indisponible.

#### V8 — Tâches d'arrière-plan perdues par le GC (Commit : `6cf898d`, Sévérité : MOYENNE)

**Description de la vulnérabilité.** Les écritures de persistance étaient lancées en *fire-and-forget* via `asyncio.create_task` sans conserver de référence forte. Or `asyncio` ne garde qu'une **référence faible** aux tâches : une tâche non référencée peut être **collectée par le ramasse-miettes** avant la fin de son exécution, entraînant la **perte silencieuse** d'écritures en base — y compris d'entrées d'audit, ce qui constitue un risque d'intégrité.

**Code vulnérable (avant).**
```python
asyncio.create_task(self._persist(data))  # référence perdue → GC possible
```

**Correction appliquée.** Conservation des tâches dans un ensemble (référence forte) et journalisation des exceptions :
```python
task = loop.create_task(coro)
self._pending_tasks.add(task)
task.add_done_callback(lambda t: (self._pending_tasks.discard(t),
    logger.error("Background persistence task failed", error=str(t.exception())) if t.exception() else None))
```

**Impact de la correction.** Les écritures asynchrones, dont l'audit, ne peuvent plus être perdues par le GC, et leurs erreurs sont tracées.

#### V9 — Fuite d'informations par les erreurs (Commit : `e2fb262`, Sévérité : MOYENNE)

**Description de la vulnérabilité.** Les exceptions non gérées pouvaient renvoyer au client des traces d'exécution (*stack traces*) révélant la structure interne, les chemins de fichiers, voire des fragments de requêtes — autant d'informations utiles à un attaquant. L'absence de corrélation rendait par ailleurs le diagnostic difficile.

**Code vulnérable (avant).**
```python
# pas de handler global : FastAPI/Starlette renvoie la trace en cas d'exception non gérée
```

**Correction appliquée.** Un middleware de corrélation (`X-Request-ID`) et un handler centralisé qui renvoie un 500 générique :
```python
except Exception as exc:
    logger.error("Unhandled exception", error=str(exc), exc_info=True)
    response = JSONResponse(status_code=500,
        content={"detail": "Internal server error", "request_id": request_id})
```

**Impact de la correction.** Aucun détail interne ne fuit vers le client ; chaque erreur reste tracée et corrélable côté serveur via son `request_id`.

#### V10 — Absence de limitation contre la force brute (Commit : `5a46ddf`, Sévérité : HAUTE)

**Description de la vulnérabilité.** L'endpoint de connexion n'imposait aucune limite au nombre de tentatives, permettant une attaque par **force brute** ou par **bourrage d'identifiants** (*credential stuffing*) à grande vitesse contre les mots de passe.

**Code vulnérable (avant).**
```python
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # aucune limite : essais illimités
```

**Correction appliquée.** Une limitation atomique par IP+identifiant via un script Lua Redis :
```python
allowed = await redis_client.check_rate_limit(
    f"login:{client_ip}:{form_data.username}", max_requests=10, window_seconds=300)
if not allowed:
    raise HTTPException(status_code=429, detail="Too many login attempts, please try again later")
```

**Impact de la correction.** Au-delà de 10 tentatives en 5 minutes, les connexions sont rejetées, rendant la force brute impraticable.

#### V11 — Durcissement du déploiement Docker (Commit : `97d284c`, Sévérité : HAUTE)

**Description de la vulnérabilité.** Le déploiement initial exposait les datastores sur toutes les interfaces, exécutait les conteneurs en root et utilisait des images non figées, exposant à une compromission de l'hôte et à des déploiements non reproductibles.

**Code vulnérable (avant).**
```yaml
ports:
  - "5434:5432"   # exposé sur 0.0.0.0
# conteneur exécuté en root, images en tags flottants
```

**Correction appliquée.** Liaison des datastores à `127.0.0.1`, exécution non-root (UID 10001), images épinglées et sondes de santé :
```dockerfile
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 CMD python -c "..."
```

**Impact de la correction.** La surface d'exposition réseau et de privilèges est drastiquement réduite (cf. §7.2).

#### V12 — Absence de filet de sécurité automatisé (Commit : `8f93b6b`, Sévérité : PROCESSUS)

**Description de la vulnérabilité.** Sans tests automatisés ni intégration continue, toute régression — y compris de sécurité — pouvait passer inaperçue. L'absence de tests sur le cœur sécurité (JWT, RBAC, validation) signifiait qu'une modification pouvait silencieusement réintroduire une faille corrigée.

**Correction appliquée.** Mise en place d'une suite de tests `pytest` ciblant la sécurité et d'un pipeline GitHub Actions exécutant ces tests à chaque poussée (détaillé en §5.2 et §5.3). Les tests vérifient notamment qu'un JWT forgé est rejeté, qu'une mauvaise audience est rejetée et que `require_role` refuse les rôles non autorisés.

**Impact de la correction.** Toute régression sur le cœur sécurité fait désormais échouer le *build*, empêchant sa fusion.

#### V13 — SSRF via le test de connecteur et intégrité de l'authentification (Commit : `088de77`, Sévérité : HAUTE)

**Description de la vulnérabilité.** L'endpoint de test de configuration de connecteur (`test-preview`) acceptait une cible arbitraire fournie par l'utilisateur, ce qui permettait une attaque **SSRF** (*Server-Side Request Forgery*) : un utilisateur pouvait faire émettre par le serveur des requêtes vers des cibles internes non exposées. Par ailleurs, l'authentification reposait insuffisamment sur le magasin d'utilisateurs persistant.

**Code vulnérable (avant).**
```python
@router.post("/test-preview")
async def test_connector_preview(data: ConnectorTestRequest, current_user: dict = Depends(get_current_user)):
    # tout utilisateur pouvait faire tester une cible arbitraire
```

**Correction appliquée.** Restriction du *test-preview* au rôle `admin` (réduisant la surface SSRF aux administrateurs de confiance) et adossement du login au magasin `gateway_users` :
```python
@router.post("/test-preview")
async def test_connector_preview(data: ConnectorTestRequest,
        current_user: dict = Depends(require_role(["admin"]))):
    """Teste une config avant sauvegarde (admin uniquement : cible arbitraire = risque SSRF)."""
```

**Impact de la correction.** Seuls les administrateurs peuvent déclencher des requêtes vers des cibles arbitraires, et l'authentification s'appuie sur la source de vérité persistante.

> **Note sur les commits de CI.** Deux commits supplémentaires (`07e4b78` sur `security-hardening`, `b3cdb0a` sur `iam-connector-improvements`) corrigent la configuration du cache npm en CI ; ils ne relèvent pas de la sécurité applicative mais de la fiabilité du pipeline, et sont mentionnés ici par souci d'exhaustivité de l'historique.

### 4.3 Analyse des dépendances (pip-audit)

L'analyse des vulnérabilités connues dans les dépendances tierces est intégrée au pipeline d'intégration continue sous la forme d'une étape `pip-audit -r requirements.txt`. `pip-audit` interroge les bases de données publiques de vulnérabilités (notamment l'*Open Source Vulnerability database* et l'index consultatif Python) et signale toute dépendance dont une version présente une CVE connue. Cet outil scanne l'arbre complet des dépendances déclarées, ce qui couvre non seulement les bibliothèques directes (FastAPI, SQLAlchemy, ldap3, etc.) mais aussi leurs dépendances transitives.

Le choix de rendre cette étape **non bloquante** (`continue-on-error: true`) est un parti pris assumé et raisonné. Une dépendance peut présenter une CVE connue qui n'est **pas exploitable** dans le contexte précis du projet (par exemple, une faille dans une fonctionnalité non utilisée). Bloquer systématiquement le *build* sur toute CVE conduirait soit à une paralysie, soit à la désactivation pure et simple de l'analyse. Le choix retenu — **signaler sans bloquer** — préserve la visibilité (l'alerte apparaît dans les journaux du *build*) tout en laissant à l'équipe le soin de trancher au cas par cas, en distinguant les vulnérabilités réellement exploitables (à corriger en priorité) des faux positifs contextuels. La distinction entre étapes **bloquantes** et **non bloquantes** structure ainsi une politique de qualité graduée, détaillée en §5.3 :

| Étape | Statut | Effet sur le *build* |
|---|---|---|
| `pytest` | bloquante | échec → *build* rouge, fusion impossible |
| `npm run build` | bloquante | échec → *build* rouge, fusion impossible |
| `ruff` | non bloquante | signale la dette de lint sans bloquer |
| `pip-audit` | non bloquante | signale les CVE sans bloquer |
| ESLint | non bloquante | signale les avertissements sans bloquer |

Cette gradation reflète un principe : ce qui garantit la **correction** (les tests, le build) bloque ; ce qui apporte de l'**information** (lint, audit) avertit sans paralyser la livraison.

### 4.4 Bilan sécurité post-audit

Le tableau ci-dessous synthétise la posture de sécurité avant et après l'audit, par catégorie de risque.

| Catégorie | Avant audit | Après audit |
|---|---|---|
| **Authentification** | Secret par défaut, JWT sans `iss`/`aud`, pas de révocation | Secret *fail-fast* (≥ 32 car.), `iss`/`aud` vérifiés, révocation par `jti` Redis |
| **Autorisation** | RBAC partiel sur les écritures | `require_role` sur tous les endpoints mutants |
| **Injection** | Filtres LDAP et colonnes SQL non échappés | `escape_filter_chars`/`escape_rdn` + liste blanche d'identifiants SQL |
| **Cryptographie** | Mot de passe temporaire prévisible, bcrypt bloquant | Mot de passe aléatoire, bcrypt déporté hors boucle |
| **Configuration** | Identifiants en dur, démarrage permissif | Secrets par environnement, refus de démarrer si faibles |
| **Infrastructure** | Datastores exposés, conteneur root, images flottantes | Liaison `127.0.0.1`, non-root (UID 10001), images épinglées |
| **Logging** | Traces renvoyées au client, pas de corrélation | 500 générique, `request_id` corrélé, logs JSON structurés |

Au terme de l'audit, la **posture de sécurité** de la plateforme est nettement renforcée sur l'ensemble des sept axes. Les vecteurs d'attaque les plus graves — forge de jetons, injection, usurpation de webhook, élévation de privilèges — sont fermés. La défense est en outre **vérifiable** : les tests automatisés (§5.2) attestent en continu que les protections clés (rejet d'un JWT forgé, refus d'une mauvaise audience, blocage des rôles non autorisés, rejet d'un identifiant SQL malveillant) restent effectives.

Subsistent néanmoins des **points connus** qui relèveraient d'un durcissement de production, et qu'il serait malhonnête de passer sous silence. L'absence de **terminaison TLS** signifie que les échanges transitent en HTTP clair sur l'hôte de démonstration ; un reverse-proxy chiffrant (NGINX) serait indispensable en production. La **gestion des secrets** par fichier `.env` devrait céder la place à un coffre dédié (Vault, Docker secrets). Le mode `start-dev` de Keycloak et la fixture `TEMP_USERS` (active uniquement en DEBUG) constituent des risques **conditionnels à la configuration** : sûrs tant que la production est correctement paramétrée, mais à proscrire en l'état. Enfin, un **WAF** (*Web Application Firewall*) en frontal apporterait une couche de défense supplémentaire contre les attaques applicatives génériques. Détaillons brièvement ces compléments. La **terminaison TLS** chiffrerait l'intégralité des échanges (navigateur↔frontend, frontend↔API, et idéalement les liaisons internes sensibles), neutralisant l'écoute passive et les attaques de l'homme du milieu ; elle s'accompagnerait d'une redirection HTTP→HTTPS et de l'en-tête HSTS. La **gestion des secrets** par un coffre (Vault) permettrait la rotation automatique, l'audit des accès aux secrets et le chiffrement au repos, là où un `.env` reste un fichier en clair. Un **WAF** filtrerait en amont les charges malveillantes connues (injections, scans), réduisant la surface d'exposition de l'application. À cela s'ajouteraient un **durcissement des en-têtes HTTP** (CSP, HSTS au-delà des trois en-têtes nginx déjà présents) et une **journalisation de sécurité** dédiée (tentatives d'accès refusées, élévations de privilèges) alimentant un SIEM. Ces compléments, listés en §9, dessinent le chemin d'un durcissement de niveau production au-delà du périmètre académique du projet.

---

## 5. Qualité logicielle et DevOps

### 5.1 Organisation du code et maintenabilité

La maintenabilité d'une base de code de près de 27 000 lignes Python ne s'improvise pas : elle découle de choix structurels appliqués avec constance. Le premier de ces choix est l'**architecture en couches strictes** déjà évoquée (API / Service / Connecteur / Core / Models). Cette stratification n'est pas qu'une commodité d'organisation ; elle **impose la séparation des préoccupations** au niveau du code. Un routeur ne contient que de la logique de transport (parsing, validation, autorisation, délégation) ; un service ne contient que de la logique métier ; un connecteur ne connaît qu'un protocole. Cette discipline réduit le couplage et rend chaque modification localisée : corriger un bug de protocole LDAP n'oblige à toucher qu'un fichier, et l'ajout d'un système cible n'impacte ni l'API ni les services.

Le deuxième pilier de maintenabilité est le **patron d'injection de dépendances** de FastAPI. Plutôt que d'instancier manuellement les dépendances (session de base, utilisateur courant, vérification de rôle) dans chaque fonction, on les déclare en paramètres via `Depends(...)`. Le framework les résout automatiquement, ce qui rend le code **plus lisible** (la signature documente les besoins), **plus testable** (on peut substituer les dépendances en test) et **moins répétitif**. La session de base de données illustre ce patron : `session=Depends(get_session)` fournit à chaque handler une session asynchrone qui effectue automatiquement un `rollback` en cas d'exception non gérée, garantissant qu'aucune transaction partielle ne fuit.

Le troisième pilier est la **validation déclarative par Pydantic v2**. Les corps de requête sont typés par des modèles Pydantic (`ProvisioningRequest`, `ConnectorCreate`, `UserCreate`...), et FastAPI valide automatiquement les entrées contre ces schémas avant même que le handler ne s'exécute, renvoyant un 422 structuré en cas de non-conformité. Le bénéfice est double : **zéro validation manuelle** à écrire (donc zéro oubli possible), et une **documentation OpenAPI** générée automatiquement à partir des types. Le recours systématique aux **annotations de type** dans toute la base de code (paramètres, retours, attributs) prolonge cette rigueur et permet une vérification statique partielle.

Le quatrième pilier est la **configuration centralisée et typée** via `core/config.py`. Toutes les variables d'environnement y sont déclarées comme des champs Pydantic Settings typés, avec valeur par défaut et, pour les secrets, un validateur de robustesse. Cette centralisation présente plusieurs vertus : la configuration est **documentée par le code** (un développeur lit `config.py` pour connaître tous les paramètres), **validée au démarrage** (un type incorrect échoue immédiatement) et **injectable** partout via le singleton `settings`. Un extrait illustre ce style typé et auto-documenté :

```python
class Settings(BaseSettings):
    APP_NAME: str = "Gateway IAM"
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="")
    DATABASE_URL: str = Field(default="postgresql+asyncpg://gateway:gateway@localhost:5434/gateway")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    MIDPOINT_URL: str = Field(default="http://midpoint-core:8080/midpoint")
    MIDPOINT_ENABLED: bool = Field(default=True)
    JWT_SECRET_KEY: str = Field(default="")
    JWT_EXPIRE_MINUTES: int = Field(default=60)
    BCRYPT_ROUNDS: int = Field(default=12)
    WORKFLOW_MAX_LEVELS: int = Field(default=5)
    # ... une cinquantaine de champs typés ...
    class Config:
        env_file = ".env"
        case_sensitive = True
```

Chaque champ porte son type (qui conditionne la conversion automatique depuis la variable d'environnement) et sa valeur par défaut (adaptée au développement). Le `env_file = ".env"` permet de surcharger ces valeurs sans modifier le code, et `case_sensitive = True` impose une correspondance stricte des noms. Enfin, la **stratégie de gestion des erreurs** — handler global renvoyant un 500 générique sans fuite d'information, handlers dédiés pour les `HTTPException` et les erreurs de validation — assure une réponse cohérente et sûre sur toute la surface d'API, complétant le tableau d'une base de code pensée pour durer.

Ces piliers de maintenabilité peuvent se synthétiser ainsi :

| Pilier | Mécanisme | Bénéfice |
|---|---|---|
| Séparation des couches | API / Service / Connecteur / Core / Models | Modifications localisées, couches substituables |
| Injection de dépendances | `Depends(...)` (FastAPI) | Lisibilité, testabilité, sécurité déclarative |
| Validation déclarative | Modèles Pydantic v2 | Zéro validation manuelle, OpenAPI auto-généré |
| Configuration typée | `pydantic-settings` (`config.py`) | Config documentée, validée au démarrage |
| Gestion d'erreurs centralisée | Middleware + handlers | Réponses cohérentes, pas de fuite interne |
| Annotations de type | Typage systématique | Vérification statique, auto-documentation |

Chacun de ces piliers, pris isolément, est une bonne pratique courante ; c'est leur **application conjointe et systématique** sur l'ensemble de la base de code qui produit une maintenabilité réelle, et non un vernis ponctuel.

### 5.2 Suite de tests automatisés

**Philosophie de test.** La suite de tests automatisés du projet adopte une priorisation délibérée : **tester d'abord le code de sécurité**. Ce choix répond à une logique de risque. Le code de sécurité (JWT, RBAC, validation des secrets, anti-injection) est à la fois celui dont une défaillance a les conséquences les plus graves et celui qui est le plus **difficile à valider manuellement** : on ne « voit » pas à l'œil nu qu'un JWT forgé est correctement rejeté, ni qu'un identifiant SQL malveillant est bloqué. Automatiser ces vérifications, c'est garantir en continu que les protections les plus critiques — et les plus subtiles — restent effectives à chaque modification. La suite compte **13 fonctions de test** réparties sur trois fichiers, exécutées via `pytest` en mode asynchrone automatique (`asyncio_mode = auto`) :

| Fichier | Fonctions | Cible | Vulnérabilité couverte |
|---|---|---|---|
| `test_security.py` | 6 | JWT, bcrypt, RBAC | V1, V3, V6 |
| `test_config.py` | 5 | validation *fail-fast* des secrets | V1 |
| `test_connectors.py` | 2 (paramétrées, 10 cas) | garde anti-injection SQL | V5 |

**`test_security.py` — Tests JWT et RBAC (6 fonctions).** La fonction `test_password_hash_and_verify` vérifie que le hachage bcrypt produit bien un condensé différent du clair et que la vérification distingue le bon mot de passe du mauvais ; un échec signalerait une rupture du mécanisme de stockage des mots de passe. `test_async_password_helpers` valide le bon fonctionnement des variantes asynchrones (`get_password_hash_async`/`verify_password_async`), garantissant que le déport hors boucle (cf. §4.2 V6) n'altère pas la correction. `test_jwt_roundtrip_includes_iss_aud_jti` est centrale : elle crée un jeton puis le décode et vérifie la présence et l'exactitude de `sub`, `roles`, `iss`, `aud` et `jti` ; elle protège l'ensemble du contrat JWT. `test_jwt_forged_with_wrong_key_is_rejected` est une **vérification d'attaque directe** : elle forge un jeton avec une mauvaise clé de signature et exige que le décodage lève une exception — si ce test échoue, la forge de jetons (V1) est de nouveau possible. `test_jwt_wrong_audience_is_rejected` couvre la confusion d'audience : un jeton portant une audience étrangère doit être rejeté. Enfin, `test_require_role_allows_matching_and_denies_others` valide le RBAC : elle confirme qu'un rôle autorisé passe et qu'un rôle non autorisé est refusé par une exception — la garantie automatisée que V3 ne réapparaîtra pas.

**`test_config.py` — Tests de configuration (5 fonctions).** Ces tests verrouillent la validation *fail-fast* des secrets (V1). `test_production_rejects_missing_secret` exige qu'en mode non-DEBUG, des secrets vides provoquent une `RuntimeError` au démarrage. `test_production_rejects_known_placeholder` exige le rejet d'un secret égal à un placeholder connu (`jwt-secret-change-in-production`). `test_production_rejects_short_secret` exige le rejet d'un secret de moins de 32 caractères. `test_production_accepts_strong_secrets` confirme qu'un secret fort est accepté. `test_debug_autogenerates_when_unset` valide qu'en mode DEBUG, des secrets vides sont automatiquement remplacés par des secrets éphémères suffisamment longs. Ensemble, ces cinq tests garantissent qu'aucune régression ne pourra rouvrir la voie au démarrage avec un secret faible. Leur concision témoigne de la lisibilité visée :

```python
def test_production_rejects_known_placeholder():
    with pytest.raises(RuntimeError):
        Settings(DEBUG=False, SECRET_KEY="a" * 48, JWT_SECRET_KEY="jwt-secret-change-in-production")

def test_production_accepts_strong_secrets():
    s = Settings(DEBUG=False, SECRET_KEY="a" * 48, JWT_SECRET_KEY="b" * 48)
    assert s.JWT_SECRET_KEY == "b" * 48

def test_debug_autogenerates_when_unset():
    s = Settings(DEBUG=True, SECRET_KEY="", JWT_SECRET_KEY="")
    assert len(s.SECRET_KEY) >= 32 and len(s.JWT_SECRET_KEY) >= 32
```

Chaque test instancie directement la classe `Settings` avec des valeurs contrôlées et vérifie le comportement attendu (levée de `RuntimeError` ou acceptation), couvrant tous les chemins du validateur *fail-fast*.

**`test_connectors.py` — Tests des connecteurs (2 fonctions paramétrées, 10 cas).** Ces tests ciblent la garde anti-injection SQL (V5). `test_safe_sql_identifier_accepts_valid` est paramétrée sur cinq identifiants légitimes (`username`, `email`, `first_name`, `_x`, `col1`) et vérifie qu'ils sont acceptés tels quels. `test_safe_sql_identifier_rejects_injection` est paramétrée sur cinq tentatives d'injection (dont la charge classique `"email) VALUES ('a') RETURNING id; DROP TABLE users;--"`, ainsi que des identifiants malformés comme `1col`, `a b`, la chaîne vide, `col;`) et exige qu'elles lèvent toutes une `ValueError`. La paramétrisation expand ces deux fonctions en **dix cas exécutés**, couvrant aussi bien le chemin nominal que les chemins d'attaque.

**`conftest.py` — Configuration partagée.** Le fichier `conftest.py` joue un rôle subtil mais essentiel : il positionne, **avant tout import de module applicatif**, un environnement de test déterministe (`DEBUG=true`, `SECRET_KEY` et `JWT_SECRET_KEY` fixes de plus de 32 caractères, `BCRYPT_ROUNDS=4`). Le `DEBUG=true` est nécessaire pour que le validateur *fail-fast* de `config.py` n'échoue pas au chargement (en DEBUG, il génère des secrets plutôt que de lever) ; le `BCRYPT_ROUNDS=4` réduit drastiquement le coût du hachage pour accélérer les tests. Sans cette configuration préalable, l'import même des modules applicatifs échouerait. Le fichier est volontairement compact :

```python
import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-" + "x" * 40)
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-" + "y" * 40)
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # hachage rapide en test
```

L'ordre est ici décisif : ces variables doivent être posées **au moment de l'import** de `conftest.py` (que pytest charge avant tout autre module), car le validateur de secrets de `config.py` s'exécute dès l'instanciation du singleton `settings`. Le `BCRYPT_ROUNDS=4` mérite une mention : bcrypt avec son coût par défaut (12) rendrait les tests de hachage lents ; en le ramenant à 4, on conserve la validité du test (le mécanisme est exercé) tout en divisant le temps d'exécution.

À titre d'illustration, le test de rejet d'un jeton forgé — l'un des plus importants — s'écrit ainsi dans `test_security.py` :

```python
def test_jwt_forged_with_wrong_key_is_rejected():
    forged = jwt.encode(
        {"sub": "attacker", "roles": ["admin"], "iss": settings.JWT_ISSUER, "aud": settings.JWT_AUDIENCE},
        "the-wrong-signing-key", algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(HTTPException):
        sec.decode_token(forged)
```

Ce test reconstitue exactement le scénario d'attaque de V1 : un attaquant forge un jeton se prétendant `admin`, mais avec une mauvaise clé de signature ; le test exige que le décodage lève une exception. De même, la garde anti-injection SQL est vérifiée par paramétrisation dans `test_connectors.py` :

```python
@pytest.mark.parametrize("name", [
    "email) VALUES ('a') RETURNING id; DROP TABLE users;--", "1col", "a b", "", "col;"])
def test_safe_sql_identifier_rejects_injection(name):
    with pytest.raises(ValueError):
        _safe_sql_identifier(name)
```

La première valeur paramétrée est une charge d'injection SQL classique ; le test exige son rejet par `ValueError`. Ces deux exemples montrent la philosophie : **automatiser la reproduction des attaques** pour garantir en continu que les défenses tiennent.

**Résultats et interprétation.** L'exécution attendue, `pytest tests/ -v`, produit un rapport listant chaque test avec son statut. Un **succès à 100 %** sur ces 13 fonctions signifie que le cœur sécurité — la partie la plus risquée du code — se comporte exactement comme spécifié : les jetons valides sont acceptés, les jetons forgés ou mal adressés rejetés, les rôles correctement filtrés, les secrets faibles refusés, et les injections SQL bloquées. Il faut toutefois être lucide sur ce qui **n'est pas encore couvert** : il n'existe pas de **tests d'intégration** (le dialogue réel avec MidPoint, LDAP, Odoo n'est pas testé de bout en bout), pas de **tests de la couche service** (la logique de provisionnement n'est pas testée en isolation), pas de **tests d'endpoints** (les routeurs ne sont pas testés via un client HTTP de test), ni de **tests frontend**. Une suite complète ajouterait ces niveaux, idéalement avec des conteneurs éphémères pour l'intégration. Reconnaître cette limite (cf. §9) fait partie de l'honnêteté d'ingénierie attendue d'un rapport sérieux.

### 5.3 Pipeline CI/CD GitHub Actions

Le pipeline d'intégration continue, défini dans `.github/workflows/ci.yml`, se déclenche à chaque poussée sur **toute branche** (`branches: ["**"]`) et à chaque *pull request*. Il comporte deux *jobs* indépendants exécutés sur `ubuntu-latest`.

Le fichier `ci.yml` lui-même, dans sa structure essentielle, se lit ainsi :

```yaml
on:
  push:
    branches: ["**"]
  pull_request:
jobs:
  backend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: gateway } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -r requirements-dev.txt
      - name: Lint (ruff)
        continue-on-error: true     # dette legacy : signaler sans bloquer
        run: ruff check app
      - name: Tests
        run: pytest -q              # BLOQUANT
      - name: Dependency vulnerability audit
        continue-on-error: true
        run: pip-audit -r requirements.txt
  frontend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: gateway/frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }   # pas de cache npm (lockfile absent)
      - run: npm install
      - name: Lint
        continue-on-error: true
        run: npm run lint
      - name: Build
        run: npm run build           # BLOQUANT
```

**Job backend.** Ce *job*, dont le répertoire de travail est `gateway`, enchaîne quatre étapes. La première récupère le code (`actions/checkout@v4`). La deuxième installe **Python 3.11** avec le cache pip activé (`actions/setup-python@v5`, `cache: pip`). La troisième installe les dépendances de développement (`pip install -r requirements-dev.txt`, qui inclut transitivement `requirements.txt`). La quatrième est le **lint avec ruff** (`ruff check app`), marqué `continue-on-error: true`. Le choix de **ruff** est justifié : c'est le *linter* Python le plus rapide (écrit en Rust), qui remplace à lui seul une combinaison d'outils historiques (flake8, isort, pyupgrade) ; son caractère non bloquant reflète la présence d'une dette de *lint* sur le code *legacy*, que l'on souhaite **rendre visible sans bloquer** la livraison. La cinquième étape est l'exécution des **tests** (`pytest -q`), seule étape **bloquante** du *job* : un test en échec fait échouer le *build*. La sixième est l'**audit des dépendances** (`pip-audit`), également non bloquant pour les raisons exposées en §4.3. L'ordre est significatif : on *linte* d'abord (rapide), on teste ensuite (la garantie fonctionnelle), puis on audite (l'information complémentaire) — et seule la garantie fonctionnelle bloque. Le tableau récapitule les étapes du job backend :

| Étape | Commande | Bloquant ? | Rôle |
|---|---|---|---|
| Checkout | `actions/checkout@v4` | — | récupère le code |
| Setup Python | `actions/setup-python@v5` (3.11, cache pip) | — | environnement |
| Install | `pip install -r requirements-dev.txt` | oui | dépendances |
| Lint | `ruff check app` | **non** | dette de lint visible |
| Tests | `pytest -q` | **oui** | garantie fonctionnelle |
| Audit | `pip-audit -r requirements.txt` | **non** | CVE des dépendances |

**Job frontend.** Ce *job*, dont le répertoire de travail est `gateway/frontend`, récupère le code, installe **Node.js 20** (`actions/setup-node@v4`) **sans cache npm**, installe les dépendances (`npm install`), exécute le *lint* ESLint (non bloquant) puis le **build** (`npm run build`, soit `tsc && vite build`), seule étape bloquante. L'absence de cache npm s'explique par un point connu : **aucun `package-lock.json` n'est versionné** (il est dans `.gitignore`), or le cache de `setup-node` requiert un *lockfile* pour calculer sa clé. C'est un compromis : il rend les *builds* légèrement plus lents et **non parfaitement reproductibles** (un `npm install` peut récupérer des versions correctives plus récentes), problème inscrit à la feuille de route dont le correctif évident est de versionner le *lockfile* (cf. §9). Le **build TypeScript** sert de garde de typage : `tsc` échoue si le typage est incohérent, transformant la compilation en vérification de qualité. L'avertissement de taille de *chunk* (Monaco) reste non bloquant.

**Politique de fusion.** Pour qu'une *pull request* soit fusionnable, **les deux étapes bloquantes doivent réussir** : `pytest` (backend) et `npm run build` (frontend). Les étapes non bloquantes (ruff, pip-audit, ESLint) remontent la dette et les vulnérabilités sans empêcher la livraison. Le projet a par ailleurs mis en œuvre un **workflow de *stacked PRs*** : la branche `iam-connector-improvements` ayant été créée à partir de `security-hardening`, sa *pull request* (PR #2) ciblait initialement `security-hardening` afin que son *diff* ne montre que le delta « connecteurs » ; une fois la PR #1 (`security-hardening` → `main`) fusionnée, la PR #2 a été **rebasculée sur `main`** puis fusionnée. Ce schéma de *pull requests* empilées, classique pour des branches de fonctionnalités dépendantes, a constitué une difficulté de gestion de version analysée en §8.3.

### 5.4 Observabilité et logging

L'observabilité repose sur **structlog**, configuré (dans `core/logging.py`) pour émettre des **journaux structurés au format JSON** sur la sortie standard. Chaque entrée de log est un objet JSON horodaté (`TimeStamper(fmt="iso")`) portant un niveau, un nom de logger et des champs contextuels arbitraires. Ce format n'est pas un choix esthétique : il rend les journaux **directement exploitables** par une chaîne d'agrégation et d'analyse (ELK — Elasticsearch/Logstash/Kibana, ou Grafana Loki), où chaque champ devient interrogeable, là où des logs en texte libre exigeraient un parsing fragile.

La **corrélation des requêtes** est assurée par le middleware `request_context_middleware` de `main.py`, en conjonction avec les *contextvars* de structlog. À chaque requête entrante, le middleware génère (ou propage) un `X-Request-ID`, le lie au contexte de log via `bind_contextvars`, mesure la latence (`time.perf_counter`) et journalise méthode, chemin, code de statut et durée. Ainsi, **toutes les lignes de log émises au cours d'une même requête partagent le même `request_id`**, ce qui permet de reconstituer a posteriori le parcours complet d'une requête à travers les couches — capacité essentielle au diagnostic en production. Le même middleware capture les exceptions non gérées pour renvoyer un 500 générique (cf. §4.2 V9), sans fuite d'information. En production, cette télémétrie structurée alimenterait naturellement des tableaux de bord (Grafana) et des alertes sur les taux d'erreur ou les latences. Une ligne de log typique émise par la gateway illustre la richesse exploitable de ce format :

```json
{"event": "request", "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
 "method": "POST", "path": "/api/v1/provision/", "status_code": 200,
 "duration_ms": 142.7, "level": "info", "logger": "app.main",
 "timestamp": "2026-06-21T10:15:03.421Z"}
```

Chaque champ (`request_id`, `method`, `path`, `status_code`, `duration_ms`) est directement indexable et agrégeable : on peut ainsi calculer une latence médiane par endpoint, compter les réponses 5xx par fenêtre de temps, ou retrouver toutes les lignes d'une requête donnée par son `request_id` — autant d'analyses impossibles avec des logs en texte libre. La configuration structlog empile pour cela une chaîne de processeurs (`merge_contextvars`, `add_log_level`, `TimeStamper(fmt="iso")`, `format_exc_info`, `JSONRenderer`) qui transforme chaque appel de log en un objet JSON complet et horodaté.

### 5.5 Gestion des dépendances

La gestion des dépendances Python sépare clairement les besoins **runtime** des besoins **développement**. Le fichier `requirements.txt` liste les dépendances de production, organisées par domaine fonctionnel : framework (`fastapi`, `uvicorn[standard]`), authentification (`python-jose[cryptography]`, `bcrypt`, `httpx`), base de données (`sqlalchemy>=2.0.0`, `sqlmodel`, `asyncpg`, `psycopg2-binary`, `redis`), connecteur LDAP (`ldap3`), moteur de règles (`pyyaml`, `jinja2`, `jsonschema`), IA optionnelle (`openai`), vecteurs (`qdrant-client`), validation (`pydantic>=2.0.0`, `pydantic-settings`, `email-validator`), logging (`structlog`) et ordonnanceur (`apscheduler>=3.10.0`). Le fichier `requirements-dev.txt`, lui, inclut `requirements.txt` puis y ajoute les outils de qualité : `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`, `ruff>=0.5.0` et `pip-audit>=2.7.0`. Cette séparation garantit que l'image de production n'embarque pas l'outillage de test. Les dépendances structurantes et leur rôle :

| Domaine | Bibliothèques | Rôle |
|---|---|---|
| Framework | `fastapi`, `uvicorn[standard]` | API asynchrone + serveur ASGI |
| Auth | `python-jose[cryptography]`, `bcrypt`, `httpx` | JWT, hachage, client HTTP |
| Base de données | `sqlalchemy`, `sqlmodel`, `asyncpg`, `redis` | ORM async, PostgreSQL, Redis |
| Connecteurs | `ldap3`, `httpx`, `xmlrpc.client` (stdlib) | LDAP, REST, XML-RPC |
| Règles | `jinja2`, `pyyaml`, `jsonschema` | templates sandboxés, configs |
| Validation / log | `pydantic`, `pydantic-settings`, `structlog` | contrats typés, logs JSON |
| Vecteurs / IA | `qdrant-client`, `openai` | recherche sémantique, assistant |
| Ordonnanceur | `apscheduler` | jobs périodiques |
| Qualité (dev) | `pytest`, `pytest-asyncio`, `ruff`, `pip-audit` | tests, lint, audit CVE |

Deux choix d'infrastructure de build complètent cette gestion. Le premier est l'image de base **`python:3.11-slim`** : la variante *slim* élimine les outils superflus, réduisant à la fois la **surface d'attaque** (moins de binaires exploitables) et la **taille de l'image** (téléchargement et démarrage plus rapides). Le second est l'option **`--no-cache-dir`** lors de l'installation pip dans le Dockerfile : elle empêche pip de conserver son cache de téléchargement dans la couche d'image, ce qui **allège l'image finale**. Combinés à l'ordre judicieux des instructions `COPY` (le `requirements.txt` avant le code, pour maximiser la réutilisation du cache de couches Docker), ces choix traduisent une attention portée non seulement au code mais à l'ensemble de la chaîne de construction.

L'organisation des dépendances par domaine fonctionnel dans `requirements.txt` (framework, authentification, base de données, LDAP, moteur de règles, IA, vecteurs, validation, logging, ordonnanceur) n'est pas qu'esthétique : elle documente, par regroupement, **à quoi sert chaque dépendance**, facilitant les revues de sécurité (un auditeur identifie immédiatement les bibliothèques cryptographiques) et les mises à jour ciblées. La séparation runtime/dev garantit en outre que l'image de production reste minimale : `pytest`, `ruff` et `pip-audit` n'y figurent pas, ce qui réduit d'autant la surface d'attaque. Un point d'amélioration subsiste néanmoins : la plupart des dépendances ne sont pas épinglées à une version exacte (on trouve `>=` plutôt que `==`), ce qui, comme pour le `package-lock.json` frontend, affecte la reproductibilité parfaite des builds — un épinglage strict assorti d'un outil de mise à jour maîtrisée (Dependabot, Renovate) serait l'évolution naturelle.

---

## 6. Modèle de données et persistance

### 6.1 Architecture polyglotte

Le projet met en œuvre une **persistance polyglotte** : plutôt que de forcer toutes les données dans un moteur unique, chaque catégorie de données est confiée à la technologie la mieux adaptée à son motif d'accès. Trois familles de bases coexistent, et jusqu'à cinq instances PostgreSQL (chaque produit — gateway, MidPoint, Odoo, Keycloak, intranet — disposant de la sienne, par autonomie de service). Le **relationnel (PostgreSQL)** accueille les données structurées, transactionnelles et durables : opérations, audit, workflows, règles, utilisateurs, connecteurs ; on y recherche l'intégrité (types, contraintes d'unicité, énumérations) et la durabilité. Le **clé-valeur en mémoire (Redis)** accueille les données éphémères à durée de vie et les opérations atomiques : liste noire de jetons, compteurs de limitation de débit, caches ; on y recherche la latence sub-milliseconde et l'atomicité. Le **vectoriel (Qdrant)** accueille les index de similarité sur les journaux d'audit ; on y recherche la recherche par proximité plutôt que par mots-clés exacts.

Le principe directeur est **« le bon magasin pour la bonne charge »**. Un compteur de limitation de débit, qui doit être incrémenté atomiquement et expirer automatiquement, est trivial en Redis et lourd en SQL. Une recherche par similarité sémantique est native en Qdrant et impraticable en SQL relationnel. La traçabilité d'audit, qui exige durabilité et requêtes structurées, appelle PostgreSQL. Cette hétérogénéité, loin d'être une complication gratuite, est l'expression d'une conception qui adapte l'outil au besoin. Elle est orchestrée de manière cohérente par Docker Compose, qui lève et relie ces moteurs hétérogènes en un ensemble fonctionnel. Le tableau suivant résume l'adéquation entre chaque moteur et sa charge :

| Moteur | Modèle | Optimisé pour | Données du projet |
|---|---|---|---|
| PostgreSQL | Relationnel | Intégrité, durabilité, requêtes structurées | Opérations, audit, workflows, règles, utilisateurs |
| Redis | Clé-valeur en mémoire | Latence, atomicité, expiration (TTL) | Blacklist JWT, compteurs de rate-limit, caches |
| Qdrant | Vectoriel | Recherche par similarité (ANN) | Index des journaux d'audit pour l'assistant IA |

### 6.2 Modèle relationnel PostgreSQL

La base `gateway-db` est la base applicative centrale. Son schéma est défini par deux mécanismes coexistants qu'il faut distinguer : les **classes SQLModel** (`gateway/app/models/*`), qui décrivent les modèles ORM et sont matérialisées au démarrage par `SQLModel.metadata.create_all`, et le script **`db/migrations.py`**, idempotent et **autoritatif**, qui crée 24 tables, 4 énumérations PostgreSQL, 16 index et des données de *seed*. Un point d'ingénierie important — et honnêtement documenté — est que ces deux mécanismes peuvent **diverger** : certaines colonnes présentes dans la DDL de `migrations.py` n'apparaissent pas dans les classes SQLModel, et les énumérations Python (en minuscules) diffèrent des énumérations PostgreSQL (en majuscules), d'où les `CAST` explicites dans `memory_store.py`. La règle retenue est claire : **`migrations.py` fait foi** pour le schéma réel. Ce script crée d'abord les quatre énumérations PostgreSQL de manière idempotente, puis sème les données initiales (utilisateur admin, règle d'exemple, configuration de workflow) :

```python
enums = [
    ("operationtype", ["CREATE", "UPDATE", "DELETE", "DISABLE", "ENABLE", "ASSIGN_ROLE", "REVOKE_ROLE", "SYNC"]),
    ("operationstatus", ["PENDING", "IN_PROGRESS", "SUCCESS", "FAILED", "AWAITING_APPROVAL", "APPROVED", "REJECTED", "ROLLED_BACK"]),
    ("auditeventtype", ["PROVISION", "RECONCILIATION", "WORKFLOW", "AUTH", "SYSTEM", "ERROR"]),
    ("auditseverity", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
]
# seed : utilisateur admin avec mot de passe bcrypt
admin_password_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
# INSERT ... ON CONFLICT (username) DO NOTHING  → idempotent
```

On notera que les valeurs d'énumération sont en **MAJUSCULES** côté PostgreSQL, alors que les énumérations Python correspondantes (par exemple `OperationStatus.SUCCESS = "success"`) sont en minuscules : c'est précisément cette différence qui impose les `CAST(... AS operationstatus)` et les `.upper()` du `memory_store.py`, illustration concrète de la dérive de schéma évoquée plus haut. L'usage systématique de `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS` et `ON CONFLICT DO NOTHING` garantit l'**idempotence** : le script peut être rejoué sans risque, ce qui en fait un mécanisme de migration sûr quoique manuel.

Les principales tables et leur finalité sont les suivantes. La table **`provisioning_operations`** est le journal des opérations de provisionnement : identifiant UUID, type d'opération (énumération `operationtype`), statut (énumération `operationstatus`), systèmes cibles, attributs d'entrée et calculés (JSONB), horodatages. La table **`audit_logs`** trace tous les événements (type, sévérité, acteur, action, détails JSONB, horodatage indexé). La table **`workflows`** porte les instances d'approbation multi-niveaux (niveau courant, total de niveaux, approbateurs en attente, contexte JSONB, jetons d'approbation/rejet). La table **`rules`** stocke les règles de mapping (système cible, expression Jinja2, priorité, conditions). La table **`gateway_users`**, clé du modèle d'identité, contient les comptes de la gateway : `username`/`email` uniques, `password_hash`, `role` et `roles` (JSONB), `permission_level`, `is_active`. La table **`connector_configurations`** persiste les connecteurs dynamiques. S'y ajoutent `reconciliation_jobs`, `account_state_cache`, `discrepancies`, `rule_versions`, `rollback_actions`, `system_states`, et plusieurs tables de workflow et de permissions. On peut regrouper les 24 tables par domaine fonctionnel :

| Domaine | Tables |
|---|---|
| Provisionnement | `provisioning_operations`, `target_account_states`, `rollback_actions`, `account_state_cache` |
| Audit | `audit_logs`, `vector_log_entries` |
| Réconciliation | `reconciliation_jobs`, `discrepancies` |
| Workflows | `workflows`, `workflow_configs`, `workflow_instances`, `approval_levels`, `approval_decisions`, `approval_roles` |
| Règles | `rules`, `rule_versions`, `policy_configs` |
| Identité / accès | `gateway_users`, `app_users`, `app_profiles`, `app_user_permissions` |
| Connecteurs / système | `connector_configurations`, `ai_configuration`, `system_states` |

Un trait architectural notable est l'**absence de clés étrangères déclarées** au niveau ORM : les relations (`operation_id`, `rule_id`, `workflow_id`, `audit_log_id`...) sont **logiques**, matérialisées par des UUID indexés mais non contraintes par la base. Ce choix privilégie la souplesse (et la tolérance aux écritures asynchrones partielles via le `MemoryStore`) au prix d'un report de la cohérence référentielle sur la couche applicative. Le diagramme entité-relation logique ci-dessous illustre les principales relations.

```
┌────────────────────┐         ┌──────────────────────────┐
│ gateway_users      │         │ provisioning_operations  │
├────────────────────┤  1   N  ├──────────────────────────┤
│ PK id (UUID)       │────────▶│ PK id (UUID)             │
│ username (UNIQUE)  │(logique │ account_id (idx)         │
│ email (UNIQUE)     │ created │ operation_type (enum)    │
│ password_hash      │ _by)    │ status (enum)            │
│ role / roles(JSONB)│         │ target_systems / attrs   │
│ permission_level   │         │ created_at / updated_at  │
└────────────────────┘         └───┬───────────┬──────────┘
                                   │1:N        │1:N
                          ┌────────▼───┐  ┌─────▼─────────────┐
                          │ rollback_  │  │ workflows         │
                          │ actions    │  │ (instances)       │
                          └────────────┘  └─────┬─────────────┘
                                                │1:N (niveaux/décisions)
┌────────────────┐ 1   N ┌────────────────┐    ▼
│ rules          │──────▶│ rule_versions  │  approval_levels / approval_decisions
└────────────────┘       └────────────────┘
┌────────────────────┐ 1  1 ┌────────────────────┐   ┌──────────────────────┐ 1 N ┌───────────────┐
│ audit_logs         │─────▶│ vector_log_entries │   │ reconciliation_jobs  │────▶│ discrepancies │
└────────────────────┘      └────────────────────┘   └──────────────────────┘     └───────────────┘
```

Le détail des principales tables, tel que défini dans `db/migrations.py` (schéma autoritatif), est reproduit ci-dessous colonne par colonne.

**Table `provisioning_operations`** — journal des opérations de provisionnement.

| Colonne | Type PostgreSQL | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK, défaut `gen_random_uuid()` | Identifiant de l'opération |
| `correlation_id` | VARCHAR(100) | index | Corrélation de la requête |
| `operation_type` | `operationtype` (enum) | NOT NULL, défaut `CREATE` | Type d'opération |
| `status` | `operationstatus` (enum) | NOT NULL, défaut `PENDING` | Statut courant |
| `source_system` / `target_systems` | VARCHAR | — | Système source / cibles |
| `account_id` | VARCHAR(255) | index | Identité concernée |
| `input_attributes` / `calculated_attributes` | JSONB | — | Attributs source / calculés |
| `error_message` | TEXT | — | Message d'erreur éventuel |
| `rollback_data` | JSONB | — | Données de compensation |
| `created_at` / `updated_at` / `completed_at` | TIMESTAMPTZ | défaut `CURRENT_TIMESTAMP` | Horodatages |

**Table `audit_logs`** — piste d'audit (indexée pour Qdrant).

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | — |
| `created_at` | TIMESTAMPTZ | défaut now, index | Horodatage |
| `event_type` | `auditeventtype` (enum) | NOT NULL, défaut `SYSTEM` | Catégorie d'événement |
| `source_system` / `target_system` | VARCHAR(100) | — | Systèmes concernés |
| `account_id` | VARCHAR(255) | index | Identité concernée |
| `operation_id` | UUID | — | Opération liée (logique) |
| `action` | VARCHAR(100) | NOT NULL | Libellé de l'action |
| `severity` | `auditseverity` (enum) | défaut `INFO` | Sévérité |
| `actor` / `actor_ip` | VARCHAR | — | Auteur et IP |
| `details` / `changes` / `error_details` | JSONB | — | Détails structurés |

**Table `workflows`** — instances d'approbation multi-niveaux.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | VARCHAR(100) | PK | Identifiant du workflow |
| `workflow_id` / `operation_id` | VARCHAR | — | Template et opération liés |
| `status` | VARCHAR(50) | NOT NULL, défaut `pending` | État du workflow |
| `current_level` / `total_levels` | INTEGER | défaut 1 / 1 | Progression |
| `user_name` / `operation_name` | VARCHAR(255) | — | Libellés d'affichage |
| `pending_approvers` | TEXT | — | Approbateurs en attente |
| `context` | JSONB | défaut `{}` | Contexte de l'opération |
| `approve_token` / `reject_token` | VARCHAR(255) | — | Jetons d'approbation par email |
| `email_sent` | BOOLEAN | défaut false | Notification envoyée ? |
| `created_at` / `expires_at` / `decided_at` | TIMESTAMPTZ | — | Horodatages |

**Table `rules`** — règles de calcul d'attributs.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | — |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE | Nom de la règle |
| `target_system` | VARCHAR(100) | NOT NULL, index | Système cible |
| `rule_type` | VARCHAR(50) | défaut `attribute_mapping` | Type de règle |
| `priority` | INTEGER | défaut 100 | Ordre d'exécution (desc.) |
| `is_active` | BOOLEAN | défaut true | Active ? |
| `conditions` | JSONB | — | Conditions d'application |
| `attribute_mappings` | JSONB | NOT NULL, défaut `{}` | Mappings Jinja2 |
| `version` | INTEGER | défaut 1 | Version courante |
| `created_at` / `updated_at` / `created_by` | — | — | Métadonnées |

**Table `gateway_users`** — comptes de la gateway (cœur du modèle d'identité).

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | — |
| `username` | VARCHAR(100) | NOT NULL, **UNIQUE** | Identifiant de connexion |
| `email` | VARCHAR(255) | NOT NULL, **UNIQUE** | Adresse e-mail |
| `password_hash` | VARCHAR(255) | NOT NULL | Condensé bcrypt |
| `full_name` | VARCHAR(255) | — | Nom complet |
| `role` | VARCHAR(50) | NOT NULL, défaut `viewer` | Rôle principal (legacy) |
| `roles` | JSONB | défaut `[]` | Liste des rôles (RBAC) |
| `permission_level` | INTEGER | défaut 1 | Niveau de droits (1–5) |
| `is_active` | BOOLEAN | défaut true | Compte actif ? |
| `created_at` / `last_login` | TIMESTAMPTZ | — | Métadonnées |

**Table `connector_configurations`** — connecteurs dynamiques.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | VARCHAR(100) | PK | — |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE | Nom interne |
| `connector_type` / `connector_subtype` | VARCHAR(50) | NOT NULL | Type et sous-type |
| `display_name` | VARCHAR(255) | NOT NULL | Libellé affiché |
| `is_active` | BOOLEAN | défaut true | Activé ? |
| `configuration` | JSONB | NOT NULL, défaut `{}` | Configuration (credentials inclus) |
| `last_health_status` / `last_health_check` / `last_health_error` | — | — | Santé |
| `midpoint_resource_oid` | VARCHAR(255) | index | Resource MidPoint liée |
| `midpoint_sync_status` | VARCHAR(50) | défaut `not_synced` | Statut de sync |

Outre ces tables, `migrations.py` crée également `reconciliation_jobs`, `account_state_cache`, `discrepancies`, `rule_versions`, `rollback_actions`, `target_account_states`, `workflow_configs`, `workflow_instances`, `approval_levels`, `approval_decisions`, `approval_roles`, `system_states`, `vector_log_entries`, `ai_configuration`, `policy_configs`, ainsi que `app_users`/`app_profiles`/`app_user_permissions` — soit 24 tables au total, accompagnées de 4 énumérations et 16 index. Les index, créés de manière idempotente, ciblent les colonnes les plus interrogées :

```sql
CREATE INDEX IF NOT EXISTS idx_operations_correlation ON provisioning_operations(correlation_id);
CREATE INDEX IF NOT EXISTS idx_operations_status      ON provisioning_operations(status);
CREATE INDEX IF NOT EXISTS idx_operations_account     ON provisioning_operations(account_id);
CREATE INDEX IF NOT EXISTS idx_operations_created     ON provisioning_operations(created_at);
CREATE INDEX IF NOT EXISTS idx_workflows_status       ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_audit_created          ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_account          ON audit_logs(account_id);
CREATE INDEX IF NOT EXISTS idx_audit_event            ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_connectors_type        ON connector_configurations(connector_type);
CREATE INDEX IF NOT EXISTS idx_recon_status           ON reconciliation_jobs(status);
-- … (16 index au total)
```

Le choix de ces index reflète les motifs d'accès réels : on filtre fréquemment les opérations par statut, compte ou corrélation, et les logs d'audit par date, compte ou type d'événement — précisément les colonnes indexées. Cette optimisation, conjuguée au cache mémoire du `MemoryStore`, assure des temps de réponse faibles même lorsque les tables grossissent.

La **configuration du pool de connexions** (dans `database.py`) reflète une exploitation soignée : `pool_size=10` (connexions persistantes), `max_overflow=20` (connexions de pic), `pool_recycle=1800` (recyclage toutes les 30 minutes contre les coupures *idle* des proxys), `pool_pre_ping=True` (détection et remplacement d'une connexion morte après un redémarrage PostgreSQL), et `echo=settings.DEBUG` (journalisation SQL réservée au debug). Ces paramètres, loin des valeurs par défaut, traduisent une anticipation des conditions réelles d'exploitation.

### 6.3 Modèles Pydantic et IAM

Le fichier `models/iam.py` définit dix modèles Pydantic v2 (tous en `extra="ignore"`) qui **typent les objets MidPoint** exposés par l'API, sans être des tables : ils servent de sur-ensemble tolérant des formes renvoyées par le `MidPointConnector`. Le tableau suivant les récapitule :

| Modèle | Rôle | Correspondance MidPoint |
|---|---|---|
| `ActivationStatus` (Enum) | État d'activation | `enabled`/`disabled`/`archived` |
| `ObjectRef` | Référence (oid, type, name) | `<targetRef>` / `<resourceRef>` |
| `Assignment` | Rôle ou compte cible | `<assignment>` |
| `MidpointShadow` | Projection dans une ressource | `ShadowType` |
| `MidpointUser` | Identité simplifiée | `UserType` |
| `MidpointRole` | Rôle | `RoleType` |
| `MidpointResource` | Système cible | `ResourceType` |
| `MidpointUserList` | Enveloppe (total + users) | — |
| `MidpointRoleList` | Enveloppe (total + roles) | — |
| `MidpointResourceList` | Enveloppe (total + resources) | — | L'énumération `ActivationStatus` (`enabled`/`disabled`/`archived`) reflète l'état d'activation MidPoint. `ObjectRef` modélise une référence (`oid`, `type`, `name`) correspondant aux éléments `<targetRef>`/`<resourceRef>` du XML MidPoint. `Assignment` modélise un `<assignment>`, qui est **soit un rôle** (`targetRef` de type `RoleType`), **soit un compte cible** (`resourceRef` + `kind` + `intent`) — distinction fondamentale dans le modèle MidPoint. `MidpointShadow` modélise une projection d'identité dans une ressource (le compte réel côté LDAP/Odoo/SQL).

Le modèle central `MidpointUser` simplifie le `UserType` MidPoint : tous ses champs sont **optionnels** (pour tolérer les variations de réponse sans casser le `response_model`), et chacun correspond à un attribut MidPoint précis (`firstname`→`givenName`, `lastname`→`familyName`, `email`→`emailAddress`, `department`→`organizationalUnit`, `active`→`activation/administrativeStatus == enabled`, `roles`→OIDs des `assignment/targetRef` de type rôle). Les modèles `MidpointRole` et `MidpointResource` typent respectivement les rôles et les ressources (systèmes cibles), et les enveloppes `MidpointUserList`/`MidpointRoleList`/`MidpointResourceList` ajoutent un compteur `total` à une liste typée — utilisées comme `response_model` des endpoints de listing. Un exemple de réponse JSON pour un `MidpointUser` :

```json
{
  "oid": "f6a3...e21", "name": "jdupont", "fullName": "Jean Dupont",
  "firstname": "Jean", "lastname": "Dupont", "email": "jean.dupont@example.com",
  "employeeNumber": "E1024", "department": "Finance", "active": true,
  "administrativeStatus": "enabled", "roles": ["a1b2...c3d4"], "shadows": null
}
```

Les autres modèles produisent des réponses JSON tout aussi typées. Un `MidpointRole` et son enveloppe de liste :

```json
{
  "total": 2,
  "roles": [
    {"oid": "a1b2...c3", "name": "ldap-user", "displayName": "Utilisateur LDAP",
     "description": "Déclenche la création d'un compte dans OpenLDAP"},
    {"oid": "d4e5...f6", "name": "odoo-user", "displayName": "Utilisateur Odoo",
     "description": "Déclenche la création d'un compte dans Odoo"}
  ]
}
```

Un `MidpointShadow` (projection d'une identité dans une ressource) :

```json
{
  "oid": "7788...99", "resourceOid": "9f0e...77",
  "kind": "account", "intent": "default", "name": "uid=jdupont,ou=users,dc=example,dc=com"
}
```

Un `Assignment` peut représenter soit un rôle (`targetRef`), soit un compte cible (`resourceRef` + `kind`/`intent`) :

```json
{ "targetRef": {"oid": "a1b2...c3", "type": "RoleType", "name": "ldap-user"},
  "resourceRef": null, "kind": null, "intent": null }
```

Ces modèles jouent un rôle d'**adaptateur de contrat** : ils transforment la structure XML/JSON parfois verbeuse et imbriquée de l'API MidPoint en objets Python typés et stables, sur lesquels l'API de la gateway peut s'appuyer sans exposer la complexité sous-jacente du hub.

### 6.4 Cache Redis et patterns de clés

Redis héberge cinq familles de clés, chacune avec sa sémantique, sa durée de vie et son usage, récapitulées ci-dessous :

| Pattern de clé | Type | TTL | Contenu | Utilisé par |
|---|---|---|---|---|
| `blacklist:{jti}` | String | durée résiduelle du jeton | jeton révoqué | `get_current_user`, `/logout` |
| `rate:login:{ip}:{username}` | Compteur | 300 s | tentatives de connexion | `/token` (`check_rate_limit`) |
| `session:{username}` | String (JSON) | 3600 s | données de session | cache de sessions |
| `wf_token:{token}` | String (JSON) | 259 200 s (72 h) | jeton d'approbation workflow | workflows par email |
| `cache:{key}` | String | 300 s | cache générique | `set_cache`/`get_cache` | La clé **`blacklist:{jti}`** (chaîne `"1"`, TTL égal à la durée de vie résiduelle du jeton) marque un jeton révoqué et est consultée à chaque requête authentifiée. La clé **`rate:{key}`** (compteur, TTL égal à la fenêtre) — concrètement `rate:login:{ip}:{username}` — porte le comptage de la limitation de débit du login. La clé **`session:{username}`** (JSON, TTL 3600 s) cache des données de session. La clé **`wf_token:{token}`** (JSON, TTL 259 200 s, soit 72 h) cache un jeton d'approbation de workflow. La clé **`cache:{key}`** (TTL 300 s) sert de cache générique.

Le mécanisme le plus remarquable est le **script Lua atomique** de limitation de débit, dont la justification est détaillée en §8.2. Son code est concis :

```lua
local c = redis.call('INCR', KEYS[1])
if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return c
```

L'intérêt du Lua est l'**atomicité** : Redis exécute le script comme une opération indivisible, de sorte que l'incrémentation et la pose du TTL ne peuvent pas être interrompues entre elles. Une implémentation naïve en deux commandes séparées (`INCR` puis `EXPIRE`) comporterait une fenêtre de course : si le processus s'interrompt entre les deux, la clé resterait **sans expiration** et bloquerait l'utilisateur indéfiniment. Le script garantit que le TTL est posé exactement lors de la première incrémentation. La fonction `check_rate_limit` qui l'invoque dégrade par ailleurs en mode **ouvert** si Redis est indisponible (retour `True`), privilégiant la disponibilité du login. Le `RedisClient` (singleton) expose un ensemble de méthodes cohérentes, dont la robustesse repose sur une garde systématique de connexion :

```python
async def blacklist_token(self, token_jti: str, ttl_seconds: int = 3600) -> bool:
    if not self._redis:
        return False
    await self._redis.setex(f"blacklist:{token_jti}", ttl_seconds, "1")
    return True

async def check_rate_limit(self, key: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    if not self._redis:
        return True  # Redis indisponible : on ne bloque pas (disponibilité > défense-en-profondeur)
    current = await self._redis.eval(self._RATE_LIMIT_LUA, 1, f"rate:{key}", window_seconds)
    return int(current) <= max_requests
```

Chaque méthode vérifie d'abord la disponibilité de la connexion (`if not self._redis`) et adopte un comportement de repli explicite : `False` pour les écritures (l'opération n'a pas eu lieu), `True` pour la limitation de débit (on autorise). Cette discipline garantit qu'une panne Redis ne provoque jamais d'exception non gérée, mais une dégradation maîtrisée — illustration concrète, au niveau du code, du principe de §2.1.

### 6.5 Qdrant — base vectorielle

Qdrant matérialise la couche de recherche sémantique. Une **base vectorielle** stocke des vecteurs (listes de nombres flottants) et permet d'y rechercher les plus proches voisins selon une distance, ce qui convient à la recherche « par sens » : on transforme un texte en vecteur, puis on retrouve les entrées dont le vecteur est le plus proche, indépendamment des mots exacts. Dans le projet (`qdrant_store.py`), la collection se nomme **`audit_logs`**, les vecteurs ont une dimension de **128**, et la métrique de distance est le **cosinus** (`Distance.COSINE`). Chaque point indexé porte un *payload* qui permet à la fois la recherche et le filtrage :

| Champ du payload | Contenu | Usage |
|---|---|---|
| `event_type` | type d'événement d'audit | filtre |
| `action` | libellé de l'action | recherche |
| `account_id` | identité concernée | filtre/recherche |
| `target_system` | système cible | recherche |
| `actor` | auteur de l'action | recherche |
| `severity` | sévérité | filtre |
| `created_at` | horodatage | tri |
| `summary` | texte vectorisé | recherche sémantique |
| `db_id` | identifiant en base relationnelle | jointure |

La recherche (`search_logs`) accepte des filtres optionnels sur `event_type` et `severity` (via `FieldCondition`/`MatchValue`), combinant ainsi recherche vectorielle et filtrage structuré. Le cas d'usage est la recherche d'audit pour l'assistant IA : `POST /api/v1/admin/audit/search` vectorise une requête textuelle et retourne les entrées les plus similaires, classées par score.

Un point d'exactitude doit être souligné, déjà mentionné en §3.9. La fonction de vectorisation `_text_to_vector` **ne repose pas, à ce stade, sur un modèle d'embedding par apprentissage automatique** : elle construit un vecteur **déterministe par hachage** (SHA-256 sur des fragments du texte, puis normalisation L2) de dimension 128. Le code lui-même indique que cette approche est destinée à être remplacée par un véritable modèle d'embedding (par exemple `all-MiniLM-L6-v2`, dont le nom figure d'ailleurs en valeur par défaut du modèle `VectorLogEntry`). La conséquence est que la « recherche sémantique » se comporte actuellement comme une similarité **lexicale déterministe** (des textes identiques produisent des vecteurs identiques) plutôt que comme une véritable proximité de sens. L'**infrastructure** vectorielle (collection, distance cosinus, dimension fixe, *payload*, indexation et recherche) est néanmoins entièrement en place, et le passage à de vrais embeddings ne nécessiterait que le remplacement de la fonction de vectorisation — un point d'évolution clairement identifié. La fonction actuelle est la suivante :

```python
COLLECTION_NAME = "audit_logs"
VECTOR_SIZE = 128

def _text_to_vector(text: str) -> List[float]:
    """Vecteur déterministe par hachage. Peut être remplacé par un modèle ML (ex. all-MiniLM-L6-v2)."""
    vector = []
    for i in range(VECTOR_SIZE):
        h = hashlib.sha256(f"{text}_{i}".encode()).digest()
        val = struct.unpack('f', h[:4])[0]
        vector.append(max(-1.0, min(1.0, val / 1e10)))
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm > 0 else vector
```

La création de la collection (`VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)`) et l'indexation (`upsert` d'un `PointStruct` avec vecteur et *payload*) sont, elles, parfaitement standard : seul le calcul du vecteur diffère d'une implémentation à base d'embeddings, ce qui circonscrit nettement le travail d'évolution. Le commentaire du code lui-même documente cette intention de remplacement, témoignant d'une dette technique **consciente et tracée** plutôt que cachée.

---

## 7. Infrastructure Docker et déploiement

### 7.1 Analyse du docker-compose.yml

Le fichier `docker-compose.yml` constitue la spécification déclarative complète de l'infrastructure. Il décrit **14 services** sur un unique réseau bridge `iam-network` et **13 volumes nommés**, au format Compose `"3.9"`. Sa lecture révèle plusieurs partis pris d'orchestration cohérents. Le premier est la **séparation systématique des bases** : chaque produit majeur (gateway, MidPoint, Odoo, Keycloak, intranet) possède sa propre instance PostgreSQL, ce qui isole les schémas et les cycles de vie. Le deuxième est la **stratégie de volumes** : toutes les données durables (les cinq bases, l'annuaire LDAP, le *home* MidPoint, les données Odoo et Qdrant, les journaux gateway) sont confiées à des volumes nommés gérés par Docker, garantissant leur persistance indépendamment du cycle de vie des conteneurs.

Les treize volumes nommés se répartissent ainsi :

| Volume | Service | Données |
|---|---|---|
| `gateway_db_data` | gateway-db | Opérations, audit, workflows, users |
| `gateway_logs` | gateway | Journaux applicatifs |
| `midpoint_postgres_data` | midpoint-postgres | Dépôt MidPoint |
| `midpoint_home` | midpoint | Keystore, configuration |
| `redis_data` | redis | Blacklist, compteurs |
| `qdrant_data` | qdrant | Collection vectorielle |
| `openldap_data` / `openldap_config` | openldap | Annuaire + config slapd |
| `odoo_db_data` / `odoo_data` / `odoo_addons` | odoo(-db) | Base + données + modules |
| `intranet_db_data` | intranet-db | Base cible SQL |
| `keycloak_db_data` | keycloak-db | Base Keycloak |

Le troisième parti pris, le plus subtil, est l'**ordonnancement par dépendances et sondes de santé**. Les directives `depends_on` ne se contentent pas d'ordonner le lancement ; elles le **conditionnent à l'état de santé réel** des dépendances. Le service `gateway` attend que `gateway-db` et `redis` soient *healthy* et que `qdrant` soit démarré ; le service `gateway-frontend` attend que `gateway` soit *healthy* ; les services `midpoint`, `odoo` et `keycloak` attendent que leur base respective soit *healthy*. Il en résulte une **cascade de démarrage** maîtrisée : bases → services IAM → gateway → frontend. Cette cascade, couplée à la politique `restart: unless-stopped` appliquée à tous les services, rend le démarrage **résilient** aux variations de temps d'initialisation et aux redémarrages de l'hôte. Le détail des dépendances conditionnées est le suivant :

| Service | Attend (condition) |
|---|---|
| `midpoint` | `midpoint-postgres` (service_healthy) |
| `gateway` | `gateway-db` (healthy), `redis` (healthy), `qdrant` (started) |
| `gateway-frontend` | `gateway` (healthy) |
| `odoo` | `odoo-db` (healthy) |
| `keycloak` | `keycloak-db` (healthy) |
| `phpldapadmin` | `openldap` (démarré) | Les *healthchecks* eux-mêmes sont adaptés à chaque service : `pg_isready` pour PostgreSQL (intervalle 10 s), `redis-cli ping` pour Redis, et une sonde HTTP `/health` en Python pour la gateway (intervalle 15 s, 40 s de grâce au démarrage pour laisser FastAPI s'initialiser).

### 7.2 Sécurité Docker

Le durcissement Docker, introduit par le commit `97d284c` (cf. §4.2 V11), empile plusieurs mesures. La première est l'**exécution en utilisateur non privilégié** : l'image gateway crée un compte `appuser` d'UID **10001** et bascule sur lui (`USER appuser`) avant le démarrage. Le choix d'un UID élevé évite toute collision avec un utilisateur de l'hôte, et l'exécution non-root limite drastiquement les conséquences d'une éventuelle exécution de code dans le conteneur : un attaquant n'y obtiendrait pas les privilèges root, rendant l'évasion vers l'hôte plus difficile. Le `Dockerfile` de la gateway condense ces choix :

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc libpq-dev libldap2-dev libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*          # nettoyage dans la même couche
COPY requirements.txt .                      # avant le code → cache de couche
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/logs && chown -R appuser:appuser /app
USER appuser                                 # exécution non privilégiée
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode()==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Chaque ligne porte une intention : l'image *slim* réduit la surface, l'installation des dépendances système précède la copie du code (pour la même raison de cache que `requirements.txt`), le `--no-cache-dir` allège l'image, et la sonde de santé utilise Python plutôt que `curl` (absent de l'image *slim*).

La deuxième mesure est la **liaison des ports de datastores à `127.0.0.1`** : `gateway-db` (5434), `midpoint-postgres` (5433), `intranet-db` (55432), `redis` (6379), `qdrant` (6333/6334) et `openldap` (10389/10636) ne sont accessibles que depuis l'hôte local, tandis que `odoo-db` et `keycloak-db` ne publient aucun port. Cette mesure ferme le scénario où un `gateway-db` publié sur `0.0.0.0` serait joignable depuis le réseau local, permettant une connexion PostgreSQL directe contournant entièrement l'authentification de la gateway. La répartition de l'exposition des ports est la suivante :

| Exposition | Services / ports |
|---|---|
| Public (applicatif) | gateway `8000`, frontend `3000`, MidPoint `8080`, Keycloak `8081`, Odoo `8069`, phpLDAPadmin `8088` |
| `127.0.0.1` (datastores) | gateway-db `5434`, midpoint-postgres `5433`, intranet-db `55432`, redis `6379`, qdrant `6333/6334`, openldap `10389/10636` |
| Interne (aucun port hôte) | odoo-db, keycloak-db | La troisième mesure concerne les **limites mémoire** : MidPoint reçoit **3 Gio** parce que sa JVM est intrinsèquement gourmande (`MP_MEM_MAX=2048m`) ; Keycloak, Odoo et Qdrant reçoivent 1 Gio chacun ; la gateway 768 Mio. Sous `mem_limit`, un conteneur qui dépasse sa limite est tué par l'OOM killer **de manière ciblée** puis redémarré, plutôt que de provoquer un OOM de l'hôte entier qui ferait tomber tous les services — un cloisonnement de ressilience. La quatrième mesure, enfin, est l'**épinglage des images** : aucune n'utilise `:latest` ; certaines sont épinglées au correctif (`qdrant/qdrant:v1.12.4`, `keycloak:23.0`, `openldap:1.5.0`, `phpldapadmin:0.9.0`), garantissant des déploiements déterministes.

### 7.3 Guide de déploiement complet

Le déploiement de la plateforme suppose **Docker Desktop ≥ 4.x** (avec backend WSL2 sous Windows) sur un hôte Windows, macOS ou Linux. La stack minimale (gateway + base + Redis) requiert environ 2 Gio de RAM, tandis que la stack complète en recommande 16 (8 minimum, MidPoint en consommant jusqu'à 3 à lui seul). L'espace disque nécessaire est estimé à 8–10 Gio pour les images, complété par les volumes selon l'usage.

La **configuration initiale** consiste à cloner le dépôt, créer un fichier `.env` à partir de `.env.example`, puis **générer les secrets obligatoires** :

```bash
git clone https://github.com/Nostradam4ik/IAM-Gateway.git
cd IAM-Gateway
cp .env.example .env          # copy sous Windows PowerShell
python -c "import secrets; print(secrets.token_hex(32))"   # → SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"   # → JWT_SECRET_KEY
```

En production (`DEBUG=false`), cette étape est impérative : l'application refuse de démarrer avec des secrets vides ou faibles (cf. §4.2 V1). La **stack minimale de développement** se lève par `docker compose up gateway gateway-db redis --build` (Compose démarre aussi Qdrant via `depends_on`), l'API étant alors disponible sur `http://localhost:8000` avec Swagger sur `/docs`. La **stack complète** se lève par `docker compose up --build`, suivie d'une initialisation unique du schéma par `docker compose exec -T gateway python -m app.db.migrations`. Le démarrage complet prend environ dix minutes, MidPoint et Odoo initialisant leur schéma au premier *boot* ; on vérifie l'état par `docker compose ps` (tous *healthy*) et `curl http://localhost:8000/health`.

Les **URL et identifiants** des services (valeurs de développement à changer impérativement avant toute exposition) sont récapitulés ci-dessous :

| Service | URL | Identifiant | Mot de passe |
|---|---|---|---|
| Frontend | http://localhost:3000 | `admin` | `admin123` |
| API / Swagger | http://localhost:8000 · `/docs` | `admin` | `admin123` (→ JWT) |
| MidPoint | http://localhost:8080/midpoint | `administrator` | `5ecr3t` |
| Keycloak | http://localhost:8081 | `admin` | `admin` |
| Odoo | http://localhost:8069 | `admin` | `admin` |
| phpLDAPadmin | http://localhost:8088 | `cn=admin,dc=example,dc=com` | `secret` |
| Qdrant (dashboard) | http://localhost:6333/dashboard | — | — | Les **commandes de maintenance** courantes sont `docker compose logs -f gateway` (journaux), `docker compose ps` (état et santé), `docker compose restart gateway` (redémarrage), `docker compose down` (arrêt sans perte de données), `docker compose down -v` (arrêt **destructif** supprimant les volumes) et `docker compose up gateway --build` (reconstruction après modification du code).

### 7.4 Remarques sur la production

Le passage à un déploiement de production réel exigerait plusieurs évolutions, déjà esquissées dans l'audit de sécurité. La première est la mise en place d'une **terminaison TLS** : un reverse-proxy (NGINX, Traefik) devant la gateway et le frontend, assurant le chiffrement HTTPS et la redirection des requêtes en clair. La deuxième est une **gestion des secrets** de niveau production, remplaçant le fichier `.env` par un coffre dédié (HashiCorp Vault ou Docker secrets), avec rotation des identifiants. La troisième est une **stratégie de sauvegarde** : sauvegardes régulières des volumes critiques (les cinq bases PostgreSQL, l'annuaire LDAP, l'index Qdrant), par `pg_dump` pour les bases et archivage de volumes pour le reste, assorties d'une procédure de restauration testée. La quatrième est un **dispositif de supervision** : exporter les métriques (Prometheus) et les visualiser (Grafana), avec des alertes sur les taux d'erreur, les latences et la consommation mémoire — d'autant que les journaux JSON structurés existants s'y prêtent naturellement. À ces évolutions s'ajouteraient le passage de Keycloak hors `start-dev`, le bornage mémoire des bases (aujourd'hui sans `mem_limit`) et la suppression du *bind mount* de code au profit d'un code figé dans l'image.

On peut synthétiser ces évolutions de production dans le tableau suivant, qui distingue l'état actuel (démonstration) de l'état cible (production) :

| Domaine | État actuel (démonstration) | État cible (production) |
|---|---|---|
| Transport | HTTP clair sur l'hôte | HTTPS via reverse-proxy (NGINX/Traefik) |
| Secrets | Fichier `.env` | Coffre (Vault / Docker secrets) + rotation |
| Keycloak | `start-dev` | `start` avec hostname/HTTPS configurés |
| Réseau | Réseau unique `iam-network` | Segmentation (réseau backend isolé) |
| Limites mémoire | 5 services bornés | Toutes les bases bornées |
| Code gateway | *bind mount* (rechargement) | Figé dans l'image |
| Supervision | Logs JSON stdout | Prometheus + Grafana + alertes |
| Sauvegarde | Volumes persistants | `pg_dump` planifié + restauration testée |

Ce tableau matérialise le chemin de durcissement : aucune de ces évolutions n'est bloquante pour la **démonstration** du projet, mais toutes seraient nécessaires pour un **usage réel** — et leur identification précise fait partie de la valeur du livrable.

---

## 8. Difficultés rencontrées et solutions

Cette section relate les principales difficultés techniques rencontrées au cours du projet, non comme une liste de problèmes, mais comme des récits d'ingénierie illustrant la démarche de diagnostic et de résolution. Le tableau ci-dessous en offre une vue synthétique avant le détail de chacune :

| # | Difficulté | Cause profonde | Solution |
|---|---|---|---|
| 8.1 | I/O bloquantes en contexte async | bcrypt/ldap3/xmlrpc bloquent l'event loop | `asyncio.to_thread` + timeouts |
| 8.2 | Race condition du rate-limit | `INCR`+`EXPIRE` non atomiques | script Lua atomique |
| 8.3 | Stacked PRs | branches dépendantes | rebasculement de base après fusion |
| 8.4 | Tâches perdues par le GC | référence faible asyncio | ensemble `_pending_tasks` (réf. forte) |
| 8.5 | Cache npm CI / timeouts connecteurs | lockfile absent / aléas réseau | désactivation cache + retry/timeouts |
| 8.6 | Parsing des réponses MidPoint | formes JSON variables | parsing défensif normalisant en liste |
| 8.7 | Migration Pydantic v2 | API divergente de la v1 | conversion complète des idiomes |
| 8.8 | Architecture double-mode | risque de duplication | abstraction `BaseConnector` |

### 8.1 Gestion des bibliothèques bloquantes dans un contexte asynchrone

La première difficulté majeure est née de la rencontre entre un framework asynchrone (FastAPI) et des bibliothèques fondamentalement synchrones. Au début du développement, les appels à bcrypt (hachage de mot de passe), à ldap3 (connexion à l'annuaire) et à `xmlrpc.client` (dialogue avec Odoo) étaient effectués directement dans les *handlers* asynchrones. Les symptômes sont apparus sous charge : l'API devenait globalement non réactive pendant certaines opérations. Le diagnostic a révélé la cause profonde : ces bibliothèques **bloquent le fil d'exécution** pendant leur travail, et comme un serveur ASGI traite de nombreuses requêtes sur une **unique boucle d'événements**, bloquer ce fil revient à figer **toutes** les requêtes en cours, pas seulement celle qui appelle bcrypt.

La solution a consisté à **déporter ces appels bloquants hors de la boucle d'événements** via `asyncio.to_thread`, qui exécute la fonction synchrone dans le pool de *threads* par défaut tout en rendant la main à la boucle. Pour les connecteurs, ce déport a été complété par un **bornage rigoureux des timeouts** (10 s pour LDAP, 15 s pour Odoo), afin qu'un système externe lent ne monopolise pas indéfiniment un *thread*. Les leçons tirées de cet épisode sont structurantes. D'abord, la distinction entre travail **lié au CPU** (bcrypt — un *thread* suffit car le GIL est relâché par la bibliothèque C sous-jacente) et travail **lié aux I/O** (LDAP/SMTP — où le *thread* attend une réponse réseau) éclaire le choix de `to_thread` plutôt qu'un pool dédié. Ensuite, la compréhension du **GIL** (*Global Interpreter Lock*) de Python : `to_thread` est efficace pour les I/O et pour les bibliothèques C qui relâchent le GIL, mais ne paralléliserait pas du pur calcul Python. Enfin, la règle d'or de la programmation asynchrone : **ne jamais bloquer la boucle d'événements**, qui est devenue un réflexe de conception pour la suite du projet.

### 8.2 Race condition dans le rate limiting Redis

La deuxième difficulté concerne la limitation de débit du *login*. L'implémentation initiale procédait en deux commandes Redis distinctes : d'abord `INCR` pour incrémenter le compteur, puis `EXPIRE` pour lui poser une durée de vie. Cette approche, apparemment correcte, recelait une **condition de course** subtile : entre l'exécution de `INCR` et celle d'`EXPIRE`, si le processus était interrompu (crash, *timeout*, redéploiement), la clé restait **sans expiration**. Le compteur ne redescendant jamais, l'utilisateur (ou l'IP) concerné se retrouvait **bloqué indéfiniment**, même longtemps après la fin de la fenêtre de limitation. Le problème était d'autant plus pernicieux qu'il ne se manifestait qu'occasionnellement, au gré des interruptions.

La découverte a résulté d'un raisonnement sur les invariants : « que se passe-t-il si le processus meurt entre les deux commandes ? ». La réponse — une clé orpheline sans TTL — a immédiatement désigné le problème d'**atomicité**. La solution adoptée est un **script Lua exécuté côté Redis**, qui réalise l'incrémentation et la pose conditionnelle du TTL en une **opération unique et indivisible** : `local c = redis.call('INCR', KEYS[1]); if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end; return c`. Redis garantissant l'atomicité de l'exécution d'un script Lua, il devient impossible d'observer un état intermédiaire où le compteur existerait sans TTL. La leçon retenue dépasse le cas particulier : dès qu'une logique repose sur plusieurs opérations devant être atomiques sur un état partagé, il faut soit une transaction, soit — pour Redis — un script Lua. Cette prise de conscience de l'atomicité comme propriété à concevoir explicitement, et non à espérer, est l'un des acquis les plus transférables du projet.

### 8.3 Stacked PRs et workflow Git complexe

La troisième difficulté fut d'ordre méthodologique. Le chantier de fiabilisation des connecteurs (`iam-connector-improvements`) s'appuyait directement sur le code de sécurité (`security-hardening`) : les connecteurs venaient d'être touchés par les corrections d'injection et de déport des I/O. Créer la branche connecteurs à partir de `main` aurait signifié travailler sans ces corrections ; elle a donc été créée **à partir de `security-hardening`**, formant une paire de *pull requests* **empilées** (*stacked PRs*). La PR #2 (connecteurs) ciblait alors `security-hardening` comme base, et non `main`, afin que son *diff* ne montre que le delta « connecteurs » et reste revuable.

Le problème d'**ordonnancement de fusion** est apparu au moment d'intégrer : on ne pouvait pas fusionner la PR #2 dans `main` tant que la PR #1 n'y était pas, sous peine d'y entraîner aussi tous les commits de sécurité de manière confuse. La solution a suivi le schéma canonique des *stacked PRs* : fusionner d'abord la PR #1 (`security-hardening` → `main`), puis **rebasculer la base de la PR #2 sur `main`** (opération `gh pr edit 2 --base main`), et enfin la fusionner. Cet épisode a mis en lumière la mécanique des branches de fonctionnalités dépendantes : une branche enfant porte les commits de sa branche parente jusqu'à ce que celle-ci soit fusionnée, après quoi un *rebase*/retargeting nettoie l'historique. La leçon est qu'un *workflow* Git doit être **pensé en amont** lorsque des fonctionnalités dépendent l'une de l'autre, et que GitHub gère gracieusement le rebasculement de base à condition de respecter l'ordre de fusion. Cet épisode s'est d'ailleurs rejoué lors de la rédaction de ce rapport, où un *cherry-pick* du correctif CI s'est révélé vide car le correctif était déjà présent sur la branche cible — illustration concrète de la convergence des historiques après fusion.

### 8.4 Background tasks et le garbage collector Python

La quatrième difficulté, déjà évoquée comme vulnérabilité V8, mérite d'être racontée comme un récit de débogage car elle illustre un piège classique de l'asyncio. Le `MemoryStore` persiste ses écritures en base de manière *fire-and-forget* : il met à jour le cache immédiatement et lance une tâche asynchrone pour écrire en PostgreSQL sans attendre. L'implémentation initiale créait ces tâches par `asyncio.create_task(coro)` sans conserver la référence retournée. Le symptôme — des écritures (et des entrées d'audit) **manquant occasionnellement** en base — était particulièrement difficile à diagnostiquer car non déterministe.

La cause profonde réside dans une particularité documentée mais peu connue d'asyncio : la boucle d'événements ne conserve qu'une **référence faible** aux tâches. Si le code appelant ne garde pas de référence forte, la tâche peut être **collectée par le ramasse-miettes** avant d'avoir terminé, et son écriture est silencieusement perdue. La solution, appliquée dans le commit `6cf898d`, consiste à conserver chaque tâche dans un ensemble `_pending_tasks` (référence forte garantissant la survie jusqu'à la fin), assorti d'un *callback* de complétion qui retire la tâche de l'ensemble et **journalise toute exception** au lieu de la perdre :

```python
def _run_async(self, coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)              # pas de loop : exécution bloquante immédiate
    task = loop.create_task(coro)
    self._pending_tasks.add(task)             # référence forte → survit au GC
    def _on_done(t):
        self._pending_tasks.discard(t)
        if not t.cancelled() and t.exception() is not None:
            logger.error("Background persistence task failed", error=str(t.exception()))
    task.add_done_callback(_on_done)
```

Ce patron — créer la tâche, l'ajouter à un ensemble persistant, puis l'en retirer à la complétion via un *callback* qui journalise l'éventuelle exception — est désormais la manière recommandée de lancer des tâches *fire-and-forget* en asyncio. Il combine deux garanties : la **survie** de la tâche (référence forte) et la **non-perte des erreurs** (journalisation explicite), corrigeant à la fois le symptôme (écritures manquantes) et son corollaire (erreurs silencieuses). La leçon est double : d'une part, comprendre que la responsabilité de maintenir une tâche en vie incombe à l'appelant ; d'autre part, qu'une opération *fire-and-forget* ne dispense pas de gérer ses erreurs — sans le *callback*, une exception de persistance disparaissait sans trace.

### 8.5 Autres difficultés : CI npm, fiabilisation des connecteurs

Plusieurs autres difficultés, de moindre ampleur mais instructives, ont jalonné le projet. La première concerne le **cache npm en intégration continue**. Le *job* frontend échouait à l'étape `actions/setup-node` avec le message « Some specified paths were not resolved, unable to cache dependencies » : la configuration `cache: npm` exigeait un `package-lock.json` pour calculer sa clé, or ce fichier est volontairement absent du dépôt (présent dans `.gitignore`). Le correctif (commits `07e4b78` puis `b3cdb0a`) a consisté à **désactiver le cache npm** : `npm install` fonctionne sans *lockfile*, et le *build* a été vérifié localement. La leçon — qu'un mécanisme de cache impose ses propres prérequis — a conduit à inscrire le versionnement du *lockfile* à la feuille de route comme correctif de fond.

La seconde concerne le **réglage des timeouts et des retries des connecteurs**. Les premiers tests d'intégration avec MidPoint révélaient des échecs intermittents lors des redémarrages du hub : une requête émise pendant que MidPoint propageait vers ses ressources échouait par coupure de connexion. La solution a consisté à doter le `MidPointConnector` d'un transport `httpx.AsyncHTTPTransport(retries=2)` retentant les échecs transitoires, le `LDAPConnector` d'une reconnexion du *bind* (deux tentatives) et l'`OdooConnector` d'une ré-authentification sur session expirée. Ces réglages, qui paraissent mineurs, font la différence entre un système fragile et un système robuste face aux aléas réseau ; ils sont l'aboutissement du chantier `iam-connector-improvements`. La leçon générale de ces deux épisodes est que la **fiabilité d'un système distribué se gagne dans les détails** : les valeurs de *timeout*, les politiques de *retry* et les prérequis d'outillage, souvent négligés, conditionnent la robustesse réelle.

### 8.6 Parsing défensif des réponses MidPoint

Une difficulté récurrente d'intégration a été la **variabilité de forme** des réponses JSON de MidPoint. Selon l'opération et le nombre d'objets retournés, la structure imbriquée variait : `data["object"]` pouvait être un dictionnaire contenant lui-même une clé `object` (une liste), ou directement une liste, ou encore un objet unique non encapsulé dans une liste. Une lecture naïve (`data["object"]["object"]`) échouait donc de manière intermittente selon les cas. Le diagnostic a nécessité d'observer plusieurs formes de réponses réelles avant de comprendre que MidPoint **n'encapsule pas un résultat unique dans une liste**. La solution a consisté en un **parsing défensif** systématique, vérifiant le type à chaque niveau et normalisant toujours vers une liste : `obj = data.get("object", {}); users = obj.get("object", []) if isinstance(obj, dict) else obj; users = users if isinstance(users, list) else [users]`. La leçon est qu'intégrer une API tierce impose de **ne jamais présumer de la forme** des réponses et de coder défensivement contre toutes les variations observées — surtout lorsque la documentation est lacunaire.

### 8.7 Migration et adoption de Pydantic v2

Le projet s'appuie sur **Pydantic v2**, dont l'API diffère sensiblement de la v1. Plusieurs ajustements ont été nécessaires : l'usage de `ConfigDict(extra="ignore")` (remplaçant la classe `Config` interne) dans les modèles IAM, l'emploi de `model_validator(mode="after")` (et non plus `@root_validator`) pour la validation *fail-fast* des secrets, et `model_dump(exclude_none=True)` (et non `.dict()`) dans certains endpoints. Ces évolutions, mineures isolément, ont demandé de la vigilance pour ne pas mélanger les idiomes des deux versions. Le bénéfice de la v2 est néanmoins tangible : performances de validation nettement supérieures (cœur réécrit en Rust) et messages d'erreur plus précis. La leçon retenue est que l'adoption d'une version majeure d'une bibliothèque centrale doit être **assumée pleinement** — en convertissant tous les idiomes — plutôt que partiellement, sous peine d'incohérences subtiles.

### 8.8 Concevoir l'architecture double-mode sans dupliquer la logique

Une difficulté plus conceptuelle qu'opérationnelle a été de **concilier deux modes de provisionnement** (hub via MidPoint et direct via connecteurs) sans dupliquer la logique métier. La tentation initiale était d'écrire deux chemins entièrement séparés, au risque de voir les corrections de bugs et les évolutions diverger entre les deux. La solution est venue de l'abstraction `BaseConnector` : en faisant manipuler aux services des connecteurs interchangeables respectant un contrat uniforme, le mode direct (`ProvisionService`) et le mode hub (`MidPointProvisionService`) partagent la même conception sans partager leur code d'orchestration — chacun reste spécialisé, mais aucun ne réinvente l'interface des cibles. La méthode `continue_after_approval` matérialise même une **passerelle entre les deux modes** : elle tente d'abord MidPoint, puis retombe sur les écritures directes. La leçon est qu'une bonne abstraction (ici, le contrat de connecteur) permet de soutenir plusieurs paradigmes sans payer le prix de la duplication — à condition de l'identifier tôt et de s'y tenir. Cette décision, prise au début du projet, a porté ses fruits tout au long du développement : ajouter une fiabilisation (timeout, retry) à un connecteur bénéficie automatiquement aux deux modes.

---

## 9. Limites actuelles et perspectives

### 9.1 Limites techniques connues

Un rapport d'ingénierie honnête se reconnaît à sa capacité à documenter ses propres limites avec précision. La plateforme, fonctionnelle et sécurisée sur son cœur, présente plusieurs limites techniques connues qu'il convient d'exposer sans détour.

**Moteur de règles incomplet.** Comme indiqué en §3.5, plusieurs méthodes de persistance du `RuleEngine` renvoient encore des données par défaut (mocks) plutôt que d'interroger réellement la table `rules`. Concrètement, le listing, la création et le test de règles fonctionnent au niveau de l'API, mais le câblage complet entre le moteur et sa table de persistance n'est pas finalisé partout. L'impact est que certaines opérations sur les règles peuvent ne pas être durablement persistées dans l'état actuel. La table `rules` existe pourtant et est correctement semée par les migrations (une règle LDAP d'exemple) ; il manque donc essentiellement le branchement des méthodes du service sur les requêtes SQL réelles. C'est une dette technique circonscrite et clairement identifiée, dont la résorption consisterait à remplacer les retours mock par des appels à la base via la session asynchrone. Cette transparence est délibérée : il est plus honnête, dans un rapport d'ingénierie, de signaler précisément qu'un sous-ensemble de méthodes n'est pas encore câblé que de laisser croire à une complétude trompeuse. La structure de persistance (table `rules`, modèle SQLModel, données de *seed*) étant déjà en place, l'effort résiduel est bien délimité et non bloquant pour la démonstration des autres fonctionnalités.

**Absence de `package-lock.json`.** Le `package-lock.json` du frontend étant exclu par `.gitignore`, les *builds* frontend ne sont pas parfaitement **reproductibles** : un `npm install` peut récupérer des versions correctives (*patch*) plus récentes que celles utilisées lors du développement, ce qui peut, en théorie, introduire des écarts de comportement entre deux *builds*. C'est aussi la cause directe de la désactivation du cache npm en CI (cf. §8.5). Le correctif est trivial dans son principe — committer le *lockfile* et réactiver le cache — mais il a une implication : il fige les versions, ce qui impose ensuite une mise à jour maîtrisée des dépendances.

**Couverture de tests insuffisante.** La suite actuelle compte trois fichiers de tests unitaires couvrant la sécurité, la configuration et la garde anti-injection des connecteurs. Manquent à l'appel : les **tests d'intégration** (dialogue réel avec MidPoint, LDAP, Odoo, par exemple via des conteneurs éphémères), les **tests de la couche service** (logique de provisionnement, de workflow, de réconciliation testée en isolation avec des connecteurs simulés), les **tests d'endpoints** (appels HTTP de bout en bout via le client de test FastAPI) et les **tests frontend** (composants React, parcours utilisateur). Une suite complète viserait une pyramide de tests équilibrée :

| Niveau | Couverture actuelle | Couverture cible |
|---|---|---|
| Unitaire (sécurité, config, connecteurs) | ✅ 13 fonctions (cœur sécurité) | étendre aux services et au moteur de règles |
| Service (logique métier isolée) | ❌ absent | provisioning, workflows, réconciliation avec connecteurs simulés |
| Intégration (systèmes réels) | ❌ absent | MidPoint/LDAP/Odoo via conteneurs éphémères |
| Endpoint (HTTP de bout en bout) | ❌ absent | les 149 endpoints via le client de test FastAPI |
| Frontend (composants, parcours) | ❌ absent | composants React, parcours utilisateur (Vitest/Playwright) |

L'investissement initial sur le niveau unitaire de sécurité — la zone de plus haut risque — est cohérent avec une stratégie de priorisation par le risque, mais l'extension vers les niveaux supérieurs de la pyramide reste une priorité de consolidation clairement identifiée. L'investissement initial consenti sur la sécurité — la zone de plus haut risque — est cohérent, mais l'extension de la couverture est une priorité de consolidation.

**Mode start-dev de Keycloak.** Keycloak est lancé en `command: start-dev`, mode explicitement destiné au développement et non à la production. Ce mode désactive certaines optimisations et certains contrôles (notamment autour du *hostname* et du HTTPS). Une configuration de production exigerait le mode `start`, avec un *hostname* configuré, le HTTPS activé et une base de données dimensionnée — sans quoi Keycloak refuserait d'ailleurs de démarrer en mode production. Cette limite est typique d'un environnement de démonstration et est sans conséquence dans ce cadre, mais elle est à lever pour tout usage réel.

**Fixture TEMP_USERS en mode DEBUG.** La fixture d'utilisateurs codés en dur (`admin`/`operator`) n'est active que lorsque `DEBUG=true`. C'est un garde-fou réel, mais il reporte la sûreté sur la **rigueur de configuration** : si `DEBUG=true` était activé par erreur en production, ces comptes de test deviendraient exploitables. Le risque est conditionnel et maîtrisable (par une discipline de configuration et, idéalement, une vérification automatisée que `DEBUG=false` en production), mais il mérite d'être explicité comme une limite assumée plutôt que masqué.

### 9.2 Roadmap court terme

À l'horizon des trois prochains mois, cinq priorités de consolidation se dégagent. La première est de **committer le `package-lock.json`** et de réactiver le cache npm en CI, rétablissant la reproductibilité des *builds* frontend. La deuxième est d'enrichir la **présence du projet sur GitHub** (un `README.md` complet en page d'accueil du dépôt, des badges de CI, une documentation d'accueil), améliorant son accessibilité. La troisième est la mise en place d'une **suite de tests d'intégration**, idéalement avec des conteneurs éphémères pour MidPoint, LDAP et Odoo, validant les connecteurs de bout en bout. La quatrième est le **câblage complet du moteur de règles** sur sa table de persistance, éliminant les retours mock résiduels. La cinquième est la **configuration de production de Keycloak**, préparant un déploiement réel. Ces priorités peuvent se hiérarchiser ainsi :

| Priorité | Chantier | Effort | Bénéfice |
|---|---|---|---|
| 1 | Committer `package-lock.json` + cache npm CI | faible | reproductibilité des builds |
| 2 | `README.md` d'accueil + badges CI | faible | accessibilité du projet |
| 3 | Suite de tests d'intégration (conteneurs éphémères) | moyen | fiabilité des connecteurs |
| 4 | Câblage complet du moteur de règles | moyen | persistance réelle des règles |
| 5 | Configuration de production de Keycloak | moyen | préparation au déploiement réel |

Ces cinq chantiers, de difficulté modérée, transformeraient la plateforme d'un prototype abouti en un produit consolidé.

### 9.3 Roadmap long terme

À plus longue échéance, plusieurs évolutions structurantes enrichiraient la portée fonctionnelle de la plateforme, en combinant la feuille de route de l'`ARCHITECTURE.md` et l'analyse menée dans ce rapport. L'ajout d'un **endpoint SCIM 2.0** (*System for Cross-domain Identity Management*) ouvrirait l'interopérabilité avec l'écosystème standard de provisionnement, permettant à des applications tierces conformes de dialoguer avec la gateway sans connecteur dédié. Le support de **SAML 2.0** étendrait le SSO aux applications *legacy* qui ne parlent pas OIDC. L'introduction de **WebSockets** permettrait des alertes en temps réel (par exemple, notifier l'interface d'un échec de provisionnement sans *polling*). Les **campagnes de recertification des accès** — où les responsables revoient et confirment périodiquement les droits de leurs équipes — apporteraient la dimension de gouvernance IGA la plus avancée, directement alignée sur les exigences ISO 27001. Une **application mobile** pour les workflows d'approbation fluidifierait les validations en mobilité. Enfin, un **chart Helm** pour le déploiement sur Kubernetes ferait passer l'infrastructure d'un orchestrateur mono-hôte (Compose) à une plateforme distribuée, scalable et résiliente — tirant pleinement parti du principe d'API sans état posé dès la conception. La réalisation effective de vrais embeddings sémantiques pour Qdrant (cf. §6.5) et l'adoption d'Alembic pour la gestion des migrations (résorbant la dérive de schéma) complèteraient ce tableau d'évolutions. Le tableau suivant priorise ces perspectives selon leur horizon et leur valeur :

| Évolution | Horizon | Valeur apportée |
|---|---|---|
| Endpoint SCIM 2.0 | Long terme | Interopérabilité standard avec applications tierces |
| SAML 2.0 | Long terme | SSO pour applications *legacy* non-OIDC |
| WebSockets (alertes temps réel) | Moyen terme | Notifications sans *polling* (échecs, approbations) |
| Campagnes de recertification | Long terme | Gouvernance IGA avancée (conformité ISO 27001) |
| Application mobile d'approbation | Long terme | Validations en mobilité |
| Chart Helm / Kubernetes | Long terme | Déploiement distribué, scalable, résilient |
| Embeddings sémantiques réels (Qdrant) | Moyen terme | Recherche d'audit véritablement sémantique |
| Migrations Alembic | Court/moyen terme | Fin de la dérive de schéma, montées de version sûres |

Cette feuille de route, hiérarchisée, montre que le projet n'est pas pensé comme un aboutissement figé mais comme une **base extensible** : chaque évolution s'appuie sur les fondations déjà posées (architecture sans état pour Kubernetes, infrastructure vectorielle pour les embeddings, abstraction de connecteurs pour SCIM/SAML).

---

## 10. Conclusion

**Bilan des objectifs.** Le projet IAM Gateway atteint l'objectif principal qu'il s'était fixé : offrir une passerelle de provisionnement IAM intelligente, multi-cibles, dotée d'une interface no-code et d'un assistant IA, déployable en une commande. Les chiffres en attestent : **149 endpoints** REST opérationnels répartis sur 14 routeurs, **14 services** Docker orchestrés, **82 fichiers Python** totalisant **27 406 lignes**, un frontend React de 25 fichiers TypeScript, **54 commits** structurant un historique propre, et surtout **13 vulnérabilités de sécurité** identifiées, corrigées et tracées une par une. Les cinq grands domaines fonctionnels visés — provisionnement double-mode, authentification/autorisation, automatisation par règles, gouvernance par workflows, intelligence par IA et recherche sémantique — sont tous réalisés, avec une transparence assumée sur les parties encore partielles (le câblage complet du moteur de règles, la qualité des embeddings). L'écart entre le planifié et le réalisé est donc faible et documenté, ce qui est la marque d'un projet maîtrisé. Le tableau ci-dessous synthétise les réalisations chiffrées :

| Indicateur | Valeur | Signification |
|---|---|---|
| Endpoints REST | 149 | surface fonctionnelle de l'API |
| Routeurs | 14 | domaines fonctionnels |
| Services Docker | 14 | écosystème orchestré |
| Fichiers Python | 82 | base de code backend |
| Lignes de Python | 27 406 | volume du code |
| Fichiers TS/TSX | 25 | interface React |
| Tables PostgreSQL | 24 | modèle de données |
| Fonctions de test | 13 | couverture du cœur sécurité |
| Commits | 54 | historique tracé |
| Vulnérabilités corrigées | 13 | audit de sécurité |

**Valeur technique du projet.** Au-delà des chiffres, la valeur technique d'IAM Gateway réside dans la cohérence de ses choix d'architecture. L'**architecture double-paradigme** (mode hub via MidPoint et mode direct avec rollback) est rare et révèle une compréhension fine du domaine : elle permet à la fois de s'appuyer sur un moteur IGA mature et de conserver un chemin autonome. Le **moteur de règles no-code** sandboxé démocratise une fonctionnalité habituellement réservée aux experts. Le **pipeline DevSecOps complet** (tests de sécurité, CI/CD, audit de dépendances) inscrit la qualité dans le processus et non seulement dans le produit. La **persistance polyglotte** (PostgreSQL, Redis, Qdrant) adapte rigoureusement l'outil au besoin. Et l'ensemble repose sur une **architecture asynchrone** maîtrisée, où la connaissance des pièges (boucle d'événements, atomicité Redis, GC des tâches) transparaît dans des solutions élégantes. C'est cette **cohérence d'ensemble**, plus que toute fonctionnalité isolée, qui fait la qualité technique du projet.

**Valeur pédagogique.** Sur le plan de l'apprentissage, le projet aura permis de mobiliser et d'approfondir un large spectre de compétences. La **maîtrise du domaine IAM/IGA** — concepts JML, gouvernance, réconciliation, shadows — constitue un acquis métier précieux et différenciant. La pratique de **FastAPI et de Python asynchrone à l'échelle** a confronté à des problèmes réels d'architecture asynchrone, source des leçons les plus marquantes (§8). L'**orchestration Docker** et l'écriture d'une infrastructure as code ont ancré une culture DevOps concrète. L'**ingénierie de la sécurité**, abordée comme un audit méthodique plutôt que comme un vernis, a transformé une notion abstraite en une pratique outillée et vérifiable. Le **CI/CD** a montré comment industrialiser la qualité. Enfin, la **communication technique** — quatre fiches techniques, une architecture documentée et ce rapport exhaustif — a exercé la capacité à rendre intelligible un système complexe, compétence aussi rare que recherchée.

**Perspectives professionnelles.** Ce projet démontre une aptitude à occuper des fonctions d'ingénierie exigeantes à l'intersection du développement, de la sécurité et de l'exploitation. Il atteste d'une capacité à **concevoir une architecture** cohérente et défendable, à **conduire un audit de sécurité** structuré et à le corriger de manière traçable, à **intégrer des systèmes hétérogènes** derrière des abstractions propres, et à **documenter** rigoureusement un travail technique. Ces compétences correspondent directement aux attentes des métiers d'**ingénieur DevOps**, d'**ingénieur sécurité** ou d'**ingénieur IAM** — des profils en forte tension sur le marché. Plus fondamentalement, le projet démontre une **posture d'ingénieur** : celle qui consiste non seulement à faire fonctionner un système, mais à le rendre sûr, observable, maintenable et honnêtement documenté, y compris dans ses limites. C'est cette posture, autant que les réalisations techniques, qui constitue l'aboutissement de cette SAE de fin de cursus.

En définitive, IAM Gateway illustre ce qu'une SAE de fin de BUT peut produire lorsqu'elle est menée avec ambition et rigueur : non pas une maquette jetable, mais un système cohérent, sécurisé, documenté et extensible, qui aurait sa place comme socle d'un véritable projet d'entreprise. Le chemin parcouru — d'un problème métier réel (la gestion des identités) à une plateforme opérationnelle de 149 endpoints sécurisés et orchestrant 14 services — témoigne d'une montée en compétence qui dépasse la simple accumulation de connaissances techniques. Il reste des limites, honnêtement documentées, et une feuille de route claire pour les lever ; mais c'est précisément cette capacité à **livrer un système fonctionnel tout en sachant nommer ce qui reste à faire** qui distingue l'ingénieur du simple exécutant. Le projet, son code, son audit de sécurité et cette documentation forment un ensemble qui se veut à la hauteur des exigences académiques de l'UPEC et du laboratoire LISSI, et qui constitue, pour ses auteurs, une démonstration concrète et défendable de leur aptitude à concevoir, sécuriser et documenter des systèmes d'information complexes.

---

## Annexes

### Annexe A — Liste exhaustive des endpoints API

Cette annexe énumère les **149 endpoints** de l'API, groupés par routeur, avec leur méthode HTTP, leur chemin complet, leur exigence d'authentification (`Public`, `JWT` = authentifié, `HMAC` = signature webhook) et les rôles requis pour les opérations protégées. Les chemins intègrent le préfixe de montage défini dans `main.py`.

#### admin.py — préfixe `/api/v1/admin` (11 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/admin/token` | Public (rate-limited) | — | Connexion, retourne un JWT |
| 2 | GET | `/api/v1/admin/me` | JWT | — | Identité et rôles courants |
| 3 | POST | `/api/v1/admin/logout` | JWT | — | Révoque le jeton (blacklist `jti`) |
| 4 | GET | `/api/v1/admin/status` | JWT | — | Statut DB/Redis/LDAP/MidPoint |
| 5 | POST | `/api/v1/admin/emergency-stop` | JWT | admin | Désactive tout provisionnement |
| 6 | POST | `/api/v1/admin/resume` | JWT | admin | Réactive le provisionnement |
| 7 | POST | `/api/v1/admin/audit/search` | JWT | — | Recherche dans les logs d'audit |
| 8 | GET | `/api/v1/admin/audit/recent` | JWT | — | Logs d'audit récents |
| 9 | GET | `/api/v1/admin/config` | JWT | admin | Configuration (sans secrets) |
| 10 | GET | `/api/v1/admin/connectors/status` | JWT | — | Connectivité des connecteurs |
| 11 | GET | `/api/v1/admin/metrics` | JWT | — | Métriques d'opérations/workflows |

#### provision.py — préfixe `/api/v1/provision` (13 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 12 | POST | `/api/v1/provision/` | JWT | admin, iam_engineer | Provisionner (hub ou direct) |
| 13 | GET | `/api/v1/provision/{operation_id}` | JWT | — | Statut d'une opération |
| 14 | POST | `/api/v1/provision/{operation_id}/rollback` | JWT | admin, iam_engineer | Annuler une opération |
| 15 | GET | `/api/v1/provision/` | JWT | — | Lister les opérations |
| 16 | PUT | `/api/v1/provision/{operation_id}` | JWT | admin, iam_engineer | Mettre à jour un compte |
| 17 | DELETE | `/api/v1/provision/{operation_id}` | JWT | admin | Supprimer le compte des cibles |
| 18 | GET | `/api/v1/provision/midpoint/users` | JWT | — | Lister les utilisateurs MidPoint |
| 19 | GET | `/api/v1/provision/midpoint/users/{account_id}` | JWT | — | Utilisateur + shadows |
| 20 | GET | `/api/v1/provision/midpoint/roles` | JWT | — | Lister les rôles MidPoint |
| 21 | POST | `/api/v1/provision/midpoint/users/{account_id}/roles/{role_name}` | JWT | admin | Assigner un rôle |
| 22 | DELETE | `/api/v1/provision/midpoint/users/{account_id}/roles/{role_name}` | JWT | admin | Retirer un rôle |
| 23 | GET | `/api/v1/provision/midpoint/resources` | JWT | — | Lister les ressources |
| 24 | GET | `/api/v1/provision/midpoint/status` | JWT | — | Statut de connexion MidPoint |

#### midpoint.py — préfixe `/api/v1/midpoint` (14 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 25 | GET | `/api/v1/midpoint/users` | JWT | — | Lister les utilisateurs |
| 26 | GET | `/api/v1/midpoint/users/{user_id}` | JWT | — | Détail utilisateur + shadows |
| 27 | POST | `/api/v1/midpoint/users` | JWT | admin, iam_engineer | Créer un utilisateur |
| 28 | PUT | `/api/v1/midpoint/users/{user_id}` | JWT | admin, iam_engineer | Modifier un utilisateur |
| 29 | DELETE | `/api/v1/midpoint/users/{user_id}` | JWT | admin | Supprimer (cascade cibles) |
| 30 | POST | `/api/v1/midpoint/users/{user_id}/disable` | JWT | admin, iam_engineer | Désactiver |
| 31 | POST | `/api/v1/midpoint/users/{user_id}/enable` | JWT | admin, iam_engineer | Activer |
| 32 | GET | `/api/v1/midpoint/roles` | JWT | — | Lister les rôles (typé) |
| 33 | POST | `/api/v1/midpoint/users/{user_id}/roles/{role_id}` | JWT | admin | Assigner un rôle |
| 34 | DELETE | `/api/v1/midpoint/users/{user_id}/roles/{role_id}` | JWT | admin | Retirer un rôle |
| 35 | GET | `/api/v1/midpoint/users/{user_id}/roles` | JWT | — | Rôles d'un utilisateur |
| 36 | GET | `/api/v1/midpoint/resources` | JWT | — | Lister les ressources (typé) |
| 37 | GET | `/api/v1/midpoint/users/{user_id}/shadows` | JWT | — | Comptes shadow (projections) |
| 38 | GET | `/api/v1/midpoint/health` | JWT | — | Joignabilité de MidPoint |

#### rules.py — préfixe `/api/v1/rules` (11 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 39 | GET | `/api/v1/rules/` | JWT | — | Lister les règles |
| 40 | POST | `/api/v1/rules/` | JWT | admin, iam_engineer | Créer une règle |
| 41 | GET | `/api/v1/rules/{rule_id}` | JWT | — | Détail d'une règle |
| 42 | PUT | `/api/v1/rules/{rule_id}` | JWT | admin, iam_engineer | Modifier une règle |
| 43 | DELETE | `/api/v1/rules/{rule_id}` | JWT | admin | Supprimer (soft delete) |
| 44 | POST | `/api/v1/rules/test` | JWT | — | Tester une règle sur données |
| 45 | GET | `/api/v1/rules/{rule_id}/versions` | JWT | — | Historique des versions |
| 46 | POST | `/api/v1/rules/{rule_id}/restore/{version}` | JWT | admin, iam_engineer | Restaurer une version |
| 47 | GET | `/api/v1/rules/policies/` | JWT | — | Lister les politiques |
| 48 | POST | `/api/v1/rules/policies/` | JWT | admin | Créer une politique |
| 49 | GET | `/api/v1/rules/policies/{policy_id}` | JWT | — | Détail d'une politique |

#### workflow.py — préfixe `/api/v1/workflow` (13 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 50 | GET | `/api/v1/workflow/configs` | JWT | — | Lister les configs de workflow |
| 51 | POST | `/api/v1/workflow/configs` | JWT | admin | Créer une config |
| 52 | GET | `/api/v1/workflow/configs/{config_id}` | JWT | — | Détail d'une config |
| 53 | PUT | `/api/v1/workflow/configs/{config_id}` | JWT | admin | Modifier une config |
| 54 | GET | `/api/v1/workflow/instances` | JWT | — | Lister les instances |
| 55 | GET | `/api/v1/workflow/instances/pending` | JWT | — | Approbations en attente |
| 56 | GET | `/api/v1/workflow/instances/{instance_id}` | JWT | — | Détail d'une instance |
| 57 | POST | `/api/v1/workflow/instances/{instance_id}/approve` | JWT (objet) | — | Approuver (`can_approve`) |
| 58 | POST | `/api/v1/workflow/instances/{instance_id}/reject` | JWT (objet) | — | Rejeter |
| 59 | POST | `/api/v1/workflow/instances/{instance_id}/cancel` | JWT | admin | Annuler |
| 60 | GET | `/api/v1/workflow/instances/{instance_id}/history` | JWT | — | Historique des décisions |
| 61 | GET | `/api/v1/workflow/instances/{instance_id}/details` | JWT | — | Détails complets (niveaux) |
| 62 | GET | `/api/v1/workflow/approve-by-email` | Public (token) | — | Approbation par lien email |

#### reconcile.py — préfixe `/api/v1/reconcile` (7 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 63 | POST | `/api/v1/reconcile/start` | JWT | admin, iam_engineer | Démarrer un job de réconciliation |
| 64 | GET | `/api/v1/reconcile/status/{job_id}` | JWT | — | Statut d'un job |
| 65 | GET | `/api/v1/reconcile/jobs` | JWT | — | Lister les jobs |
| 66 | GET | `/api/v1/reconcile/{job_id}/discrepancies` | JWT | — | Divergences détectées |
| 67 | POST | `/api/v1/reconcile/{job_id}/resolve` | JWT | admin, iam_engineer | Résoudre les divergences |
| 68 | POST | `/api/v1/reconcile/sync-cache` | JWT | admin | Rafraîchir le cache d'état |
| 69 | GET | `/api/v1/reconcile/cache/stats` | JWT | — | Statistiques du cache |

#### connectors.py — préfixe `/api/v1/connectors` (16 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 70 | GET | `/api/v1/connectors/` | JWT | — | Lister les connecteurs |
| 71 | GET | `/api/v1/connectors/types` | JWT | — | Types disponibles + schémas |
| 72 | GET | `/api/v1/connectors/health` | JWT | — | Santé de tous les connecteurs |
| 73 | GET | `/api/v1/connectors/{connector_id}` | JWT | — | Détail d'un connecteur |
| 74 | POST | `/api/v1/connectors/` | JWT | admin | Créer un connecteur |
| 75 | PUT | `/api/v1/connectors/{connector_id}` | JWT | admin | Modifier un connecteur |
| 76 | DELETE | `/api/v1/connectors/{connector_id}` | JWT | admin | Supprimer un connecteur |
| 77 | POST | `/api/v1/connectors/{connector_id}/test` | JWT | — | Tester un connecteur stocké |
| 78 | POST | `/api/v1/connectors/test-preview` | JWT | admin | Tester une config (SSRF-gated) |
| 79 | POST | `/api/v1/connectors/{connector_id}/toggle` | JWT | admin | Activer/désactiver |
| 80 | POST | `/api/v1/connectors/health-check` | JWT | admin | Lancer tous les health checks |
| 81 | POST | `/api/v1/connectors/{connector_id}/sync-to-midpoint` | JWT | admin | Créer/MAJ Resource MidPoint |
| 82 | GET | `/api/v1/connectors/{connector_id}/midpoint-status` | JWT | — | Statut de sync MidPoint |
| 83 | POST | `/api/v1/connectors/{connector_id}/test-midpoint-resource` | JWT | admin | Tester la Resource MidPoint |
| 84 | DELETE | `/api/v1/connectors/{connector_id}/midpoint-resource` | JWT | admin | Supprimer la Resource |
| 85 | GET | `/api/v1/connectors/midpoint/resources` | JWT | — | Lister les Resources MidPoint |

#### scheduler.py — préfixe `/api/v1/scheduler` (14 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 86 | GET | `/api/v1/scheduler/jobs` | JWT | — | Lister les jobs planifiés |
| 87 | GET | `/api/v1/scheduler/jobs/{job_id}` | JWT | — | Détail d'un job |
| 88 | POST | `/api/v1/scheduler/jobs/daily` | JWT | admin, iam_engineer | Créer une sync quotidienne |
| 89 | POST | `/api/v1/scheduler/jobs/interval` | JWT | admin, iam_engineer | Créer une sync par intervalle |
| 90 | POST | `/api/v1/scheduler/jobs/cron` | JWT | admin, iam_engineer | Créer une sync cron |
| 91 | POST | `/api/v1/scheduler/jobs/{job_id}/toggle` | JWT | admin, iam_engineer | Activer/désactiver un job |
| 92 | POST | `/api/v1/scheduler/jobs/{job_id}/run` | JWT | admin, iam_engineer | Exécuter immédiatement |
| 93 | DELETE | `/api/v1/scheduler/jobs/{job_id}` | JWT | admin | Supprimer un job |
| 94 | GET | `/api/v1/scheduler/history` | JWT | — | Historique des synchronisations |
| 95 | POST | `/api/v1/scheduler/presets/workday` | JWT | admin, iam_engineer | Preset jours ouvrés (8/12/18 h) |
| 96 | POST | `/api/v1/scheduler/presets/nightly` | JWT | admin, iam_engineer | Preset nocturne |
| 97 | POST | `/api/v1/scheduler/presets/hourly` | JWT | admin, iam_engineer | Preset horaire |
| 98 | POST | `/api/v1/scheduler/jobs/contract-check` | JWT | admin, iam_engineer | Vérification des contrats |
| 99 | GET | `/api/v1/scheduler/contracts/history` | JWT | — | Historique des vérifications |

#### users.py — préfixe `/api/v1/users` (9 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 100 | GET | `/api/v1/users/` | JWT | admin | Lister les utilisateurs gateway |
| 101 | POST | `/api/v1/users/` | JWT | admin | Créer un utilisateur |
| 102 | GET | `/api/v1/users/roles` | JWT | — | Rôles disponibles |
| 103 | GET | `/api/v1/users/by-role/{role}` | JWT | admin, iam_engineer | Utilisateurs par rôle |
| 104 | GET | `/api/v1/users/emails-by-role/{role}` | JWT | admin, iam_engineer | Emails par rôle |
| 105 | GET | `/api/v1/users/approval-chain/{workflow_type}` | JWT | admin, iam_engineer | Chaîne d'approbation |
| 106 | GET | `/api/v1/users/{username}` | JWT | admin | Détail d'un utilisateur |
| 107 | PUT | `/api/v1/users/{username}/roles` | JWT | admin | Mettre à jour les rôles |
| 108 | DELETE | `/api/v1/users/{username}` | JWT | admin | Désactiver un utilisateur |

#### permissions.py — préfixe `/api/v1/permissions` (6 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 109 | GET | `/api/v1/permissions/levels` | JWT | — | Niveaux de droits (1–5) |
| 110 | GET | `/api/v1/permissions/users` | JWT | — | Utilisateurs et leurs niveaux |
| 111 | GET | `/api/v1/permissions/users/{user_id}` | JWT | — | Droits d'un utilisateur |
| 112 | POST | `/api/v1/permissions/assign` | JWT | admin, iam_engineer | Assigner un niveau |
| 113 | GET | `/api/v1/permissions/stats` | JWT | — | Distribution des niveaux |
| 114 | GET | `/api/v1/permissions/check/{user_id}/{permission}` | JWT | — | Vérifier une permission |

#### live_comparison.py — préfixe `/api/v1/live` (17 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 115 | GET | `/api/v1/live/stats` | JWT | — | Statistiques temps réel |
| 116 | GET | `/api/v1/live/compare` | JWT | admin, iam_engineer | Comparer tous les systèmes |
| 117 | GET | `/api/v1/live/user/{identifier}` | JWT | — | Référence croisée d'un user |
| 118 | POST | `/api/v1/live/sync-user/{identifier}` | JWT | admin, iam_engineer | Synchroniser un user |
| 119 | GET | `/api/v1/live/odoo/contacts` | JWT | — | Contacts Odoo |
| 120 | GET | `/api/v1/live/health-check` | JWT | — | Santé de tous les systèmes |
| 121 | GET | `/api/v1/live/odoo/employees` | JWT | — | Employés Odoo |
| 122 | GET | `/api/v1/live/midpoint/users` | JWT | — | Users MidPoint (comparaison) |
| 123 | GET | `/api/v1/live/sync/odoo-midpoint/compare` | JWT | admin, iam_engineer | Comparer Odoo/MidPoint |
| 124 | POST | `/api/v1/live/sync/odoo-to-midpoint` | JWT | admin, iam_engineer | Sync Odoo→MidPoint |
| 125 | POST | `/api/v1/live/sync/odoo-to-midpoint/with-approval` | JWT | admin, iam_engineer | Sync avec approbation |
| 126 | POST | `/api/v1/live/sync/execute-approved/{workflow_id}` | JWT | admin, it_admin | Exécuter un sync approuvé |
| 127 | POST | `/api/v1/live/account/{username}/disable` | JWT | admin, iam_engineer | Désactiver (multi-systèmes) |
| 128 | POST | `/api/v1/live/account/{username}/enable` | JWT | admin, iam_engineer | Activer (multi-systèmes) |
| 129 | GET | `/api/v1/live/contracts/expired` | JWT | admin, iam_engineer | Contrats expirés |
| 130 | GET | `/api/v1/live/contracts/expiring` | JWT | admin, iam_engineer | Contrats expirants |
| 131 | GET | `/api/v1/live/odoo/employees-with-contracts` | JWT | — | Employés + contrats |

#### ldap_groups.py — préfixe `/api/v1/ldap/groups` (6 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 132 | GET | `/api/v1/ldap/groups` | JWT | — | Lister les groupes LDAP |
| 133 | GET | `/api/v1/ldap/groups/{group_name}` | JWT | — | Détail d'un groupe + membres |
| 134 | POST | `/api/v1/ldap/groups/{group_name}/members` | JWT | admin, iam_engineer | Ajouter un membre |
| 135 | DELETE | `/api/v1/ldap/groups/{group_name}/members/{username}` | JWT | admin, iam_engineer | Retirer un membre |
| 136 | GET | `/api/v1/ldap/groups/users/search` | JWT | — | Recherche d'utilisateurs LDAP |
| 137 | GET | `/api/v1/ldap/groups/user/{username}/memberships` | JWT | — | Groupes d'un utilisateur |

#### ai_assistant.py — préfixe `/api/v1/ai` (9 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 138 | POST | `/api/v1/ai/query` | JWT | — | Question en langage naturel |
| 139 | POST | `/api/v1/ai/suggest-mappings` | JWT | — | Suggestions de mapping |
| 140 | POST | `/api/v1/ai/generate-connector` | JWT | — | Générer un squelette de connecteur |
| 141 | POST | `/api/v1/ai/analyze-error` | JWT | — | Diagnostiquer une erreur |
| 142 | POST | `/api/v1/ai/explain-rule` | JWT | — | Expliquer une règle |
| 143 | GET | `/api/v1/ai/conversations/{conversation_id}` | JWT | — | Historique d'une conversation |
| 144 | DELETE | `/api/v1/ai/conversations/{conversation_id}` | JWT | — | Supprimer une conversation |
| 145 | GET | `/api/v1/ai/config` | JWT | — | Indique si un fournisseur est configuré |
| 146 | POST | `/api/v1/ai/config` | JWT | admin | Configurer le fournisseur IA |

#### webhooks.py — préfixe `/api/v1/webhooks` (3 endpoints)

| # | Méthode | Chemin | Auth | Rôles | Description |
|---|---|---|---|---|---|
| 147 | POST | `/api/v1/webhooks/midpoint/user-change` | HMAC | — | Notification MidPoint → Keycloak |
| 148 | POST | `/api/v1/webhooks/midpoint/sync-all` | JWT | admin | Sync complète manuelle |
| 149 | GET | `/api/v1/webhooks/health` | Public | — | Liveness du webhook |

### Annexe B — Variables d'environnement complètes

Liste exhaustive issue de `.env.example` et de `core/config.py`. « Requis en prod » signifie que l'application refuse de démarrer sans la variable lorsque `DEBUG=false`.

| Variable | Type | Requis en prod | Description | Valeur exemple |
|---|---|---|---|---|
| `DEBUG` | bool | Non | Mode debug (echo SQL, fixture, auto-secret) | `false` |
| `DEV_MODE` | bool | Non | Journalise les emails au lieu de les envoyer | `false` |
| `SECRET_KEY` | str | **Oui** | Secret applicatif (≥ 32 car.) | *(généré)* |
| `JWT_SECRET_KEY` | str | **Oui** | Clé de signature JWT (≥ 32 car.) | *(généré)* |
| `JWT_ALGORITHM` | str | Non | Algorithme JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | int | Non | Durée de vie du jeton | `60` |
| `JWT_ISSUER` | str | Non | Claim `iss` | `iam-gateway` |
| `JWT_AUDIENCE` | str | Non | Claim `aud` | `iam-gateway` |
| `BCRYPT_ROUNDS` | int | Non | Coût bcrypt | `12` |
| `MIDPOINT_WEBHOOK_SECRET` | str | Oui* | Secret HMAC des webhooks | *(secret)* |
| `MIDPOINT_URL` | str | Non | URL REST MidPoint | `http://midpoint-core:8080/midpoint` |
| `MIDPOINT_USER` | str | Non | Admin MidPoint | `administrator` |
| `MIDPOINT_PASSWORD` | str | Non | Mot de passe MidPoint | *(secret)* |
| `MIDPOINT_ENABLED` | bool | Non | Mode hub vs direct | `true` |
| `MIDPOINT_VERIFY_SSL` | bool | Non | Vérification TLS MidPoint | `true` |
| `DATABASE_URL` | str | Non | DSN PostgreSQL (asyncpg) | `postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway` |
| `REDIS_URL` | str | Non | DSN Redis | `redis://redis:6379/0` |
| `QDRANT_HOST` / `QDRANT_PORT` | str/int | Non | Localisation Qdrant | `qdrant` / `6333` |
| `LDAP_HOST` / `LDAP_PORT` | str/int | Non | Serveur LDAP | `openldap` / `389` |
| `LDAP_BIND_DN` | str | Non | Identité de bind | `cn=admin,dc=example,dc=com` |
| `LDAP_BIND_PASSWORD` | str | Non | Mot de passe bind | *(secret)* |
| `LDAP_BASE_DN` | str | Non | Contexte de base | `dc=example,dc=com` |
| `ODOO_URL` / `ODOO_DB` | str | Non | Connexion Odoo | `http://odoo:8069` / `odoo` |
| `ODOO_USER` / `ODOO_PASSWORD` | str | Non | Identifiants Odoo | `admin` / *(secret)* |
| `INTRANET_DB_URL` | str | Non | DSN cible SQL | `postgresql://intranet:intranet@intranet-db:5432/intranet` |
| `KEYCLOAK_URL` / `KEYCLOAK_REALM` | str | Non | Base + realm Keycloak | `http://keycloak:8080` / `gateway` |
| `KEYCLOAK_CLIENT_ID` / `KEYCLOAK_CLIENT_SECRET` | str | Non | Client OIDC | `gateway-client` / *(secret)* |
| `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD` | str | Non | Admin Keycloak | `admin` / *(secret)* |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | str | Non | Fournisseur IA optionnel | *(vide)* / `gpt-4-turbo-preview` |
| `DEEPSEEK_API_KEY` | str | Non | Fournisseur IA alternatif | *(vide)* |
| `SMTP_HOST` / `SMTP_PORT` | str/int | Non | Serveur d'envoi d'emails | `smtp.gmail.com` / `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | str | Non | Identifiants SMTP | *(secret)* |
| `FROM_EMAIL` | str | Non | Expéditeur | `noreply@iam-gateway.local` |
| `BASE_URL` | str | Non | URL publique pour les liens email | `http://localhost:8000` |
| `WORKFLOW_DEFAULT_TIMEOUT_HOURS` | int | Non | Délai par défaut des workflows | `72` |
| `WORKFLOW_MAX_LEVELS` | int | Non | Niveaux max d'approbation | `5` |
| `LOG_LEVEL` | str | Non | Niveau de log | `INFO` |
| `CORS_ORIGINS` | list | Non | Origines navigateur autorisées | `["http://localhost:3000"]` |

\* `MIDPOINT_WEBHOOK_SECRET` : le webhook échoue *closed* (503) sans secret en production ; en DEBUG la vérification est contournée.

### Annexe C — Inventaire des dépendances Python

Issu de `requirements.txt` (runtime) et `requirements-dev.txt` (développement/CI).

| Package | Version | Rôle dans le projet |
|---|---|---|
| `fastapi` | ≥ 0.109.0 | Framework web asynchrone, cœur de l'API |
| `uvicorn[standard]` | ≥ 0.27.0 | Serveur ASGI exécutant l'application |
| `python-multipart` | — | Parsing des formulaires (login OAuth2) |
| `python-jose[cryptography]` | — | Création et vérification des JWT |
| `bcrypt` | — | Hachage des mots de passe |
| `httpx` | — | Client HTTP asynchrone (MidPoint, Keycloak) |
| `sqlalchemy` | ≥ 2.0.0 | ORM / moteur de base asynchrone |
| `sqlmodel` | — | Modèles ORM typés (couche models) |
| `asyncpg` | — | Pilote PostgreSQL asynchrone |
| `psycopg2-binary` | — | Pilote PostgreSQL synchrone (migrations) |
| `redis` | — | Client Redis (blacklist, rate-limit, cache) |
| `ldap3` | — | Connecteur LDAP |
| `pyyaml` | — | Lecture de configurations YAML |
| `jinja2` | — | Moteur de templates (règles sandboxées) |
| `jsonschema` | — | Validation de schémas de connecteurs |
| `openai` | — | Client IA optionnel |
| `qdrant-client` | — | Client base vectorielle Qdrant |
| `pydantic` | ≥ 2.0.0 | Validation des données (modèles) |
| `pydantic-settings` | — | Configuration typée par environnement |
| `email-validator` | — | Validation des adresses email |
| `structlog` | — | Journalisation structurée JSON |
| `apscheduler` | ≥ 3.10.0 | Ordonnanceur de tâches périodiques |
| `python-dotenv` | — | Chargement du fichier `.env` |
| `pytest` | ≥ 8.0.0 | Framework de test (dev) |
| `pytest-asyncio` | ≥ 0.23.0 | Support des tests asynchrones (dev) |
| `ruff` | ≥ 0.5.0 | Linter Python rapide (dev/CI) |
| `pip-audit` | ≥ 2.7.0 | Audit de vulnérabilités des dépendances (dev/CI) |

### Annexe D — Commandes de référence

**Workflow Git.**
```bash
git checkout -b feature/ma-fonctionnalite     # créer une branche
git add -p && git commit -m "type(scope): …"  # commit conventionnel
git push origin feature/ma-fonctionnalite     # pousser
gh pr create --base main --fill               # ouvrir une PR
gh pr edit <N> --base main                    # rebasculer la base (stacked PR)
git log --oneline --graph --all               # visualiser l'historique
```

**Docker Compose.**
```bash
docker compose up gateway gateway-db redis --build   # stack minimale
docker compose up --build                            # stack complète
docker compose ps                                    # état + santé
docker compose logs -f gateway                       # journaux en direct
docker compose restart gateway                       # redémarrer un service
docker compose down                                  # arrêt (volumes conservés)
docker compose down -v                               # arrêt DESTRUCTIF (volumes supprimés)
```

**Tests (pytest).**
```bash
cd gateway
pip install -r requirements-dev.txt
pytest tests/ -v                  # suite complète, verbeuse
pytest tests/ -v --tb=short       # traceback court
pytest tests/test_security.py -v  # un seul fichier
```

**Génération de secrets.**
```bash
python -c "import secrets; print(secrets.token_hex(32))"      # 64 caractères hex
python -c "import secrets; print(secrets.token_urlsafe(48))"  # variante url-safe
```

**Inspection base de données.**
```bash
docker compose exec gateway-db psql -U gateway -d gateway -c "\dt"      # lister les tables
docker compose exec gateway-db psql -U gateway -d gateway -c "SELECT username, role FROM gateway_users;"
docker compose exec -T gateway python -m app.db.migrations             # rejouer les migrations
docker compose exec redis redis-cli KEYS 'blacklist:*'                 # jetons révoqués
```

**Inspection des journaux et de la santé.**
```bash
curl http://localhost:8000/health                    # santé de la gateway
docker compose logs --tail=100 gateway | grep ERROR  # erreurs récentes
docker stats --no-stream                             # consommation par conteneur
```

### Annexe E — Glossaire IAM

| Terme | Définition |
|---|---|
| **IAM** | *Identity and Access Management* — gestion des identités et des accès. |
| **IGA** | *Identity Governance and Administration* — gouvernance des identités (rôles, recertification, workflows). |
| **RBAC** | *Role-Based Access Control* — contrôle d'accès fondé sur les rôles. |
| **ABAC** | *Attribute-Based Access Control* — contrôle d'accès fondé sur les attributs. |
| **JML** | *Joiner / Mover / Leaver* — cycle de vie d'une identité (arrivée, mobilité, départ). |
| **Provisioning** | Création/mise à jour des comptes et droits dans les systèmes cibles. |
| **Deprovisioning** | Désactivation/suppression des accès lors d'un départ ou d'un changement. |
| **Réconciliation** | Comparaison entre l'état attendu (hub) et l'état réel (cibles) pour détecter les écarts. |
| **Shadow** | Projection d'une identité MidPoint dans une ressource (le compte réel côté LDAP/Odoo/SQL). |
| **Resource** | (MidPoint) Système cible connecté au hub et provisionné par lui. |
| **Role** | (MidPoint) Ensemble de droits/constructions dont l'assignation déclenche le provisionnement. |
| **Assignment** | Lien entre une identité et un rôle ou un compte cible. |
| **Connector** | Adaptateur traduisant les opérations IAM vers un protocole cible (REST, LDAP, XML-RPC, SQL). |
| **Workflow** | Processus d'approbation encadrant une opération sensible. |
| **Approval Chain** | Chaîne d'approbateurs successifs (ex. Manager → RH → IT). |
| **Recertification** | Revue périodique des droits par les responsables pour confirmer leur légitimité. |
| **Orphan Account** | Compte resté actif après le départ de son titulaire — risque de sécurité majeur. |
| **Over-provisioning** | Accumulation de droits excédentaires (*privilege creep*). |
| **Least Privilege** | Principe du moindre privilège : n'accorder que les droits strictement nécessaires. |
| **Audit Trail** | Piste d'audit : journal horodaté et traçable de toutes les actions. |
| **LDAP** | *Lightweight Directory Access Protocol* — protocole d'annuaire (comptes, groupes). |
| **SCIM** | *System for Cross-domain Identity Management* — standard de provisionnement par API REST. |
| **SAML** | *Security Assertion Markup Language* — standard d'authentification fédérée (SSO). |
| **OIDC** | *OpenID Connect* — couche d'identité au-dessus d'OAuth2 (rôle de Keycloak). |
| **SSO** | *Single Sign-On* — authentification unique sur plusieurs applications. |
| **JWT** | *JSON Web Token* — jeton signé porteur des revendications d'authentification. |
| **HMAC** | *Hash-based Message Authentication Code* — signature à clé partagée (authentifie le webhook). |
| **SSRF** | *Server-Side Request Forgery* — falsification de requête côté serveur. |
| **CORS** | *Cross-Origin Resource Sharing* — politique d'origines autorisées côté navigateur. |
| **TTL** | *Time To Live* — durée de vie d'une donnée (clé Redis, jeton). |

---

### Annexe F — Récapitulatif et vérification

Cette annexe synthétise les indicateurs vérifiables du projet et la structure du présent document.

**Indicateurs mesurés sur le dépôt (révision `50d2bc6`).**

| Indicateur | Valeur | Méthode de mesure |
|---|---|---|
| Endpoints REST | 149 | décompte des décorateurs `@router.<méthode>` dans `app/api/*.py` |
| Routeurs | 14 | nombre de fichiers de routeurs montés dans `main.py` |
| Services Docker | 14 | services déclarés dans `docker-compose.yml` |
| Réseaux Docker | 1 | `iam-network` (bridge) |
| Volumes nommés | 13 | section `volumes` du compose |
| Fichiers Python | 82 | `git ls-files '*.py'` |
| Lignes de Python | 27 406 | `wc -l` sur les fichiers Python suivis |
| Fichiers TS/TSX (frontend) | 25 | `git ls-files '*.ts' '*.tsx'` |
| Fonctions de test | 13 | décompte des `def test_` dans `tests/` |
| Tables PostgreSQL (migrations) | 24 | `CREATE TABLE` dans `db/migrations.py` |
| Commits (branche `main`) | 54 | `git rev-list --count HEAD` |
| Vulnérabilités corrigées | 13 | commits de la branche `security-hardening` |

**Couverture sectorielle du document.** Les dix sections principales et les annexes couvrent l'intégralité du périmètre demandé : introduction et contexte (§1), architecture technique (§2), fonctionnalités (§3, la plus développée, avec douze sous-sections), audit de sécurité exhaustif des 13 vulnérabilités (§4), qualité et DevOps (§5), modèle de données (§6), infrastructure Docker (§7), difficultés rencontrées sous forme de récits (§8), limites et perspectives (§9), conclusion (§10), et six annexes de référence (endpoints exhaustifs, variables d'environnement, dépendances, commandes, glossaire, et ce récapitulatif).

**Méthode rédactionnelle.** Chaque affirmation technique est fondée sur la lecture directe des fichiers source du dépôt : routeurs, connecteurs, services, modèles, migrations, tests, configuration CI et `docker-compose.yml`. Les extraits de code reproduisent le code réel (ou, pour les motifs « avant correction » de §4.2, reconstituent fidèlement le motif vulnérable). Les tableaux emploient les valeurs effectives relevées dans les fichiers. Le document a été rédigé en prose développée, conformément à l'exigence, chaque sous-section combinant explication, code et tableaux plutôt que de simples listes.

### Annexe G — Schémas de configuration des connecteurs

Les schémas JSON ci-dessous (extraits de `models/connector.py`, dictionnaire `CONNECTOR_CONFIG_SCHEMAS`) pilotent la génération dynamique des formulaires de configuration dans l'interface. Les champs `format: "password"` sont masqués dans les réponses API.

**PostgreSQL (sous-type `postgresql`).**
```json
{
  "type": "object",
  "required": ["host", "port", "database", "username", "password"],
  "properties": {
    "host": {"type": "string", "default": "localhost"},
    "port": {"type": "integer", "default": 5432},
    "database": {"type": "string"},
    "username": {"type": "string"},
    "password": {"type": "string", "format": "password"},
    "ssl_mode": {"type": "string", "enum": ["disable", "allow", "prefer", "require"], "default": "prefer"}
  }
}
```

**OpenLDAP (sous-type `openldap`).**
```json
{
  "type": "object",
  "required": ["host", "port", "bind_dn", "bind_password", "base_dn"],
  "properties": {
    "host": {"type": "string", "default": "localhost"},
    "port": {"type": "integer", "default": 389},
    "bind_dn": {"type": "string", "placeholder": "cn=admin,dc=example,dc=com"},
    "bind_password": {"type": "string", "format": "password"},
    "base_dn": {"type": "string", "placeholder": "dc=example,dc=com"},
    "use_ssl": {"type": "boolean", "default": false},
    "users_ou": {"type": "string", "default": "ou=users"},
    "groups_ou": {"type": "string", "default": "ou=groups"}
  }
}
```

**Keycloak (sous-type `keycloak`).**
```json
{
  "type": "object",
  "required": ["server_url", "realm", "client_id", "client_secret"],
  "properties": {
    "server_url": {"type": "string", "format": "uri"},
    "realm": {"type": "string", "default": "master"},
    "client_id": {"type": "string"},
    "client_secret": {"type": "string", "format": "password"},
    "verify_ssl": {"type": "boolean", "default": true}
  }
}
```

**Odoo (sous-type `odoo`).**
```json
{
  "type": "object",
  "required": ["url", "database", "username", "password"],
  "properties": {
    "url": {"type": "string", "format": "uri", "placeholder": "http://odoo:8069"},
    "database": {"type": "string"},
    "username": {"type": "string"},
    "password": {"type": "string", "format": "password"},
    "timeout": {"type": "integer", "default": 30}
  }
}
```

**REST générique (sous-type `generic_rest`).**
```json
{
  "type": "object",
  "required": ["base_url", "auth_type"],
  "properties": {
    "base_url": {"type": "string", "format": "uri"},
    "auth_type": {"type": "string", "enum": ["none", "basic", "bearer", "api_key"], "default": "none"},
    "api_key": {"type": "string", "format": "password"},
    "api_key_header": {"type": "string", "default": "X-API-Key"},
    "bearer_token": {"type": "string", "format": "password"},
    "verify_ssl": {"type": "boolean", "default": true}
  }
}
```

Ces schémas illustrent la philosophie *no-code* poussée jusqu'à la configuration des connecteurs : l'interface génère automatiquement le formulaire adéquat à partir du schéma, valide les entrées contre lui, et masque les champs sensibles — sans qu'aucun code spécifique d'interface ne soit nécessaire par sous-type.

### Annexe H — Extrait du docker-compose.yml (service gateway)

L'extrait suivant montre la définition du service central et de sa base, illustrant les conventions décrites en §7 (dépendances conditionnées, sondes de santé, limites mémoire, liaison `127.0.0.1`, injection de secrets par `${VAR:-}`).

```yaml
  gateway:
    build: { context: ./gateway, dockerfile: Dockerfile }
    container_name: gateway-iam
    mem_limit: 768m
    depends_on:
      gateway-db: { condition: service_healthy }
      redis: { condition: service_healthy }
      qdrant: { condition: service_started }
    environment:
      DEBUG: "${DEBUG:-true}"
      SECRET_KEY: ${SECRET_KEY:-}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-}
      DATABASE_URL: postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway
      REDIS_URL: redis://redis:6379/0
      MIDPOINT_URL: http://midpoint-core:8080/midpoint
      MIDPOINT_WEBHOOK_SECRET: ${MIDPOINT_WEBHOOK_SECRET:-}
    ports: ["8000:8000"]
    volumes: ["./gateway/app:/app/app", "gateway_logs:/app/logs"]
    networks: [iam-network]
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode()==200 else 1)"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 40s
    restart: unless-stopped

  gateway-db:
    image: postgres:15
    ports: ["127.0.0.1:5434:5432"]      # lié à l'hôte local uniquement
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gateway"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes: ["gateway_db_data:/var/lib/postgresql/data"]
    restart: unless-stopped
```

On y retrouve la limite mémoire de 768 Mio, les trois dépendances conditionnées par l'état de santé, l'injection des secrets depuis le `.env` (sans valeur en dur), la sonde HTTP `/health` avec sa période de grâce de 40 secondes, et la liaison de la base à `127.0.0.1` — soit l'application concrète des principes de sécurité et de résilience exposés tout au long de ce rapport.

---

> **Note de fidélité documentaire.** Ce rapport décrit l'architecture réellement déployée à la révision `50d2bc6`. Conformément à l'exigence d'exactitude, deux points sont explicitement signalés : (1) la plateforme **n'utilise pas MongoDB** — sa persistance repose sur PostgreSQL, Redis et Qdrant ; (2) la « recherche sémantique » Qdrant repose actuellement sur une vectorisation **déterministe par hachage** (128 dimensions) et non sur un modèle d'embedding par apprentissage, ce dernier constituant un point d'évolution identifié (§6.5). Toutes les valeurs chiffrées (149 endpoints, 14 services, 13 tests, 82 fichiers Python, 27 406 lignes, 54 commits) sont mesurées sur le dépôt.

*Rapport de réalisation — Plateforme IAM Gateway — SAE S5/S6, BUT Informatique, UPEC / Laboratoire LISSI. Co-auteur référencé : `achibani@gmail.com`. Révision `50d2bc6`, juin 2026.*







