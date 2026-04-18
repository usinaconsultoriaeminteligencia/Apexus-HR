import React, { createContext, useContext, useState, useEffect } from 'react';

const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings deve ser usado dentro de um SettingsProvider');
  }
  return context;
};

// Configurações padrão
const defaultSettings = {
  // Geral
  theme: 'system', // light, dark, system
  language: 'pt-BR',
  timezone: 'America/Sao_Paulo',
  density: 'comfortable', // compact, comfortable, spacious
  defaultView: 'dashboard',
  
  // Notificações
  notifications: {
    interviewReminders: true,
    candidateStatusChanges: true,
    dailyDigest: true,
    weeklyReport: true,
    quietHoursEnabled: false,
    quietHoursStart: '22:00',
    quietHoursEnd: '08:00',
    channels: {
      email: true,
      inApp: true
    }
  },
  
  // Entrevistas
  interviews: {
    defaultDuration: 60,
    bufferTime: 15,
    enableRecording: true,
    requireConsent: true,
    autoTranscription: true
  },
  
  // Relatórios
  reports: {
    defaultDateRange: '30',
    exportFormat: 'pdf',
    includeCharts: true,
    autoRefresh: true
  },
  
  // Privacidade
  privacy: {
    dataRetentionDays: 365,
    allowDataExport: true,
    anonymizeAfterDays: 180,
    consentRequired: true
  },
  
  // Acessibilidade
  accessibility: {
    reducedMotion: false,
    highContrast: false,
    largerFonts: false,
    keyboardNavHints: true
  }
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(defaultSettings);
  const [isLoading, setIsLoading] = useState(true);
  const [isDirty, setIsDirty] = useState(false);

  // Carregar configurações do localStorage na inicialização
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem('rh:settings');
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      }
    } catch (error) {
      console.error('Erro ao carregar configurações:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Salvar configurações com debounce
  useEffect(() => {
    if (isDirty && !isLoading) {
      const timeoutId = setTimeout(() => {
        try {
          localStorage.setItem('rh:settings', JSON.stringify(settings));
          setIsDirty(false);
        } catch (error) {
          console.error('Erro ao salvar configurações:', error);
        }
      }, 1000);

      return () => clearTimeout(timeoutId);
    }
  }, [settings, isDirty, isLoading]);

  const updateSetting = (path, value) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      const keys = path.split('.');
      let current = newSettings;
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {};
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
    setIsDirty(true);
  };

  const getSetting = (path, defaultValue = null) => {
    const keys = path.split('.');
    let current = settings;
    
    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return defaultValue;
      }
    }
    
    return current;
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
    setIsDirty(true);
  };

  const exportSettings = () => {
    const blob = new Blob([JSON.stringify(settings, null, 2)], { 
      type: 'application/json' 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rh-settings-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const importSettings = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target.result);
        
        // Validação de segurança: bloquear chaves perigosas
        const dangerousKeys = ['__proto__', 'constructor', 'prototype'];
        const hasDangerousKeys = (obj, path = '') => {
          for (const key in obj) {
            if (dangerousKeys.includes(key)) {
              throw new Error(`Chave não permitida encontrada: ${path}${key}`);
            }
            if (obj[key] && typeof obj[key] === 'object') {
              hasDangerousKeys(obj[key], `${path}${key}.`);
            }
          }
        };
        
        hasDangerousKeys(imported);
        
        // Merge seguro apenas de configurações válidas
        const safeImport = {};
        const validTopLevelKeys = Object.keys(defaultSettings);
        
        for (const key of validTopLevelKeys) {
          if (imported[key] !== undefined) {
            safeImport[key] = imported[key];
          }
        }
        
        setSettings(prev => ({ ...prev, ...safeImport }));
        setIsDirty(true);
        
        alert('Configurações importadas com sucesso!');
      } catch (error) {
        console.error('Erro ao importar configurações:', error);
        alert('Erro ao importar configurações. Verifique o formato do arquivo.');
      }
    };
    reader.readAsText(file);
  };

  // Verificação de segurança para evitar erro de preamble
  if (typeof window !== 'undefined' && window.$RefreshReg$) {
    window.$RefreshReg$ = undefined;
    window.$RefreshSig$ = undefined;
  }

  return (
    <SettingsContext.Provider
      value={{
        settings,
        updateSetting,
        getSetting,
        resetSettings,
        exportSettings,
        importSettings,
        isLoading,
        isDirty
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};