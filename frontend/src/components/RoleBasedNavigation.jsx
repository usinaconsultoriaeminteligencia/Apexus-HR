import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  LayoutDashboard, 
  Users, 
  UserPlus, 
  Calendar, 
  FileText, 
  BarChart3,
  Settings,
  Mic,
  Eye,
  TrendingUp,
  Activity,
  ChevronRight
} from 'lucide-react';

// Configuração de navegação baseada em roles
const ROLE_NAVIGATION = {
  admin: [
    { group: 'Principal', items: [
      { key: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', badge: null },
      { key: 'candidates', icon: Users, label: 'Candidatos', badge: null },
      { key: 'new-candidate', icon: UserPlus, label: 'Novo Candidato', badge: null },
    ]},
    { group: 'Entrevistas', items: [
      { key: 'interviews', icon: Calendar, label: 'Entrevistas', badge: null },
      { key: 'audio-interview', icon: Mic, label: 'Entrevista por Áudio', badge: null },
    ]},
    { group: 'Análises', items: [
      { key: 'reports', icon: FileText, label: 'Relatórios', badge: null },
      { key: 'analytics', icon: BarChart3, label: 'Analytics', badge: null },
      { key: 'settings', icon: Settings, label: 'Configurações', badge: null },
    ]}
  ],
  recruiter: [
    { group: 'Principal', items: [
      { key: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', badge: null },
      { key: 'candidates', icon: Users, label: 'Candidatos', badge: null },
      { key: 'new-candidate', icon: UserPlus, label: 'Novo Candidato', badge: null },
    ]},
    { group: 'Entrevistas', items: [
      { key: 'interviews', icon: Calendar, label: 'Entrevistas', badge: null },
      { key: 'audio-interview', icon: Mic, label: 'Entrevista por Áudio', badge: null },
    ]}
  ],
  manager: [
    { group: 'Principal', items: [
      { key: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', badge: null },
      { key: 'candidates', icon: Users, label: 'Candidatos', badge: null },
    ]},
    { group: 'Análises', items: [
      { key: 'reports', icon: FileText, label: 'Relatórios', badge: null },
      { key: 'analytics', icon: BarChart3, label: 'Analytics', badge: null },
    ]}
  ],
  analyst: [
    { group: 'Principal', items: [
      { key: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', badge: null },
    ]},
    { group: 'Análises', items: [
      { key: 'reports', icon: FileText, label: 'Relatórios', badge: null },
      { key: 'analytics', icon: BarChart3, label: 'Analytics', badge: null },
      { key: 'trends', icon: TrendingUp, label: 'Tendências', badge: null },
    ]}
  ],
  viewer: [
    { group: 'Principal', items: [
      { key: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', badge: null },
      { key: 'candidates', icon: Eye, label: 'Ver Candidatos', badge: null },
      { key: 'reports', icon: FileText, label: 'Ver Relatórios', badge: null },
    ]}
  ],
  candidate: [
    { group: 'Principal', items: [
      { key: 'interview', icon: Mic, label: 'Minha Entrevista', badge: null },
      { key: 'status', icon: Activity, label: 'Status', badge: null },
    ]}
  ]
};

const RoleBasedNavigation = ({ currentView, onNavigation }) => {
  const { userRole, getRoleDisplayName } = useAuth();
  
  // Obter navegação para o role atual
  const navigationGroups = ROLE_NAVIGATION[userRole] || ROLE_NAVIGATION.viewer;

  return (
    <nav className="flex-1 px-4 py-6 space-y-6 overflow-y-auto">
      {navigationGroups.map((group, groupIndex) => (
        <div key={groupIndex} className="space-y-1">
          <h3 className="px-3 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
            {group.group}
          </h3>
          <div className="space-y-1">
            {group.items.map((item) => {
              const isActive = currentView === item.key;
              const Icon = item.icon;
              
              return (
                <button
                  key={item.key}
                  onClick={() => onNavigation(item.key)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium
                    transition-all duration-200 ease-out relative group
                    ${isActive 
                      ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-lg shadow-indigo-500/25' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/50 dark:hover:bg-gray-700/50 hover:scale-[1.02]'
                    }
                  `}
                >
                  {/* Indicador de página ativa */}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r-full animate-pulse" />
                  )}
                  
                  {/* Ícone com animação */}
                  <Icon className={`
                    w-5 h-5 flex-shrink-0 transition-transform duration-200
                    ${isActive ? 'text-white' : 'text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 group-hover:scale-110'}
                  `} />
                  
                  {/* Label */}
                  <span className="flex-1 text-left">{item.label}</span>
                  
                  {/* Badge se houver */}
                  {item.badge && (
                    <span className={`
                      px-2 py-0.5 text-xs font-medium rounded-full
                      ${isActive 
                        ? 'bg-white/20 text-white' 
                        : 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400'
                      }
                    `}>
                      {item.badge}
                    </span>
                  )}
                  
                  {/* Chevron animado no hover */}
                  <ChevronRight className={`
                    w-4 h-4 opacity-0 -ml-2 transition-all duration-200
                    ${isActive ? 'opacity-100 ml-0' : 'group-hover:opacity-100 group-hover:ml-0'}
                  `} />
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
};

export default RoleBasedNavigation;