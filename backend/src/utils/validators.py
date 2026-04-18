"""
Sistema de validação de dados de entrada
"""
import re
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from email.utils import parseaddr

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exceção para erros de validação"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class Validator:
    """Classe base para validadores"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        if not email or not isinstance(email, str):
            return False
        
        # Regex básico para email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Verificar se parseaddr retorna um email válido
        name, addr = parseaddr(email)
        return bool(addr and '@' in addr)
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de telefone brasileiro"""
        if not phone:
            return True  # Telefone é opcional
        
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', phone)
        
        # Telefone brasileiro: 10 ou 11 dígitos (com DDD)
        return len(digits) in [10, 11]
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Valida formato de URL"""
        if not url:
            return True  # URL é opcional
        
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """Valida se campo é obrigatório"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"Campo '{field_name}' é obrigatório", field_name)
    
    @staticmethod
    def validate_length(value: str, min_length: int = 0, max_length: int = None, 
                       field_name: str = "campo") -> None:
        """Valida comprimento de string"""
        if not isinstance(value, str):
            raise ValidationError(f"Campo '{field_name}' deve ser uma string", field_name)
        
        length = len(value)
        if min_length and length < min_length:
            raise ValidationError(
                f"Campo '{field_name}' deve ter no mínimo {min_length} caracteres",
                field_name
            )
        
        if max_length and length > max_length:
            raise ValidationError(
                f"Campo '{field_name}' deve ter no máximo {max_length} caracteres",
                field_name
            )
    
    @staticmethod
    def validate_range(value: float, min_value: float = None, max_value: float = None,
                      field_name: str = "campo") -> None:
        """Valida valor numérico dentro de um range"""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Campo '{field_name}' deve ser numérico", field_name)
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"Campo '{field_name}' deve ser maior ou igual a {min_value}",
                field_name
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"Campo '{field_name}' deve ser menor ou igual a {max_value}",
                field_name
            )
    
    @staticmethod
    def validate_enum(value: Any, allowed_values: List[Any], field_name: str = "campo") -> None:
        """Valida se valor está em lista de valores permitidos"""
        if value not in allowed_values:
            raise ValidationError(
                f"Campo '{field_name}' deve ser um dos seguintes: {', '.join(map(str, allowed_values))}",
                field_name
            )


