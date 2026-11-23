-- Supabase PostgreSQL 16 Migration: 004_security_remediation_sprint1.sql
-- Sprint: Sprint 1 - Security, Integrity & Privacy Remediations
-- Description:
--   1. SEC-01: Atomic claim_clinician_access RPC (SECURITY DEFINER) with row-level locking,
--      single-use code clearing, and dropping the permissive BOLA UPDATE policy.
--   2. SEC-04: Enforce clinician verification (profiles.is_verified = TRUE) across RLS policies
--      for public.scans and storage.objects.
--   3. SEC-06 / ARCH-01: Add confidence, image_url, and clinician_notes columns to public.scans.
--      Enforce strict column immutability via BEFORE UPDATE trigger (grade, confidence, image_url,
--      created_at locked; only clinician_notes updates allowed for authorized clinicians).
--   4. SEC-08: Add generate_patient_grant_code RPC (SECURITY DEFINER) generating cryptographically
--      secure 6-character codes using gen_random_bytes (pgcrypto).
--   5. SEC-09 / PRIV-01: Add storage DELETE policy for GDPR Right to Erasure and restrict upload extensions.

-- Ensure pgcrypto extension is available for CSPRNG
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. SCHEMA EXTENSIONS: SCANS & CLINICIAN DIRECTORY
-- ==============================================================================

-- Ensure diagnostic integrity and note columns exist on public.scans
ALTER TABLE public.scans
    ADD COLUMN IF NOT EXISTS confidence NUMERIC,
    ADD COLUMN IF NOT EXISTS image_url TEXT,
    ADD COLUMN IF NOT EXISTS clinician_notes TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Standardized view for clinician profiles
CREATE OR REPLACE VIEW public.clinician_profiles AS
SELECT 
    id,
    role,
    full_name,
    medical_license_no,
    institution_name,
    specialty,
    medical_degree,
    jurisdiction,
    clinic_address_city,
    years_of_experience,
    is_verified,
    verification_status,
    verified_at,
    created_at,
    updated_at
FROM public.profiles
WHERE role = 'clinician';

-- Sanitized public directory for verified clinicians (SEC-10: hides private phone numbers)
CREATE OR REPLACE VIEW public.verified_clinicians_directory AS
SELECT 
    id,
    full_name,
    medical_license_no,
    institution_name,
    specialty,
    medical_degree,
    jurisdiction,
    clinic_address_city,
    years_of_experience,
    verified_at
FROM public.profiles
WHERE role = 'clinician' AND is_verified = TRUE;

-- ==============================================================================
-- 2. SEC-01 REMEDIATION: ATOMIC CLINICIAN GRANT CLAIM & DROP BOLA POLICY
-- ==============================================================================

-- Drop the vulnerable direct UPDATE policy that permitted mass unauthenticated grant claiming
DROP POLICY IF EXISTS "Clinicians claim active grant with code" ON public.clinician_access_grants;

-- Ensure patients can still update/revoke their own grants directly
DROP POLICY IF EXISTS "Patients update own grants" ON public.clinician_access_grants;
CREATE POLICY "Patients update own grants"
    ON public.clinician_access_grants FOR UPDATE
    USING (auth.uid() = patient_id)
    WITH CHECK (auth.uid() = patient_id);

-- Atomic grant claim RPC enforcing authentication, clinician role, code match, non-expiration, single-use
CREATE OR REPLACE FUNCTION public.claim_clinician_access(p_code TEXT)
RETURNS jsonb AS $$
DECLARE
    v_grant public.clinician_access_grants%ROWTYPE;
    v_clinician_role TEXT;
    v_is_verified BOOLEAN;
    v_clean_code TEXT;
