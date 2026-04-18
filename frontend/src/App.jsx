import React, { useState, useEffect } from 'react';
import { POSITIONS } from './data/positions.js';
import { SettingsProvider, useSettings } from './contexts/SettingsContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import SettingsModal from './components/SettingsModal';
import LogoutConfirmationDialog from './components/LogoutConfirmationDialog';
import Login from './components/Login';
import ProtectedRoute from './components/ProtectedRoute';
import RoleBasedNavigation from './components/RoleBasedNavigation';
import { 
  LayoutDashboard, 
  Users, 
  UserPlus, 
  Calendar, 
  FileText, 
  LogOut,
  TrendingUp,
  Clock,
  CheckCircle,
  Star,
  BarChart3,
  PieChart,
  Activity,
  Search,
  Filter,
  Download,
  Plus,
  Eye,
  Edit,
  Mic,
  Volume2,
  Trash2,
  Phone,
  Mail,
  MapPin,
  Briefcase,
  GraduationCap,
  Award,
  MessageSquare,
  HelpCircle,
  Moon,
  Sun,
  ChevronDown,
  ChevronRight,
  ArrowUp,
  ArrowDown,
  Bell,
  Settings,
  MessageCircle,
  Video,
  Menu,
  Pin,
  X,
  User
} from 'lucide-react';
import AudioInterview from './components/AudioInterview';
import InterviewsList from './components/InterviewsList';
import CandidateList from './components/CandidateList';
import NewCandidateForm from './components/NewCandidateForm';
import Reports from './components/Reports';
import Analytics from './components/Analytics';
import CandidateDetailsModal from './components/CandidateDetailsModal';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
// Note: CSS files are imported globally in main.jsx

// Sem dados simulados - apenas dados reais da API

