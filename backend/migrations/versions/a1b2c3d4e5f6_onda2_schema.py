"""add feedback, appointment, assessment tables and interview sharing fields

Revision ID: a1b2c3d4e5f6
Revises: 33fe37926e5a
Create Date: 2026-04-17 00:00:00.000000

Handoff Onda 2 — item 3.1:
- Cria tabelas `feedbacks`, `appointments` e `interview_assessments`.
- Acrescenta campos de compartilhamento/convite em `interviews`
  (interview_token, token_expires_at, invitation_*, token_accessed_at,
  token_access_count) com índice único em `interview_token` e índice
  composto em (status, started_at) para dashboards.

Observação: esta migration foi escrita à mão (o dev Windows não tinha
Postgres rodando para `flask db migrate`). Ela reflete fielmente os
modelos em `backend/src/models/*.py` na data de criação.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '33fe37926e5a'
branch_labels = None
depends_on = None


def upgrade():
    # --- interviews: novos campos de compartilhamento e índices ---
    with op.batch_alter_table('interviews', schema=None) as batch_op:
        batch_op.add_column(sa.Column('interview_token', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('token_expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('invitation_sent_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('invitation_channel', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column(
            'invitation_status', sa.String(length=20), nullable=True, server_default='pending'
        ))
        batch_op.add_column(sa.Column('invitation_phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('invitation_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('token_accessed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column(
            'token_access_count', sa.Integer(), nullable=True, server_default='0'
        ))
        batch_op.create_index(
            batch_op.f('ix_interviews_interview_token'),
            ['interview_token'], unique=True,
        )
        batch_op.create_index(
            'ix_interviews_status_started_at',
            ['status', 'started_at'], unique=False,
        )

    # --- feedbacks ---
    op.create_table(
        'feedbacks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('interview_id', sa.Integer(), nullable=True),
        sa.Column('candidate_id', sa.Integer(), nullable=True),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('priority', sa.String(length=20), nullable=True, server_default='medium'),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        # colunas do AuditMixin
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('consent_date', sa.DateTime(), nullable=True),
        sa.Column('data_retention_date', sa.DateTime(), nullable=True),
        sa.Column('anonymized', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('anonymized_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('feedbacks', schema=None) as batch_op:
        batch_op.create_index(
            'ix_feedbacks_status_priority', ['status', 'priority'], unique=False
        )

    # --- appointments ---
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('interviewer_id', sa.Integer(), nullable=False),
        sa.Column('interview_id', sa.Integer(), nullable=True),
        sa.Column('appointment_token', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('timezone', sa.String(length=50), nullable=True, server_default='America/Sao_Paulo'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('confirmation_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('reminder_sent', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
        sa.Column('confirmation_sent', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('confirmation_sent_at', sa.DateTime(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('meeting_type', sa.String(length=50), nullable=True, server_default='audio'),
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        # AuditMixin
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('consent_date', sa.DateTime(), nullable=True),
        sa.Column('data_retention_date', sa.DateTime(), nullable=True),
        sa.Column('anonymized', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('anonymized_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.ForeignKeyConstraint(['interviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ),
        sa.ForeignKeyConstraint(['cancelled_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('appointments', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_appointments_appointment_token'),
            ['appointment_token'], unique=True,
        )
        batch_op.create_index(
            'ix_appointments_scheduled_at', ['scheduled_at'], unique=False,
        )

    # --- interview_assessments (auditoria de scoring) ---
    op.create_table(
        'interview_assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('interview_id', sa.Integer(), nullable=False),
        sa.Column('question_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('answer_excerpt', sa.Text(), nullable=True),
        sa.Column('rubric_id', sa.String(length=100), nullable=False),
        sa.Column('rubric_version', sa.String(length=40), nullable=False),
        sa.Column('dimension', sa.String(length=100), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='0'),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('prompt_hash', sa.String(length=64), nullable=True),
        sa.Column(
            'human_review_status', sa.String(length=20),
            nullable=False, server_default='pending',
        ),
        sa.Column('human_reviewer_id', sa.Integer(), nullable=True),
        sa.Column('human_review_notes', sa.Text(), nullable=True),
        sa.Column('adjusted_score', sa.Float(), nullable=True),
        sa.Column('human_reviewed_at', sa.DateTime(), nullable=True),
        # AuditMixin
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('consent_date', sa.DateTime(), nullable=True),
        sa.Column('data_retention_date', sa.DateTime(), nullable=True),
        sa.Column('anonymized', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('anonymized_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ),
        sa.ForeignKeyConstraint(['human_reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('interview_assessments', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_interview_assessments_interview_id'),
            ['interview_id'], unique=False,
        )
        batch_op.create_index(
            batch_op.f('ix_interview_assessments_rubric_id'),
            ['rubric_id'], unique=False,
        )
        batch_op.create_index(
            'ix_interview_assessments_interview_rubric',
            ['interview_id', 'rubric_id'], unique=False,
        )


def downgrade():
    with op.batch_alter_table('interview_assessments', schema=None) as batch_op:
        batch_op.drop_index('ix_interview_assessments_interview_rubric')
        batch_op.drop_index(batch_op.f('ix_interview_assessments_rubric_id'))
        batch_op.drop_index(batch_op.f('ix_interview_assessments_interview_id'))
    op.drop_table('interview_assessments')

    with op.batch_alter_table('appointments', schema=None) as batch_op:
        batch_op.drop_index('ix_appointments_scheduled_at')
        batch_op.drop_index(batch_op.f('ix_appointments_appointment_token'))
    op.drop_table('appointments')

    with op.batch_alter_table('feedbacks', schema=None) as batch_op:
        batch_op.drop_index('ix_feedbacks_status_priority')
    op.drop_table('feedbacks')

    with op.batch_alter_table('interviews', schema=None) as batch_op:
        batch_op.drop_index('ix_interviews_status_started_at')
        batch_op.drop_index(batch_op.f('ix_interviews_interview_token'))
        batch_op.drop_column('token_access_count')
        batch_op.drop_column('token_accessed_at')
        batch_op.drop_column('invitation_message')
        batch_op.drop_column('invitation_phone')
        batch_op.drop_column('invitation_status')
        batch_op.drop_column('invitation_channel')
        batch_op.drop_column('invitation_sent_at')
        batch_op.drop_column('token_expires_at')
        batch_op.drop_column('interview_token')