BEGIN
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Authentication required to claim clinician access code';
    END IF;

    -- Verify caller identity and clinician role
    SELECT role, is_verified 
    INTO v_clinician_role, v_is_verified
    FROM public.profiles 
    WHERE id = auth.uid();

    IF v_clinician_role IS DISTINCT FROM 'clinician' THEN
        RAISE EXCEPTION 'Only registered clinicians are authorized to claim patient access codes';
    END IF;

    v_clean_code := UPPER(TRIM(p_code));

    IF v_clean_code IS NULL OR length(v_clean_code) = 0 THEN
        RAISE EXCEPTION 'Access code cannot be empty';
    END IF;

    -- Atomically lock and retrieve the active, unclaimed, unexpired grant matching the code
    SELECT * INTO v_grant
    FROM public.clinician_access_grants
    WHERE UPPER(TRIM(grant_code)) = v_clean_code
      AND status = 'active'
      AND expires_at > NOW()
      AND clinician_id IS NULL
    FOR UPDATE;

    IF v_grant.id IS NULL THEN
        RAISE EXCEPTION 'Access code is invalid, expired, or has already been claimed.';
    END IF;

    -- Prevent self-delegation
    IF v_grant.patient_id = auth.uid() THEN
        RAISE EXCEPTION 'Cannot redeem your own patient access code as a clinician.';
    END IF;

    -- Single-use consumption: set clinician_id and nullify grant_code atomically
    UPDATE public.clinician_access_grants
    SET 
        clinician_id = auth.uid(),
        grant_code = NULL
    WHERE id = v_grant.id;

    RETURN jsonb_build_object(
        'success', true, 
        'grant_id', v_grant.id, 
        'patient_id', v_grant.patient_id,
        'claimed_at', NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Backwards-compatibility alias for redeem_clinician_grant
CREATE OR REPLACE FUNCTION public.redeem_clinician_grant(p_grant_code TEXT)
RETURNS jsonb AS $$
BEGIN
    RETURN public.claim_clinician_access(p_grant_code);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.claim_clinician_access(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.redeem_clinician_grant(TEXT) TO authenticated;

-- ==============================================================================
-- 3. SEC-04 REMEDIATION: REQUIRE CLINICIAN VERIFICATION ON SCANS & STORAGE
-- ==============================================================================

-- Scans SELECT: strictly require clinician_profiles.is_verified = TRUE
DROP POLICY IF EXISTS "Authorized clinicians view patient scans" ON public.scans;
CREATE POLICY "Authorized clinicians view patient scans"
    ON public.scans FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.clinician_access_grants g
            JOIN public.profiles p ON p.id = g.clinician_id
            WHERE g.patient_id = scans.patient_id
              AND g.clinician_id = auth.uid()
              AND g.status = 'active'
              AND g.expires_at > NOW()
              AND p.role = 'clinician'
              AND p.is_verified = TRUE
        )
    );

-- Storage SELECT: strictly require clinician_profiles.is_verified = TRUE
DROP POLICY IF EXISTS "Authorized clinicians read patient scans from storage" ON storage.objects;
CREATE POLICY "Authorized clinicians read patient scans from storage"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'retinal-scans' AND
        EXISTS (
            SELECT 1 FROM public.clinician_access_grants g
            JOIN public.profiles p ON p.id = g.clinician_id
            WHERE g.patient_id::text = (storage.foldername(name))[1]
              AND g.clinician_id = auth.uid()
              AND g.status = 'active'
              AND g.expires_at > NOW()
              AND p.role = 'clinician'
              AND p.is_verified = TRUE
        )
    );

-- Storage DELETE: Allow patients to delete own scans (GDPR Art. 17 Right to Erasure / PRIV-01)
DROP POLICY IF EXISTS "Patients delete own scans from storage" ON storage.objects;
CREATE POLICY "Patients delete own scans from storage"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'retinal-scans' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Storage INSERT: Restrict uploaded file types to safe retinal image MIME/extensions (SEC-09)
DROP POLICY IF EXISTS "Patients upload own scans to storage" ON storage.objects;
CREATE POLICY "Patients upload own scans to storage"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'retinal-scans' AND
        auth.uid()::text = (storage.foldername(name))[1] AND
        (storage.extension(name) IN ('jpg', 'jpeg', 'png', 'webp'))
    );

-- ==============================================================================
-- 4. SEC-06 REMEDIATION: SCAN IMMUTABILITY TRIGGER & CLINICIAN NOTES UPDATES
-- ==============================================================================

