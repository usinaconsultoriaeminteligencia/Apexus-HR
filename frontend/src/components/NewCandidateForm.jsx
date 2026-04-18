import React, { useState } from 'react';
import { User, Mail, Phone, MapPin, Briefcase, Clock, Save, X } from 'lucide-react';
import { POSITIONS } from '../data/positions.js';

const NewCandidateForm = ({ onCancel, onSuccess }) => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    position_applied: '',
    experience_years: 0,
    current_company: '',
    current_position: '',
    skills: '',
    source: 'manual',
    consent_given: false
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Converter skills string em array
      const skillsArray = formData.skills
        .split(',')
        .map(skill => skill.trim())
        .filter(skill => skill.length > 0);

      const candidateData = {
        ...formData,
        skills: skillsArray,
        experience_years: parseInt(formData.experience_years) || 0
      };

      const response = await fetch('/api/candidates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(candidateData)
      });

      if (response.ok) {
        const newCandidate = await response.json();
        onSuccess && onSuccess(newCandidate);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Erro ao cadastrar candidato');
      }
    } catch (err) {
      console.error('Erro na requisição:', err);
      setError('Erro de conexão. Verifique sua internet.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="section-primary">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="heading-1">Novo Candidato</h1>
          <p className="text-body">Cadastre um novo candidato no sistema</p>
        </div>
        <button 
          onClick={onCancel}
          className="btn btn-outline"
        >
          <X className="h-4 w-4" />
          <span>Cancelar</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Informações Pessoais */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <User className="h-5 w-5" />
              <span>Informações Pessoais</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Digite o nome completo"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  E-mail *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="candidato@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="(11) 99999-9999"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Anos de Experiência
                </label>
                <input
                  type="number"
                  name="experience_years"
                  value={formData.experience_years}
                  onChange={handleChange}
                  min="0"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Informações Profissionais */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <Briefcase className="h-5 w-5" />
              <span>Informações Profissionais</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cargo Desejado *
                </label>
                <select
                  name="position_applied"
                  value={formData.position_applied}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Selecione um cargo</option>
                  {POSITIONS.map((position, index) => (
                    <option key={`position-${index}`} value={position}>
                      {position}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Empresa Atual
                </label>
                <input
                  type="text"
                  name="current_company"
                  value={formData.current_company}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Nome da empresa atual"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cargo Atual
                </label>
                <input
                  type="text"
                  name="current_position"
                  value={formData.current_position}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Cargo atual"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Origem
                </label>
                <select
                  name="source"
                  value={formData.source}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="manual">Cadastro Manual</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="site">Site da Empresa</option>
                  <option value="indicacao">Indicação</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
            </div>
          </div>

          {/* Habilidades */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Habilidades
            </label>
            <textarea
              name="skills"
              value={formData.skills}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Digite as habilidades separadas por vírgula (ex: JavaScript, React, Node.js)"
            />
            <p className="text-xs text-gray-500 mt-1">
              Separe as habilidades por vírgula
            </p>
          </div>

          {/* Consentimento LGPD */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                name="consent_given"
                checked={formData.consent_given}
                onChange={handleChange}
                className="mt-1"
                required
              />
              <div className="text-sm">
                <p className="font-medium text-blue-900">Consentimento LGPD</p>
                <p className="text-blue-700">
                  Confirmo que o candidato autorizou o tratamento de seus dados pessoais 
                  para fins de recrutamento e seleção, conforme a Lei Geral de Proteção de Dados.
                </p>
              </div>
            </div>
          </div>

          {/* Botões */}
          <div className="flex items-center justify-end space-x-4 pt-6 border-t">
            <button
              type="button"
              onClick={onCancel}
              className="btn btn-outline"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
            >
              <Save className="h-4 w-4" />
              <span>{loading ? 'Cadastrando...' : 'Cadastrar Candidato'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewCandidateForm;