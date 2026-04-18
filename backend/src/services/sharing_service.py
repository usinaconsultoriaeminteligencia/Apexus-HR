"""
Serviço de compartilhamento de entrevistas via email, SMS e WhatsApp
"""
import os
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from urllib.parse import quote

# Referencias às integrações SendGrid e Twilio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from twilio.rest import Client

from sqlalchemy.orm import Session
from ..models import Interview, Candidate
from ..utils.type_helpers import as_float, as_str, as_int, dt_iso, safe_bool

logger = logging.getLogger(__name__)

class SharingService:
    """Serviço para compartilhar entrevistas com candidatos"""
    
    def __init__(self):
        # Configurar SendGrid
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        self.sg_client = SendGridAPIClient(self.sendgrid_key) if self.sendgrid_key else None
        
        # Configurar Twilio
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            self.twilio_client = None
        
        # URL base da aplicação
        self.base_url = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@apexushr.com')
        self.company_name = os.environ.get('COMPANY_NAME', 'Apexus HR')
    
    def create_and_share_interview(
        self,
        db: Session,
        interview_id: int,
        channel: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        custom_message: Optional[str] = None,
        expiration_hours: int = 48
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Cria token e compartilha entrevista pelo canal escolhido
        Returns: (success, message, share_link)
        """
        try:
            # Buscar entrevista
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return False, "Entrevista não encontrada", None
            
            # Buscar dados do candidato
            candidate = interview.candidate
            if not candidate:
                return False, "Candidato não encontrado", None
            
            # Gerar token se não existir
            if interview.interview_token is None or as_str(interview.interview_token) == "":
                interview.generate_interview_token(expiration_hours)
            
            # Obter URL pública
            public_url = interview.get_public_url(self.base_url)
            
            # Enviar pelo canal escolhido
            success = False
            message = ""
            
            if channel == 'email' and email:
                success, message = self._send_email_invitation(
                    to_email=email,
                    candidate_name=candidate.full_name,
                    position=as_str(interview.position),
                    link=public_url,
                    custom_message=custom_message
                )
            elif channel == 'sms' and phone:
                success, message = self._send_sms_invitation(
                    to_phone=phone,
                    candidate_name=candidate.full_name,
                    position=as_str(interview.position),
                    link=public_url
                )
            elif channel == 'whatsapp' and phone:
                success, message = self._generate_whatsapp_link(
                    to_phone=phone,
                    candidate_name=candidate.full_name,
                    position=as_str(interview.position),
                    link=public_url
                )
            elif channel == 'link':
                success = True
                message = "Link gerado com sucesso"
            else:
                return False, "Canal inválido ou dados faltando", None
            
            if success:
                # Atualizar dados da entrevista
                setattr(interview, "invitation_channel", channel)
                setattr(interview, "invitation_sent_at", datetime.now(timezone.utc).replace(tzinfo=None))
                setattr(interview, "invitation_status", "sent")
                setattr(interview, "invitation_phone", phone)
                setattr(interview, "invitation_message", custom_message)
                db.commit()
            
            return success, message, public_url
            
        except Exception as e:
            logger.error(f"Erro ao compartilhar entrevista: {str(e)}")
            db.rollback()
            return False, f"Erro ao compartilhar: {str(e)}", None
    
    def resend_invitation(self, db: Session, interview_id: int) -> Tuple[bool, str]:
        """Reenvia convite usando o canal original"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return False, "Entrevista não encontrada"
            
            if interview.interview_token is None or as_str(interview.interview_token) == "":
                return False, "Token não gerado para esta entrevista"
            
            # Verificar se o token ainda é válido
            if safe_bool(interview.is_token_valid()) == False:
                # Regenerar token se expirado
                interview.generate_interview_token()
            
            # Obter dados do candidato
            candidate = interview.candidate
            
            # Reenviar pelo canal original
            channel = as_str(interview.invitation_channel) if interview.invitation_channel is not None else 'email'
            email = candidate.email if hasattr(candidate, 'email') else None
            phone = as_str(interview.invitation_phone) if interview.invitation_phone is not None else (candidate.phone if hasattr(candidate, 'phone') else None)
            
            success, message, _ = self.create_and_share_interview(
                db=db,
                interview_id=interview_id,
                channel=as_str(channel),
                email=email,
                phone=phone,
                custom_message=as_str(interview.invitation_message) if interview.invitation_message is not None else None
            )
            
            return success, message
            
        except Exception as e:
            logger.error(f"Erro ao reenviar convite: {str(e)}")
            return False, f"Erro ao reenviar: {str(e)}"
    
    def _send_email_invitation(
        self,
        to_email: str,
        candidate_name: str,
        position: str,
        link: str,
        custom_message: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Envia convite por email usando SendGrid"""
        try:
            if not self.sg_client:
                return False, "SendGrid não configurado"
            
            # HTML Template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        background-color: #f5f5f5;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 40px auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 28px;
                        font-weight: 600;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .content h2 {{
                        color: #667eea;
                        font-size: 22px;
                        margin-top: 0;
                    }}
                    .info-box {{
                        background: #f8f9fa;
                        border-left: 4px solid #667eea;
                        padding: 15px;
                        margin: 20px 0;
                    }}
                    .button-container {{
                        text-align: center;
                        margin: 30px 0;
                    }}
                    .cta-button {{
                        display: inline-block;
                        padding: 14px 40px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        text-decoration: none;
                        border-radius: 25px;
                        font-weight: 600;
                        font-size: 16px;
                        transition: transform 0.3s;
                    }}
                    .cta-button:hover {{
                        transform: translateY(-2px);
                    }}
                    .instructions {{
                        background: #fff3cd;
                        border: 1px solid #ffc107;
                        border-radius: 4px;
                        padding: 15px;
                        margin: 20px 0;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 20px;
                        background: #f8f9fa;
                        color: #666;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{self.company_name}</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Convite para Entrevista</p>
                    </div>
                    <div class="content">
                        <h2>Olá, {candidate_name}!</h2>
                        
                        <p>Temos o prazer de convidá-lo(a) para participar do processo seletivo para a vaga de <strong>{position}</strong>.</p>
                        
                        {f'<p>{custom_message}</p>' if custom_message else ''}
                        
                        <div class="info-box">
                            <strong>📋 Informações da Entrevista:</strong><br>
                            • Formato: Entrevista em Áudio<br>
                            • Duração estimada: 15-20 minutos<br>
                            • Prazo: 48 horas<br>
                            • Acesso: Totalmente online
                        </div>
                        
                        <div class="instructions">
                            <strong>🎯 Como funciona:</strong>
                            <ol style="margin: 10px 0; padding-left: 20px;">
                                <li>Clique no botão abaixo para acessar a entrevista</li>
                                <li>Permita o acesso ao microfone quando solicitado</li>
                                <li>Responda as perguntas com calma e naturalidade</li>
                                <li>Ao finalizar, suas respostas serão enviadas automaticamente</li>
                            </ol>
                        </div>
                        
                        <div class="button-container">
                            <a href="{link}" class="cta-button">Iniciar Entrevista</a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px;">
                            <strong>Dicas importantes:</strong><br>
                            • Escolha um local calmo e sem ruídos<br>
                            • Use fones de ouvido para melhor qualidade de áudio<br>
                            • Teste seu microfone antes de começar<br>
                            • Seja você mesmo(a) e boa sorte!
                        </p>
                        
                        <p style="margin-top: 30px; color: #999; font-size: 12px;">
                            Se o botão não funcionar, copie e cole este link no navegador:<br>
                            <a href="{link}" style="color: #667eea; word-break: break-all;">{link}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>Este é um email automático. Por favor, não responda.</p>
                        <p>© {datetime.now().year} {self.company_name} - Todos os direitos reservados</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Criar mensagem
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=f"Convite para Entrevista - {position}",
            )
            message.content = Content("text/html", html_content)
            
            # Enviar email
            self.sg_client.send(message)
            
            logger.info(f"Email enviado para {to_email}")
            return True, "Email enviado com sucesso"
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            return False, f"Erro ao enviar email: {str(e)}"
    
    def _send_sms_invitation(
        self,
        to_phone: str,
        candidate_name: str,
        position: str,
        link: str
    ) -> Tuple[bool, str]:
        """Envia convite por SMS usando Twilio"""
        try:
            if not self.twilio_client:
                return False, "Twilio não configurado"
            
            # Formatar telefone se necessário
            if not to_phone.startswith('+'):
                # Assumir Brasil se não tiver código de país
                to_phone = f"+55{to_phone}"
            
            # Mensagem SMS (precisa ser concisa)
            message_body = (
                f"Olá {candidate_name}!\n\n"
                f"Você foi convidado(a) para uma entrevista - {position}.\n"
                f"Acesse o link para começar:\n{link}\n\n"
                f"Válido por 48h. Boa sorte!"
            )
            
            # Enviar SMS
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=self.twilio_phone_number,
                to=to_phone
            )
            
            logger.info(f"SMS enviado para {to_phone} com SID: {message.sid}")
            return True, "SMS enviado com sucesso"
            
        except Exception as e:
            logger.error(f"Erro ao enviar SMS: {str(e)}")
            return False, f"Erro ao enviar SMS: {str(e)}"
    
    def _generate_whatsapp_link(
        self,
        to_phone: str,
        candidate_name: str,
        position: str,
        link: str
    ) -> Tuple[bool, str]:
        """Gera link para enviar via WhatsApp Web"""
        try:
            # Formatar telefone (remover caracteres especiais)
            phone_clean = ''.join(filter(str.isdigit, to_phone))
            if not phone_clean.startswith('55'):
                phone_clean = f"55{phone_clean}"
            
            # Mensagem para WhatsApp
            message = (
                f"Olá {candidate_name}! 👋\n\n"
                f"*Convite para Entrevista*\n"
                f"Você foi selecionado(a) para a vaga de *{position}*!\n\n"
                f"📋 *Formato:* Entrevista em Áudio\n"
                f"⏱️ *Duração:* 15-20 minutos\n"
                f"📅 *Prazo:* 48 horas\n\n"
                f"Para iniciar sua entrevista, acesse:\n{link}\n\n"
                f"Boa sorte! 🍀"
            )
            
            # Codificar mensagem para URL
            message_encoded = quote(message)
            
            # Gerar link do WhatsApp Web
            whatsapp_link = f"https://api.whatsapp.com/send?phone={phone_clean}&text={message_encoded}"
            
            logger.info(f"Link WhatsApp gerado para {to_phone}")
            return True, whatsapp_link
            
        except Exception as e:
            logger.error(f"Erro ao gerar link WhatsApp: {str(e)}")
            return False, f"Erro ao gerar link: {str(e)}"
    
    def validate_token_access(
        self,
        db: Session,
        token: str
    ) -> Tuple[bool, Optional[Interview], str]:
        """
        Valida acesso via token público
        Returns: (is_valid, interview, message)
        """
        try:
            # Buscar entrevista pelo token
            interview = db.query(Interview).filter(
                Interview.interview_token == token
            ).first()
            
            if not interview:
                return False, None, "Link inválido ou expirado"
            
            # Verificar validade do token
            if safe_bool(interview.is_token_valid()) == False:
                return False, None, "Link expirado. Solicite um novo convite."
            
            # Verificar status da entrevista
            if as_str(interview.status) == 'concluida':
                return False, None, "Esta entrevista já foi concluída"
            
            if as_str(interview.status) == 'cancelada':
                return False, None, "Esta entrevista foi cancelada"
            
            # Registrar acesso
            interview.record_token_access()
            db.commit()
            
            return True, interview, "Token válido"
            
        except Exception as e:
            logger.error(f"Erro ao validar token: {str(e)}")
            return False, None, f"Erro ao validar acesso: {str(e)}"