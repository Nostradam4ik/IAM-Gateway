"""
Service d'envoi d'emails pour les notifications de workflow.
Supporte l'envoi d'emails via SMTP ou simulation en mode dev.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import structlog
import secrets
import hashlib
from datetime import datetime, timedelta

from app.core.config import settings

logger = structlog.get_logger()


class EmailService:
    """Service d'envoi d'emails pour les notifications."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.base_url = settings.BASE_URL
        self.dev_mode = settings.DEV_MODE

        logger.info(
            "EmailService initialized",
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            smtp_user=self.smtp_user[:3] + "***" if self.smtp_user else "not set",
            dev_mode=self.dev_mode
        )

    def _generate_approval_token(self, workflow_id: str, approver_email: str) -> str:
        """
        Genere un token securise pour l'approbation par email.
        Le token est base sur:
        - L'ID du workflow
        - L'email de l'approbateur
        - Un secret aleatoire
        - Un timestamp
        """
        secret = secrets.token_urlsafe(32)
        timestamp = datetime.utcnow().isoformat()

        # Hash pour verification
        data = f"{workflow_id}:{approver_email}:{secret}:{timestamp}"
        token_hash = hashlib.sha256(data.encode()).hexdigest()[:32]

        # Token final: combine secret + hash (permet verification et securite)
        return f"{secret[:16]}{token_hash}"

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envoie un email via SMTP.
        En mode dev, affiche l'email dans les logs au lieu de l'envoyer.
        """
        if self.dev_mode:
            logger.info(
                "EMAIL (DEV MODE - non envoye)",
                to=to_email,
                subject=subject,
                preview=text_content[:200] if text_content else html_content[:200]
            )
            print("\n" + "="*60)
            print(f"EMAIL NOTIFICATION (Mode Dev)")
            print("="*60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print("-"*60)
            print(text_content or html_content)
            print("="*60 + "\n")
            return True

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())

            logger.info("Email sent successfully", to=to_email, subject=subject)
            return True

        except Exception as e:
            logger.error("Failed to send email", error=str(e), to=to_email)
            return False

    async def send_approval_request(
        self,
        workflow_id: str,
        approver_email: str,
        user_data: Dict[str, Any],
        requester: str
    ) -> Dict[str, Any]:
        """
        Envoie une demande d'approbation par email au manager.
        Retourne le token genere pour l'approbation.
        """
        # Generer les tokens pour approve/reject
        approve_token = self._generate_approval_token(workflow_id, approver_email)
        reject_token = self._generate_approval_token(workflow_id, approver_email)

        # URLs d'approbation
        approve_url = f"{self.base_url}/api/v1/workflow/approve-by-email?token={approve_token}&workflow_id={workflow_id}&action=approve"
        reject_url = f"{self.base_url}/api/v1/workflow/approve-by-email?token={reject_token}&workflow_id={workflow_id}&action=reject"
        dashboard_url = f"{self.base_url}/dashboard/workflows"

        # Extraire les infos utilisateur
        firstname = user_data.get('firstname', 'N/A')
        lastname = user_data.get('lastname', 'N/A')
        email = user_data.get('email', 'N/A')
        department = user_data.get('department', 'N/A')
        account_id = user_data.get('account_id', 'N/A')
        permission_level = user_data.get('permission_level', 'N/A')

        subject = f"[IAM Gateway] Demande d'approbation - Nouveau compte: {firstname} {lastname}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
        .user-info {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e2e8f0; }}
        .user-info table {{ width: 100%; border-collapse: collapse; }}
        .user-info td {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; }}
        .user-info td:first-child {{ font-weight: bold; color: #64748b; width: 40%; }}
        .buttons {{ text-align: center; margin: 25px 0; }}
        .btn {{ display: inline-block; padding: 12px 30px; margin: 0 10px; border-radius: 6px; text-decoration: none; font-weight: bold; }}
        .btn-approve {{ background: #22c55e; color: white; }}
        .btn-reject {{ background: #ef4444; color: white; }}
        .btn-dashboard {{ background: #3b82f6; color: white; margin-top: 15px; }}
        .footer {{ text-align: center; padding: 20px; color: #64748b; font-size: 12px; }}
        .warning {{ background: #fef3c7; border: 1px solid #f59e0b; padding: 10px; border-radius: 6px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">Demande d'Approbation</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">IAM Gateway - Provisionnement</p>
        </div>

        <div class="content">
            <p>Bonjour,</p>

            <p><strong>{requester}</strong> a soumis une demande de creation de compte qui necessite votre approbation.</p>

            <div class="user-info">
                <h3 style="margin-top: 0; color: #1e40af;">Informations du nouvel utilisateur</h3>
                <table>
                    <tr><td>Nom complet</td><td>{firstname} {lastname}</td></tr>
                    <tr><td>Identifiant</td><td><code>{account_id}</code></td></tr>
                    <tr><td>Email</td><td>{email}</td></tr>
                    <tr><td>Departement</td><td>{department}</td></tr>
                    <tr><td>Niveau de droits</td><td>Niveau {permission_level}</td></tr>
                </table>
            </div>

            <div class="warning">
                <strong>Important:</strong> En approuvant cette demande, vous autorisez la creation de ce compte dans les systemes cibles (LDAP, SQL, etc.).
            </div>

            <div class="buttons">
                <a href="{approve_url}" class="btn btn-approve">Approuver</a>
                <a href="{reject_url}" class="btn btn-reject">Rejeter</a>
                <br><br>
                <a href="{dashboard_url}" class="btn btn-dashboard">Voir dans le tableau de bord</a>
            </div>

            <p style="color: #64748b; font-size: 14px;">
                Vous pouvez egalement vous connecter a l'interface IAM Gateway pour gerer cette demande avec des commentaires detailles.
            </p>
        </div>

        <div class="footer">
            <p>Ce message a ete envoye automatiquement par IAM Gateway.</p>
            <p>ID Workflow: {workflow_id}</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
DEMANDE D'APPROBATION - IAM Gateway
====================================

Bonjour,

{requester} a soumis une demande de creation de compte qui necessite votre approbation.

INFORMATIONS DU NOUVEL UTILISATEUR:
- Nom complet: {firstname} {lastname}
- Identifiant: {account_id}
- Email: {email}
- Departement: {department}
- Niveau de droits: Niveau {permission_level}

ACTIONS:
- Pour APPROUVER: {approve_url}
- Pour REJETER: {reject_url}

Vous pouvez aussi vous connecter a l'interface IAM Gateway:
{dashboard_url}

---
ID Workflow: {workflow_id}
Ce message a ete envoye automatiquement par IAM Gateway.
"""

        success = self._send_email(
            to_email=approver_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        return {
            "sent": success,
            "approve_token": approve_token,
            "reject_token": reject_token,
            "workflow_id": workflow_id,
            "approver_email": approver_email
        }

    async def send_approval_notification(
        self,
        user_email: str,
        user_data: Dict[str, Any],
        approved: bool,
        approver: str,
        comments: Optional[str] = None
    ) -> bool:
        """
        Notifie le demandeur du resultat de l'approbation.
        """
        firstname = user_data.get('firstname', 'Utilisateur')
        lastname = user_data.get('lastname', '')
        account_id = user_data.get('account_id', 'N/A')

        status = "approuve" if approved else "rejete"
        status_color = "#22c55e" if approved else "#ef4444"

        subject = f"[IAM Gateway] Compte {status}: {firstname} {lastname}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .status-box {{ background: {status_color}; color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .content {{ background: #f8fafc; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status-box">
            <h1 style="margin: 0;">Compte {status.upper()}</h1>
        </div>
        <div class="content">
            <p>Bonjour,</p>
            <p>La demande de creation de compte pour <strong>{firstname} {lastname}</strong> (identifiant: {account_id}) a ete <strong>{status}</strong> par {approver}.</p>
            {f'<p><strong>Commentaires:</strong> {comments}</p>' if comments else ''}
            {'<p>Le compte a ete cree avec succes dans les systemes cibles.</p>' if approved else '<p>Veuillez contacter votre responsable pour plus d informations.</p>'}
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
COMPTE {status.upper()} - IAM Gateway
=====================================

La demande de creation de compte pour {firstname} {lastname} (identifiant: {account_id}) a ete {status} par {approver}.

{f'Commentaires: {comments}' if comments else ''}

{'Le compte a ete cree avec succes dans les systemes cibles.' if approved else 'Veuillez contacter votre responsable pour plus d informations.'}
"""

        return self._send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    async def send_multilevel_approval_request(
        self,
        workflow_id: str,
        approver_email: str,
        user_data: Dict[str, Any],
        requester: str,
        level: int,
        level_name: str,
        total_levels: int
    ) -> Dict[str, Any]:
        """
        Envoie une demande d'approbation pour un niveau specifique du workflow multi-niveaux.
        """
        # Generer les tokens pour approve/reject
        approve_token = self._generate_approval_token(workflow_id, approver_email)
        reject_token = self._generate_approval_token(workflow_id, approver_email)

        # URLs d'approbation
        approve_url = f"{self.base_url}/api/v1/workflow/approve-by-email?token={approve_token}&workflow_id={workflow_id}&action=approve"
        reject_url = f"{self.base_url}/api/v1/workflow/approve-by-email?token={reject_token}&workflow_id={workflow_id}&action=reject"
        dashboard_url = f"{self.base_url}/dashboard/workflows"

        # Extraire les infos utilisateur
        firstname = user_data.get('firstname', 'N/A')
        lastname = user_data.get('lastname', 'N/A')
        email = user_data.get('email', 'N/A')
        department = user_data.get('department', 'N/A')
        account_id = user_data.get('account_id', 'N/A')
        permission_level = user_data.get('permission_level', 'N/A')
        job_title = user_data.get('job_title', 'N/A')

        # Couleurs selon le niveau
        level_colors = {
            1: {"bg": "#3b82f6", "accent": "#1d4ed8"},  # Bleu - Manager
            2: {"bg": "#8b5cf6", "accent": "#6d28d9"},  # Violet - RH
            3: {"bg": "#10b981", "accent": "#047857"},  # Vert - IT Admin
        }
        colors = level_colors.get(level, level_colors[1])

        # Icones selon le niveau
        level_icons = {
            1: "👤",  # Manager
            2: "📋",  # RH
            3: "🔧",  # IT Admin
        }
        level_icon = level_icons.get(level, "📝")

        subject = f"[IAM Gateway] {level_icon} Approbation Niveau {level}/{total_levels} - {level_name}: {firstname} {lastname}"

        # Barre de progression
        progress_html = ""
        for i in range(1, total_levels + 1):
            if i < level:
                status_class = "completed"
                status_text = "✓"
            elif i == level:
                status_class = "current"
                status_text = str(i)
            else:
                status_class = "pending"
                status_text = str(i)
            progress_html += f'<div class="step {status_class}">{status_text}</div>'

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, {colors['bg']} 0%, {colors['accent']} 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .level-badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; font-size: 14px; margin-top: 10px; }}
        .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
        .progress-bar {{ display: flex; justify-content: center; gap: 10px; margin: 20px 0; padding: 15px; background: white; border-radius: 8px; }}
        .step {{ width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }}
        .step.completed {{ background: #22c55e; color: white; }}
        .step.current {{ background: {colors['bg']}; color: white; box-shadow: 0 0 0 4px {colors['bg']}33; }}
        .step.pending {{ background: #e2e8f0; color: #64748b; }}
        .user-info {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e2e8f0; }}
        .user-info table {{ width: 100%; border-collapse: collapse; }}
        .user-info td {{ padding: 8px 0; border-bottom: 1px solid #f1f5f9; }}
        .user-info td:first-child {{ font-weight: bold; color: #64748b; width: 40%; }}
        .buttons {{ text-align: center; margin: 25px 0; }}
        .btn {{ display: inline-block; padding: 14px 35px; margin: 0 10px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; }}
        .btn-approve {{ background: #22c55e; color: white; }}
        .btn-reject {{ background: #ef4444; color: white; }}
        .btn-dashboard {{ background: {colors['bg']}; color: white; margin-top: 15px; }}
        .footer {{ text-align: center; padding: 20px; color: #64748b; font-size: 12px; }}
        .warning {{ background: #fef3c7; border: 1px solid #f59e0b; padding: 10px; border-radius: 6px; margin: 15px 0; }}
        .level-info {{ background: {colors['bg']}11; border-left: 4px solid {colors['bg']}; padding: 12px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">{level_icon} Demande d'Approbation</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">IAM Gateway - Provisionnement</p>
            <div class="level-badge">Niveau {level}/{total_levels}: {level_name}</div>
        </div>

        <div class="content">
            <div class="progress-bar">
                {progress_html}
            </div>

            <p>Bonjour,</p>

            <p><strong>{requester}</strong> a soumis une demande de creation de compte qui necessite votre approbation en tant que <strong>{level_name}</strong>.</p>

            <div class="level-info">
                <strong>Votre role dans ce workflow:</strong><br>
                Vous etes l'approbateur du <strong>niveau {level}</strong> sur {total_levels}.
                {'Ce niveau a deja ete approuve par le(s) niveau(x) precedent(s).' if level > 1 else 'Vous etes le premier approbateur de cette demande.'}
            </div>

            <div class="user-info">
                <h3 style="margin-top: 0; color: {colors['accent']};">Informations du nouvel utilisateur</h3>
                <table>
                    <tr><td>Nom complet</td><td>{firstname} {lastname}</td></tr>
                    <tr><td>Identifiant</td><td><code>{account_id}</code></td></tr>
                    <tr><td>Email</td><td>{email}</td></tr>
                    <tr><td>Departement</td><td>{department}</td></tr>
                    <tr><td>Poste</td><td>{job_title}</td></tr>
                    <tr><td>Niveau de droits</td><td>Niveau {permission_level}</td></tr>
                </table>
            </div>

            <div class="warning">
                <strong>Important:</strong>
                {'En approuvant cette demande, elle sera transmise au niveau suivant pour validation.' if level < total_levels else 'En approuvant cette demande (niveau final), vous autorisez la creation de ce compte dans les systemes cibles.'}
                En rejetant, le workflow entier sera annule.
            </div>

            <div class="buttons">
                <a href="{approve_url}" class="btn btn-approve">✓ Approuver</a>
                <a href="{reject_url}" class="btn btn-reject">✗ Rejeter</a>
                <br><br>
                <a href="{dashboard_url}" class="btn btn-dashboard">Voir dans le tableau de bord</a>
            </div>

            <p style="color: #64748b; font-size: 14px;">
                Vous pouvez egalement vous connecter a l'interface IAM Gateway pour gerer cette demande avec des commentaires detailles.
            </p>
        </div>

        <div class="footer">
            <p>Ce message a ete envoye automatiquement par IAM Gateway.</p>
            <p>ID Workflow: {workflow_id} | Niveau: {level}/{total_levels}</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
{level_icon} DEMANDE D'APPROBATION - NIVEAU {level}/{total_levels}: {level_name}
{'='*60}

Bonjour,

{requester} a soumis une demande de creation de compte qui necessite votre approbation en tant que {level_name}.

VOTRE ROLE:
Vous etes l'approbateur du niveau {level} sur {total_levels}.
{'Ce niveau a deja ete approuve par le(s) niveau(x) precedent(s).' if level > 1 else 'Vous etes le premier approbateur de cette demande.'}

INFORMATIONS DU NOUVEL UTILISATEUR:
- Nom complet: {firstname} {lastname}
- Identifiant: {account_id}
- Email: {email}
- Departement: {department}
- Poste: {job_title}
- Niveau de droits: Niveau {permission_level}

ACTIONS:
- Pour APPROUVER: {approve_url}
- Pour REJETER: {reject_url}

{'En approuvant, la demande sera transmise au niveau suivant.' if level < total_levels else 'En approuvant (niveau final), le compte sera cree.'}
En rejetant, le workflow entier sera annule.

Vous pouvez aussi vous connecter a l'interface IAM Gateway:
{dashboard_url}

---
ID Workflow: {workflow_id} | Niveau: {level}/{total_levels}
Ce message a ete envoye automatiquement par IAM Gateway.
"""

        success = self._send_email(
            to_email=approver_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        return {
            "sent": success,
            "approve_token": approve_token,
            "reject_token": reject_token,
            "workflow_id": workflow_id,
            "approver_email": approver_email,
            "level": level
        }

    async def send_workflow_complete_notification(
        self,
        user_email: str,
        user_data: Dict[str, Any],
        approved: bool,
        workflow_id: str,
        rejection_reason: Optional[str] = None,
        rejected_by: Optional[str] = None,
        rejected_at_level: Optional[str] = None
    ) -> bool:
        """
        Notifie le demandeur que le workflow est termine (approuve ou rejete).
        """
        firstname = user_data.get('firstname', 'Utilisateur')
        lastname = user_data.get('lastname', '')
        account_id = user_data.get('account_id', 'N/A')

        if approved:
            status = "APPROUVE"
            status_color = "#22c55e"
            icon = "✅"
            message = "Le compte a ete cree avec succes dans tous les systemes cibles. L'utilisateur peut maintenant se connecter."
        else:
            status = "REJETE"
            status_color = "#ef4444"
            icon = "❌"
            message = f"La demande a ete rejetee au niveau '{rejected_at_level}' par {rejected_by}."
            if rejection_reason:
                message += f"\n\nMotif du rejet: {rejection_reason}"

        subject = f"[IAM Gateway] {icon} Workflow {status}: {firstname} {lastname}"

        # Pre-format message for HTML
        message_html = message.replace('\n', '<br>')
        questions_text = '<p>Si vous avez des questions, veuillez contacter votre responsable ou le service IT.</p>' if not approved else '<p>L utilisateur recevra ses identifiants de connexion par email.</p>'

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .status-box {{ background: {status_color}; color: white; padding: 25px; border-radius: 8px; text-align: center; }}
        .status-icon {{ font-size: 48px; margin-bottom: 10px; }}
        .content {{ background: #f8fafc; padding: 20px; }}
        .info-box {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e2e8f0; }}
        .footer {{ text-align: center; padding: 20px; color: #64748b; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status-box">
            <div class="status-icon">{icon}</div>
            <h1 style="margin: 0;">Workflow {status}</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Tous les niveaux d'approbation ont ete traites</p>
        </div>
        <div class="content">
            <p>Bonjour,</p>

            <div class="info-box">
                <h3 style="margin-top: 0;">Demande concernee</h3>
                <p><strong>Utilisateur:</strong> {firstname} {lastname}</p>
                <p><strong>Identifiant:</strong> {account_id}</p>
            </div>

            <p>{message_html}</p>

            {questions_text}
        </div>
        <div class="footer">
            <p>ID Workflow: {workflow_id}</p>
            <p>Ce message a ete envoye automatiquement par IAM Gateway.</p>
        </div>
    </div>
</body>
</html>
"""

        questions_plain = 'Si vous avez des questions, veuillez contacter votre responsable ou le service IT.' if not approved else "L'utilisateur recevra ses identifiants de connexion par email."
        separator_line = '=' * 50

        text_content = f"""
{icon} WORKFLOW {status} - IAM Gateway
{separator_line}

Bonjour,

La demande de creation de compte pour {firstname} {lastname} (identifiant: {account_id}) a ete {status.lower()}.

{message}

{questions_plain}

---
ID Workflow: {workflow_id}
Ce message a ete envoye automatiquement par IAM Gateway.
"""

        return self._send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


# Instance globale
email_service = EmailService()