class CandidateValidator:
    """Validador específico para candidatos"""
    
    VALID_STATUSES = ['novo', 'triagem', 'entrevista', 'entrevista_realizada', 
                      'aprovado', 'rejeitado', 'contratado', 'desistiu']
    
    @staticmethod
    def validate_candidate_data(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Valida dados de candidato"""
        errors = []
        validated_data = {}
        
        # Campos obrigatórios (apenas na criação)
        if not is_update:
            try:
                Validator.validate_required(data.get('full_name'), 'full_name')
                validated_data['full_name'] = data['full_name'].strip()
                Validator.validate_length(validated_data['full_name'], min_length=2, max_length=255, 
                                         field_name='full_name')
            except ValidationError as e:
                errors.append(str(e))
            
            try:
                Validator.validate_required(data.get('email'), 'email')
                email = data['email'].strip().lower()
                if not Validator.validate_email(email):
                    raise ValidationError("Email inválido", 'email')
                validated_data['email'] = email
            except ValidationError as e:
                errors.append(str(e))
            
            try:
                Validator.validate_required(data.get('position_applied'), 'position_applied')
                validated_data['position_applied'] = data['position_applied'].strip()
                Validator.validate_length(validated_data['position_applied'], min_length=2, max_length=255,
                                         field_name='position_applied')
            except ValidationError as e:
                errors.append(str(e))
        else:
            # Na atualização, campos opcionais
            if 'full_name' in data:
                validated_data['full_name'] = data['full_name'].strip()
                try:
                    Validator.validate_length(validated_data['full_name'], min_length=2, max_length=255,
                                             field_name='full_name')
                except ValidationError as e:
                    errors.append(str(e))
            
            if 'email' in data:
                email = data['email'].strip().lower()
                try:
                    if not Validator.validate_email(email):
                        raise ValidationError("Email inválido", 'email')
                    validated_data['email'] = email
                except ValidationError as e:
                    errors.append(str(e))
            
            if 'position_applied' in data:
                validated_data['position_applied'] = data['position_applied'].strip()
                try:
                    Validator.validate_length(validated_data['position_applied'], min_length=2, max_length=255,
                                             field_name='position_applied')
                except ValidationError as e:
                    errors.append(str(e))
        
        # Campos opcionais
        if 'phone' in data and data['phone']:
            phone = data['phone'].strip()
            if not Validator.validate_phone(phone):
                errors.append("Telefone inválido (formato esperado: (XX) XXXXX-XXXX)")
            else:
                validated_data['phone'] = phone
        
        if 'experience_years' in data:
            try:
                experience = int(data['experience_years'])
                Validator.validate_range(experience, min_value=0, max_value=50, field_name='experience_years')
                validated_data['experience_years'] = experience
            except (ValueError, ValidationError) as e:
                errors.append(f"Anos de experiência inválidos: {str(e)}")
        
        if 'status' in data:
            try:
                Validator.validate_enum(data['status'], CandidateValidator.VALID_STATUSES, 'status')
                validated_data['status'] = data['status']
            except ValidationError as e:
                errors.append(str(e))
        
        if 'linkedin_url' in data and data['linkedin_url']:
            if not Validator.validate_url(data['linkedin_url']):
                errors.append("URL do LinkedIn inválida")
            else:
                validated_data['linkedin_url'] = data['linkedin_url'].strip()
        
        if 'portfolio_url' in data and data['portfolio_url']:
            if not Validator.validate_url(data['portfolio_url']):
                errors.append("URL do portfólio inválida")
            else:
                validated_data['portfolio_url'] = data['portfolio_url'].strip()
        
        # Scores (0-100)
        for score_field in ['technical_score', 'behavioral_score', 'cultural_fit_score', 'ai_confidence']:
            if score_field in data:
                try:
                    score = float(data[score_field])
                    Validator.validate_range(score, min_value=0.0, max_value=100.0, field_name=score_field)
                    validated_data[score_field] = score
                except (ValueError, ValidationError) as e:
                    errors.append(f"Score '{score_field}' inválido: {str(e)}")
        
        # Skills (lista ou string)
        if 'skills' in data:
            if isinstance(data['skills'], list):
                validated_data['skills'] = [str(skill).strip() for skill in data['skills'] if skill]
            elif isinstance(data['skills'], str):
                validated_data['skills'] = [s.strip() for s in data['skills'].split(',') if s.strip()]
            else:
                errors.append("Skills deve ser uma lista ou string")
        
        if errors:
            raise ValidationError("Erros de validação: " + "; ".join(errors))
        
        return validated_data


class InterviewValidator:
    """Validador específico para entrevistas"""
    
    VALID_TYPES = ['audio', 'video', 'presencial']
    VALID_STATUSES = ['agendada', 'em_andamento', 'concluida', 'cancelada']
    
    @staticmethod
    def validate_interview_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados de entrevista"""
        errors = []
        validated_data = {}
        
        # Campos obrigatórios
        try:
            Validator.validate_required(data.get('candidate_id'), 'candidate_id')
            candidate_id = int(data['candidate_id'])
            if candidate_id <= 0:
                raise ValidationError("ID do candidato inválido", 'candidate_id')
            validated_data['candidate_id'] = candidate_id
        except (ValueError, ValidationError) as e:
            errors.append(f"candidate_id: {str(e)}")
        
        try:
            Validator.validate_required(data.get('position'), 'position')
            validated_data['position'] = data['position'].strip()
            Validator.validate_length(validated_data['position'], min_length=2, max_length=255,
                                     field_name='position')
        except ValidationError as e:
            errors.append(str(e))
        
        # Campos opcionais
        if 'interview_type' in data:
            try:
                Validator.validate_enum(data['interview_type'], InterviewValidator.VALID_TYPES, 'interview_type')
                validated_data['interview_type'] = data['interview_type']
            except ValidationError as e:
                errors.append(str(e))
        
        if 'status' in data:
            try:
                Validator.validate_enum(data['status'], InterviewValidator.VALID_STATUSES, 'status')
                validated_data['status'] = data['status']
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            raise ValidationError("Erros de validação: " + "; ".join(errors))
        
        return validated_data

