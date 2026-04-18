# Sistema de Design Profissional - HR Corporativo

## 📋 Visão Geral

O sistema foi redesenhado para apresentar uma aparência **profissional, sóbria e corporativa**, adequada para um ambiente empresarial de Recursos Humanos.

## 🎨 Paleta de Cores Corporativa

### Cores Primárias

**Azul Corporativo** - Cor principal do sistema
- `#334E68` - Tom sóbrio e confiável
- Usado em: botões primários, links, elementos de destaque

**Cinza Neutro** - Cor secundária
- `#757575` - Tom neutro e profissional
- Usado em: textos secundários, bordas, fundos

### Cores de Estado

**Sucesso**: `#047857` - Verde moderado
**Aviso**: `#B45309` - Amarelo moderado
**Erro**: `#B91C1C` - Vermelho moderado
**Informação**: `#0369A1` - Azul informativo

### Background

- **Fundo principal**: `#FAFAFA` (cinza muito claro)
- **Cards e elementos**: `#FFFFFF` (branco)
- **Bordas**: `#E0E0E0` (cinza claro)

## 🔤 Tipografia

**Fonte**: Inter
- Peso leve (300) para textos longos
- Peso normal (400) para corpo de texto
- Peso médio (500) para labels
- Peso semibold (600) para títulos
- Peso bold (700) para destaques

## 📐 Componentes

### Botões

```html
<!-- Botão Primário -->
<button class="btn btn-primary">Ação Principal</button>

<!-- Botão Secundário -->
<button class="btn btn-secondary">Ação Secundária</button>

<!-- Botão Outline -->
<button class="btn btn-outline">Delineado</button>

<!-- Botão Ghost -->
<button class="btn btn-ghost">Sutil</button>

<!-- Tamanhos -->
<button class="btn btn-primary btn-sm">Pequeno</button>
<button class="btn btn-primary">Normal</button>
<button class="btn btn-primary btn-lg">Grande</button>
```

### Cards

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Título do Card</h3>
    <p class="card-subtitle">Subtítulo opcional</p>
  </div>
  <div class="card-body">
    Conteúdo do card
  </div>
</div>
```

### Tabelas

```html
<div class="table-container">
  <table>
    <thead>
      <tr>
        <th>Coluna 1</th>
        <th>Coluna 2</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Dado 1</td>
        <td>Dado 2</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Formulários

```html
<div class="form-group">
  <label class="form-label">Nome do Campo</label>
  <input type="text" class="form-input" placeholder="Digite aqui">
  <p class="form-helper">Texto de ajuda</p>
</div>
```

### Badges

```html
<span class="badge badge-primary">Novo</span>
<span class="badge badge-success">Ativo</span>
<span class="badge badge-warning">Pendente</span>
<span class="badge badge-danger">Cancelado</span>
<span class="badge badge-gray">Neutro</span>
```

### Navegação

```html
<nav class="nav-sidebar">
  <a href="#" class="nav-item nav-item-active">
    <span>Dashboard</span>
  </a>
  <a href="#" class="nav-item">
    <span>Candidatos</span>
  </a>
  
  <div class="nav-group-title">Seção</div>
  
  <a href="#" class="nav-item">
    <span>Relatórios</span>
  </a>
</nav>
```

### Métricas e KPIs

```html
<div class="metric-card">
  <p class="metric-label">Total de Candidatos</p>
  <p class="metric-value">1,234</p>
  <div class="metric-change metric-change-positive">
    ↑ 12% vs mês anterior
  </div>
</div>
```

## 🎭 Classes Utilitárias Tailwind

### Cores com Tailwind

```html
<!-- Background -->
<div class="bg-primary">Fundo azul corporativo</div>
<div class="bg-gray-50">Fundo cinza claro</div>

<!-- Texto -->
<p class="text-primary">Texto azul corporativo</p>
<p class="text-gray-600">Texto cinza médio</p>

<!-- Bordas -->
<div class="border border-gray-300">Com borda</div>
```

### Botões com Tailwind

```html
<button class="bg-primary hover:bg-primary-800 text-white px-4 py-2 rounded-md transition">
  Botão Customizado
</button>
```

## 📏 Espaçamento

Baseado em múltiplos de 8px:
- `--space-1`: 4px
- `--space-2`: 8px
- `--space-3`: 12px
- `--space-4`: 16px
- `--space-6`: 24px
- `--space-8`: 32px
- `--space-12`: 48px

## 🔄 Transições

- **Rápida**: 150ms - Para hover states
- **Normal**: 200ms - Para a maioria das transições
- **Lenta**: 250ms - Para animações complexas

## ✅ Boas Práticas

### Do's ✓

- Use tons neutros e profissionais
- Mantenha hierarquia visual clara
- Use espaçamento consistente
- Privilegie legibilidade sobre estética
- Mantenha contraste adequado para acessibilidade

### Don'ts ✗

- Evite cores vibrantes ou infantis
- Não use gradientes chamativos
- Evite animações excessivas
- Não use sombras muito fortes
- Evite bordas arredondadas demais

## 🌓 Modo Escuro

O sistema suporta modo escuro automaticamente. As cores são ajustadas para manter a profissionalidade:

```html
<!-- Ativar modo escuro -->
<html class="dark">
  ...
</html>
```

## 📱 Responsividade

O design é totalmente responsivo:
- Desktop: Layout completo
- Tablet: Sidebar compacta
- Mobile: Sidebar oculta (menu hambúrguer)

## 🔗 Importação

Para usar o sistema de design profissional, importe o CSS no seu arquivo principal:

```css
/* No seu arquivo CSS principal ou index.css */
@import './styles/professional-theme.css';
```

Ou use com Tailwind (já configurado):

```jsx
import './index.css';
```

## 📊 Comparação: Antes vs Depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Cores primárias** | Indigo vibrante (#4F46E5) | Azul corporativo (#334E68) |
| **Cores secundárias** | Teal vibrante (#0D9488) | Cinza neutro (#757575) |
| **Gradientes** | Coloridos e chamativos | Sutis ou removidos |
| **Bordas** | Muito arredondadas (24px) | Moderadas (8-12px) |
| **Sombras** | Coloridas (glow) | Sutis e neutras |
| **Animações** | Bounce, float, shimmer | Transições suaves |
| **Tom geral** | Infantil e vibrante | Profissional e sóbrio |

## 🎯 Objetivo

Transmitir **confiabilidade, profissionalismo e seriedade** - características essenciais para um sistema de gestão de RH empresarial.
