import React, { useState } from 'react';
import { 
  X, Settings, Moon, Sun, Monitor, Globe, Clock, Layout,
  Bell, BellOff, Mail, Smartphone, Volume2, Mic, Users,
  FileText, Download, Shield, Eye, Database, Accessibility,
  Palette, Type, MousePointer, Keyboard
} from 'lucide-react';
import { useSettings } from '../contexts/SettingsContext';
import { useAuth } from '../contexts/AuthContext';

const SettingsModal = ({ isOpen, onClose }) => {
  const { settings, updateSetting, getSetting, resetSettings, exportSettings } = useSettings();
  const { userRole, canAccessSetting, isCandidate, getRoleDisplayName, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('general');

  // Definir abas fora para evitar recreação
  const allTabs = React.useMemo(() => [
    { id: 'general', label: 'Geral', icon: Settings, roles: ['admin', 'recruiter', 'manager', 'analyst', 'viewer', 'candidate'] },
    { id: 'notifications', label: 'Notificações', icon: Bell, roles: ['admin', 'recruiter', 'manager'] },
    { id: 'interviews', label: 'Entrevistas', icon: Mic, roles: ['admin', 'recruiter'] },
    { id: 'reports', label: 'Relatórios', icon: FileText, roles: ['admin', 'manager', 'analyst'] },
    { id: 'privacy', label: 'Privacidade', icon: Shield, roles: ['admin', 'candidate'] },
    { id: 'accessibility', label: 'Acessibilidade', icon: Accessibility, roles: ['admin', 'recruiter', 'manager', 'analyst', 'viewer', 'candidate'] },
    { id: 'system', label: 'Sistema', icon: Database, roles: ['admin'] }
  ], []);

  const tabs = React.useMemo(() => 
    allTabs.filter(tab => tab.roles.includes(userRole)),
    [allTabs, userRole]
  );

  // Garantir que existe uma aba ativa válida
  React.useEffect(() => {
    const validTab = tabs.find(tab => tab.id === activeTab);
    if (!validTab && tabs.length > 0) {
      setActiveTab(tabs[0].id);
    }
  }, [userRole]); // Apenas depende do userRole mudando

  // Renderização condicional - DEVE vir DEPOIS de todos os hooks
  if (!isOpen) return null;

  const GeneralSettings = () => (
    <div className="space-y-6">
      {/* Indicador de perfil do usuário */}
      <div className="bg-muted/30 rounded-lg p-4 border border-border">
        <h4 className="font-medium mb-2">Perfil do Usuário</h4>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            Nível de acesso: <strong>{getRoleDisplayName()}</strong>
          </span>
          {isCandidate() && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
              Acesso via entrevista
            </span>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Tema</label>
        <div className="grid grid-cols-3 gap-2">
          {[
            { value: 'light', label: 'Claro', icon: Sun },
            { value: 'dark', label: 'Escuro', icon: Moon },
            { value: 'system', label: 'Sistema', icon: Monitor }
          ].map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => updateSetting('theme', value)}
              className={`p-3 rounded-lg border-2 flex flex-col items-center space-y-1 transition-colors ${
                getSetting('theme') === value
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border hover:border-border-hover'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="text-xs">{label}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Densidade da Interface</label>
        <select
          value={getSetting('density')}
          onChange={(e) => updateSetting('density', e.target.value)}
          className="w-full p-2 border border-border rounded-lg bg-background"
        >
          <option value="compact">Compacta</option>
          <option value="comfortable">Confortável</option>
          <option value="spacious">Espaçosa</option>
        </select>
      </div>

      {!isCandidate() && (
        <div>
          <label className="block text-sm font-medium mb-2">Visualização Inicial</label>
          <select
            value={getSetting('defaultView')}
            onChange={(e) => updateSetting('defaultView', e.target.value)}
            className="w-full p-2 border border-border rounded-lg bg-background"
          >
            <option value="dashboard">Dashboard</option>
            {(userRole === 'admin' || userRole === 'recruiter') && <option value="candidates">Candidatos</option>}
            {(userRole === 'admin' || userRole === 'recruiter') && <option value="interviews">Entrevistas</option>}
            {(userRole === 'admin' || userRole === 'manager' || userRole === 'analyst') && <option value="reports">Relatórios</option>}
          </select>
        </div>
      )}

      {!isCandidate() && (
        <div>
          <label className="block text-sm font-medium mb-2">Idioma</label>
          <select
            value={getSetting('language')}
            onChange={(e) => updateSetting('language', e.target.value)}
            className="w-full p-2 border border-border rounded-lg bg-background"
          >
            <option value="pt-BR">Português (Brasil)</option>
            <option value="en-US">English (US)</option>
            <option value="es-ES">Español</option>
          </select>
        </div>
      )}

      {!isCandidate() && (
        <div>
          <label className="block text-sm font-medium mb-2">Fuso Horário</label>
          <select
            value={getSetting('timezone')}
            onChange={(e) => updateSetting('timezone', e.target.value)}
            className="w-full p-2 border border-border rounded-lg bg-background"
          >
            <option value="America/Sao_Paulo">São Paulo (BRT)</option>
            <option value="America/Manaus">Manaus (AMT)</option>
            <option value="America/Recife">Recife (BRT)</option>
            <option value="UTC">UTC</option>
          </select>
        </div>
      )}
    </div>
  );

  const NotificationSettings = () => (
    <div className="space-y-6">
      <div className="space-y-4">
        <h4 className="font-medium">Tipos de Notificação</h4>
        
        {[
          { key: 'interviewReminders', label: 'Lembretes de Entrevistas', desc: 'Notificações antes das entrevistas agendadas' },
          { key: 'candidateStatusChanges', label: 'Mudanças de Status', desc: 'Quando o status de um candidato é alterado' },
          { key: 'dailyDigest', label: 'Resumo Diário', desc: 'Relatório diário das atividades' },
          { key: 'weeklyReport', label: 'Relatório Semanal', desc: 'Resumo semanal de métricas e estatísticas' }
        ].map(({ key, label, desc }) => (
          <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div>
              <div className="font-medium">{label}</div>
              <div className="text-sm text-muted-foreground">{desc}</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={getSetting(`notifications.${key}`)}
                onChange={(e) => updateSetting(`notifications.${key}`, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        <h4 className="font-medium">Canais de Notificação</h4>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center space-x-3 p-3 rounded-lg border border-border">
            <Mail className="h-5 w-5 text-muted-foreground" />
            <div className="flex-1">
              <div className="font-medium">Email</div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={getSetting('notifications.channels.email')}
                  onChange={(e) => updateSetting('notifications.channels.email', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>

          <div className="flex items-center space-x-3 p-3 rounded-lg border border-border">
            <Smartphone className="h-5 w-5 text-muted-foreground" />
            <div className="flex-1">
              <div className="font-medium">In-App</div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={getSetting('notifications.channels.inApp')}
                  onChange={(e) => updateSetting('notifications.channels.inApp', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h4 className="font-medium">Horário Silencioso</h4>
        
        <div className="flex items-center justify-between p-3 rounded-lg border border-border">
          <div>
            <div className="font-medium">Ativar Horário Silencioso</div>
            <div className="text-sm text-muted-foreground">Não enviar notificações em horários específicos</div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={getSetting('notifications.quietHoursEnabled')}
              onChange={(e) => updateSetting('notifications.quietHoursEnabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        {getSetting('notifications.quietHoursEnabled') && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Início</label>
              <input
                type="time"
                value={getSetting('notifications.quietHoursStart')}
                onChange={(e) => updateSetting('notifications.quietHoursStart', e.target.value)}
                className="w-full p-2 border border-border rounded-lg bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Fim</label>
              <input
                type="time"
                value={getSetting('notifications.quietHoursEnd')}
                onChange={(e) => updateSetting('notifications.quietHoursEnd', e.target.value)}
                className="w-full p-2 border border-border rounded-lg bg-background"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const InterviewSettings = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2">Duração Padrão da Entrevista (minutos)</label>
        <input
          type="number"
          min="15"
          max="180"
          value={getSetting('interviews.defaultDuration')}
          onChange={(e) => updateSetting('interviews.defaultDuration', parseInt(e.target.value))}
          className="w-full p-2 border border-border rounded-lg bg-background"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Tempo de Buffer (minutos)</label>
        <input
          type="number"
          min="0"
          max="60"
          value={getSetting('interviews.bufferTime')}
          onChange={(e) => updateSetting('interviews.bufferTime', parseInt(e.target.value))}
          className="w-full p-2 border border-border rounded-lg bg-background"
        />
      </div>

      <div className="space-y-4">
        {[
          { key: 'enableRecording', label: 'Habilitar Gravação de Áudio', desc: 'Permitir gravação das entrevistas por áudio' },
          { key: 'requireConsent', label: 'Exigir Consentimento', desc: 'Solicitar consentimento explícito antes da gravação' },
          { key: 'autoTranscription', label: 'Transcrição Automática', desc: 'Transcrever automaticamente as gravações de áudio' }
        ].map(({ key, label, desc }) => (
          <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div>
              <div className="font-medium">{label}</div>
              <div className="text-sm text-muted-foreground">{desc}</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={getSetting(`interviews.${key}`)}
                onChange={(e) => updateSetting(`interviews.${key}`, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        ))}
      </div>
    </div>
  );

  const ReportsSettings = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2">Período Padrão dos Relatórios</label>
        <select
          value={getSetting('reports.defaultDateRange')}
          onChange={(e) => updateSetting('reports.defaultDateRange', e.target.value)}
          className="w-full p-2 border border-border rounded-lg bg-background"
        >
          <option value="7">Últimos 7 dias</option>
          <option value="30">Últimos 30 dias</option>
          <option value="90">Últimos 90 dias</option>
          <option value="365">Último ano</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Formato de Exportação Padrão</label>
        <select
          value={getSetting('reports.exportFormat')}
          onChange={(e) => updateSetting('reports.exportFormat', e.target.value)}
          className="w-full p-2 border border-border rounded-lg bg-background"
        >
          <option value="pdf">PDF</option>
          <option value="excel">Excel</option>
          <option value="csv">CSV</option>
        </select>
      </div>

      <div className="space-y-4">
        {[
          { key: 'includeCharts', label: 'Incluir Gráficos', desc: 'Adicionar visualizações gráficas nos relatórios' },
          { key: 'autoRefresh', label: 'Atualização Automática', desc: 'Atualizar dados automaticamente em tempo real' }
        ].map(({ key, label, desc }) => (
          <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div>
              <div className="font-medium">{label}</div>
              <div className="text-sm text-muted-foreground">{desc}</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={getSetting(`reports.${key}`)}
                onChange={(e) => updateSetting(`reports.${key}`, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        ))}
      </div>
    </div>
  );

  const PrivacySettings = () => (
    <div className="space-y-6">
      {isCandidate() ? (
        // Configurações de privacidade simplificadas para entrevistados
        <>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Seus Direitos de Privacidade</h4>
            <p className="text-sm text-blue-800">
              Como entrevistado, você tem controle sobre seus dados pessoais durante o processo seletivo.
            </p>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg border border-border">
              <div>
                <div className="font-medium">Permitir Gravação da Entrevista</div>
                <div className="text-sm text-muted-foreground">Consentir com a gravação de áudio da entrevista para análise</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={getSetting('privacy.allowRecording', false)}
                  onChange={(e) => updateSetting('privacy.allowRecording', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border border-border">
              <div>
                <div className="font-medium">Receber Feedback da Entrevista</div>
                <div className="text-sm text-muted-foreground">Permitir que a empresa compartilhe feedback sobre sua performance</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={getSetting('privacy.allowFeedback', true)}
                  onChange={(e) => updateSetting('privacy.allowFeedback', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </>
      ) : (
        // Configurações completas para usuários autenticados
        <>
          <div>
            <label className="block text-sm font-medium mb-2">Retenção de Dados (dias)</label>
            <input
              type="number"
              min="30"
              max="2555"
              value={getSetting('privacy.dataRetentionDays')}
              onChange={(e) => updateSetting('privacy.dataRetentionDays', parseInt(e.target.value))}
              className="w-full p-2 border border-border rounded-lg bg-background"
            />
            <p className="text-xs text-muted-foreground mt-1">Tempo que os dados são mantidos antes da exclusão automática</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Anonimização Automática (dias)</label>
            <input
              type="number"
              min="90"
              max="365"
              value={getSetting('privacy.anonymizeAfterDays')}
              onChange={(e) => updateSetting('privacy.anonymizeAfterDays', parseInt(e.target.value))}
              className="w-full p-2 border border-border rounded-lg bg-background"
            />
            <p className="text-xs text-muted-foreground mt-1">Após este período, dados pessoais são anonimizados</p>
          </div>

          <div className="space-y-4">
            {[
              { key: 'allowDataExport', label: 'Permitir Exportação de Dados', desc: 'Usuários podem exportar seus dados pessoais' },
              { key: 'consentRequired', label: 'Consentimento Obrigatório', desc: 'Exigir consentimento explícito para processamento de dados' }
            ].map(({ key, label, desc }) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-border">
                <div>
                  <div className="font-medium">{label}</div>
                  <div className="text-sm text-muted-foreground">{desc}</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={getSetting(`privacy.${key}`)}
                    onChange={(e) => updateSetting(`privacy.${key}`, e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );

  const AccessibilitySettings = () => (
    <div className="space-y-6">
      {isCandidate() && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-green-900 mb-2">Configurações de Acessibilidade</h4>
          <p className="text-sm text-green-800">
            Ajuste a interface para melhor adequar suas necessidades durante a entrevista.
          </p>
        </div>
      )}
      
      <div className="space-y-4">
        {[
          { key: 'reducedMotion', label: 'Reduzir Animações', desc: 'Diminuir ou remover animações da interface' },
          { key: 'highContrast', label: 'Alto Contraste', desc: 'Aumentar contraste para melhor visibilidade' },
          { key: 'largerFonts', label: 'Fontes Maiores', desc: 'Aumentar tamanho das fontes' },
          { key: 'keyboardNavHints', label: 'Dicas de Navegação', desc: 'Mostrar dicas para navegação por teclado' }
        ].map(({ key, label, desc }) => (
          <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div>
              <div className="font-medium">{label}</div>
              <div className="text-sm text-muted-foreground">{desc}</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={getSetting(`accessibility.${key}`)}
                onChange={(e) => updateSetting(`accessibility.${key}`, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        ))}
      </div>
    </div>
  );

  const SystemSettings = () => (
    <div className="space-y-6">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h4 className="font-medium text-red-900 mb-2">⚠️ Configurações do Sistema</h4>
        <p className="text-sm text-red-800">
          Estas configurações afetam todo o sistema. Use com cuidado.
        </p>
      </div>

      <div className="space-y-4">
        <h4 className="font-medium">Configurações Organizacionais</h4>
        
        <div>
          <label className="block text-sm font-medium mb-2">Modo de Manutenção</label>
          <div className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div>
              <div className="font-medium">Ativar Modo de Manutenção</div>
              <div className="text-sm text-muted-foreground">Impede acesso de usuários não-admin ao sistema</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={getSetting('system.maintenanceMode', false)}
                onChange={(e) => updateSetting('system.maintenanceMode', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Configurações de Backup</label>
          <div className="space-y-2">
            <select
              value={getSetting('system.backupFrequency', 'daily')}
              onChange={(e) => updateSetting('system.backupFrequency', e.target.value)}
              className="w-full p-2 border border-border rounded-lg bg-background"
            >
              <option value="hourly">A cada hora</option>
              <option value="daily">Diário</option>
              <option value="weekly">Semanal</option>
              <option value="monthly">Mensal</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Logs do Sistema</label>
          <div className="space-y-2">
            <select
              value={getSetting('system.logLevel', 'info')}
              onChange={(e) => updateSetting('system.logLevel', e.target.value)}
              className="w-full p-2 border border-border rounded-lg bg-background"
            >
              <option value="debug">Debug (Detalhado)</option>
              <option value="info">Info (Normal)</option>
              <option value="warning">Warning (Avisos)</option>
              <option value="error">Error (Apenas Erros)</option>
            </select>
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="font-medium">Configurações de Segurança</h4>
          
          {[
            { key: 'enforcePasswordPolicy', label: 'Política de Senhas Rigorosa', desc: 'Exigir senhas complexas para todos os usuários' },
            { key: 'enableTwoFactor', label: 'Autenticação de Dois Fatores', desc: 'Habilitar 2FA para contas administrativas' },
            { key: 'enableAuditLog', label: 'Log de Auditoria', desc: 'Registrar todas as ações administrativas' }
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-border">
              <div>
                <div className="font-medium">{label}</div>
                <div className="text-sm text-muted-foreground">{desc}</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={getSetting(`system.${key}`, false)}
                  onChange={(e) => updateSetting(`system.${key}`, e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general': return <GeneralSettings />;
      case 'notifications': return <NotificationSettings />;
      case 'interviews': return <InterviewSettings />;
      case 'reports': return <ReportsSettings />;
      case 'privacy': return <PrivacySettings />;
      case 'accessibility': return <AccessibilitySettings />;
      case 'system': return <SystemSettings />;
      default: return <GeneralSettings />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex overflow-hidden">
        {/* Sidebar com abas */}
        <div className="w-64 bg-muted/30 border-r border-border">
          <div className="p-4 border-b border-border">
            <h2 className="text-lg font-semibold flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Configurações
            </h2>
          </div>
          
          <nav className="p-2">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                  activeTab === id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>

          <div className="absolute bottom-4 left-4 right-4 space-y-2">
            <button
              onClick={exportSettings}
              className="w-full flex items-center space-x-2 px-3 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>Exportar</span>
            </button>
            
            <button
              onClick={resetSettings}
              className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-destructive border border-destructive rounded-lg hover:bg-destructive/10 transition-colors"
            >
              <span>Restaurar Padrões</span>
            </button>
          </div>
        </div>

        {/* Conteúdo principal */}
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="text-lg font-medium">
              {tabs.find(tab => tab.id === activeTab)?.label}
            </h3>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          
          <div className="flex-1 p-6 overflow-y-auto">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;