// Componente de Métrica
const MetricCard = ({ icon: Icon, title, value, change, changeType, description }) => (
  <div className="metric-card">
    <div className="flex items-center justify-between">
      <div className="flex items-center" style={{ gap: 'var(--space-3)' }}>
        <div className={`p-2 rounded-lg ${
          changeType === 'positive' ? 'bg-green-100 text-green-600' : 
          changeType === 'negative' ? 'bg-red-100 text-red-600' : 
          'bg-blue-100 text-blue-600'
        }`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="metric-label">{title}</p>
          <p className="metric-value">{value}</p>
        </div>
      </div>
      {change && (
        <div className={`flex items-center text-sm ${
          changeType === 'positive' ? 'text-green-600' : 'text-red-600'
        }`} style={{ gap: 'var(--space-1)' }}>
          {changeType === 'positive' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />}
          <span>{change}</span>
        </div>
      )}
    </div>
    {description && (
      <p className="text-small" style={{ marginTop: 'var(--space-2)', color: 'var(--color-gray-500)' }}>{description}</p>
    )}
  </div>
);

// Componente Principal
function AppContent() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [candidateDetailsOpen, setCandidateDetailsOpen] = useState(false);
  const [isInterviewMode, setIsInterviewMode] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { settings, updateSetting, getSetting } = useSettings();
  const { user, userRole, isAuthenticated, isLoading, logout, getRoleDisplayName } = useAuth();
  
  // Aplicar tema do contexto de configurações
  const [darkMode, setDarkMode] = useState(false);

  // Aplicar tema baseado nas configurações
  useEffect(() => {
    const theme = settings.theme || 'system';
    let isDark = false;
    
    if (theme === 'system') {
      isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      
      // Escutar mudanças do tema do sistema
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleSystemThemeChange = (e) => {
        if (settings.theme === 'system') {
          setDarkMode(e.matches);
          document.documentElement.classList.toggle('dark', e.matches);
        }
      };
      
      mediaQuery.addEventListener('change', handleSystemThemeChange);
      return () => mediaQuery.removeEventListener('change', handleSystemThemeChange);
    } else {
      isDark = theme === 'dark';
    }
    
    setDarkMode(isDark);
    document.documentElement.classList.toggle('dark', isDark);
  }, [settings.theme]);
  
  // Aplicar densidade da interface
  useEffect(() => {
    const density = settings.density || 'comfortable';
    document.documentElement.setAttribute('data-density', density);
  }, [settings.density]);
  
  // Aplicar configurações de acessibilidade
  useEffect(() => {
    const accessibility = settings.accessibility || {};
    
    document.documentElement.classList.toggle('reduced-motion', accessibility.reducedMotion);
    document.documentElement.classList.toggle('high-contrast', accessibility.highContrast);
    document.documentElement.classList.toggle('large-fonts', accessibility.largerFonts);
  }, [settings.accessibility]);

  // Redirecionamento inteligente baseado em role após login
  const getDefaultViewForRole = (role) => {
    switch (role) {
      case 'admin':
        return 'dashboard';
      case 'recruiter':
        return 'candidates';
      case 'manager':
        return 'dashboard';
      case 'analyst':
        return 'reports';
      case 'viewer':
        return 'dashboard';
      case 'candidate':
        return 'interview';
      default:
        return 'dashboard';
    }
  };

  // Atualizar view quando autenticação mudar
  useEffect(() => {
    if (isAuthenticated && userRole) {
      const defaultView = getDefaultViewForRole(userRole);
      setCurrentView(defaultView);
    }
  }, [isAuthenticated, userRole]);

  // Manipular login bem-sucedido
  const handleLoginSuccess = (userData) => {
    // Verificação de segurança para garantir que userData existe e tem role
    if (userData && userData.role) {
      const defaultView = getDefaultViewForRole(userData.role);
      setCurrentView(defaultView);
    } else {
      console.warn('Dados de usuário inválidos recebidos no login:', userData);
      // Fallback para dashboard se não conseguir determinar o role
      setCurrentView('dashboard');
    }
  };

  // Manipular logout
  const handleLogout = () => {
    setLogoutDialogOpen(true);
  };

  const handleNavigation = (view) => {
    setCurrentView(view);
    setIsInterviewMode(false);
    setDrawerOpen(false); // Fechar drawer em mobile ao navegar
  };

  // Loading state durante inicialização
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando...</p>
        </div>
      </div>
    );
  }

  // Mostrar tela de login se não autenticado
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const renderDashboard = () => (
    <div className="section-primary">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="heading-1">Dashboard</h1>
          <p className="text-body">Visão geral do sistema de recrutamento</p>
        </div>
      </div>

      <div className="grid cols-4 mb-8">
        <MetricCard
          icon={Users}
          title="Total de Candidatos"
          value="0"
          change={null}
          changeType="positive"
          description="Este mês"
        />
        <MetricCard
          icon={Calendar}
          title="Entrevistas Hoje"
          value="0"
          change={null}
          changeType="neutral"
          description="Aguardando dados"
        />
        <MetricCard
          icon={TrendingUp}
          title="Taxa de Aprovação"
          value="0%"
          change={null}
          changeType="positive"
          description="Este mês"
        />
        <MetricCard
          icon={Star}
          title="Score Médio"
          value="0"
          change={null}
          changeType="positive"
          description="Últimos 30 dias"
        />
      </div>

      <div className="grid cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Candidatos por Mês</h3>
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <p>Nenhum dado disponível</p>
              <p className="text-sm">Aguarde dados reais do sistema</p>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Status dos Candidatos</h3>
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <p>Nenhum dado disponível</p>
              <p className="text-sm">Aguarde dados reais do sistema</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderCandidates = () => (
    <div className="section-primary">
      <CandidateList 
        onNewCandidate={() => setCurrentView('new-candidate')} 
        onViewCandidate={(candidate) => {
          setSelectedCandidate(candidate);
          setCandidateDetailsOpen(true);
        }} 
        onStartInterview={(candidate) => {
          setSelectedCandidate(candidate);
          setIsInterviewMode(true);
        }} 
      />
    </div>
  );

  const renderCurrentView = () => {
    if (isInterviewMode) {
      return <div>Modo Entrevista</div>;
    }

    switch (currentView) {
      case 'dashboard':
        return renderDashboard();
      case 'candidates':
        return (
          <ProtectedRoute allowedRoles={['admin', 'recruiter', 'manager', 'viewer']}>
            {renderCandidates()}
          </ProtectedRoute>
        );
      case 'new-candidate':
        return (
          <ProtectedRoute requiredPermission="create">
            <NewCandidateForm 
              onCancel={() => setCurrentView('candidates')}
              onSuccess={(candidate) => {
                setCurrentView('candidates');
              }}
            />
          </ProtectedRoute>
        );
      case 'interviews':
        return (
          <ProtectedRoute allowedRoles={['admin', 'recruiter', 'manager']}>
            <InterviewsList />
          </ProtectedRoute>
        );
      case 'audio-interview':
        return (
          <ProtectedRoute requiredPermission="conduct_interviews">
            <AudioInterview />
          </ProtectedRoute>
        );
      case 'reports':
        return (
          <ProtectedRoute allowedRoles={['admin', 'manager', 'analyst', 'viewer']}>
            <Reports />
          </ProtectedRoute>
        );
      case 'analytics':
        return (
          <ProtectedRoute allowedRoles={['admin', 'manager', 'analyst']}>
            <Analytics />
          </ProtectedRoute>
        );
      case 'settings':
        return (
          <ProtectedRoute allowedRoles={['admin']}>
            <div className="section-primary"><h1 className="heading-1">Configurações do Sistema</h1></div>
          </ProtectedRoute>
        );
      case 'interview':
        return (
          <ProtectedRoute allowedRoles={['candidate']}>
            <div className="section-primary"><h1 className="heading-1">Minha Entrevista</h1></div>
          </ProtectedRoute>
        );
      default:
        return renderDashboard();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-indigo-950">
      {/* Overlay para mobile drawer */}
      {drawerOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setDrawerOpen(false)}
        />
      )}
      
      {/* Sidebar Moderna com Glass Morphism - Responsiva */}
      <aside className={`
        fixed inset-y-0 left-0 w-72 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl 
        border-r border-gray-200/50 dark:border-gray-700/50 shadow-2xl z-50 
        transition-all duration-300 transform
        ${drawerOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        {/* Header com Gradiente Vibrante */}
        <div className="flex items-center gap-4 p-4 lg:p-6 border-b border-gray-200/50 dark:border-gray-700/50 bg-gradient-to-r from-indigo-500/10 to-teal-500/10 relative">
          {/* Botão fechar drawer - Mobile Only */}
          <button
            onClick={() => setDrawerOpen(false)}
            className="absolute top-4 right-4 lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <X className="h-5 w-5 text-gray-700 dark:text-gray-300" />
          </button>
          <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/25 animate-pulse-slow">
            <Users className="h-8 w-8 text-white" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-teal-600 bg-clip-text text-transparent">Apexus HR</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Plataforma Inteligente</p>
          </div>
        </div>

        {/* Navigation */}
        <RoleBasedNavigation 
          currentView={currentView} 
          onNavigation={handleNavigation} 
        />
        
        {/* User info and logout com Visual Moderno */}
        <div className="mt-auto p-4 lg:p-6 border-t border-gray-200/50 dark:border-gray-700/50 bg-gradient-to-r from-indigo-500/5 to-teal-500/5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg hover:scale-110 transition-transform duration-200">
              <User className="h-6 w-6 text-white" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                {user?.full_name || user?.email || 'Usuário'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {getRoleDisplayName()}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-red-50/50 dark:bg-red-950/20 hover:bg-red-100 dark:hover:bg-red-950/40 transition-all duration-200 group"
          >
            <LogOut className="h-5 w-5 text-red-600 dark:text-red-400 group-hover:scale-110 transition-transform" />
            <span className="text-sm font-medium text-red-600 dark:text-red-400">Sair</span>
          </button>
        </div>
      </aside>

      {/* Main Content com Layout Moderno */}
      <div className="lg:ml-72 transition-all duration-300">
        {/* Header com Glass Effect */}
        <header className="sticky top-0 z-40 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50 shadow-sm h-16">
          <div className="flex items-center justify-between h-full px-4 lg:px-8">
            {/* Hamburger Menu - Mobile Only */}
            <button
              onClick={() => setDrawerOpen(!drawerOpen)}
              className="lg:hidden p-2.5 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200"
            >
              <Menu className="h-6 w-6 text-gray-700 dark:text-gray-300" />
            </button>
            <div className="flex-1 lg:flex-none">
              <h2 className="text-lg lg:text-2xl font-bold bg-gradient-to-r from-indigo-600 to-teal-600 bg-clip-text text-transparent capitalize">
                {currentView.replace('-', ' ')}
              </h2>
              <p className="text-xs lg:text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
                {currentView === 'dashboard' && 'Visão geral do sistema de recrutamento'}
                {currentView === 'candidates' && 'Gerenciar candidatos e aplicações'}
                {currentView === 'new-candidate' && 'Cadastrar novo candidato'}
                {currentView === 'interviews' && 'Acompanhar entrevistas agendadas'}
                {currentView === 'audio-interview' && 'Conduzir entrevista por áudio'}
                {currentView === 'reports' && 'Relatórios e análises detalhadas'}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button 
                onClick={() => {
                  const currentTheme = getSetting('theme', 'system');
                  const nextTheme = currentTheme === 'light' ? 'dark' : currentTheme === 'dark' ? 'system' : 'light';
                  updateSetting('theme', nextTheme);
                }}
                className="p-2.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-200 hover:scale-110 hover:rotate-180 group"
                title={`Tema atual: ${getSetting('theme', 'system') === 'system' ? 'Sistema' : getSetting('theme') === 'dark' ? 'Escuro' : 'Claro'}`}
              >
                {getSetting('theme') === 'system' ? <Sun className="h-5 w-5 text-yellow-500" /> : darkMode ? <Sun className="h-5 w-5 text-yellow-500" /> : <Moon className="h-5 w-5 text-indigo-600" />}
              </button>
              
              <button 
                onClick={() => alert('Notificações: Nenhuma notificação nova')}
                className="p-2.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-200 hover:scale-110 group"
                title="Notificações"
              >
                <Bell className="h-5 w-5 text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 transition-colors" />
              </button>
              
              <button 
                onClick={() => setSettingsOpen(true)}
                className="p-2.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-200 hover:scale-110 group"
                title="Configurações"
              >
                <Settings className="h-5 w-5 text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 transition-colors" />
              </button>
              
              <button 
                onClick={() => alert('Ajuda: Para suporte, entre em contato com a equipe de TI')}
                className="p-2.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-200 hover:scale-110 group"
                title="Ajuda"
              >
                <HelpCircle className="h-5 w-5 text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 transition-colors" />
              </button>
            </div>
          </div>
        </header>

        {/* Main Content com Animação */}
        <main className="p-4 lg:p-8 animate-fade-in">
          <div className="max-w-7xl mx-auto">
            {renderCurrentView()}
          </div>
        </main>
      </div>
      
      {/* Settings Modal */}
      <SettingsModal 
        isOpen={settingsOpen} 
        onClose={() => setSettingsOpen(false)} 
      />
      
      {/* Logout Confirmation Dialog */}
      <LogoutConfirmationDialog 
        open={logoutDialogOpen}
        onOpenChange={setLogoutDialogOpen}
      />

      {/* Candidate Details Modal */}
      <CandidateDetailsModal 
        candidate={selectedCandidate}
        isOpen={candidateDetailsOpen}
        onClose={() => {
          setCandidateDetailsOpen(false);
          setSelectedCandidate(null);
        }}
        onStartInterview={(candidate) => {
          setSelectedCandidate(candidate);
          setIsInterviewMode(true);
        }}
      />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <SettingsProvider>
        <AppContent />
      </SettingsProvider>
    </AuthProvider>
  );
}

export default App;