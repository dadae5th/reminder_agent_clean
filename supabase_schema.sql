-- 3. 완료 기록 테이블
CREATE TABLE IF NOT EXISTS completion_logs (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL,
    completion_method VARCHAR(50) DEFAULT 'email' CHECK (completion_method IN ('email', 'dashboard', 'api')),
    user_agent TEXT,
    ip_address INET,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 이메일 발송 기록 테이블
CREATE TABLE IF NOT EXISTS email_logs (
    id BIGSERIAL PRIMARY KEY,
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    task_count INTEGER DEFAULT 0,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'bounced')),
    error_message TEXT
);

-- 5. 시스템 설정 테이블
CREATE TABLE IF NOT EXISTS system_settings (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);-- supabase_schema.sql - Supabase 데이터베이스 스키마
-- Supabase 프로젝트의 SQL Editor에서 실행하세요

-- 1. 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 업무 테이블
CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    assignee_email VARCHAR(255) NOT NULL REFERENCES users(email) ON UPDATE CASCADE,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'done')),
    creator_name VARCHAR(255),
    due_date DATE,
    hmac_token TEXT UNIQUE,
    last_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 완료 기록 테이블 (이메일에서 체크한 내용 자동 저장)
CREATE TABLE IF NOT EXISTS completion_logs (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL,
    completion_method VARCHAR(50) DEFAULT 'email' CHECK (completion_method IN ('email', 'dashboard', 'api')),
    user_agent TEXT,
    ip_address INET,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 이메일 발송 기록 테이블
CREATE TABLE IF NOT EXISTS email_logs (
    id BIGSERIAL PRIMARY KEY,
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    task_count INTEGER DEFAULT 0,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'bounced')),
    error_message TEXT
);

-- 5. 시스템 설정 테이블
CREATE TABLE IF NOT EXISTS system_settings (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_tasks_assignee_email ON tasks(assignee_email);
CREATE INDEX IF NOT EXISTS idx_tasks_frequency ON tasks(frequency);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_hmac_token ON tasks(hmac_token);
CREATE INDEX IF NOT EXISTS idx_completion_logs_task_id ON completion_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_completion_logs_completed_at ON completion_logs(completed_at);
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at);

-- 기본 시스템 설정 데이터 삽입
INSERT INTO system_settings (key, value, description) VALUES
    ('email_send_time', '09:00', '일일 이메일 발송 시간 (KST)'),
    ('dashboard_title', '해야할일 관리 대시보드', '대시보드 제목'),
    ('email_template_version', '1.0', '이메일 템플릿 버전')
ON CONFLICT (key) DO NOTHING;

-- Row Level Security (RLS) 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE completion_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- RLS 정책 (모든 사용자가 읽기/쓰기 가능하도록 설정)
-- 실제 운영에서는 더 세밀한 권한 설정이 필요합니다

-- 사용자 정책
CREATE POLICY "Users are viewable by everyone" ON users FOR SELECT USING (true);
CREATE POLICY "Users can be inserted by everyone" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can be updated by everyone" ON users FOR UPDATE USING (true);

-- 업무 정책
CREATE POLICY "Tasks are viewable by everyone" ON tasks FOR SELECT USING (true);
CREATE POLICY "Tasks can be inserted by everyone" ON tasks FOR INSERT WITH CHECK (true);
CREATE POLICY "Tasks can be updated by everyone" ON tasks FOR UPDATE USING (true);

-- 완료 기록 정책
CREATE POLICY "Completion logs are viewable by everyone" ON completion_logs FOR SELECT USING (true);
CREATE POLICY "Completion logs can be inserted by everyone" ON completion_logs FOR INSERT WITH CHECK (true);

-- 이메일 로그 정책
CREATE POLICY "Email logs are viewable by everyone" ON email_logs FOR SELECT USING (true);
CREATE POLICY "Email logs can be inserted by everyone" ON email_logs FOR INSERT WITH CHECK (true);

-- 시스템 설정 정책
CREATE POLICY "System settings are viewable by everyone" ON system_settings FOR SELECT USING (true);
CREATE POLICY "System settings can be updated by everyone" ON system_settings FOR UPDATE USING (true);

-- 함수: 업데이트 시간 자동 갱신
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거: updated_at 자동 갱신
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰: 업무 완료 통계
CREATE OR REPLACE VIEW task_completion_stats AS
SELECT 
    t.id,
    t.title,
    t.assignee_email,
    t.frequency,
    t.status,
    t.created_at,
    t.last_completed_at,
    COUNT(cl.id) as completion_count,
    MAX(cl.completed_at) as last_completion
FROM tasks t
LEFT JOIN completion_logs cl ON t.id = cl.task_id
GROUP BY t.id, t.title, t.assignee_email, t.frequency, t.status, t.created_at, t.last_completed_at;

-- 뷰: 일일 완료 통계
CREATE OR REPLACE VIEW daily_completion_stats AS
SELECT 
    DATE(cl.completed_at) as completion_date,
    COUNT(*) as completed_tasks,
    COUNT(DISTINCT cl.task_id) as unique_tasks,
    COUNT(DISTINCT t.assignee_email) as active_users
FROM completion_logs cl
JOIN tasks t ON cl.task_id = t.id
WHERE cl.completed_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(cl.completed_at)
ORDER BY completion_date DESC;
