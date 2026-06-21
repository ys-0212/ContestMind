-- =================================================================================
-- ContestMind Supabase Auth Trigger
-- Run this in the Supabase SQL Editor to automatically create a public.users row
-- whenever a new user signs up via Supabase Auth.
-- =================================================================================

-- 1. Create a function that handles the insert
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, codeforces_handle, current_rating, max_rating, avatar_url)
  VALUES (
    new.id,
    -- Extract the codeforces_handle from the metadata sent during signup
    new.raw_user_meta_data->>'codeforces_handle', 
    0, 
    0, 
    ''
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Create the trigger on the auth.users table
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
