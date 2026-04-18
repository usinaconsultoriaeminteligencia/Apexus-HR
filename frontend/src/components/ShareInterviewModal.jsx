import React, { useState } from 'react';
import {
  X,
  Mail,
  MessageSquare,
  Phone,
  Link,
  Send,
  Copy,
  CheckCircle,
  AlertCircle,
  User,
  Clock,
  Loader2,
  Eye
} from 'lucide-react';

const ShareInterviewModal = ({ candidate, onClose, onShare, existingInterview }) => {
  const [channel, setChannel] = useState('email');
  const [email, setEmail] = useState(candidate?.email || '');
  const [phone, setPhone] = useState(candidate?.phone || '');
  const [position, setPosition] = useState(candidate?.position_applied || '');
  const [customMessage, setCustomMessage] = useState('');
  const [expirationHours, setExpirationHours] = useState(48);
  const [loading, setLoading] = useState(false);
  const [shareLink, setShareLink] = useState('');
  const [whatsappLink, setWhatsappLink] = useState('');
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);
    
    try {
      const payload = {
        channel,
        email: channel === 'email' ? email : undefined,
        phone: channel === 'sms' || channel === 'whatsapp' ? phone : undefined,
        position,
        custom_message: customMessage,
        expiration_hours: expirationHours
      };
      
      // Se já existe uma entrevista, apenas compartilhar
      let response;
      if (existingInterview) {
        response = await fetch(`/api/interviews/${existingInterview.id}/share`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify(payload)
        });
      } else {
        // Criar nova entrevista e compartilhar
        response = await fetch('/api/interviews/create-and-share', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            ...payload,
            candidate_id: candidate.id,
            interviewer_id: 1 // Será obtido da sessão no backend
          })
        });
      }
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Erro ao compartilhar entrevista');
      }
      
      setShareLink(data.share_link);
      if (data.whatsapp_link) {
        setWhatsappLink(data.whatsapp_link);
      }
      
      setSuccess(true);
      
      // Se for WhatsApp, abrir o link em nova aba
      if (channel === 'whatsapp' && data.whatsapp_link) {
        window.open(data.whatsapp_link, '_blank');
      }
      
      // Callback para atualizar lista
      if (onShare) {
        onShare(data);
      }
      
      // Fechar modal após 3 segundos se sucesso
      if (channel !== 'link') {
        setTimeout(() => {
          onClose();
        }, 3000);
      }
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Link copiado!');
    } catch (err) {
      alert('Erro ao copiar link');
    }
  };
  
  const getChannelIcon = (ch) => {
    switch (ch) {
      case 'email':
        return <Mail className="w-5 h-5" />;
      case 'sms':
        return <MessageSquare className="w-5 h-5" />;
      case 'whatsapp':
        return <Phone className="w-5 h-5" />;
      case 'link':
        return <Link className="w-5 h-5" />;
      default:
        return null;
    }
  };
  
  const getPreviewContent = () => {
    switch (channel) {
      case 'email':
        return (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">Prévia do Email</h4>
            <div className="bg-white p-3 rounded border">
              <p className="text-sm text-gray-600 mb-1">Para: {email}</p>
              <p className="text-sm text-gray-600 mb-2">Assunto: Convite para Entrevista - {position}</p>
              <div className="border-t pt-2">
                <p className="text-sm">Olá {candidate?.full_name},</p>
                <p className="text-sm mt-2">
                  Temos o prazer de convidá-lo(a) para participar do processo seletivo para a vaga de {position}.
                </p>
                {customMessage && (
                  <p className="text-sm mt-2 italic">{customMessage}</p>
                )}
                <div className="mt-3 inline-block px-4 py-2 bg-purple-600 text-white rounded text-sm">
                  Iniciar Entrevista
                </div>
              </div>
            </div>
          </div>
        );
      case 'sms':
        return (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">Prévia do SMS</h4>
            <div className="bg-white p-3 rounded border">
              <p className="text-sm text-gray-600 mb-2">Para: {phone}</p>
              <p className="text-sm">
                Olá {candidate?.full_name}! Você foi convidado(a) para uma entrevista - {position}. 
                Acesse o link para começar. Válido por {expirationHours}h. Boa sorte!
              </p>
            </div>
          </div>
        );
      case 'whatsapp':
        return (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">Prévia do WhatsApp</h4>
            <div className="bg-white p-3 rounded border">
              <p className="text-sm text-gray-600 mb-2">Para: {phone}</p>
              <p className="text-sm">
                Olá {candidate?.full_name}! 👋<br/><br/>
                <strong>Convite para Entrevista</strong><br/>
                Você foi selecionado(a) para a vaga de <strong>{position}</strong>!<br/><br/>
                📋 Formato: Entrevista em Áudio<br/>
                ⏱️ Duração: 15-20 minutos<br/>
                📅 Prazo: {expirationHours} horas<br/><br/>
                Para iniciar sua entrevista, acesse o link.<br/><br/>
                Boa sorte! 🍀
              </p>
            </div>
          </div>
        );
      default:
        return null;
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Compartilhar Entrevista
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Envie o convite para {candidate?.full_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Canal de Envio */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Como deseja enviar o convite?
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { id: 'email', label: 'Email', icon: Mail },
                { id: 'sms', label: 'SMS', icon: MessageSquare },
                { id: 'whatsapp', label: 'WhatsApp', icon: Phone },
                { id: 'link', label: 'Copiar Link', icon: Link }
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setChannel(id)}
                  className={`
                    flex flex-col items-center justify-center p-3 rounded-lg border-2 transition
                    ${channel === id 
                      ? 'border-purple-600 bg-purple-50 text-purple-600'
                      : 'border-gray-200 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-6 h-6 mb-1" />
                  <span className="text-sm font-medium">{label}</span>
                </button>
              ))}
            </div>
          </div>
          
          {/* Campos dinâmicos baseados no canal */}
          {channel === 'email' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email do Candidato
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="candidato@email.com"
              />
            </div>
          )}
          
          {(channel === 'sms' || channel === 'whatsapp') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Telefone do Candidato
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="(11) 98765-4321"
              />
            </div>
          )}
          
          {/* Posição */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Vaga
            </label>
            <input
              type="text"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Ex: Desenvolvedor Frontend"
            />
          </div>
          
          {/* Mensagem Personalizada */}
          {channel === 'email' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mensagem Personalizada (Opcional)
              </label>
              <textarea
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Adicione uma mensagem personalizada para o candidato..."
              />
            </div>
          )}
          
          {/* Prazo de Expiração */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prazo para Realizar a Entrevista
            </label>
            <div className="flex items-center space-x-4">
              <select
                value={expirationHours}
                onChange={(e) => setExpirationHours(Number(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value={24}>24 horas</option>
                <option value={48}>48 horas</option>
                <option value={72}>72 horas</option>
                <option value={120}>5 dias</option>
                <option value={168}>1 semana</option>
              </select>
              <div className="flex items-center text-sm text-gray-600">
                <Clock className="w-4 h-4 mr-1" />
                Link expira em {expirationHours} horas
              </div>
            </div>
          </div>
          
          {/* Preview Button */}
          {channel !== 'link' && (
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="flex items-center text-sm text-purple-600 hover:text-purple-700"
            >
              <Eye className="w-4 h-4 mr-1" />
              {showPreview ? 'Ocultar' : 'Ver'} Prévia da Mensagem
            </button>
          )}
          
          {/* Preview Content */}
          {showPreview && getPreviewContent()}
          
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
          
          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center mb-2">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <span className="text-sm text-green-700 font-medium">
                  {channel === 'link' ? 'Link gerado com sucesso!' : 'Convite enviado com sucesso!'}
                </span>
              </div>
              
              {shareLink && (
                <div className="mt-2 p-2 bg-white rounded border">
                  <div className="flex items-center justify-between">
                    <input
                      type="text"
                      value={shareLink}
                      readOnly
                      className="flex-1 text-sm text-gray-600 bg-transparent"
                    />
                    <button
                      type="button"
                      onClick={() => copyToClipboard(shareLink)}
                      className="ml-2 text-purple-600 hover:text-purple-700"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </form>
        
        {/* Footer */}
        <div className="flex justify-between items-center px-6 py-4 border-t bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            Cancelar
          </button>
          
          <button
            onClick={handleSubmit}
            disabled={loading || success}
            className="flex items-center px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Enviando...
              </>
            ) : (
              <>
                {getChannelIcon(channel)}
                <span className="ml-2">
                  {channel === 'link' ? 'Gerar Link' : 'Enviar Convite'}
                </span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShareInterviewModal;