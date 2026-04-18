# TalentIA

## Overview
TalentIA is an AI-powered HR recruitment system tailored for the Brazilian market. Its core purpose is to streamline the hiring process through intelligent audio-based interviews, automated candidate scoring, and comprehensive behavioral analysis, all while ensuring LGPD compliance. The system supports over 75 job positions, offering real-time audio processing and AI-driven recommendations to inform hiring decisions. TalentIA aims to provide a unified, professional, and technologically advanced solution for enterprise HR operations in Brazil.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The system features a professional, sober, and corporate design with a focus on trust and reliability. It uses a professional corporate blue (#334E68) and neutral grays, avoiding excessive gradients, glow effects, and animations. UI elements include moderate border radius, subtle shadows, and clean typography. The interface is fully responsive, supporting mobile devices with a hamburger menu, side drawer, card-based tables, optimized forms, and touch targets. It also functions as a Progressive Web App (PWA). The login screen is designed to be modern and visually appealing, with animated gradient backgrounds, glass morphism effects, and interactive elements.

### Technical Implementations
The frontend is built with React 18+ and Vite, using Tailwind CSS for styling and a custom component library with Lucide React icons. State management is handled by React hooks and context. The backend uses Flask (Python 3.11+), structured with modular blueprints. SQLAlchemy and Flask-SQLAlchemy manage database operations with PostgreSQL. Authentication is JWT-based using Flask-JWT-Extended, implementing role-based access control (RBAC). The API is RESTful with versioned endpoints. Audio processing leverages Librosa, and AI integration is primarily with OpenAI API for analysis and scoring. Celery handles background jobs. Security measures include rate limiting, CORS, and comprehensive security headers.

### Feature Specifications
Key features include:
- **Audio Interviews**: Real-time processing, transcription, and AI-driven analysis.
- **AI Scoring**: Automated evaluation of technical, behavioral, and cultural fit (0-10 scale), and DISC personality profiles with hiring recommendations.
- **LGPD Compliance**: Built-in privacy controls, data export, anonymization, and consent tracking.
- **Multi-role Support**: Admin, recruiter, manager, analyst, and viewer roles with role-based navigation.
- **Interview Sharing System**: Unique UUID tokens for sharing via email, SMS, WhatsApp, or direct link, with public access pages and configurable link expiration.
- **Security**: JWT tokens with refresh rotation, RBAC, Redis-backed rate limiting, password hashing (bcrypt), secure session management, HTTPS enforcement (HSTS), and input validation.

### System Design Choices
The system emphasizes a modular backend structure and a responsive, mobile-first frontend. It incorporates comprehensive error handling and fallback mechanisms, such as gTTS for text-to-speech when OpenAI API is unavailable. Data integrity is maintained through PostgreSQL, Alembic for migrations, and features like soft deletion and anonymization. Security is paramount, with a robust authentication and authorization system, and a focus on enterprise-grade compliance. Logging is structured and detailed for monitoring.

## External Dependencies

### AI Services
- **OpenAI API**: Used for candidate analysis, interview question generation, behavioral scoring, and text-to-speech (TTS).
- **Librosa**: For audio feature extraction and voice analysis.

### Database & Cache
- **PostgreSQL**: Primary relational database.
- **Redis**: For session storage, caching, and rate limiting.

### Development & Deployment
- **Docker**: For containerized deployment.
- **Gunicorn**: Production WSGI server.
- **Nginx**: Reverse proxy and static file serving (in production).

### Audio Processing
- **Librosa**: Advanced audio analysis.
- **SoundFile**: Audio file I/O.
- **Pydub**: Audio format conversion.

### Monitoring & Observability
- **Prometheus**: Metrics collection.
- **Flask-Talisman**: For HTTPS enforcement and security headers.
- **Flask-Limiter**: For request rate limiting.
- **gtts**: Google Text-to-Speech library (fallback for OpenAI TTS).