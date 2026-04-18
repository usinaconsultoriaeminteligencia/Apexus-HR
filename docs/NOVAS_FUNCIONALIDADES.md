# 🚀 Novas Funcionalidades Implementadas

Este documento descreve as três novas funcionalidades implementadas: WebSocket para feedback em tempo real, Sistema de Avaliações e Sistema de Agendamento de Entrevistas.

## 📋 Índice

1. [Sistema WebSocket](#1-sistema-websocket)
2. [Sistema de Avaliações/Feedback](#2-sistema-de-avaliaçõesfeedback)
3. [Sistema de Agendamento de Entrevistas](#3-sistema-de-agendamento-de-entrevistas)

---

## 1. Sistema WebSocket

### Arquivo: `backend/src/services/websocket_service.py`

**Funcionalidades Implementadas:**
- ✅ Conexão WebSocket com autenticação JWT
- ✅ Salas por usuário (`user_{user_id}`)
- ✅ Broadcast para todos os clientes
- ✅ Envio direto para usuário específico
- ✅ Gerenciamento de conexões ativas
- ✅ Keepalive (ping/pong)

**Eventos Suportados:**
- `connect` - Conexão de cliente
- `disconnect` - Desconexão
- `join_room` - Entrar em sala
- `leave_room` - Sair de sala
- `ping` - Keepalive
- `connected` - Confirmação de conexão
- `notification` - Notificação genérica
- `new_feedback` - Novo feedback criado
- `feedback_updated` - Feedback atualizado
- `new_appointment` - Novo agendamento
- `appointment_confirmed` - Agendamento confirmado
- `appointment_declined` - Agendamento recusado
- `appointment_cancelled` - Agendamento cancelado

**Uso no Backend:**
```python
from src.services.websocket_service import emit_to_user, broadcast

# Enviar para usuário específico
emit_to_user(user_id, 'notification', {'message': 'Olá!'})

# Broadcast para todos
broadcast('system_message', {'message': 'Manutenção programada'})
```

---

## 2. Sistema de Avaliações/Feedback

### Modelo: `backend/src/models/feedback.py`

**Campos:**
- `user_id` - Usuário que criou o feedback
- `feedback_type` - Tipo (system, interview, candidate, feature)
- `category` - Categoria (bug, suggestion, complaint, praise)
- `title` - Título do feedback
- `description` - Descrição detalhada
- `rating` - Avaliação (1-5 estrelas)
- `status` - Status (pending, reviewed, resolved, dismissed)
- `priority` - Prioridade (low, medium, high, critical)
- `admin_response` - Resposta do administrador
- `resolved_by` - Admin que resolveu
- `resolved_at` - Data de resolução

### Serviço: `backend/src/services/feedback_service.py`

**Métodos:**
- `create_feedback()` - Cria novo feedback
- `get_feedback()` - Busca por ID
- `list_feedbacks()` - Lista com filtros e paginação
- `update_feedback_status()` - Atualiza status
- `get_feedback_statistics()` - Estatísticas

### Rotas: `backend/src/routes/feedback.py`

**Endpoints:**
- `POST /api/feedback` - Criar feedback
- `GET /api/feedback` - Listar feedbacks
- `GET /api/feedback/<id>` - Obter feedback
- `PATCH /api/feedback/<id>/status` - Atualizar status (admin)
- `GET /api/feedback/statistics` - Estatísticas (admin)

**Exemplo de Uso:**
```bash
# Criar feedback
POST /api/feedback
{
  "title": "Bug no sistema",
  "description": "Não consigo salvar candidato",
  "feedback_type": "system",
  "category": "bug",
  "rating": 2
}

# Listar feedbacks
GET /api/feedback?status=pending&page=1&per_page=20
```

---

## 3. Sistema de Agendamento de Entrevistas

### Modelo: `backend/src/models/appointment.py`

**Campos:**
- `candidate_id` - Candidato
- `interviewer_id` - Entrevistador
- `appointment_token` - Token único para acesso público
- `title` - Título do agendamento
- `scheduled_at` - Data e horário agendados
- `duration_minutes` - Duração em minutos
- `timezone` - Fuso horário
- `status` - Status (pending, confirmed, cancelled, completed, no_show)
- `confirmation_status` - Status de confirmação (pending, confirmed, declined)
- `meeting_type` - Tipo (audio, video, presencial)
- `location` - Localização física ou link
- `meeting_link` - Link para video conferência

### Serviço: `backend/src/services/appointment_service.py`

**Métodos:**
- `create_appointment()` - Cria agendamento
- `get_appointment()` - Busca por ID
- `get_appointment_by_token()` - Busca por token público
- `list_appointments()` - Lista com filtros
- `confirm_appointment()` - Confirma agendamento
- `decline_appointment()` - Recusa agendamento
- `cancel_appointment()` - Cancela agendamento
- `get_upcoming_appointments()` - Próximos agendamentos
- `check_reminders()` - Verifica lembretes pendentes

### Rotas: `backend/src/routes/appointments.py`

**Endpoints:**
- `POST /api/appointments` - Criar agendamento
- `GET /api/appointments` - Listar agendamentos
- `GET /api/appointments/<id>` - Obter agendamento
- `GET /api/appointments/token/<token>` - Obter por token (público)
- `POST /api/appointments/<id>/confirm` - Confirmar
- `POST /api/appointments/<id>/decline` - Recusar
- `POST /api/appointments/<id>/cancel` - Cancelar
- `GET /api/appointments/upcoming` - Próximos agendamentos

**Exemplo de Uso:**
```bash
# Criar agendamento
POST /api/appointments
{
  "candidate_id": 1,
  "scheduled_at": "2024-12-20T14:00:00Z",
  "duration_minutes": 30,
  "meeting_type": "video",
  "meeting_link": "https://meet.google.com/xxx",
  "title": "Entrevista Técnica"
}

# Confirmar agendamento (candidato ou entrevistador)
POST /api/appointments/1/confirm

# Recusar agendamento (candidato)
POST /api/appointments/1/decline
{
  "reason": "Conflito de horário"
}
```

---

## 🔧 Configuração

### Dependências Adicionadas

```txt
flask-socketio==5.3.6
python-socketio==5.10.0
eventlet==0.36.1
```

### Variáveis de Ambiente

Nenhuma variável adicional necessária. O sistema usa as mesmas configurações existentes.

### Migrações de Banco de Dados

**IMPORTANTE:** É necessário criar migrações para as novas tabelas:

```bash
# Criar migração
flask db migrate -m "Add feedback and appointment tables"

# Aplicar migração
flask db upgrade
```

**Tabelas Criadas:**
- `feedbacks` - Feedback/avaliações
- `appointments` - Agendamentos

---

## 📡 Integração Frontend

### WebSocket Client

```javascript
import io from 'socket.io-client';

// Conectar
const socket = io('http://localhost:8000', {
  auth: {
    token: localStorage.getItem('auth_token')
  }
});

// Escutar eventos
socket.on('connected', (data) => {
  console.log('Conectado:', data);
});

socket.on('notification', (data) => {
  console.log('Notificação:', data);
});

socket.on('new_appointment', (data) => {
  console.log('Novo agendamento:', data);
});

// Entrar em sala
socket.emit('join_room', { room: 'user_123' });
```

### Exemplo de Componente React

```jsx
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

function FeedbackForm() {
  const [socket, setSocket] = useState(null);
  
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const newSocket = io('http://localhost:8000', {
      auth: { token }
    });
    
    newSocket.on('feedback_updated', (data) => {
      console.log('Feedback atualizado:', data);
    });
    
    setSocket(newSocket);
    
    return () => newSocket.close();
  }, []);
  
  const submitFeedback = async (data) => {
    const response = await fetch('/api/feedback', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    // Notificação será recebida via WebSocket
  };
  
  return <div>...</div>;
}
```

---

## 🎯 Próximos Passos

### Frontend (Pendente)
1. Componente de Feedback Form
2. Componente de Lista de Agendamentos
3. Componente de Calendário
4. Hook React para WebSocket
5. Notificações em tempo real na UI

### Melhorias Futuras
1. Envio de emails para lembretes de agendamento
2. Integração com Google Calendar
3. Dashboard de feedbacks para admin
4. Relatórios de agendamentos
5. Sistema de lembretes automáticos

---

## 📝 Notas de Implementação

### WebSocket
- Usa Flask-SocketIO com eventlet
- Autenticação via JWT no handshake
- Suporta múltiplas conexões por usuário
- Fallback graceful se WebSocket não disponível

### Feedback
- Notificações automáticas para admins
- Respostas podem ser enviadas aos usuários
- Sistema de prioridades
- Estatísticas agregadas

### Agendamentos
- Tokens públicos para acesso sem login
- Confirmação/recusa por ambas as partes
- Lembretes automáticos (precisa de task scheduler)
- Integração com entrevistas existentes

---

## ✅ Status

- ✅ Backend completo
- ✅ Modelos de dados
- ✅ Serviços implementados
- ✅ Rotas REST API
- ✅ WebSocket funcional
- ⏳ Frontend (próximo passo)
- ⏳ Migrações de banco (precisa executar)

**Pronto para uso após executar migrações!**

