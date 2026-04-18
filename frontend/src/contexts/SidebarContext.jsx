import React, { createContext, useContext, useState, useEffect } from 'react';
import { useIsMobile } from '../hooks/use-mobile';

const SidebarContext = createContext();

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within SidebarProvider');
  }
  return context;
};

export const SidebarProvider = ({ children }) => {
  const isMobile = useIsMobile();
  
  // Estado do sidebar
  const [isPinned, setIsPinned] = useState(() => {
    // Recupera estado salvo no localStorage (apenas desktop)
    if (typeof window !== 'undefined' && !isMobile) {
      return localStorage.getItem('sidebar-pinned') === 'true';
    }
    return false;
  });
  
  const [isOpen, setIsOpen] = useState(false); // Para hover flyout/mobile drawer
  const [isHovered, setIsHovered] = useState(false); // Para hover estado
  
  // Persiste estado do pin
  useEffect(() => {
    if (!isMobile) {
      localStorage.setItem('sidebar-pinned', isPinned.toString());
    }
  }, [isPinned, isMobile]);
  
  // Reset estados no mobile
  useEffect(() => {
    if (isMobile) {
      setIsPinned(false);
      setIsHovered(false);
    }
  }, [isMobile]);
  
  const togglePin = () => {
    if (!isMobile) {
      setIsPinned(prev => !prev);
      setIsHovered(false); // Limpa hover quando pina
    }
  };
  
  const toggleOpen = () => {
    setIsOpen(prev => !prev);
  };
  
  const handleMouseEnter = () => {
    if (!isMobile && !isPinned) {
      setIsHovered(true);
    }
  };
  
  const handleMouseLeave = () => {
    if (!isMobile && !isPinned) {
      setIsHovered(false);
    }
  };
  
  // Computed states
  const isExpanded = isMobile ? isOpen : (isPinned || isHovered);
  const showLabels = isExpanded;
  
  const value = {
    // Estados
    isPinned,
    isOpen,
    isHovered,
    isExpanded,
    showLabels,
    isMobile,
    
    // Ações
    togglePin,
    toggleOpen,
    setIsOpen,
    handleMouseEnter,
    handleMouseLeave,
    
    // Computed
    sidebarWidth: isExpanded ? 280 : 72,
    railWidth: 72,
    expandedWidth: 280
  };
  
  return (
    <SidebarContext.Provider value={value}>
      {children}
    </SidebarContext.Provider>
  );
};