-- Allow verified clinicians with active grant to update clinician_notes on authorized patient scans
DROP POLICY IF EXISTS "Authorized clinicians update clinician notes on scans" ON public.scans;
CREATE POLICY "Authorized clinicians update clinician notes on scans"
    ON public.scans FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.clinician_access_grants g
            JOIN public.profiles p ON p.id = g.clinician_id
            WHERE g.patient_id = scans.patient_id
              AND g.clinician_id = auth.uid()
              AND g.status = 'active'
              AND g.expires_at > NOW()
              AND p.role = 'clinician'
              AND p.is_verified = TRUE
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.clinician_access_grants g
            JOIN public.profiles p ON p.id = g.clinician_id
            WHERE g.patient_id = scans.patient_id
              AND g.clinician_id = auth.uid()
              AND g.status = 'active'
              AND g.expires_at > NOW()
              AND p.role = 'clinician'
              AND p.is_verified = TRUE
        )
    );

-- Keep patient update policy scoped to ownership
DROP POLICY IF EXISTS "Patients update own scans" ON public.scans;
CREATE POLICY "Patients update own scans"
    ON public.scans FOR UPDATE
    USING (auth.uid() = patient_id)
    WITH CHECK (auth.uid() = patient_id);

-- Enforce strict immutability of diagnostic fields via BEFORE UPDATE trigger
CREATE OR REPLACE FUNCTION public.protect_scan_immutability()
RETURNS TRIGGER AS $$
DECLARE
    is_service_or_admin BOOLEAN;
    is_authorized_clinician BOOLEAN;
BEGIN
    -- Superuser and service_role can perform administrative updates if necessary
    is_service_or_admin := (
        COALESCE(auth.jwt()->>'role', '') = 'service_role' 
        OR current_user = 'postgres'
    );

    IF is_service_or_admin THEN
        NEW.updated_at := NOW();
        RETURN NEW;
    END IF;

    -- 1. Strictly lock immutable clinical & audit fields from client mutations (SEC-06)
    IF NEW.grade IS DISTINCT FROM OLD.grade THEN
        RAISE EXCEPTION 'Modification of diagnostic grade is prohibited (SEC-06)';
    END IF;

    IF NEW.confidence IS DISTINCT FROM OLD.confidence THEN
        RAISE EXCEPTION 'Modification of model confidence is prohibited (SEC-06)';
    END IF;

    IF NEW.image_url IS DISTINCT FROM OLD.image_url THEN
        RAISE EXCEPTION 'Modification of image_url is prohibited (SEC-06)';
    END IF;

    IF NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION 'Modification of created_at timestamp is prohibited (SEC-06)';
    END IF;

    IF NEW.patient_id IS DISTINCT FROM OLD.patient_id THEN
        RAISE EXCEPTION 'Modification of scan ownership (patient_id) is prohibited';
    END IF;

    IF NEW.storage_path IS DISTINCT FROM OLD.storage_path THEN
        RAISE EXCEPTION 'Modification of storage_path is prohibited';
    END IF;

    IF NEW.label IS DISTINCT FROM OLD.label THEN
        RAISE EXCEPTION 'Modification of diagnostic label is prohibited';
    END IF;

    IF NEW.probabilities IS DISTINCT FROM OLD.probabilities THEN
        RAISE EXCEPTION 'Modification of diagnostic probabilities is prohibited';
    END IF;

    IF NEW.model_version IS DISTINCT FROM OLD.model_version THEN
        RAISE EXCEPTION 'Modification of model_version is prohibited';
    END IF;

    IF NEW.eye IS DISTINCT FROM OLD.eye THEN
        RAISE EXCEPTION 'Modification of eye classification is prohibited';
    END IF;

    -- 2. Authorization rule for clinician_notes: only verified clinicians with an active grant
    IF NEW.clinician_notes IS DISTINCT FROM OLD.clinician_notes THEN
        SELECT EXISTS (
            SELECT 1 FROM public.clinician_access_grants g
            JOIN public.profiles p ON p.id = g.clinician_id
            WHERE g.patient_id = OLD.patient_id
              AND g.clinician_id = auth.uid()
              AND g.status = 'active'
              AND g.expires_at > NOW()
              AND p.role = 'clinician'
              AND p.is_verified = TRUE
        ) INTO is_authorized_clinician;

        IF NOT is_authorized_clinician THEN
            RAISE EXCEPTION 'Only verified clinicians with an active access grant can update clinician_notes';
        END IF;
    END IF;

    -- 3. If caller is clinician (not patient), prevent editing patient-only fields
    IF auth.uid() <> OLD.patient_id THEN
        IF NEW.patient_notes IS DISTINCT FROM OLD.patient_notes OR NEW.is_favorite IS DISTINCT FROM OLD.is_favorite THEN
            RAISE EXCEPTION 'Clinicians are only permitted to update clinician_notes on patient scans';
        END IF;
    END IF;

    -- 4. If caller is patient, prevent editing clinician_notes
    IF auth.uid() = OLD.patient_id THEN
        IF NEW.clinician_notes IS DISTINCT FROM OLD.clinician_notes THEN
            RAISE EXCEPTION 'Patients cannot modify clinician_notes';
        END IF;
    END IF;

    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_protect_scan_immutability ON public.scans;
