/**
 * Exemplo de uso do VoiceProfileAssistant
 * 
 * Este arquivo mostra como integrar o componente VoiceProfileAssistant
 * no sistema existente de RH.
 */

import React, { useState } from 'react';
import VoiceProfileAssistant from './VoiceProfileAssistant';
import { POSITIONS, POSITION_CATEGORIES } from '../data/positions';

/**
 * OPÇÃO 1: Uso Básico
 * Componente standalone para página dedicada de entrevista por voz
 */
export function VoiceInterviewPage() {
  const [candidateName, setCandidateName] = useState('');
  const [position, setPosition] = useState('');
  const [seniority, setSeniority] = useState('Pleno');
  const [started, setStarted] = useState(false);

  const handleComplete = (result) => {
    console.log('Avaliação completa:', result);
    alert(`Avaliação salva com sucesso! Score: ${result.score_final}`);
    setStarted(false);
  };

  if (!started) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Entrevista por Voz</h1>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Nome Completo</label>
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Ex: João Silva"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Cargo Pretendido</label>
            <select
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">Selecione...</option>
              {Object.entries(POSITION_CATEGORIES).map(([category, positions]) => (
                <optgroup key={category} label={category}>
                  {positions.map(pos => (
                    <option key={pos} value={pos}>{pos}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Nível</label>
            <select
              value={seniority}
              onChange={(e) => setSeniority(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="Júnior">Júnior</option>
              <option value="Pleno">Pleno</option>
              <option value="Sênior">Sênior</option>
              <option value="Especialista">Especialista</option>
            </select>
          </div>

          <button
            onClick={() => setStarted(true)}
            disabled={!candidateName || !position}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Iniciar Entrevista
          </button>
        </div>
      </div>
    );
  }

  return (
    <VoiceProfileAssistant
      candidateName={candidateName}
      position={position}
      seniority={seniority}
      onComplete={handleComplete}
    />
  );
}

/**
 * OPÇÃO 2: Integração no CandidateList
 * Adicionar botão "Entrevista por Voz" na lista de candidatos
 */
export function CandidateListWithVoice() {
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  const handleStartVoiceInterview = (candidate) => {
    setSelectedCandidate(candidate);
  };

  if (selectedCandidate) {
    return (
      <div className="p-6">
        <button
          onClick={() => setSelectedCandidate(null)}
          className="mb-4 text-blue-600 hover:underline"
        >
          ← Voltar para lista
        </button>
        
        <VoiceProfileAssistant
          candidateName={selectedCandidate.full_name}
          position={selectedCandidate.position}
          seniority={selectedCandidate.seniority || 'Pleno'}
          onComplete={() => setSelectedCandidate(null)}
        />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Candidatos</h2>
      {/* Lista de candidatos com botão de entrevista por voz */}
      <div className="space-y-2">
        {/* Exemplo de candidato */}
        <div className="p-4 border rounded-lg flex justify-between items-center">
          <div>
            <h3 className="font-semibold">Maria Silva</h3>
            <p className="text-sm text-gray-600">Desenvolvedora React</p>
          </div>
          <button
            onClick={() => handleStartVoiceInterview({
              full_name: 'Maria Silva',
              position: 'Desenvolvedor React',
              seniority: 'Pleno'
            })}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            🎙️ Entrevista por Voz
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * OPÇÃO 3: Modal/Popup
 * Usar como modal sobreposto à interface atual
 */
export function VoiceInterviewModal({ isOpen, onClose, candidate }) {
  if (!isOpen || !candidate) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-auto">
        <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold">Entrevista por Voz</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕ Fechar
          </button>
        </div>
        
        <div className="p-6">
          <VoiceProfileAssistant
            candidateName={candidate.full_name}
            position={candidate.position}
            seniority={candidate.seniority || 'Pleno'}
            onComplete={(result) => {
              console.log('Resultado:', result);
              onClose();
            }}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * OPÇÃO 4: Integração no App.jsx
 * 
 * Adicione estas linhas no seu App.jsx:
 * 
 * import VoiceProfileAssistant from './components/VoiceProfileAssistant';
 * 
 * // Em algum lugar do render:
 * {currentView === 'voice-interview' && (
 *   <VoiceProfileAssistant
 *     candidateName="Nome do Candidato"
 *     position="Cargo"
 *     seniority="Pleno"
 *     onComplete={(result) => {
 *       console.log('Avaliação completa:', result);
 *       setCurrentView('dashboard');
 *     }}
 *   />
 * )}
 */

/**
 * OPÇÃO 5: Auto-start (para links compartilhados)
 * Útil quando candidato acessa link direto de entrevista
 */
export function VoiceInterviewAutoStart({ candidateData }) {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <VoiceProfileAssistant
        candidateName={candidateData.name}
        position={candidateData.position}
        seniority={candidateData.seniority}
        autoStart={true}
        onComplete={(result) => {
          window.location.href = '/obrigado';
        }}
      />
    </div>
  );
}

export default VoiceInterviewPage;
