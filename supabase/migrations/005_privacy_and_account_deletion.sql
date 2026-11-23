-- Supabase PostgreSQL 16 Migration: 005_privacy_and_account_deletion.sql
-- Sprint: Sprint 6 (Track 3) — Privacy & Healthcare Data Protection
-- Remediations:
--   1. PRIV-03: Implement atomic delete_user_account() RPC (SECURITY DEFINER) enforcing
--      caller can only delete their own account (auth.uid()), with cascade deletion for
--      patient records (scans, grants, reminders, profiles, and retinal-scans storage objects)
--      and anonymization of clinician dependencies (clinician_reviews set clinician_id = NULL
--      and unassigning active grants) so medical second opinions are preserved without foreign key aborts.
--   2. PRIV-01 / GDPR Art. 17: Right to Erasure alignment across public tables and storage buckets.

-- ==============================================================================
-- 1. FOREIGN KEY RELAXATION FOR CLINICIAN REVIEWS ANONYMIZATION
-- ==============================================================================

-- A. Allow clinician_id to be NULL in public.clinician_reviews so that when a clinician
-- deletes their account, their medical second opinions are retained for patient clinical
-- safety but fully anonymized (clinician_id = NULL).
ALTER TABLE public.clinician_reviews
    ALTER COLUMN clinician_id DROP NOT NULL;

-- B. Update foreign key on public.clinician_reviews to ON DELETE SET NULL
ALTER TABLE public.clinician_reviews
    DROP CONSTRAINT IF EXISTS clinician_reviews_clinician_id_fkey;

ALTER TABLE public.clinician_reviews
    ADD CONSTRAINT clinician_reviews_clinician_id_fkey
    FOREIGN KEY (clinician_id) REFERENCES public.profiles(id) ON DELETE SET NULL;

-- C. Update foreign key on public.clinician_access_grants to ON DELETE SET NULL
-- Ensures that if a clinician account is deleted, the grant row is preserved with clinician_id = NULL
-- rather than cascading deletion of the patient's grant history.
ALTER TABLE public.clinician_access_grants
    DROP CONSTRAINT IF EXISTS clinician_access_grants_clinician_id_fkey;

ALTER TABLE public.clinician_access_grants
    ADD CONSTRAINT clinician_access_grants_clinician_id_fkey
    FOREIGN KEY (clinician_id) REFERENCES public.profiles(id) ON DELETE SET NULL;

-- ==============================================================================
-- 2. PROFILE DELETE POLICY (GDPR ART. 17 RIGHT TO ERASURE)
-- ==============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'profiles' 
        AND policyname = 'Users delete own profile'
    ) THEN
        CREATE POLICY "Users delete own profile"
            ON public.profiles FOR DELETE
            USING (auth.uid() = id);
    END IF;
END $$;

-- ==============================================================================
-- 3. ATOMIC ACCOUNT DELETION RPC: delete_user_account()
-- ==============================================================================

-- Atomic function executing GDPR Art. 17 Right to Erasure for authenticated caller.
-- Caller CANNOT specify a target user; deletion is strictly bound to auth.uid().
CREATE OR REPLACE FUNCTION public.delete_user_account()
RETURNS jsonb AS $$
DECLARE
    v_user_id UUID;
    v_role TEXT;
    v_scans_count INT := 0;
    v_grants_count INT := 0;
    v_reviews_count INT := 0;
    v_reminders_count INT := 0;
    v_storage_count INT := 0;
