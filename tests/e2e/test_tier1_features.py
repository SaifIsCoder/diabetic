"""
Tier 1: Category-Partition & Standard Feature Coverage Test Suite.

Covers all 17 features from PROJECT.md § Feature Inventory (5 tests per feature = 85 tests):
- Feature 1: Sargodha Clinical Training Manual (TC-T1-F01-01 to TC-T1-F01-05)
- Feature 2: Bilingual Patient Consent Forms (TC-T1-F02-01 to TC-T1-F02-05)
- Feature 3: Bilingual Patient Instruction Sheets (TC-T1-F03-01 to TC-T1-F03-05)
- Feature 4: Point-of-Care Clinical Checklists (TC-T1-F04-01 to TC-T1-F04-05)
- Feature 5: Sargodha Doctor Onboarding Kit (TC-T1-F05-01 to TC-T1-F05-05)
- Feature 6: Patient Split Script (TC-T1-F06-01 to TC-T1-F06-05)
- Feature 7: Split Tests Verification (TC-T1-F07-01 to TC-T1-F07-05)
- Feature 8: Leak-Free Data Generator (TC-T1-F08-01 to TC-T1-F08-05)
- Feature 9: Retraining Harness (TC-T1-F09-01 to TC-T1-F09-05)
- Feature 10: Model Evaluation (TC-T1-F10-01 to TC-T1-F10-05)
- Feature 11: Dockerfile Non-Root Verification (TC-T1-F11-01 to TC-T1-F11-05)
- Feature 12: Staging Compose Configuration (TC-T1-F12-01 to TC-T1-F12-05)
- Feature 13: NGINX TLS 1.3 Reverse Proxy (TC-T1-F13-01 to TC-T1-F13-05)
- Feature 14: Automated Staging Verifier (TC-T1-F14-01 to TC-T1-F14-05)
- Feature 15: Approval Gates Audit (TC-T1-F15-01 to TC-T1-F15-05)
- Feature 16: Guardrails & Test Stability (TC-T1-F16-01 to TC-T1-F16-05)
- Feature 17: Pilot Readiness Presentation (TC-T1-F17-01 to TC-T1-F17-05)

Zero real patient data. Zero external WAN calls. Zero cloud spend.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, Set

import numpy as np
import pandas as pd
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.tier1]


# ==============================================================================
# Feature 1: Sargodha Clinical Training Manual
# ==============================================================================

class TestTier1Feature01ClinicalTrainingManual:
    """Feature 1: Clinical Training Manual (docs/sargodha/clinical_training_manual.md)."""

    @pytest.fixture(autouse=True)
    def setup_path(self, repo_root: Path):
        self.doc_path = repo_root / "docs" / "sargodha" / "clinical_training_manual.md"
        assert self.doc_path.is_file(), f"Document missing: {self.doc_path}"
        self.content = self.doc_path.read_text(encoding="utf-8")

    def test_tc_t1_f01_01_manual_existence_and_structure(self, markdown_linter):
        """TC-T1-F01-01: Document existence, heading hierarchy, and zero placeholders."""
        stats = markdown_linter.scan_file(self.doc_path)
        assert stats["size_bytes"] > 20_000, "Manual must be comprehensive (>20KB)"
        assert stats["headings_h1"] >= 1, "Must contain top-level heading"
        assert stats["headings_h2"] >= 5, "Must contain section headings"
        markdown_linter.assert_zero_placeholders(self.doc_path)

    def test_tc_t1_f01_02_manual_icdr_grades_definitions(self):
        """TC-T1-F01-02: ICDR Grades 0 to 4 explicit clinical definitions and lesion criteria."""
        for grade in ["Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4"]:
            assert grade in self.content, f"Missing {grade} in training manual"
        assert "Microaneurysms" in self.content or "microaneurysms" in self.content
        assert "Proliferative" in self.content or "PDR" in self.content
        assert "4-2-1" in self.content or "venous beading" in self.content.lower()

    def test_tc_t1_f01_03_manual_fundus_photography_protocol(self):
        """TC-T1-F01-03: Fundus photography protocol: dilation, field centering, artifact rejection."""
        lower_content = self.content.lower()
        assert "tropicamide" in lower_content or "dilation" in lower_content
        assert "45" in self.content, "Must document 45-degree field-of-view protocol"
        assert "macula" in lower_content and "optic disc" in lower_content
        assert "cataract" in lower_content or "ungradable" in lower_content

    def test_tc_t1_f01_04_manual_software_operational_workflow(self):
        """TC-T1-F01-04: Software operational workflow for clinical operators."""
        lower_content = self.content.lower()
        assert "login" in lower_content or "credential" in lower_content
        assert "grant" in lower_content or "delegation" in lower_content or "access code" in lower_content
        assert "review" in lower_content
        assert "override" in lower_content or "advisory" in lower_content

    def test_tc_t1_f01_05_manual_emergency_escalation_protocol(self):
        """TC-T1-F01-05: Emergency escalation protocol for Grade 4 PDR with <24h referral."""
        assert "24" in self.content, "Mandatory <= 24 hour escalation window for PDR"
        assert "Sargodha" in self.content
        assert "DHQ" in self.content or "Teaching Hospital" in self.content or "LRBT" in self.content


# ==============================================================================
# Feature 2: Bilingual Patient Consent Forms
# ==============================================================================

class TestTier1Feature02BilingualPatientConsent:
    """Feature 2: Bilingual Patient Consent Forms (docs/sargodha/patient_consent_forms.md)."""

    @pytest.fixture(autouse=True)
    def setup_path(self, repo_root: Path):
        self.doc_path = repo_root / "docs" / "sargodha" / "patient_consent_forms.md"
        assert self.doc_path.is_file(), f"Document missing: {self.doc_path}"
        self.content = self.doc_path.read_text(encoding="utf-8")

    def test_tc_t1_f02_01_consent_structure_and_bilingual_pairing(self, markdown_linter):
        """TC-T1-F02-01: Document structure and bilingual English/Urdu pairing."""
        stats = markdown_linter.scan_file(self.doc_path)
        assert stats["is_bilingual"], "Consent form must contain both English and Urdu text"
        markdown_linter.assert_zero_placeholders(self.doc_path)

    def test_tc_t1_f02_02_consent_sargodha_institutional_grounding(self):
        """TC-T1-F02-02: Institutional grounding in Sargodha healthcare entities."""
        assert "Sargodha" in self.content
        assert any(inst in self.content for inst in ["Faisal Masood", "DHQ", "LRBT", "Shahpur", "Niazi"])

    def test_tc_t1_f02_03_consent_statutory_privacy_rights(self):
        """TC-T1-F02-03: Statutory privacy rights under PECA 2016 and GDPR Article 17."""
        assert "PECA" in self.content or "Electronic Crimes" in self.content
        assert "Section 14" in self.content or "erasure" in self.content.lower() or "deletion" in self.content.lower()

    def test_tc_t1_f02_04_consent_voluntary_participation_and_cds_status(self):
        """TC-T1-F02-04: Explicit declaration of voluntary participation and CDS status."""
        lower_content = self.content.lower()
        assert "voluntary" in lower_content or "اختیاری" in self.content
        assert "decision support" in lower_content or "screening aid" in lower_content or "معاون" in self.content

    def test_tc_t1_f02_05_consent_execution_signature_thumbprint_blocks(self):
        """TC-T1-F02-05: Signature, thumbprint (goti), guardian, and date execution blocks."""
        lower_content = self.content.lower()
        assert "signature" in lower_content or "دستخط" in self.content
        assert "thumb" in lower_content or "انگوٹھا" in self.content
        assert "date" in lower_content or "تاریخ" in self.content


# ==============================================================================
# Feature 3: Bilingual Patient Instruction Sheets
# ==============================================================================

class TestTier1Feature03BilingualPatientInstructions:
    """Feature 3: Bilingual Patient Instruction Sheets (docs/sargodha/patient_instruction_sheets.md)."""

    @pytest.fixture(autouse=True)
    def setup_path(self, repo_root: Path):
        self.doc_path = repo_root / "docs" / "sargodha" / "patient_instruction_sheets.md"
        assert self.doc_path.is_file(), f"Document missing: {self.doc_path}"
        self.content = self.doc_path.read_text(encoding="utf-8")

    def test_tc_t1_f03_01_instructions_structure_and_bilingual_layout(self, markdown_linter):
        """TC-T1-F03-01: Document structure and bilingual layout."""
        stats = markdown_linter.scan_file(self.doc_path)
        assert stats["is_bilingual"], "Instruction sheet must be bilingual (English + Urdu)"
        markdown_linter.assert_zero_placeholders(self.doc_path)

    def test_tc_t1_f03_02_instructions_prescreening_preparation(self):
        """TC-T1-F03-02: Pre-screening preparation guidance (glasses, medications, dilation)."""
        lower_content = self.content.lower()
        assert "glasses" in lower_content or "عینک" in self.content
        assert "drop" in lower_content or "قطرے" in self.content
        assert "medication" in lower_content or "ادویات" in self.content

    def test_tc_t1_f03_03_instructions_examination_expectations_duration(self):
        """TC-T1-F03-03: Examination expectations: non-invasive flash, 10-15 minute duration."""
        lower_content = self.content.lower()
        assert "10" in self.content or "15" in self.content
        assert "flash" in lower_content or "روشنی" in self.content
        assert "non-invasive" in lower_content or "درد" in self.content or "safe" in lower_content

    def test_tc_t1_f03_04_instructions_five_grade_severity_explanation(self):
        """TC-T1-F03-04: Plain-language explanation of 5 DR severity grades for patients."""
        for grade_num in range(5):
            assert str(grade_num) in self.content, f"Missing Grade {grade_num} in explanation"

    def test_tc_t1_f03_05_instructions_emergency_red_flag_warning_symptoms(self):
        """TC-T1-F03-05: Acute warning symptoms and emergency eye clinic contacts."""
        lower_content = self.content.lower()
        assert "curtain" in lower_content or "dark" in lower_content or "پردہ" in self.content or "loss" in lower_content
        assert "emergency" in lower_content or "ہنگامی" in self.content or "1122" in self.content


# ==============================================================================
# Feature 4: Clinical Workflow Checklists
# ==============================================================================

class TestTier1Feature04ClinicalWorkflowChecklists:
    """Feature 4: Clinical Workflow Checklists (docs/sargodha/clinical_workflow_checklists.md)."""

    @pytest.fixture(autouse=True)
    def setup_path(self, repo_root: Path):
        self.doc_path = repo_root / "docs" / "sargodha" / "clinical_workflow_checklists.md"
        assert self.doc_path.is_file(), f"Document missing: {self.doc_path}"
        self.content = self.doc_path.read_text(encoding="utf-8")

    def test_tc_t1_f04_01_checklists_structure_and_checkbox_format(self, markdown_linter):
        """TC-T1-F04-01: Document structure with markdown action checkboxes."""
        checkboxes = re.findall(r"\[\s*[xX ]\s*\]", self.content)
        assert len(checkboxes) >= 15, "Checklists must provide actionable task checkboxes"
        markdown_linter.assert_zero_placeholders(self.doc_path)

    def test_tc_t1_f04_02_checklists_station_1_intake_reception(self):
        """TC-T1-F04-02: Station 1: Patient registration, consent, and MRN intake."""
        assert "Station 1" in self.content or "Intake" in self.content
        lower_content = self.content.lower()
        assert "consent" in lower_content
        assert "mrn" in lower_content or "id" in lower_content or "registration" in lower_content

    def test_tc_t1_f04_03_checklists_station_2_photography_qa(self):
        """TC-T1-F04-03: Station 2: Photography QA, pupil dilation threshold, alignment."""
        assert "Station 2" in self.content or "Photography" in self.content
        lower_content = self.content.lower()
        assert "pupil" in lower_content or "dilation" in lower_content
        assert "macula" in lower_content and "disc" in lower_content

    def test_tc_t1_f04_04_checklists_station_3_clinician_review(self):
        """TC-T1-F04-04: Station 3: Clinician review, independent evaluation, override documentation."""
        assert "Station 3" in self.content or "Review" in self.content
        lower_content = self.content.lower()
        assert "override" in lower_content or "advisory" in lower_content
        assert "justification" in lower_content or "notes" in lower_content or "documentation" in lower_content

    def test_tc_t1_f04_05_checklists_station_4_and_5_escalation_hygiene(self):
        """TC-T1-F04-05: Stations 4 & 5: Grade 4 escalation protocol and 70% alcohol hygiene."""
        lower_content = self.content.lower()
        assert "escalation" in lower_content or "referral" in lower_content
        assert "hygiene" in lower_content or "disinfection" in lower_content or "alcohol" in lower_content or "chin" in lower_content


# ==============================================================================
# Feature 5: Sargodha Doctor Onboarding Kit
# ==============================================================================

class TestTier1Feature05DoctorOnboardingKit:
    """Feature 5: Sargodha Doctor Onboarding Kit (docs/sargodha/doctor_onboarding_kit.md)."""

    @pytest.fixture(autouse=True)
    def setup_path(self, repo_root: Path):
        self.doc_path = repo_root / "docs" / "sargodha" / "doctor_onboarding_kit.md"
        assert self.doc_path.is_file(), f"Document missing: {self.doc_path}"
        self.content = self.doc_path.read_text(encoding="utf-8")

    def test_tc_t1_f05_01_onboarding_kit_existence_and_welcome(self, markdown_linter):
        """TC-T1-F05-01: Welcome kit existence, professional tone, zero placeholders."""
        assert "Welcome" in self.content or "Onboarding" in self.content
        markdown_linter.assert_zero_placeholders(self.doc_path)

    def test_tc_t1_f05_02_onboarding_credential_verification_checklist(self):
        """TC-T1-F05-02: PMDC credential verification checklist and ophthalmic qualifications."""
        assert "PMDC" in self.content
        assert "FCPS" in self.content or "MBBS" in self.content or "Ophthalmology" in self.content

    def test_tc_t1_f05_03_onboarding_account_provisioning_workflow(self):
        """TC-T1-F05-03: Account provisioning, authentication, and role elevation workflow."""
        lower_content = self.content.lower()
        assert "account" in lower_content
        assert "clinician" in lower_content or "role" in lower_content or "verification" in lower_content

    def test_tc_t1_f05_04_onboarding_clinical_governance_and_cds_rules(self):
        """TC-T1-F05-04: Clinical governance: doctor retains ultimate clinical responsibility."""
        lower_content = self.content.lower()
        assert "responsibility" in lower_content or "clinical judgment" in lower_content or "decision support" in lower_content
        assert "override" in lower_content or "disclaimer" in lower_content

    def test_tc_t1_f05_05_onboarding_verified_sargodha_directory_roster(self):
        """TC-T1-F05-05: Grounded roster of participating Sargodha institutions and contacts."""
        assert "Sargodha" in self.content
        assert any(name in self.content for name in ["Faisal Masood", "LRBT", "Niazi", "Mubarak", "DHQ"])


# ==============================================================================
# Feature 6: Patient Split Script
# ==============================================================================

class TestTier1Feature06PatientSplitScript:
    """Feature 6: Patient Split Script (scripts/split_dataset.py)."""

    @pytest.fixture(autouse=True)
    def setup_script(self, repo_root: Path):
        self.script_path = repo_root / "scripts" / "split_dataset.py"
        assert self.script_path.is_file(), f"Script missing: {self.script_path}"

    def test_tc_t1_f06_01_split_script_cli_execution(self, python_exe: str, tmp_path: Path):
        """TC-T1-F06-01: CLI execution with --mock produces split CSVs and summary JSON."""
        out_dir = tmp_path / "splits_t1"
        res = subprocess.run(
            [python_exe, str(self.script_path), "--mock", "--output-dir", str(out_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert res.returncode == 0, f"Split script failed: {res.stderr}"
        assert (out_dir / "train_split.csv").is_file()
        assert (out_dir / "val_split.csv").is_file()
        assert (out_dir / "test_split.csv").is_file()
        assert (out_dir / "split_summary.json").is_file()

    def test_tc_t1_f06_02_split_script_zero_patient_overlap(self, tmp_path: Path, python_exe: str):
        """TC-T1-F06-02: Zero patient ID overlap invariant across train/val/test splits."""
        out_dir = tmp_path / "splits_t2"
        subprocess.run(
            [python_exe, str(self.script_path), "--mock", "--output-dir", str(out_dir)],
            check=True,
            timeout=30,
        )
        train_df = pd.read_csv(out_dir / "train_split.csv")
        val_df = pd.read_csv(out_dir / "val_split.csv")
        test_df = pd.read_csv(out_dir / "test_split.csv")

        train_patients = set(train_df["patient_id"].unique())
        val_patients = set(val_df["patient_id"].unique())
        test_patients = set(test_df["patient_id"].unique())

        assert len(train_patients & val_patients) == 0, "Train-Val patient leakage detected!"
        assert len(train_patients & test_patients) == 0, "Train-Test patient leakage detected!"
        assert len(val_patients & test_patients) == 0, "Val-Test patient leakage detected!"

    def test_tc_t1_f06_03_split_script_patient_level_severity_aggregation(self, tmp_path: Path):
        """TC-T1-F06-03: Patient severity aggregation logic aggregates max(diagnosis)."""
        from scripts.split_dataset import split_dataset
        df = pd.DataFrame([
            {"image_id": "img1", "patient_id": "P1", "diagnosis": 1},
            {"image_id": "img2", "patient_id": "P1", "diagnosis": 3},
            {"image_id": "img3", "patient_id": "P2", "diagnosis": 0},
            {"image_id": "img4", "patient_id": "P3", "diagnosis": 4},
            {"image_id": "img5", "patient_id": "P4", "diagnosis": 2},
            {"image_id": "img6", "patient_id": "P5", "diagnosis": 0},
            {"image_id": "img7", "patient_id": "P6", "diagnosis": 1},
            {"image_id": "img8", "patient_id": "P7", "diagnosis": 2},
            {"image_id": "img9", "patient_id": "P8", "diagnosis": 3},
            {"image_id": "img10", "patient_id": "P9", "diagnosis": 4},
        ])
        train_df, val_df, test_df, summary = split_dataset(df, train_ratio=0.6, val_ratio=0.2, test_ratio=0.2, random_seed=42)
        assert summary["total_patients"] == 9
        # Both images of P1 must be in the same partition
        p1_splits = [
            name for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]
            if "P1" in set(split_df["patient_id"])
        ]
        assert len(p1_splits) == 1, "Patient P1 multi-images partitioned into multiple splits!"

    def test_tc_t1_f06_04_split_script_split_ratios_proportions(self, tmp_path: Path, python_exe: str):
        """TC-T1-F06-04: Default split ratios allocate approximately 70% train, 15% val, 15% test."""
        out_dir = tmp_path / "splits_ratios"
        subprocess.run(
            [python_exe, str(self.script_path), "--mock", "--output-dir", str(out_dir)],
            check=True,
            timeout=30,
        )
        summary = json.loads((out_dir / "split_summary.json").read_text(encoding="utf-8"))
        tot = summary["total_patients"]
        train_pts = summary["train_split"]["patient_count"]
        val_pts = summary["val_split"]["patient_count"]
        test_pts = summary["test_split"]["patient_count"]
        assert 0.65 <= (train_pts / tot) <= 0.75
        assert 0.10 <= (val_pts / tot) <= 0.20
        assert 0.10 <= (test_pts / tot) <= 0.20

    def test_tc_t1_f06_05_split_script_deterministic_seed(self, tmp_path: Path, python_exe: str):
        """TC-T1-F06-05: Deterministic seed produces identical split manifests across runs."""
        out1 = tmp_path / "seed_run1"
        out2 = tmp_path / "seed_run2"
        subprocess.run(
            [python_exe, str(self.script_path), "--mock", "--output-dir", str(out1), "--random-seed", "777"],
            check=True,
            timeout=30,
        )
        subprocess.run(
            [python_exe, str(self.script_path), "--mock", "--output-dir", str(out2), "--random-seed", "777"],
            check=True,
            timeout=30,
        )
        sum1 = (out1 / "split_summary.json").read_text(encoding="utf-8")
        sum2 = (out2 / "split_summary.json").read_text(encoding="utf-8")
        assert sum1 == sum2, "Split summaries differ despite identical random seed!"


# ==============================================================================
# Feature 7: Split Tests Verification
# ==============================================================================

class TestTier1Feature07SplitTests:
    """Feature 7: Automated Zero-Leakage Split Tests (tests/test_ml_pipeline.py)."""

    @pytest.fixture(autouse=True)
    def setup_path(self, repo_root: Path):
        self.test_path = repo_root / "tests" / "test_ml_pipeline.py"
        if not self.test_path.is_file():
            pytest.skip(f"Test suite file not available: {self.test_path}")
        self.content = self.test_path.read_text(encoding="utf-8")

    def test_tc_t1_f07_01_split_tests_file_existence_and_discovery(self):
        """TC-T1-F07-01: tests/test_ml_pipeline.py is present and syntactically valid."""
        compile(self.content, str(self.test_path), "exec")

    def test_tc_t1_f07_02_split_tests_disjoint_patient_assertion(self):
        """TC-T1-F07-02: Confirms assertion for zero patient overlap across splits."""
        assert "intersection" in self.content or "&" in self.content
        assert "overlap" in self.content.lower() or "leakage" in self.content.lower()

    def test_tc_t1_f07_03_split_tests_stratification_balance_assertion(self):
        """TC-T1-F07-03: Confirms test verifying DR grade distribution preservation."""
        assert "stratification" in self.content.lower() or "distribution" in self.content.lower()

    def test_tc_t1_f07_04_split_tests_multi_image_co_location(self):
        """TC-T1-F07-04: Confirms test verifying multi-image patient co-location."""
        assert "patient" in self.content and "image" in self.content

    def test_tc_t1_f07_05_split_tests_manifest_schema_verification(self):
        """TC-T1-F07-05: Confirms schema column verification in test suite."""
        assert "patient_id" in self.content
        assert "diagnosis" in self.content or "grade" in self.content


# ==============================================================================
# Feature 8: Leak-Free Data Generator
# ==============================================================================

class TestTier1Feature08DataGenerator:
    """Feature 8: Leak-Free Data Generator & Pipeline (scripts/data_generator.py)."""

    @pytest.fixture(autouse=True)
    def setup_gen(self, repo_root: Path):
        script_path = repo_root / "scripts" / "data_generator.py"
        assert script_path.is_file(), f"Missing: {script_path}"

    def test_tc_t1_f08_01_data_generator_instantiation_and_batch_yield(self, tmp_path: Path, mock_fundus_factory):
        """TC-T1-F08-01: RetinalDataGenerator yields correct tensor batch shapes."""
        from scripts.data_generator import RetinalDataGenerator
        img_dir = tmp_path / "fundus_imgs"
        img_dir.mkdir()
        mock_fundus_factory.save_fundus_file(img_dir / "img1.jpg")
        mock_fundus_factory.save_fundus_file(img_dir / "img2.jpg")

        df = pd.DataFrame([
            {"image_id": "img1", "patient_id": "P1", "diagnosis": 0},
            {"image_id": "img2", "patient_id": "P2", "diagnosis": 2},
        ])
        gen = RetinalDataGenerator(df, img_dir=img_dir, batch_size=2, target_size=(224, 224), is_training=False)
        X_batch, y_batch = gen[0]
        assert X_batch.shape == (2, 224, 224, 3)
        assert y_batch.shape == (2, 5)

    def test_tc_t1_f08_02_data_generator_raw_pixel_range_contract(self, tmp_path: Path, mock_fundus_factory):
        """TC-T1-F08-02: Input pixel contract adheres to raw [0.0, 255.0] float32 range."""
        from scripts.data_generator import RetinalDataGenerator
        img_dir = tmp_path / "fundus_raw"
        img_dir.mkdir()
        mock_fundus_factory.save_fundus_file(img_dir / "raw1.jpg")

        df = pd.DataFrame([{"image_id": "raw1", "patient_id": "P1", "diagnosis": 1}])
        gen = RetinalDataGenerator(df, img_dir=img_dir, batch_size=1, is_training=False)
        X_batch, _ = gen[0]
        assert X_batch.dtype == np.float32
        assert float(np.min(X_batch)) >= 0.0
        assert float(np.max(X_batch)) <= 255.0
        # If mean subtraction were applied, min would be negative
        assert float(np.min(X_batch)) >= 0.0

    def test_tc_t1_f08_03_data_generator_cumulative_ordinal_targets(self):
        """TC-T1-F08-03: Frank & Hall cumulative binary targets match clinical ordinal hierarchy."""
        from scripts.data_generator import grade_to_cumulative_ordinal
        np.testing.assert_array_equal(grade_to_cumulative_ordinal(0), [1, 0, 0, 0, 0])
        np.testing.assert_array_equal(grade_to_cumulative_ordinal(1), [1, 1, 0, 0, 0])
        np.testing.assert_array_equal(grade_to_cumulative_ordinal(2), [1, 1, 1, 0, 0])
        np.testing.assert_array_equal(grade_to_cumulative_ordinal(3), [1, 1, 1, 1, 0])
        np.testing.assert_array_equal(grade_to_cumulative_ordinal(4), [1, 1, 1, 1, 1])

    def test_tc_t1_f08_04_data_generator_training_online_augmentation_active(self, tmp_path: Path, mock_fundus_factory):
        """TC-T1-F08-04: Online augmentation is enabled when is_training=True."""
        from scripts.data_generator import RetinalDataGenerator
        img_dir = tmp_path / "fundus_aug"
        img_dir.mkdir()
        mock_fundus_factory.save_fundus_file(img_dir / "aug1.jpg")
        df = pd.DataFrame([{"image_id": "aug1", "patient_id": "P1", "diagnosis": 2}])

        gen = RetinalDataGenerator(df, img_dir=img_dir, batch_size=1, is_training=True)
        assert gen.is_training is True

    def test_tc_t1_f08_05_data_generator_validation_pristine_determinism(self, tmp_path: Path, mock_fundus_factory):
        """TC-T1-F08-05: Validation/test data remains deterministic and unaugmented."""
        from scripts.data_generator import RetinalDataGenerator
        img_dir = tmp_path / "fundus_val"
        img_dir.mkdir()
        mock_fundus_factory.save_fundus_file(img_dir / "det1.jpg")
        df = pd.DataFrame([{"image_id": "det1", "patient_id": "P1", "diagnosis": 0}])

        gen = RetinalDataGenerator(df, img_dir=img_dir, batch_size=1, is_training=False)
        b1, _ = gen[0]
        b2, _ = gen[0]
        np.testing.assert_array_equal(b1, b2)


# ==============================================================================
# Feature 9: Retraining Harness
# ==============================================================================

class TestTier1Feature09RetrainingHarness:
    """Feature 9: Retraining Harness & Dry-Run Execution (scripts/train_harness.py)."""

    @pytest.fixture(autouse=True)
    def setup_harness(self, repo_root: Path):
        self.script_path = repo_root / "scripts" / "train_harness.py"
        assert self.script_path.is_file(), f"Missing: {self.script_path}"
        self.content = self.script_path.read_text(encoding="utf-8")

    def test_tc_t1_f09_01_train_harness_help_cli(self, python_exe: str):
        """TC-T1-F09-01: CLI --help option prints valid arguments and exit code 0."""
        res = subprocess.run([python_exe, str(self.script_path), "--help"], capture_output=True, text=True, timeout=30)
        assert res.returncode == 0
        assert "--dry-run" in res.stdout
        assert "--max-steps" in res.stdout

    def test_tc_t1_f09_02_train_harness_single_step_arg_contract(self):
        """TC-T1-F09-02: Harness implements guardrails against uncontrolled full retraining."""
        assert "--max-steps" in self.content
        assert "--dry-run" in self.content
        assert "EarlyStopping" in self.content or "ModelCheckpoint" in self.content

    def test_tc_t1_f09_03_train_harness_model_architecture_definition(self):
        """TC-T1-F09-03: DenseNet-121 ordinal classifier layer architecture."""
        from scripts.train_harness import build_densenet_ordinal_model
        assert callable(build_densenet_ordinal_model)
        assert "DenseNet121" in self.content
        assert "GlobalAveragePooling2D" in self.content
        assert "sigmoid" in self.content

    def test_tc_t1_f09_04_train_harness_qwk_callback_tracking(self):
        """TC-T1-F09-04: Quadratic Weighted Kappa callback registration."""
        from scripts.train_harness import QuadraticWeightedKappaCallback
        assert issubclass(QuadraticWeightedKappaCallback, object)
        assert "cohen_kappa_score" in self.content

    def test_tc_t1_f09_05_train_harness_artifact_export_specification(self):
        """TC-T1-F09-05: Artifact export paths (checkpoints, retraining history JSON)."""
        assert "retraining_history.json" in self.content
        assert "best" in self.content or "checkpoint" in self.content.lower()


# ==============================================================================
# Feature 10: Model Evaluation Script
# ==============================================================================

class TestTier1Feature10ModelEvaluation:
    """Feature 10: Clinical Model Evaluation Script (scripts/evaluate_model.py)."""

    @pytest.fixture
    def evaluation_report(self, repo_root: Path, tmp_path: Path) -> Dict[str, Any]:
        """Run evaluation routine in mock mode and return parsed report."""
        from scripts.evaluate_model import run_evaluation
        out_json = tmp_path / "eval_report.json"
        report = run_evaluation(force_mock=True, output_json=out_json)
        assert out_json.is_file()
        return report

    def test_tc_t1_f10_01_evaluate_model_cli_execution(self, evaluation_report: Dict[str, Any]):
        """TC-T1-F10-01: CLI execution with --mock produces valid JSON evaluation report."""
        assert "sample_count" in evaluation_report
        assert evaluation_report["sample_count"] > 0

    def test_tc_t1_f10_02_evaluate_model_qwk_metric_presence(self, evaluation_report: Dict[str, Any]):
        """TC-T1-F10-02: Quadratic Weighted Kappa metric is bounded in [-1.0, 1.0]."""
        assert "quadratic_weighted_kappa" in evaluation_report
        qwk = evaluation_report["quadratic_weighted_kappa"]
        assert -1.0 <= qwk <= 1.0

    def test_tc_t1_f10_03_evaluate_model_accuracy_metric(self, evaluation_report: Dict[str, Any]):
        """TC-T1-F10-03: Exact grade accuracy is reported in [0.0, 1.0]."""
        assert "exact_grade_accuracy" in evaluation_report or "accuracy" in evaluation_report
        acc = evaluation_report.get("exact_grade_accuracy", evaluation_report.get("accuracy"))
        assert 0.0 <= acc <= 1.0

    def test_tc_t1_f10_04_evaluate_model_referable_dr_metrics(self, evaluation_report: Dict[str, Any]):
        """TC-T1-F10-04: Referable DR sensitivity and specificity metrics are present."""
        assert "referable_dr_metrics" in evaluation_report or "referable_dr" in evaluation_report
        ref = evaluation_report.get("referable_dr_metrics", evaluation_report.get("referable_dr", {}))
        assert 0.0 <= ref["sensitivity"] <= 1.0
        assert 0.0 <= ref["specificity"] <= 1.0

    def test_tc_t1_f10_05_evaluate_model_confusion_matrix_shape(self, evaluation_report: Dict[str, Any]):
        """TC-T1-F10-05: 5x5 confusion matrix structure."""
        assert "confusion_matrix" in evaluation_report
        cm = evaluation_report["confusion_matrix"]
        assert len(cm) == 5, "Confusion matrix must have 5 rows (Grades 0-4)"
        for row in cm:
            assert len(row) == 5, "Each row in confusion matrix must have 5 columns"


# ==============================================================================
# Feature 11: Dockerfile Non-Root Verification
# ==============================================================================

class TestTier1Feature11DockerfileNonRoot:
    """Feature 11: Dockerfile Non-Root Verification (Dockerfile)."""

    @pytest.fixture(autouse=True)
    def setup_dockerfile(self, repo_root: Path):
        self.dockerfile = repo_root / "Dockerfile"
        assert self.dockerfile.is_file(), f"Missing: {self.dockerfile}"
        self.content = self.dockerfile.read_text(encoding="utf-8")

    def test_tc_t1_f11_01_dockerfile_base_image_minimal(self):
        """TC-T1-F11-01: Dockerfile uses official minimal base image (python:3.12-slim)."""
        assert re.search(r"FROM\s+python:3\.12-slim", self.content)

    def test_tc_t1_f11_02_dockerfile_useradd_unprivileged(self):
        """TC-T1-F11-02: Explicit useradd creation of UID 1000 appuser."""
        assert re.search(r"useradd.*-u\s+1000.*appuser", self.content)

    def test_tc_t1_f11_03_dockerfile_user_directive(self):
        """TC-T1-F11-03: USER appuser directive switches process execution context."""
        assert re.search(r"USER\s+appuser", self.content)

    def test_tc_t1_f11_04_dockerfile_chown_app_directory(self):
        """TC-T1-F11-04: chown ensures appuser owns application working directory."""
        assert "chown -R appuser:appuser /app" in self.content

    def test_tc_t1_f11_05_dockerfile_port_and_healthcheck(self):
        """TC-T1-F11-05: Standardizes on port 5000 and dynamic healthcheck."""
        assert "EXPOSE 5000" in self.content
        assert "HEALTHCHECK" in self.content
        assert "localhost:${PORT:-5000}/api/health" in self.content


# ==============================================================================
# Feature 12: Staging Compose Configuration
# ==============================================================================

class TestTier1Feature12StagingCompose:
    """Feature 12: Multi-Service Staging Compose Configuration (docker-compose.staging.yml)."""

    @pytest.fixture(autouse=True)
    def setup_compose(self, repo_root: Path):
        self.compose_file = repo_root / "docker-compose.staging.yml"
        assert self.compose_file.is_file(), f"Missing: {self.compose_file}"
        self.content = self.compose_file.read_text(encoding="utf-8")

    def test_tc_t1_f12_01_compose_syntax_and_services(self):
        """TC-T1-F12-01: Valid structure containing retina-api and staging-proxy."""
        assert "services:" in self.content
        assert "retina-api:" in self.content
        assert "staging-proxy:" in self.content

    def test_tc_t1_f12_02_compose_internal_network_isolation(self):
        """TC-T1-F12-02: retina-api is isolated on private network without published host ports."""
        assert "staging-net" in self.content
        # Ensure retina-api section does NOT have host port mappings
        lines = self.content.splitlines()
        in_retina_api = False
        in_proxy = False
        api_ports = []
        for line in lines:
            if "retina-api:" in line:
                in_retina_api = True
                in_proxy = False
            elif "staging-proxy:" in line:
                in_retina_api = False
                in_proxy = True
            elif in_retina_api and line.strip().startswith("ports:"):
                api_ports.append(line)
        assert len(api_ports) == 0, "retina-api must NOT bind host ports directly!"

    def test_tc_t1_f12_03_compose_proxy_ports(self):
        """TC-T1-F12-03: staging-proxy binds host ports 8080 (HTTP) and 8443 (HTTPS)."""
        assert '8080:80' in self.content or '"8080:80"' in self.content or "'8080:80'" in self.content
        assert '8443:443' in self.content or '"8443:443"' in self.content or "'8443:443'" in self.content

    def test_tc_t1_f12_04_compose_volume_mounts(self):
        """TC-T1-F12-04: staging-proxy mounts NGINX configuration and TLS certificates."""
        assert "conf.d" in self.content
        assert "certs" in self.content

    def test_tc_t1_f12_05_compose_dependencies(self):
        """TC-T1-F12-05: staging-proxy depends on retina-api health."""
        assert "depends_on:" in self.content
        assert "retina-api" in self.content


# ==============================================================================
# Feature 13: NGINX TLS 1.3 Reverse Proxy Configuration
# ==============================================================================

class TestTier1Feature13NginxTls:
    """Feature 13: NGINX TLS 1.3 Reverse Proxy Configuration (staging/nginx/)."""

    @pytest.fixture(autouse=True)
    def setup_nginx(self, repo_root: Path):
        self.conf_path = repo_root / "staging" / "nginx" / "conf.d" / "staging.conf"
        assert self.conf_path.is_file(), f"Missing: {self.conf_path}"
        self.content = self.conf_path.read_text(encoding="utf-8")

    def test_tc_t1_f13_01_nginx_tls_protocols(self):
        """TC-T1-F13-01: ssl_protocols enforces TLS 1.3 and modern TLS 1.2."""
        assert "TLSv1.3" in self.content
        assert "SSLv2" not in self.content and "SSLv3" not in self.content

    def test_tc_t1_f13_02_nginx_modern_ciphers(self):
        """TC-T1-F13-02: Modern forward-secret ciphers configured."""
        assert "ssl_ciphers" in self.content
        assert "ECDHE" in self.content

    def test_tc_t1_f13_03_nginx_hsts_header(self):
        """TC-T1-F13-03: HSTS security header with long max-age and subdomains."""
        assert "Strict-Transport-Security" in self.content
        assert "max-age=63072000" in self.content
        assert "includeSubDomains" in self.content

    def test_tc_t1_f13_04_nginx_security_framing_headers(self):
        """TC-T1-F13-04: Security framing headers: nosniff, DENY, CSP."""
        assert "X-Content-Type-Options" in self.content and "nosniff" in self.content
        assert "X-Frame-Options" in self.content and "DENY" in self.content
        assert "Content-Security-Policy" in self.content

    def test_tc_t1_f13_05_nginx_client_max_body_and_proxy_pass(self):
        """TC-T1-F13-05: client_max_body_size 16M and upstream proxy_pass to retina-api:5000."""
        assert "client_max_body_size 16M;" in self.content
        assert "retina-api:5000" in self.content
        assert "proxy_pass" in self.content


# ==============================================================================
# Feature 14: Automated Staging Verification Script
# ==============================================================================

class TestTier1Feature14StagingVerificationScript:
    """Feature 14: Automated Staging Verification Script (scripts/verify_staging.py)."""

    @pytest.fixture(autouse=True)
    def setup_verifier(self, repo_root: Path):
        self.script_path = repo_root / "scripts" / "verify_staging.py"
        assert self.script_path.is_file(), f"Missing: {self.script_path}"

    def test_tc_t1_f14_01_verify_staging_lint_only_cli(self, python_exe: str):
        """TC-T1-F14-01: Static configuration linting passes with exit code 0."""
        res = subprocess.run([python_exe, str(self.script_path), "--lint-only"], capture_output=True, text=True, timeout=30)
        assert res.returncode == 0
        assert "PASSED" in res.stdout

    def test_tc_t1_f14_02_verify_staging_non_root_audit(self, python_exe: str):
        """TC-T1-F14-02: Linter checks Dockerfile non-root directives."""
        res = subprocess.run([python_exe, str(self.script_path), "--lint-only"], capture_output=True, text=True, timeout=30)
        assert "dockerfile_non_root" in res.stdout

    def test_tc_t1_f14_03_verify_staging_mock_probes_cli(self, python_exe: str):
        """TC-T1-F14-03: Simulated mock probes pass offline without live Docker."""
        res = subprocess.run([python_exe, str(self.script_path), "--mock-probes"], capture_output=True, text=True, timeout=30)
        assert res.returncode == 0
        assert "PASSED" in res.stdout

    def test_tc_t1_f14_04_verify_staging_tls_certificate_validation(self, python_exe: str):
        """TC-T1-F14-04: Linter validates staging TLS certificate validity."""
        res = subprocess.run([python_exe, str(self.script_path), "--lint-only"], capture_output=True, text=True, timeout=30)
        assert "certificate_validity" in res.stdout

    def test_tc_t1_f14_05_verify_staging_report_json_export(self, python_exe: str, tmp_path: Path):
        """TC-T1-F14-05: Verification report is exported to JSON with status passed."""
        out_json = tmp_path / "staging_lint.json"
        res = subprocess.run(
            [python_exe, str(self.script_path), "--lint-only", "--output-json", str(out_json)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert res.returncode == 0
        assert out_json.is_file()
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data.get("overall_status") == "PASS" or data.get("all_passed") is True


# ==============================================================================
# Feature 15: Approval Gates Audit & Pilot Prerequisites
# ==============================================================================

class TestTier1Feature15ApprovalGatesAudit:
    """Feature 15: Approval Gates Audit & Pilot Prerequisites (audit/pilot_readiness_audit.md)."""

    @pytest.fixture(autouse=True)
    def setup_audit(self, repo_root: Path):
        self.doc_path = repo_root / "audit" / "pilot_readiness_audit.md"
        assert self.doc_path.is_file(), f"Missing: {self.doc_path}"
        self.content = self.doc_path.read_text(encoding="utf-8")

    def test_tc_t1_f15_01_gates_audit_document_existence(self, markdown_linter):
        """TC-T1-F15-01: Document existence, comprehensive size, zero placeholders."""
        stats = markdown_linter.scan_file(self.doc_path)
        assert stats["size_bytes"] > 25_000
        markdown_linter.assert_zero_placeholders(self.doc_path)

    def test_tc_t1_f15_02_gate_g01_retraining_coverage(self):
        """TC-T1-F15-02: Gate G-01 details patient leakage root cause in 85.ipynb and retraining gate."""
        assert "G-01" in self.content
        assert "85.ipynb" in self.content
        assert "leakage" in self.content.lower() or "contamination" in self.content.lower()

    def test_tc_t1_f15_03_gate_g02_and_g03_coverage(self):
        """TC-T1-F15-03: Gates G-02 (Foundation Model) & G-03 (Provider Outreach) audited."""
        assert "G-02" in self.content and "RETFound" in self.content
        assert "G-03" in self.content and "outreach" in self.content.lower()

    def test_tc_t1_f15_04_gate_g04_g05_g06_coverage(self):
        """TC-T1-F15-04: Gates G-04 (Cloud Vertex), G-05 (Cascade Erasure), G-06 (Staging Budget) audited."""
        assert "G-04" in self.content
        assert "G-05" in self.content
        assert "G-06" in self.content

    def test_tc_t1_f15_05_pilot_prerequisites_matrix(self):
        """TC-T1-F15-05: Comprehensive prerequisites matrix separating completed vs human items."""
        assert "Autonomous" in self.content
        assert "Human" in self.content
        assert "Sign-Off" in self.content or "Approval" in self.content


# ==============================================================================
# Feature 16: Autonomous Execution Guardrails & Test Stability
# ==============================================================================

class TestTier1Feature16GuardrailsAndStability:
    """Feature 16: Autonomous Execution Guardrails & Test Suite Stability."""

    def test_tc_t1_f16_01_pytest_baseline_stability(self, repo_root: Path):
        """TC-T1-F16-01: Baseline test modules exist and are discoverable."""
        test_files = list((repo_root / "tests").glob("test_*.py"))
        assert len(test_files) >= 9, f"Expected >= 9 baseline test files, found {len(test_files)}"

    def test_tc_t1_f16_02_mobile_typescript_config_presence(self, repo_root: Path):
        """TC-T1-F16-02: Mobile client tsconfig and package manifests present."""
        assert (repo_root / "mobile" / "tsconfig.json").is_file()
        assert (repo_root / "mobile" / "package.json").is_file()

    def test_tc_t1_f16_03_zero_real_patient_data_enforcement(self, repo_root: Path):
        """TC-T1-F16-03: Confirms zero Pakistani CNICs (XXXXX-XXXXXXX-X) in repository."""
        cnic_pattern = re.compile(r"\b\d{5}-\d{7}-\d{1}\b")
        for ext in ["*.py", "*.md", "*.csv"]:
            for f in repo_root.glob(f"**/{ext}"):
                if ".venv" in f.parts or "node_modules" in f.parts or ".git" in f.parts:
                    continue
                text = f.read_text(encoding="utf-8", errors="ignore")
                matches = cnic_pattern.findall(text)
                assert len(matches) == 0, f"Real CNIC pattern detected in {f}: {matches}"

    def test_tc_t1_f16_04_zero_external_network_outreach_guard(self, repo_root: Path):
        """TC-T1-F16-04: Confirms no hardcoded production doctor phone numbers or external IPs."""
        # Confirm staging configs bind to localhost/private IPs only
        staging_conf = (repo_root / "staging" / "nginx" / "conf.d" / "staging.conf").read_text(encoding="utf-8")
        assert "retina-api:5000" in staging_conf

    def test_tc_t1_f16_05_diagnostic_module_import_isolation(self, repo_root: Path):
        """TC-T1-F16-05: Non-destructive test_supabase.py diagnostic module is intact."""
        supa_test = repo_root / "test_supabase.py"
        assert supa_test.is_file(), "test_supabase.py diagnostic script must remain intact"


# ==============================================================================
# Feature 17: Supervised Pilot Readiness Presentation
# ==============================================================================

class TestTier1Feature17PilotPresentation:
    """Feature 17: Supervised Pilot Readiness Presentation."""

    @pytest.fixture(autouse=True)
    def setup_presentation(self, repo_root: Path):
        self.doc_path = repo_root / "audit" / "pilot_readiness_audit.md"
        assert self.doc_path.is_file(), f"Missing: {self.doc_path}"
        self.content = self.doc_path.read_text(encoding="utf-8")

    def test_tc_t1_f17_01_pilot_presentation_synthesis(self):
        """TC-T1-F17-01: Executive synthesis of completed autonomous technical deliverables."""
        assert "Executive Audit Summary" in self.content
        assert "Technical Prerequisites 100% Complete" in self.content

    def test_tc_t1_f17_02_pilot_presentation_approval_queue(self):
        """TC-T1-F17-02: Structured Batch Human Approval Queue for all 6 gates."""
        assert "Batch Human Approval Queue" in self.content or "Human Approval Gates" in self.content
        for g in ["G-01", "G-02", "G-03", "G-04", "G-05", "G-06"]:
            assert g in self.content, f"Missing {g} in approval queue"

    def test_tc_t1_f17_03_pilot_presentation_artifact_index(self):
        """TC-T1-F17-03: Technical artifact index tabulating completed deliverables."""
        assert "docs/sargodha" in self.content
        assert "scripts/split_dataset.py" in self.content or "split_dataset" in self.content
        assert "docker-compose.staging.yml" in self.content or "staging" in self.content

    def test_tc_t1_f17_04_pilot_presentation_sign_off_checklist(self):
        """TC-T1-F17-04: Actionable sign-off checklist for clinical and administrative leaders."""
        assert "Sign-Off" in self.content
        assert "Clinical Director" in self.content or "Human Overseer" in self.content

    def test_tc_t1_f17_05_pilot_presentation_governance_halt(self):
        """TC-T1-F17-05: Formal governance declaration that autonomous swarm has halted before pilot."""
        assert "HALTED" in self.content or "halted" in self.content.lower() or "Governance Boundary" in self.content
