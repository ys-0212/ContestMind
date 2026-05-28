-- =================================================================================
-- ContestMind Supabase Schema Definition
-- Run this in the Supabase SQL Editor to initialize the relational database.
-- =================================================================================

-- 1. Users Table
-- If using Supabase Auth, you might want to link id to auth.users.id
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codeforces_handle VARCHAR(255) UNIQUE NOT NULL,
    current_rating INTEGER DEFAULT 0,
    max_rating INTEGER DEFAULT 0,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Chat Sessions Table
-- Links a continuous conversation thread to a specific user.
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Chat Messages Table
-- Stores individual messages (from User and AI Assistant) linked to a session.
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. User Attempts Table (Update existing or create new)
-- Link Codeforces submissions to the local user account.
CREATE TABLE IF NOT EXISTS public.user_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    handle VARCHAR(255) NOT NULL, -- Keep handle for quick Codeforces Syncs
    problem_id VARCHAR(50) NOT NULL,
    verdict VARCHAR(50) NOT NULL,
    rating INTEGER,
    attempt_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(handle, problem_id, verdict) -- Prevent duplicate attempt logs
);

-- 5. Hint Requests Table
-- Log when users request hints for analytics.
CREATE TABLE IF NOT EXISTS public.hint_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    problem_id VARCHAR(50) NOT NULL,
    hint_level INTEGER NOT NULL CHECK (hint_level IN (1, 2, 3)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Fix for existing tables from Tier 1: forcefully add the missing columns so indexes don't fail
ALTER TABLE public.user_attempts ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE public.hint_requests ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.users(id) ON DELETE CASCADE;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_attempts_user_id ON public.user_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_attempts_handle ON public.user_attempts(handle);