CREATE TRIGGER trg_protect_scan_immutability
    BEFORE UPDATE ON public.scans
    FOR EACH ROW
    EXECUTE FUNCTION public.protect_scan_immutability();

-- ==============================================================================
-- 5. SEC-08 REMEDIATION: CRYPTOGRAPHIC PATIENT GRANT CODE GENERATION RPC
-- ==============================================================================

-- Generates cryptographically secure 6-character alphanumeric grant code using gen_random_bytes
-- and inserts active clinician_access_grants record for caller. Returns 6-character code string.
CREATE OR REPLACE FUNCTION public.generate_patient_grant_code(p_expires_in_hours INT DEFAULT 24)
RETURNS TEXT AS $$
DECLARE
    v_raw_bytes BYTEA;
    v_chars TEXT := '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'; -- 32 unambiguous characters (no modulo bias)
    v_code TEXT := '';
    v_idx INT;
    v_expires_in INT;
    v_expires_at TIMESTAMPTZ;
BEGIN
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'Authentication required to generate patient grant code';
    END IF;

    v_expires_in := COALESCE(p_expires_in_hours, 24);
    IF v_expires_in < 1 THEN
        v_expires_in := 1;
    ELSIF v_expires_in > 168 THEN
        v_expires_in := 168; -- Cap at 7 days
    END IF;

    v_expires_at := NOW() + (v_expires_in * INTERVAL '1 hour');

    -- Generate 6 cryptographically secure characters using pgcrypto gen_random_bytes
    v_raw_bytes := gen_random_bytes(6);
    FOR i IN 0..5 LOOP
        v_idx := (get_byte(v_raw_bytes, i) % 32) + 1;
        v_code := v_code || substr(v_chars, v_idx, 1);
    END LOOP;

    -- Insert active grant into clinician_access_grants
    INSERT INTO public.clinician_access_grants (
        patient_id,
        clinician_id,
        grant_code,
        status,
        expires_at
    )
    VALUES (
        auth.uid(),
        NULL,
        v_code,
        'active',
        v_expires_at
    );

    RETURN v_code;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Complementary JSONB RPC returning full metadata for client integration
CREATE OR REPLACE FUNCTION public.generate_patient_grant(p_expires_in_hours INT DEFAULT 24)
RETURNS jsonb AS $$
DECLARE
    v_code TEXT;
    v_grant public.clinician_access_grants%ROWTYPE;
BEGIN
    v_code := public.generate_patient_grant_code(p_expires_in_hours);
    
    SELECT * INTO v_grant
    FROM public.clinician_access_grants
    WHERE grant_code = v_code AND patient_id = auth.uid()
    ORDER BY created_at DESC
    LIMIT 1;

    RETURN jsonb_build_object(
        'success', true,
        'grant_id', v_grant.id,
        'grant_code', v_code,
        'code', v_code,
        'expires_at', v_grant.expires_at
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.generate_patient_grant_code(INT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.generate_patient_grant(INT) TO authenticated;
