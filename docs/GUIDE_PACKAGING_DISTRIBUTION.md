# Guide de packaging et distribution — IAM-Gateway

**Application web full-stack (FastAPI + React) · méthodes de packaging et de distribution**

| | |
|---|---|
| **Projet** | IAM-Gateway — SAÉ « Projet 3 » |
| **Formation** | BUT Informatique, 3ᵉ année — UPEC |
| **Type de document** | Guide de packaging et de distribution |
| **Public visé** | Développeur souhaitant distribuer/déployer l'application |
| **Auteurs** | Zhmuryk Andrii · Aydin Ibrahim |
| **Co-auteur (livrables générés)** | achibani@gmail.com |

> ℹ️ **Périmètre.** IAM-Gateway est une **application web full-stack** : un backend FastAPI (Python) et un frontend React servi par Nginx, le tout orchestré par Docker Compose sur Linux. **Il n'existe pas d'application mobile native.** Ce guide présente les méthodes de packaging réellement applicables à ce type de projet, du format de distribution officiel (Docker) jusqu'aux options de « wrapping » mobile/desktop (PWA, Capacitor, Electron) et leurs limites pour un outil d'administration.

---

## Table des matières

1. [Packaging de l'application web existante](#1-packaging-de-lapplication-web-existante)
2. [Progressive Web App (PWA)](#2-progressive-web-app-pwa)
3. [Packaging APK via Capacitor](#3-packaging-apk-via-capacitor)
4. [Packaging via Electron (desktop)](#4-packaging-via-electron-desktop)
5. [Tableau comparatif des méthodes](#5-tableau-comparatif-des-méthodes)
6. [Recommandation pour IAM-Gateway](#6-recommandation-pour-iam-gateway)

---

# 1. Packaging de l'application web existante

C'est le mode de distribution **officiel et recommandé** du projet. Il repose sur trois artefacts complémentaires : le build statique du frontend, les images Docker de production, et l'archive de distribution complète.

## 1.1 Build de production du frontend React

Le frontend utilise **Vite** (et non Create React App). Le script `build` réalise d'abord une vérification de types TypeScript (`tsc`) puis génère le bundle optimisé via Vite :

```json
// gateway/frontend/package.json (extrait)
"scripts": {
  "dev": "vite",
  "build": "tsc && vite build",
  "preview": "vite preview"
}
```

```bash
cd gateway/frontend

# Installer les dépendances
npm install

# Build de production → génère le dossier dist/
npm run build

# (Optionnel) Prévisualiser le build localement sur un port statique
npm run preview
```

### Contenu du dossier `dist/`

Vite produit un dossier **`dist/`** (équivalent du `build/` de CRA) contenant des fichiers statiques prêts à être servis par n'importe quel serveur web :

```
dist/
├── index.html              # Point d'entrée HTML (références hachées vers les assets)
├── assets/
│   ├── index-<hash>.js      # Bundle JS minifié (hash de contenu pour le cache-busting)
│   ├── index-<hash>.css     # Styles compilés (Tailwind purgé)
│   └── <chunks>-<hash>.js   # Chunks de code-splitting (ex. Monaco editor)
└── vite.svg / favicons      # Ressources statiques
```

### Optimisations appliquées automatiquement par Vite

| Optimisation | Effet |
|---|---|
| **Minification** (esbuild) | JS/CSS compressés, suppression des espaces et commentaires. |
| **Tree-shaking** | Élimination du code mort / imports inutilisés. |
| **Code-splitting** | Découpage en *chunks* chargés à la demande (utile pour Monaco Editor, lourd). |
| **Hachage de contenu** | Noms de fichiers `index-<hash>.js` → invalidation de cache fiable à chaque déploiement. |
| **Purge Tailwind** | Le CSS ne contient que les classes réellement utilisées. |

### Variables d'environnement de production (`VITE_`)

⚠️ **Avec Vite, seules les variables préfixées par `VITE_`** sont exposées au code client (et non `REACT_APP_` propre à CRA). Elles sont **injectées au moment du build**, pas à l'exécution.

```bash
# gateway/frontend/.env.production (exemple)
VITE_API_BASE_URL=https://iam.example.com/api
```

```ts
// Utilisation dans le code (ex. src/lib/api.ts)
const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";
```

> ⚠️ **Ne jamais mettre de secret dans une variable `VITE_`** : tout ce qui est préfixé `VITE_` se retrouve **en clair** dans le bundle JavaScript livré au navigateur. Les secrets (clés API, mots de passe) restent côté backend.

## 1.2 Image Docker de production

Le frontend dispose déjà d'un **Dockerfile multi-stage** : une étape Node compile le bundle, une étape Nginx ne conserve que les fichiers statiques (image finale légère, sans Node ni code source).

```dockerfile
# gateway/frontend/Dockerfile (réel)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build                 # produit /app/dist

FROM nginx:alpine                 # image finale minimale
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Le backend possède lui aussi son Dockerfile (`python:3.11-slim`, utilisateur non-root, healthcheck `/health`, lancé via `uvicorn`).

### Construire les images

```bash
# Depuis la racine du dépôt

# Image frontend (tag explicite + version)
docker build -t iam-gateway-frontend:latest -t iam-gateway-frontend:1.0.0 \
  ./gateway/frontend

# Image backend
docker build -t iam-gateway-backend:latest -t iam-gateway-backend:1.0.0 \
  ./gateway

# Vérifier
docker images | grep iam-gateway
```

> ℹ️ En pratique, `docker compose build` construit déjà ces deux images via le `docker-compose.yml`. Le `docker build` manuel ci-dessus est utile pour **tagger** et **exporter** des images destinées à un autre serveur.

### Exporter une image en archive `.tar` portable (`docker save`)

Pour transférer une image sur un serveur **sans registre Docker** (ni Internet) :

```bash
# Exporter une ou plusieurs images dans une archive compressée
docker save iam-gateway-frontend:1.0.0 iam-gateway-backend:1.0.0 \
  | gzip > iam-gateway-images-1.0.0.tar.gz

# Vérifier la taille
ls -lh iam-gateway-images-1.0.0.tar.gz
```

### Importer l'image sur un autre serveur (`docker load`)

```bash
# Transférer l'archive (ex. via scp) puis sur le serveur cible :
scp iam-gateway-images-1.0.0.tar.gz user@serveur:/opt/iam-gateway/

# Sur le serveur cible : charger les images dans Docker
gunzip -c iam-gateway-images-1.0.0.tar.gz | docker load

# ✅ Vérifier que les images sont présentes
docker images | grep iam-gateway
```

✅ **Succès** : `docker images` liste `iam-gateway-frontend` et `iam-gateway-backend`. Le `docker-compose.yml` peut alors référencer ces images (`image:` au lieu de `build:`) pour démarrer sans recompiler.

> ℹ️ **Alternative avec registre.** Si un registre est disponible (Docker Hub, GitHub Container Registry, registre privé), préférez `docker push` / `docker pull` à `save`/`load` — plus simple à automatiser en CI/CD.

## 1.3 Archive ZIP de distribution

Pour livrer le projet « clé en main » à déployer sur un serveur Linux, on crée une archive contenant **uniquement les fichiers nécessaires au déploiement** (pas le code compilé ni les `node_modules`).

### Contenu type d'un package de distribution

```
iam-gateway-dist/
├── docker-compose.yml              # Orchestration des 15 services
├── .env.example                    # Modèle de configuration (à copier en .env)
├── start.sh                        # Script de démarrage par étapes
├── scripts/
│   └── init-db.sh                  # Initialisation de la base gateway
├── infrastructure/
│   ├── sql/init-intranet.sql       # Init auto de la base intranet
│   └── midpoint/                   # Ressources/rôles MidPoint à importer
├── README.md                       # Présentation du projet
└── docs/
    ├── GUIDE_INSTALLATION_DEPLOIEMENT.md
    └── GUIDE_PACKAGING_DISTRIBUTION.md
```

### Créer l'archive

Deux variantes selon que les images sont reconstruites sur place ou fournies préconstruites.

```bash
# Variante A — archive "sources" (le serveur cible reconstruira les images)
#   On inclut le code source frontend/backend mais on exclut les artefacts lourds.
tar czf iam-gateway-1.0.0.tar.gz \
  --exclude='node_modules' \
  --exclude='dist' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='.env' \
  docker-compose.yml .env.example start.sh scripts/ infrastructure/ \
  gateway/ README.md docs/

# Variante B — format .zip (compatibilité Windows / partage simple)
zip -r iam-gateway-1.0.0.zip \
  docker-compose.yml .env.example start.sh scripts/ infrastructure/ \
  gateway/ README.md docs/ \
  -x '*/node_modules/*' '*/dist/*' '*/__pycache__/*' '*.git*' '.env'
```

> ⚠️ **N'incluez jamais le fichier `.env` réel** (secrets) dans l'archive. Seul `.env.example` doit être distribué.

### Déployer depuis l'archive sur un nouveau serveur Linux

```bash
# 1. Transférer et extraire
scp iam-gateway-1.0.0.tar.gz user@serveur:/opt/
ssh user@serveur
cd /opt && tar xzf iam-gateway-1.0.0.tar.gz && cd iam-gateway-*

# 2. Configurer l'environnement
cp .env.example .env
# → éditer .env : générer SECRET_KEY, JWT_SECRET_KEY, mots de passe... (voir guide d'installation)

# 3. Démarrer la pile
./start.sh

# 4. Initialiser la base gateway (une seule fois)
./scripts/init-db.sh

# ✅ Vérifier
curl -s http://localhost:8000/health
```

> ℹ️ Si vous avez aussi livré les images via `docker save`/`load` (§1.2), le `./start.sh` les réutilisera sans reconstruction. Sinon, le premier démarrage **construira** les images localement (Node + Python requis dans Docker, ce qui est le cas).

---

# 2. Progressive Web App (PWA)

## 2.1 Qu'est-ce qu'une PWA et pourquoi c'est adapté ici

Une **Progressive Web App** est une application web qui, grâce à un *manifest* et un *service worker*, peut être **installée** sur l'écran d'accueil (mobile ou desktop), lancée en plein écran comme une app native, et offrir un **fonctionnement hors ligne basique** (mise en cache des assets). 

Pour IAM-Gateway, la PWA est la voie **la plus pertinente** pour un usage « mobile » : elle ne nécessite **aucun store**, aucun build natif, et réutilise directement le frontend Vite existant. Un administrateur peut « installer » la console sur son téléphone ou son poste en un clic depuis le navigateur.

## 2.2 Ajouter le manifest et le service worker

La méthode la plus simple avec Vite est le plugin `vite-plugin-pwa`, qui génère automatiquement le service worker (basé sur Workbox) et le manifest.

```bash
cd gateway/frontend
npm install -D vite-plugin-pwa
```

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt'],
      manifest: {
        name: 'IAM-Gateway Admin',
        short_name: 'IAM-Gateway',
        description: "Console d'administration IAM-Gateway",
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      workbox: {
        // Met en cache les assets statiques générés par le build
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}']
      }
    })
  ]
})
```

```bash
# Préparer les icônes (192px, 512px, 512px maskable)
mkdir -p public/icons
# → placer icon-192.png, icon-512.png, icon-512-maskable.png

# Rebuild : le service worker (sw.js) et le manifest sont générés dans dist/
npm run build
```

> ⚠️ **HTTPS obligatoire.** Un service worker ne s'enregistre **que** sur une origine sécurisée (HTTPS) — ou `localhost` en développement. La PWA ne fonctionnera donc en production qu'avec le reverse proxy TLS décrit dans le guide d'installation.

## 2.3 Installation sur Android / iOS

**Android (Chrome) :**
> *Description visuelle :* en visitant `https://iam.example.com`, une bannière « Ajouter à l'écran d'accueil » apparaît, ou via le menu ⋮ → **« Installer l'application »**. Une icône IAM-Gateway est ajoutée à l'écran d'accueil ; au lancement, l'app s'ouvre en plein écran sans barre d'adresse.

**iOS (Safari) :**
> *Description visuelle :* bouton **Partager** (carré avec flèche) → **« Sur l'écran d'accueil »** → *Ajouter*. L'icône apparaît sur l'écran d'accueil. (iOS impose Safari pour l'installation PWA et limite certaines fonctionnalités hors ligne.)

**Desktop (Chrome/Edge) :**
> *Description visuelle :* une icône d'installation (⊕ ou écran avec flèche) apparaît à droite de la barre d'adresse → **Installer**. L'app s'ouvre dans sa propre fenêtre.

## 2.4 Fonctionnement hors ligne basique

Le service worker met en cache la coquille applicative (HTML, JS, CSS, icônes). Conséquences :

- ✅ Le **chargement de l'interface** fonctionne hors ligne (la « coquille » s'affiche instantanément).
- ⚠️ Les **données** (opérations, audit, workflows) proviennent de l'API backend : **sans réseau, aucune donnée live**. Un écran « hors ligne » ou les dernières données mises en cache (si stratégie configurée) peuvent être affichés.

> ℹ️ Pour un outil d'administration IAM, le hors-ligne complet n'a guère de sens (toute action écrit dans des systèmes distants). La valeur de la PWA ici est surtout l'**installabilité** et le **démarrage rapide**, pas l'usage déconnecté.

## 2.5 Vérification avec Lighthouse

```
Chrome DevTools (F12) → onglet "Lighthouse" → cocher "Progressive Web App" → "Analyze page load"
```

> *Description visuelle :* Lighthouse produit un rapport avec une section **PWA** ; les critères « Installable » (manifest + service worker + HTTPS) et « PWA Optimized » doivent être au vert. Les points rouges indiquent ce qui manque (icône maskable, `theme_color`, etc.).

✅ **Succès** : tous les critères « Installable » sont validés et le bouton d'installation apparaît dans le navigateur.

---

# 3. Packaging APK via Capacitor

## 3.1 Pourquoi Capacitor

**Capacitor** (de l'équipe Ionic) est la meilleure option pour « emballer » une application web React dans une application Android native : il crée un projet Android natif contenant une **WebView** qui affiche le frontend, avec accès aux API natives si besoin. Contrairement à React Native, **aucune réécriture** n'est nécessaire — on réutilise le build web tel quel.

> ⚠️ **Limitation fondamentale.** L'APP généré est un **wrapper** : il affiche le frontend qui appelle l'API backend. **Il faut donc un serveur backend joignable** (réseau, URL configurée). Sans backend actif et accessible, l'APK n'affiche qu'une interface vide ou en erreur. Ce n'est pas une application autonome.

## 3.2 Prérequis

| Prérequis | Version / note |
|---|---|
| Node.js | 18+ (déjà requis par le projet) |
| **JDK** | **17** (requis par le plugin Android Gradle récent) |
| **Android Studio** | Hedgehog ou + (inclut le SDK Android et l'émulateur) |
| **Android SDK** | API 33+ (via le SDK Manager d'Android Studio) |
| Variables d'env | `JAVA_HOME`, `ANDROID_HOME` correctement définies |

## 3.3 Étapes complètes

```bash
cd gateway/frontend

# 1. Installer Capacitor (core, CLI, plateforme Android)
npm install @capacitor/core
npm install -D @capacitor/cli
npm install @capacitor/android

# 2. Initialiser Capacitor
#    appName : "IAM-Gateway" | appId : identifiant inversé unique
#    webDir  : dossier du build Vite = "dist"
npx cap init "IAM-Gateway" "fr.upec.iamgateway" --web-dir=dist
```

> ℹ️ Vérifiez dans `capacitor.config.ts` que `webDir` vaut bien **`dist`** (sortie de Vite). Pour pointer vers un backend distant, configurez aussi `server.url` (voir §3.6).

```bash
# 3. Construire le frontend web
npm run build

# 4. Ajouter la plateforme Android (crée le dossier android/)
npx cap add android

# 5. Copier le build web dans le projet Android
npx cap copy android

# 6. (Après chaque modif web) synchroniser build + plugins natifs
npx cap sync android

# 7. Ouvrir le projet dans Android Studio
npx cap open android
```

## 3.4 Build de l'APK depuis Android Studio

> *Description visuelle :* dans Android Studio, menu **Build → Generate Signed Bundle / APK… → APK**. Un assistant demande de créer ou sélectionner un **keystore** (clé de signature), puis le type de build (`release`). À la fin, une notification « locate » mène au fichier `.apk` signé. Pour un test rapide non signé : **Build → Build Bundle(s) / APK(s) → Build APK(s)**.

## 3.5 Build en ligne de commande

```bash
cd gateway/frontend/android

# APK de debug (non signé, pour tests)
./gradlew assembleDebug

# Récupérer l'APK généré
ls app/build/outputs/apk/debug/app-debug.apk

# APK de release (nécessite un keystore configuré dans build.gradle)
./gradlew assembleRelease
```

✅ **Succès** : le fichier `app/build/outputs/apk/debug/app-debug.apk` est généré et installable sur un appareil Android (`adb install app-debug.apk`).

## 3.6 Configuration de l'URL backend

L'app doit savoir où joindre l'API. Deux approches :

```ts
// capacitor.config.ts — pointer la WebView vers un backend distant
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'fr.upec.iamgateway',
  appName: 'IAM-Gateway',
  webDir: 'dist',
  server: {
    // L'app chargera directement le frontend servi par le serveur,
    // OU le bundle local appellera cette API via VITE_API_BASE_URL.
    url: 'https://iam.example.com',
    cleartext: false
  }
};
export default config;
```

> ⚠️ **Sécurité :** une WebView qui pointe vers un backend distant impose **HTTPS** (le trafic en clair `cleartext` est bloqué par défaut sur Android récent). Prévoyez aussi la configuration CORS côté backend et des *redirect URIs* Keycloak adaptés.

---

# 4. Packaging via Electron (desktop)

## 4.1 Pourquoi Electron

**Electron** empaquette une application web dans un exécutable **desktop autonome** (Windows `.exe`, Linux `.AppImage`/`.deb`, macOS `.dmg`) en embarquant Chromium + Node.js. Pour IAM-Gateway, cela permet de livrer la console d'administration comme une application de bureau « double-clic », sans navigateur visible.

> ⚠️ Comme Capacitor, Electron **n'embarque que le frontend** : l'application desktop reste un client qui appelle l'API backend. Le serveur FastAPI doit être joignable.

## 4.2 Configuration minimale avec electron-builder

```bash
# Dans un sous-projet (ex. gateway/frontend/electron) ou à la racine du frontend
npm install -D electron electron-builder
```

```js
// electron/main.js — fenêtre Electron chargeant le frontend
const { app, BrowserWindow } = require('electron');

function createWindow() {
  const win = new BrowserWindow({
    width: 1280, height: 800,
    webPreferences: { contextIsolation: true }
  });
  // Option A : charger le build local (dist/index.html)
  win.loadFile('dist/index.html');
  // Option B : charger le frontend servi à distance
  // win.loadURL('https://iam.example.com');
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
```

```json
// package.json — extrait de configuration electron-builder
{
  "main": "electron/main.js",
  "scripts": {
    "electron:build": "npm run build && electron-builder"
  },
  "build": {
    "appId": "fr.upec.iamgateway",
    "productName": "IAM-Gateway",
    "files": ["dist/**/*", "electron/**/*"],
    "linux": { "target": ["AppImage", "deb"], "category": "Utility" },
    "win":   { "target": ["nsis"] }
  }
}
```

## 4.3 Commandes de build (Linux)

```bash
cd gateway/frontend

# Build web + packaging desktop
npm run electron:build

# Cibler explicitement Linux (.AppImage et .deb)
npx electron-builder --linux AppImage deb

# Résultats dans dist/ (ou release/ selon config) :
#   IAM-Gateway-1.0.0.AppImage   → exécutable portable
#   iam-gateway_1.0.0_amd64.deb  → paquet Debian/Ubuntu
ls dist/*.AppImage dist/*.deb
```

```bash
# Installation du .deb
sudo dpkg -i iam-gateway_1.0.0_amd64.deb

# Ou lancement direct de l'AppImage (aucune installation requise)
chmod +x IAM-Gateway-1.0.0.AppImage
./IAM-Gateway-1.0.0.AppImage
```

✅ **Succès** : une fenêtre desktop autonome affiche la console IAM-Gateway, qui dialogue avec l'API backend configurée.

---

# 5. Tableau comparatif des méthodes

| Méthode | Format | OS / plateforme cible | Complexité | Backend requis | Adapté au projet |
|---|---|---|---|---|---|
| **Image Docker** | `.tar` (`docker save`) ou registre | Linux / macOS / Windows (Docker) | Faible | — (c'est le backend) | ✅ **Recommandé (officiel)** |
| **Archive ZIP/TAR** | `.zip` / `.tar.gz` | Tout (déploiement serveur) | Très faible | — | ✅ Simple, portable |
| **PWA** | Service worker + manifest (web) | Android / iOS / Desktop (navigateur) | Moyenne | Oui (API live) | ✅ Mobile sans installation native |
| **Capacitor APK** | `.apk` | Android | Élevée | **Oui** (serveur actif) | ⚠️ Wrapper WebView |
| **Electron** | `.AppImage` / `.deb` / `.exe` | Linux / Windows / macOS | Moyenne | **Oui** (serveur actif) | ⚠️ Client desktop |

**Lecture du tableau :**
- ✅ Les deux premières méthodes packagent **l'application réelle** (backend + frontend) → distribution complète et autonome côté serveur.
- ✅ La PWA répond au besoin « mobile » **sans store ni build natif**, en réutilisant le frontend tel quel.
- ⚠️ Capacitor et Electron ne packagent **que le frontend** : ce sont des clients d'un backend qui doit rester déployé et accessible. Ils ajoutent de la complexité (toolchain native, signature) sans rendre l'app autonome.

---

# 6. Recommandation pour IAM-Gateway

## 6.1 Pourquoi le web/Docker plutôt qu'une app mobile

IAM-Gateway est un **outil d'administration des identités et des accès**. Son public cible est constitué d'**administrateurs IT, ingénieurs IAM et approbateurs** (managers, RH) qui travaillent depuis un **poste de travail**, sur un réseau d'entreprise, avec des écrans larges (édition de règles Jinja2 dans Monaco, tableaux d'audit, comparaisons live, workflows). Ce profil d'usage **n'est pas mobile-first**.

De plus, plusieurs caractéristiques du produit rendent une app mobile native **inadaptée, voire risquée** :

- **Aucune logique métier côté client** : toutes les opérations (provisionnement, réconciliation, approbations) s'exécutent côté serveur et nécessitent une connexion à MidPoint et aux systèmes cibles. Un APK/Electron ne ferait qu'afficher l'interface — il n'apporte aucune autonomie.
- **Surface d'attaque** : distribuer une console d'administration IAM sous forme d'APK installable élargit inutilement la surface d'exposition. Un outil d'admin sensible se protège mieux derrière un reverse proxy HTTPS, du SSO et un réseau maîtrisé que sur des terminaux mobiles personnels.
- **Maintenance** : maintenir des builds natifs (signature, stores, compatibilité SDK) représente un coût sans valeur ajoutée fonctionnelle pour cet outil.

## 6.2 Stratégie de distribution retenue

| Besoin | Solution recommandée |
|---|---|
| **Distribution officielle / déploiement serveur** | **Images Docker + archive de distribution** (§1). Format reproductible, versionné, portable d'un serveur à l'autre. |
| **Accès mobile occasionnel** (consultation, approbation d'un workflow) | **PWA** (§2) : installable depuis le navigateur, sans store, réutilise le frontend existant, sécurisée par HTTPS. |
| **Confort desktop** (optionnel) | Electron (§4) **uniquement si** un réel besoin d'app de bureau émerge — sinon le navigateur suffit. |
| **APK natif** | **Non recommandé** pour un outil d'administration IAM (voir §6.1). À réserver à un cas d'usage spécifique et maîtrisé. |

## 6.3 Conclusion

> ✅ **Le format de distribution officiel d'IAM-Gateway est le packaging Docker** (images + Docker Compose), complété par une **archive de distribution** pour le déploiement clé en main. La **PWA** couvre élégamment le besoin d'accès mobile sans installation native. Les approches **Capacitor (APK)** et **Electron** restent des options de « wrapping » documentées ici par exhaustivité, mais elles n'apportent pas d'autonomie réelle (le backend doit toujours être déployé) et ne sont **pas recommandées** comme mode de distribution principal pour un outil d'administration IAM.

---

*Document généré dans le cadre de la SAÉ Projet 3 — BUT Informatique 3ᵉ année, UPEC.*
*Auteurs : Zhmuryk Andrii, Aydin Ibrahim. Co-auteur des livrables : achibani@gmail.com.*