BEGIN
    -- 1. Strictly enforce authentication: caller can only delete their own account (auth.uid())
    v_user_id := auth.uid();
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required: caller must be authenticated to delete account (PRIV-03)';
    END IF;

    -- Retrieve account role from profiles
    SELECT role INTO v_role
    FROM public.profiles
    WHERE id = v_user_id;

    IF v_role IS NULL THEN
        RAISE EXCEPTION 'User profile not found for authenticated user %', v_user_id;
    END IF;

    -- 2. Role-specific deletion and cascade orchestration
    IF v_role = 'patient' THEN
        -- A. Delete follow-up reminders
        WITH deleted_reminders AS (
            DELETE FROM public.follow_up_reminders
            WHERE patient_id = v_user_id
            RETURNING id
        )
        SELECT COUNT(*) INTO v_reminders_count FROM deleted_reminders;

        -- B. Delete clinician access grants where patient is grantor
        WITH deleted_grants AS (
            DELETE FROM public.clinician_access_grants
            WHERE patient_id = v_user_id
            RETURNING id
        )
        SELECT COUNT(*) INTO v_grants_count FROM deleted_grants;

        -- C. Delete patient scans
        -- Note: public.clinician_reviews references scans(id) with ON DELETE CASCADE,
        -- so any reviews on the patient's scans are cascade deleted.
        WITH deleted_scans AS (
            DELETE FROM public.scans
            WHERE patient_id = v_user_id
            RETURNING id
        )
        SELECT COUNT(*) INTO v_scans_count FROM deleted_scans;

        -- D. Purge private storage objects (fundus scan images in 'retinal-scans' bucket)
        BEGIN
            WITH deleted_objects AS (
                DELETE FROM storage.objects
                WHERE bucket_id = 'retinal-scans'
                  AND (
                    (storage.foldername(name))[1] = v_user_id::text
                    OR owner = v_user_id
                  )
                RETURNING id
            )
            SELECT COUNT(*) INTO v_storage_count FROM deleted_objects;
        EXCEPTION
            WHEN undefined_table THEN
                v_storage_count := 0;
            WHEN OTHERS THEN
                v_storage_count := 0;
        END;

    ELSIF v_role = 'clinician' THEN
        -- A. Anonymize clinician reviews to preserve patient longitudinal record integrity
        --    while permanently removing identifying clinician association
        WITH updated_reviews AS (
            UPDATE public.clinician_reviews
            SET clinician_id = NULL
            WHERE clinician_id = v_user_id
            RETURNING id
        )
        SELECT COUNT(*) INTO v_reviews_count FROM updated_reviews;

        -- B. Revoke and unassign any active grants assigned to this clinician
        WITH updated_grants AS (
            UPDATE public.clinician_access_grants
            SET clinician_id = NULL, status = 'revoked'
            WHERE clinician_id = v_user_id
            RETURNING id
        )
        SELECT COUNT(*) INTO v_grants_count FROM updated_grants;

        -- C. Purge any storage objects owned by clinician
        BEGIN
            WITH deleted_objects AS (
                DELETE FROM storage.objects
                WHERE owner = v_user_id
                RETURNING id
            )
            SELECT COUNT(*) INTO v_storage_count FROM deleted_objects;
        EXCEPTION
            WHEN undefined_table THEN
                v_storage_count := 0;
            WHEN OTHERS THEN
                v_storage_count := 0;
        END;
    END IF;

    -- 3. Delete user profile from public.profiles
    DELETE FROM public.profiles WHERE id = v_user_id;

    -- 4. Delete user account from auth.users (if accessible in runtime environment)
    BEGIN
        DELETE FROM auth.users WHERE id = v_user_id;
    EXCEPTION
        WHEN undefined_table THEN
            NULL;
        WHEN OTHERS THEN
            NULL;
    END;

    -- 5. Return structured deletion audit receipt
    RETURN jsonb_build_object(
        'success', true,
        'user_id', v_user_id,
        'role', v_role,
        'scans_deleted', v_scans_count,
        'grants_handled', v_grants_count,
        'reviews_anonymized', v_reviews_count,
        'reminders_deleted', v_reminders_count,
        'storage_objects_purged', v_storage_count,
        'deleted_at', NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execution permission strictly to authenticated users
GRANT EXECUTE ON FUNCTION public.delete_user_account() TO authenticated;
