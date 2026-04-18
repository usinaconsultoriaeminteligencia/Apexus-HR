import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App.jsx";
import PublicInterview from "./components/PublicInterview.jsx";

// FORÇAR LIMPEZA DE SERVICE WORKERS ANTIGOS
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for(let registration of registrations) {
      registration.unregister();
    }
  });
  // Limpar caches também
  if ('caches' in window) {
    caches.keys().then(function(names) {
      for (let name of names) {
        caches.delete(name);
      }
    });
  }
}

// CSS globais — ordem importa:
import "./index.css";               // Tailwind base + componentes + utilities
import "./styles/modern-theme.css"; // Sistema de design moderno e vibrante
import "./styles/design-system.css";// Design system tokens e componentes
import "./App.css";                 // estilos específicos do app

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/interview/:token" element={<PublicInterview />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);

