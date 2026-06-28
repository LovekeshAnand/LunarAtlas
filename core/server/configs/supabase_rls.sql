-- ============================================================================
-- LunarAtlas Supabase Row Level Security (RLS) Configuration
-- ============================================================================
-- Run this script in your Supabase SQL Editor to enable RLS and create 
-- explicit access policies for all database tables.
-- ============================================================================

-- 1) Enable RLS on all tables
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE mission ENABLE ROW LEVEL SECURITY;
ALTER TABLE instrument ENABLE ROW LEVEL SECURITY;
ALTER TABLE instrument_spec_libs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dataset_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE observation_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE observation ENABLE ROW LEVEL SECURITY;
ALTER TABLE observation_file_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurement_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE spectral_data_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurement_clean ENABLE ROW LEVEL SECURITY;
ALTER TABLE spectral_data_clean ENABLE ROW LEVEL SECURITY;
ALTER TABLE nist_lines ENABLE ROW LEVEL SECURITY;

-- 2) Create Service Role Policies (Allows full access for backend API server)
-- Note: The service_role bypasses RLS in Supabase by default, but creating
-- explicit policies is best practice for defense-in-depth.

-- User Accounts
CREATE POLICY service_all_app_users ON app_users FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_api_keys ON api_keys FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_api_usage_log ON api_usage_log FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Telemetry Schema
CREATE POLICY service_all_mission ON mission FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_instrument ON instrument FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_instrument_spec_libs ON instrument_spec_libs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_dataset_version ON dataset_version FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_observation_session ON observation_session FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_observation ON observation FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_observation_file_info ON observation_file_info FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_measurement_raw ON measurement_raw FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_spectral_data_raw ON spectral_data_raw FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_measurement_clean ON measurement_clean FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_spectral_data_clean ON spectral_data_clean FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all_nist_lines ON nist_lines FOR ALL TO service_role USING (true) WITH CHECK (true);


-- 3) Create Read-Only Public/Anon Policies for Spectral Telemetry Data
-- Allows anonymous and authenticated API consumers to fetch planetary spectral data.

CREATE POLICY public_select_mission ON mission FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_instrument ON instrument FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_instrument_spec_libs ON instrument_spec_libs FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_dataset_version ON dataset_version FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_observation_session ON observation_session FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_observation ON observation FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_observation_file_info ON observation_file_info FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_measurement_clean ON measurement_clean FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_spectral_data_clean ON spectral_data_clean FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY public_select_nist_lines ON nist_lines FOR SELECT TO anon, authenticated USING (true);


-- 4) Restrict Write/Modify Access on User & Account Data
-- Denies all public/anonymous write access to user details, API keys, and logs.
-- Only the backend (service_role) can write or alter user tables.

CREATE POLICY public_deny_all_app_users ON app_users FOR SELECT TO anon USING (false);
CREATE POLICY public_deny_all_api_keys ON api_keys FOR SELECT TO anon USING (false);
CREATE POLICY public_deny_all_api_usage_log ON api_usage_log FOR SELECT TO anon USING (false);
