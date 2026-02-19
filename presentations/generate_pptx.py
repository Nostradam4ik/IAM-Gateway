#!/usr/bin/env python3
"""
Script to generate PowerPoint presentation for IAM Gateway UPEC project
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Pt
import os

def rgb(r, g, b):
    """Create an RGBColor from r,g,b values."""
    from pptx.util import Emu
    from pptx.dml.color import RGBColor
    return RGBColor(r, g, b)

# Colors
DARK_BLUE = rgb(26, 26, 46)
MEDIUM_BLUE = rgb(50, 130, 184)
LIGHT_BLUE = rgb(187, 225, 250)
WHITE = rgb(255, 255, 255)
GREEN = rgb(76, 175, 80)
ORANGE = rgb(255, 152, 0)
RED = rgb(244, 67, 54)

def add_title_slide(prs, title, subtitle, authors, university):
    """Add title slide"""
    slide_layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(slide_layout)

    # Background
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.fill.solid()
    background.fill.fore_color.rgb = DARK_BLUE
    background.line.fill.background()

    # Logos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_iut = os.path.join(script_dir, "cropped-Logo-INFO-FOND-BLANC.jpg")
    logo_lissi = os.path.join(script_dir, "Lissi-cmjn.png")
    if os.path.exists(logo_iut):
        slide.shapes.add_picture(logo_iut, Inches(0.5), Inches(0.3), height=Inches(1.2))
    if os.path.exists(logo_lissi):
        slide.shapes.add_picture(logo_lissi, Inches(6), Inches(0.3), height=Inches(1))

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(1))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = LIGHT_BLUE
    p.alignment = PP_ALIGN.CENTER

    # Subtitle
    sub_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.5), Inches(9), Inches(0.5))
    tf = sub_box.text_frame
    p = tf.paragraphs[0]
    p.text = subtitle
    p.font.size = Pt(24)
    p.font.color.rgb = MEDIUM_BLUE
    p.alignment = PP_ALIGN.CENTER

    # Authors
    auth_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.5), Inches(9), Inches(0.5))
    tf = auth_box.text_frame
    p = tf.paragraphs[0]
    p.text = authors
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    # University
    uni_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.2), Inches(9), Inches(1))
    tf = uni_box.text_frame
    for line in university.split('\n'):
        p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(16)
        p.font.color.rgb = rgb(136, 136, 136)
        p.alignment = PP_ALIGN.CENTER

def add_content_slide(prs, title, content_left, content_right=None, image_path=None):
    """Add a content slide with title and content"""
    slide_layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(slide_layout)

    # Background
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.fill.solid()
    background.fill.fore_color.rgb = DARK_BLUE
    background.line.fill.background()

    # Top accent line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.05))
    line.fill.solid()
    line.fill.fore_color.rgb = MEDIUM_BLUE
    line.line.fill.background()

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(8), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = LIGHT_BLUE

    # Content left
    if content_right or image_path:
        left_width = Inches(4.5)
    else:
        left_width = Inches(9)

    content_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), left_width, Inches(5))
    tf = content_box.text_frame
    tf.word_wrap = True

    for item in content_left:
        p = tf.add_paragraph()
        if item.startswith('##'):
            p.text = item[2:].strip()
            p.font.size = Pt(20)
            p.font.bold = True
            p.font.color.rgb = MEDIUM_BLUE
            p.space_before = Pt(12)
        elif item.startswith('-'):
            p.text = item
            p.font.size = Pt(16)
            p.font.color.rgb = WHITE
            p.level = 1
        else:
            p.text = item
            p.font.size = Pt(18)
            p.font.color.rgb = WHITE

    # Content right or image
    if image_path and os.path.exists(image_path):
        slide.shapes.add_picture(image_path, Inches(5.2), Inches(1.2), width=Inches(4.5))
    elif content_right:
        right_box = slide.shapes.add_textbox(Inches(5.2), Inches(1.2), Inches(4.3), Inches(5))
        tf = right_box.text_frame
        tf.word_wrap = True
        for item in content_right:
            p = tf.add_paragraph()
            if item.startswith('##'):
                p.text = item[2:].strip()
                p.font.size = Pt(20)
                p.font.bold = True
                p.font.color.rgb = MEDIUM_BLUE
            else:
                p.text = item
                p.font.size = Pt(16)
                p.font.color.rgb = WHITE

def add_table_slide(prs, title, headers, rows):
    """Add a slide with a table"""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Background
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.fill.solid()
    background.fill.fore_color.rgb = DARK_BLUE
    background.line.fill.background()

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.7))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = LIGHT_BLUE

    # Table
    cols = len(headers)
    table = slide.shapes.add_table(len(rows) + 1, cols, Inches(0.5), Inches(1.2), Inches(9), Inches(0.5 * (len(rows) + 1))).table

    # Headers
    for i, header in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = header
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(15, 76, 117)
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(14)
        p.font.color.rgb = WHITE

    # Rows
    for row_idx, row in enumerate(rows):
        for col_idx, cell_text in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = str(cell_text)
            if row_idx % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(30, 45, 70)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(26, 26, 46)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(12)
            p.font.color.rgb = WHITE

def create_presentation():
    """Create the full presentation"""
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title
    add_title_slide(
        prs,
        "Plateforme No-Code & Gateway IAM",
        "Orchestration intelligente des identites multi-systemes",
        "Equipe MOE: Zhmuryk Andrii & Aydin Ibrahim",
        "Product Owner & Architecture: M. CHIBANI\nBUT Informatique 3eme annee - UPEC\nIUT Creteil-Vitry | Laboratoire LISSI\nNEXUS AI Innovation Lab - Fevrier 2026"
    )

    # Slide 2: Problematique
    add_content_slide(prs, "Problematique", [
        "## Le probleme de la gestion des identites",
        "",
        "## Situation actuelle",
        "- Active Directory / LDAP (authentification)",
        "- ERP Odoo, SAP (gestion RH)",
        "- Applications metier (bases SQL)",
        "- Services Cloud (Keycloak, OAuth)",
        "",
        "## 1 employe = 5 a 10 comptes differents",
    ], [
        "## Problemes rencontres",
        "- Creation manuelle = erreurs + temps",
        "- Depart employe = comptes oublies",
        "- Aucune tracabilite",
        "- Failles de securite",
        "",
        "## Statistiques",
        "- 30% des violations liees aux comptes orphelins",
        "- 4h pour creer tous les acces d'un employe",
    ])

    # Slide 3: Solution
    add_content_slide(prs, "Notre Solution - Innovation", [
        "## Gateway IAM: Orchestration Intelligente",
        "",
        "## 1. Interface No-Code",
        "- MidPoint est puissant MAIS complexe",
        "- Notre solution: simple, visuelle, accessible",
        "",
        "## 2. Automatisation",
        "- Regles dynamiques en YAML",
        "- Calcul automatique (login, email)",
        "- Workflows d'approbation multi-niveaux",
        "",
        "## 3. Centralisation",
        "- Un seul point d'entree",
        "- Vue temps reel",
        "- Reconciliation automatique",
    ], [
        "",
        "",
        "## Innovation cle",
        "",
        "Rendre l'IAM accessible a tous,",
        "pas seulement aux experts MidPoint",
    ])

    # Slide 4: Backlog 1
    add_table_slide(prs, "Backlog - Epic 1: Gestion Utilisateurs",
        ["User Story", "Priorite", "Points"],
        [
            ["Creer un utilisateur dans tous les systemes", "Must", "8"],
            ["Modifier les attributs d'un utilisateur", "Must", "5"],
            ["Desactiver/supprimer un compte", "Must", "5"],
            ["Voir l'historique des modifications", "Should", "3"],
        ]
    )

    # Slide 5: Backlog 2
    add_table_slide(prs, "Backlog - Epic 4: Connecteurs",
        ["User Story", "Priorite", "Points"],
        [
            ["Connecteur LDAP (OpenLDAP, AD)", "Must", "8"],
            ["Connecteur Odoo (ERP)", "Must", "8"],
            ["Connecteur SQL (PostgreSQL)", "Must", "5"],
            ["Connecteur MidPoint (REST API)", "Must", "13"],
            ["Connecteur Keycloak (OIDC)", "Should", "8"],
        ]
    )

    # Slide 6: Architecture
    add_content_slide(prs, "Architecture Globale", [
        "## Architecture 3-tiers",
        "",
        "UTILISATEUR (Navigateur)",
        "        |",
        "        v",
        "FRONTEND REACT (Port 3000)",
        "TypeScript + Tailwind CSS + Vite",
        "        |",
        "        v",
        "GATEWAY API (FastAPI - Port 8000)",
        "Rule Engine | Workflow Mgr | AI Assistant",
        "        |",
        "        v",
        "CONNECTOR LAYER",
        "MidPoint | LDAP | Odoo | SQL | Keycloak",
    ])

    # Slide 7: Architecture Technique
    add_table_slide(prs, "Architecture Technique - 14 Services Docker",
        ["Service", "Technologie", "Port"],
        [
            ["gateway", "FastAPI/Python", "8000"],
            ["gateway-frontend", "React/TypeScript", "3000"],
            ["midpoint", "MidPoint 4.4", "8080"],
            ["openldap", "OpenLDAP", "10389"],
            ["odoo", "Odoo 17", "8069"],
            ["keycloak", "Keycloak 23", "8081"],
            ["redis", "Redis 7", "6379"],
            ["qdrant", "Qdrant (Vector DB)", "6333"],
        ]
    )

    # Slide 8: Stack Technologique
    add_content_slide(prs, "Stack Technologique", [
        "## Backend (Python)",
        "- FastAPI 0.109",
        "- SQLModel (ORM)",
        "- JWT + OAuth2",
        "- ldap3 (LDAP)",
        "- APScheduler",
        "- OpenAI API",
    ], [
        "## Frontend (TypeScript)",
        "- React 18 + Vite",
        "- React Router v6",
        "- Zustand (state)",
        "- Tailwind CSS",
        "- Lucide (icons)",
        "- Axios (HTTP)",
    ])

    # Slide 9: Dashboard
    add_content_slide(prs, "Fonctionnalites - Dashboard (100%)", [
        "## Dashboard Principal",
        "- Vue d'ensemble en temps reel",
        "- Statistiques cles",
        "- Etat de sante des connecteurs",
        "- Graphiques de performance",
        "- Alertes et notifications",
        "",
        "## Endpoints API",
        "GET /api/v1/admin/status",
        "GET /api/v1/admin/metrics",
        "GET /api/v1/connectors/health",
    ], image_path="/app/presentations/screenshots/dashboard.png")

    # Slide 10: Provisioning
    add_content_slide(prs, "Fonctionnalites - Provisioning (100%)", [
        "## Gestion des Operations",
        "- Creation utilisateur multi-systeme",
        "- Modification des attributs",
        "- Suppression/desactivation",
        "- Rollback des operations",
        "- Suivi statut temps reel",
        "",
        "## Systemes cibles",
        "- LDAP (comptes + groupes)",
        "- Odoo (res.users)",
        "- PostgreSQL (tables custom)",
        "- MidPoint (utilisateurs, roles)",
    ], [
        "## Workflow type",
        "",
        "1. Creation demande",
        "2. Validation regles",
        "3. Workflow approbation",
        "4. Execution multi-systeme",
        "5. Audit & notification",
    ])

    # Slide 11: Regles
    add_content_slide(prs, "Fonctionnalites - Moteur de Regles (100%)", [
        "## Regles Dynamiques",
        "- Definition en YAML/JSON",
        "- Expressions Jinja2 sandboxees",
        "- Filtres integres (normalize_name)",
        "- Test avec donnees fictives",
        "- Versionnage",
        "",
        "## Cas d'usage",
        "- Generation automatique de login",
        "- Calcul email selon departement",
        "- Attribution groupes selon poste",
    ], [
        "## Exemple de regle",
        "",
        "target_system: LDAP",
        "rule_type: MAPPING",
        "definition: |",
        "  {%- set login = ... -%}",
        "  {",
        '    "uid": "{{ login }}",',
        '    "mail": "{{ login }}@ex.com"',
        "  }",
    ])

    # Slide 12: Workflows
    add_content_slide(prs, "Fonctionnalites - Workflows (100%)", [
        "## Workflows d'Approbation",
        "- Configuration multi-niveaux (5)",
        "- Approbation/rejet avec commentaires",
        "- Timeout configurable (72h)",
        "- Notifications email",
        "- Historique des decisions",
    ], [
        "## Niveaux type",
        "",
        "Niveau 1: Manager direct",
        "Niveau 2: Chef departement",
        "Niveau 3: Proprietaire app",
        "Niveau 4: RSSI (si sensible)",
        "",
        "[EXECUTION]",
    ])

    # Slide 13: Groupes LDAP
    add_content_slide(prs, "Fonctionnalites - Groupes LDAP (100%)", [
        "## Gestion des Groupes LDAP",
        "- Liste de tous les groupes",
        "- Visualisation des membres",
        "- Ajout avec autocomplete",
        "- Suppression de membres",
        "- Support groupOfUniqueNames",
        "",
        "## Interface",
        "- Recherche temps reel",
        "- Autocompletion intelligente",
        "- Filtrage OIDs MidPoint",
    ], image_path="/app/presentations/screenshots/ldap-groups.png")

    # Slide 14: Comparaison Live
    add_content_slide(prs, "Fonctionnalites - Comparaison Live (100%)", [
        "## Comparaison Temps Reel",
        "- Statistiques live par systeme",
        "- Comparaison croisee",
        "- Detection des ecarts",
        "- Sync Odoo -> MidPoint",
        "- Planification des syncs",
        "",
        "## Metriques",
        "- Utilisateurs par systeme",
        "- Utilisateurs communs vs orphelins",
        "- Etat derniere sync",
    ], image_path="/app/presentations/screenshots/comparaison-live.png")

    # Slide 15: Audit & IA
    add_content_slide(prs, "Fonctionnalites - Audit & IA (100%)", [
        "## Audit & Logs",
        "- Logging structure (JSON)",
        "- Recherche full-text",
        "- Recherche semantique (Qdrant)",
        "- Filtrage par date, type",
        "- Export des rapports",
    ], [
        "## Assistant IA",
        "- Chat avec GPT-4",
        "- Suggestions de regles",
        "- Aide au diagnostic",
        "- Generation code connecteur",
    ])

    # Slide 16: Fonctionnalites Partielles
    add_table_slide(prs, "Fonctionnalites Partiellement Implementees",
        ["Fonctionnalite", "Progression", "Reste a faire"],
        [
            ["Integration Keycloak", "70%", "Sync groupes, mapping roles"],
            ["Notifications Email", "50%", "Templates HTML"],
            ["Recherche Vectorielle", "80%", "Refresh embeddings"],
            ["Rollback Complet", "60%", "Nettoyage etats"],
            ["Versionnage Git Regles", "40%", "Integration Git"],
            ["Multi-langue UI", "100%", "FR, EN, UK (i18next)"],
        ]
    )

    # Slide 17: A Implementer
    add_content_slide(prs, "Fonctionnalites a Implementer", [
        "## Priorite Haute (Should)",
        "- Deploiement Kubernetes (8 pts)",
        "- Masquage donnees PII (3 pts)",
        "- Migration Alembic (5 pts)",
        "",
        "## Priorite Moyenne (Could)",
        "- Connecteur Firebase (8 pts)",
        "- Connecteur GLPI (5 pts)",
        "- Detection SoD (8 pts)",
        "- App Mobile (21 pts)",
    ], [
        "## Won't (cette version)",
        "- Multi-tenancy",
        "- MFA Biometrique",
        "- Machine Learning",
        "",
        "## Estimation restante",
        "~60 points",
        "= 3 sprints supplementaires",
    ])

    # Slide 18: Difficultes 1
    add_content_slide(prs, "Difficultes Rencontrees (1/2)", [
        "## 1. Complexite de MidPoint",
        "Probleme: XML complexe, concepts avances",
        "Solution: Abstraction via API REST",
        "",
        "## 2. Transactions Distribuees",
        "Probleme: 1 operation = 4 systemes",
        "Solution: Pattern Saga avec compensations",
    ], [
        "## 3. Securite Moteur Regles",
        "Probleme: Jinja2 peut executer du code",
        "Solution: SandboxedEnvironment",
        "",
        "## 4. Synchronisation Temps Reel",
        "Probleme: Coherence eventuelle",
        "Solution: Cache invalidation + polling",
    ])

    # Slide 19: Difficultes 2
    add_content_slide(prs, "Difficultes Rencontrees (2/2)", [
        "## 5. Mapping Attributs LDAP",
        "Probleme: Schemas differents",
        "Solution: Config mappings par connecteur",
        "",
        "## 6. Couts & Latence IA",
        "Probleme: OpenAI = $$ + latence",
        "Solution: Cache, rate limiting",
    ], [
        "## 7. Gestion des Secrets",
        "Probleme: 20+ variables sensibles",
        "Solution: .env + validation demarrage",
        "",
        "## 8. Tests d'Integration",
        "Probleme: 15 services = complexe",
        "Solution: Mocks + env dedie",
    ])

    # Slide 20: Apprentissages
    add_content_slide(prs, "Ce que nous avons appris", [
        "## Competences Techniques",
        "- Architecture microservices",
        "- API REST avec FastAPI",
        "- React moderne (hooks)",
        "- Docker & orchestration",
        "- Securite (JWT, RBAC)",
    ], [
        "## Concepts IAM",
        "- Provisionnement identites",
        "- Reconciliation",
        "- Workflows approbation",
        "- Audit et conformite",
        "- RBAC / ABAC",
        "- SSO / OIDC",
    ])

    # Slide 21: Video Demo
    add_content_slide(prs, "Demonstration Video", [
        "## Scenario 1: Creation Employe (5 min)",
        "1. Creation dans Odoo (RH)",
        "2. Synchronisation vers MidPoint",
        "3. Attribution role 'Employe Complet'",
        "4. Verification compte LDAP",
        "5. Ajout a un groupe LDAP",
        "",
        "## Scenario 2: Gestion Regles (3 min)",
        "1. Visualisation regles existantes",
        "2. Test regle avec donnees",
        "3. Modification d'une regle",
    ], [
        "## Scenario 3: Workflow (3 min)",
        "1. Demande compte sensible",
        "2. Notification manager",
        "3. Approbation avec commentaire",
        "4. Execution automatique",
        "",
        "## Scenario 4: Reconciliation (2 min)",
        "1. Comparaison live systemes",
        "2. Detection compte orphelin",
        "3. Resolution",
    ])

    # Slide 22: Roadmap
    add_content_slide(prs, "Roadmap Future", [
        "## Court terme (1-2 mois)",
        "- Finaliser Keycloak",
        "- Templates email",
        "- Tests automatises",
        "",
        "## Moyen terme (3-6 mois)",
        "- Deploiement Kubernetes",
        "- Azure AD connector",
        "- Google Workspace",
    ], [
        "## Long terme (6-12 mois)",
        "- Application mobile",
        "- Machine Learning",
        "- Multi-tenancy SaaS",
        "",
        "## Vision",
        "Plateforme IAM No-Code complete",
        "accessible aux PME",
    ])

    # Slide 23: Conclusion
    add_content_slide(prs, "Conclusion", [
        "## Ce que nous avons realise",
        "Objectif: Simplifier MidPoint",
        "Resultat: 12+ fonctionnalites operationnelles",
        "",
        "## Chiffres cles",
        "- 16,000+ lignes Python (Backend)",
        "- 5,000+ lignes TypeScript (Frontend)",
        "- 14 services Docker orchestres",
        "- 80+ endpoints API REST",
        "- 6 connecteurs (LDAP, SQL, Odoo, MidPoint, Keycloak, CSV)",
        "- 15 pages Frontend",
        "- 3 langues (FR, EN, UK)",
    ], [
        "",
        "",
        "",
        "## Merci de votre attention!",
        "",
        "Questions?",
    ])

    # Slide 24: Annexes
    add_content_slide(prs, "Annexes - Ressources", [
        "## Acces au projet",
        "- GitHub: github.com/NEXUS-AI-Innovation-lab/IAM-Gateway",
        "- Documentation: docs/GUIDE_DEVELOPPEUR.md",
        "- Video demo: [Lien video]",
        "",
        "## Technologies",
        "- MidPoint: evolveum.com/midpoint/",
        "- FastAPI: fastapi.tiangolo.com",
        "- React: react.dev",
    ], [
        "## Contact",
        "- Zhmuryk Andrii: andrijzmurik@gmail.com",
        "- Aydin Ibrahim",
        "",
        "## Remerciements",
        "- PO & Architecture: M. CHIBANI",
        "- IUT Creteil-Vitry - Dept. Informatique",
        "- Laboratoire LISSI - UPEC",
        "- Communaute Open Source",
    ])

    # Save
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "IAM_Gateway_UPEC.pptx")
    prs.save(output_path)
    print(f"Presentation saved to {output_path}")
    return output_path

if __name__ == "__main__":
    create_presentation()
