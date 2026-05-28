-- =================================================================================
-- ContestMind Supabase Row Level Security (RLS) Policies
-- Run this in the Supabase SQL Editor AFTER running init.sql
-- =================================================================================

-- 1. Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hint_requests ENABLE ROW LEVEL SECURITY;

-- 2. Create Policies for Users table
-- Users can only read and update their own profile
CREATE POLICY "Users can view their own profile" 
ON public.users FOR SELECT 
USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" 
ON public.users FOR UPDATE 
USING (auth.uid() = id);

-- 3. Create Policies for Chat Sessions
-- Users can only view, insert, and delete their own chat sessions
CREATE POLICY "Users can view their own chat sessions" 
ON public.chat_sessions FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own chat sessions" 
ON public.chat_sessions FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own chat sessions" 
ON public.chat_sessions FOR DELETE 
USING (auth.uid() = user_id);

-- 4. Create Policies for Chat Messages
-- Users can only view and insert messages for sessions they own
CREATE POLICY "Users can view messages of their sessions" 
ON public.chat_messages FOR SELECT 
USING (
    session_id IN (SELECT id FROM public.chat_sessions WHERE user_id = auth.uid())
);

CREATE POLICY "Users can insert messages into their sessions" 
ON public.chat_messages FOR INSERT 
WITH CHECK (
    session_id IN (SELECT id FROM public.chat_sessions WHERE user_id = auth.uid())
);

-- 5. Create Policies for User Attempts
CREATE POLICY "Users can view their own attempts" 
ON public.user_attempts FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own attempts" 
ON public.user_attempts FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- 6. Create Policies for Hint Requests
CREATE POLICY "Users can view their own hint requests" 
ON public.hint_requests FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own hint requests" 
ON public.hint_requests FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Note: The Service Role Key (which the FastAPI backend should use in production)
-- automatically bypasses all RLS policies, so the backend can still perform all operations.
