# Diabetic Retinopathy Detection Application

## Autonomous Multi-Agent Remediation & Production Roadmap

**Project location:** Sargodha, Punjab, Pakistan\
**Execution environment:** Google Antigravity using `/teamwork` and a
coordinated agent swarm\
**Primary objective:** Turn the existing diabetic retinopathy screening
application into a secure, reliable, maintainable application that can
be evaluated for a supervised real-world pilot with participating
healthcare providers.

------------------------------------------------------------------------

# 1. Mission and operating principles

Use `/teamwork` to coordinate specialized agents, create a shared
execution plan, assign independent workstreams, track dependencies, and
consolidate evidence.

The swarm should automate as much engineering work as safely possible:
repository inspection, planning, tests, implementation of approved
low-risk fixes, documentation, regression testing, and report
generation.

**Autonomy does not mean unrestricted authority.** The system must stop
for human approval before actions that could affect real patients,
clinical decisions, production data, external people or organizations,
paid services, model retraining, or production deployment.

## Non-negotiable principles

1.  Inspect the actual repository and running application; never assume
    the audit findings are still current.
2.  Verify every reported defect before changing code.
3.  Preserve the existing architecture unless a documented technical
    reason supports a change.
4.  Do not hardcode credentials, API keys, patient records, provider
    records, environment-specific URLs, filesystem paths, or test
    identities.
5.  Never use real patient data in development or automated tests. Use
    synthetic test data.
6.  Do not fabricate hospitals, doctors, qualifications, PMDC
    registrations, phone numbers, partnerships, appointments, or
    clinical results.
7.  Never expose patient data without explicit, recorded authorization
    and appropriate access controls.
8.  Do not present AI screening output as a confirmed medical diagnosis.
9.  Do not fabricate test results, coverage, benchmarks, metrics, or
    agent activity.
10. Keep implementation agents separate from independent verification
    agents.
11. Every code change must have a corresponding test and a documented
    rollback path.
12. Never deploy to production, contact external providers, incur costs,
    or modify production data without explicit approval.

------------------------------------------------------------------------

# 2. Starting context from the initial audit

The initial multi-agent audit reported:

-   Composite quality score: **55/100**
-   Critical findings: **7**
-   High-severity findings: **18**
-   Tracked defects: **37**
-   Automated tests reported passing: **66/66**

The audit also reported these high-priority concerns:

-   Clinician grant authorization / BOLA issue.
-   Fail-open authentication behavior in the Flask API.
-   Client-side persistence of prediction records.
-   Missing retinal image preview in the clinician review workflow.
-   Docker packaging failure due to a missing validator module.
-   Gunicorn worker/thread starvation.
-   Potential training data leakage in `85.ipynb`.
-   Model identity mismatch: described as RETFound while implementation
    reportedly uses DenseNet121.
-   Potential mismatch in inference preprocessing.
-   Weak rejection of non-retinal or invalid images.
-   Medical image transmission to a third-party AI service requiring
    privacy and contractual review.
-   Missing or incomplete data deletion behavior.
-   Exposed API credential reported in the repository `.env` file.

These are **unverified starting hypotheses**, not unquestionable facts.
Reproduce each finding against the current working tree before
remediation. If a reported issue is absent, record it as not reproduced
and explain why.

------------------------------------------------------------------------

# 3. Swarm structure and responsibilities

Use agents supported by the current Antigravity `/teamwork` environment.
Do not assume a fixed number of agents or invent capabilities. If
parallel agents are unavailable, execute the workstreams sequentially.

  -----------------------------------------------------------------------
  Agent                   Primary responsibility  Independence
  ----------------------- ----------------------- -----------------------
  Team Lead /             Plan, dependencies,     Coordinates all
  Orchestrator            assignments, status,    
                          decisions, final        
                          reports                 

  Repository Architect    Architecture, modules,  Read-only initially
                          API and data-flow       
                          inventory               

  Security Engineer       Authentication,         Implements approved
                          authorization, API and  fixes
                          storage security        

  Database Engineer       Schema, migrations, RLS Coordinates shared DB
                          and data integrity      changes

  Backend Engineer        Flask APIs, inference   Implements approved
                          integration and         fixes
                          persistence             

  Mobile Engineer         Patient and clinician   Implements approved
                          app workflows           fixes

  ML Engineer             Model architecture,     No retraining without
                          preprocessing and       approval
                          inference               

  Dataset Auditor         Dataset provenance,     Read-only initially
                          duplicates, leakage and 
                          splits                  

  Privacy Auditor         Sensitive data          Read-only initially
                          inventory, retention    
                          and consent             

  Provider Researcher     Publicly verifiable     Research only; no
                          Sargodha provider       outreach
                          information             

  UI/UX and Accessibility Mobile usability,       Implements approved
  Engineer                accessibility and       fixes
                          clinical communication  

  Performance / DevOps    Docker, runtime,        No production
  Engineer                monitoring, load and    deployment
                          deployment              

  E2E Automation Engineer Browser/device/API      Independent of feature
                          regression tests        implementation

  Independent QA /        Reproduce defects and   Read-only for
  Security Reviewer       verify fixes            verification
  -----------------------------------------------------------------------

### Shared-file coordination

-   Assign one implementation owner to each shared file or module.
-   Database migrations must have one coordinating owner.
-   Backend/mobile API contract changes must be agreed and documented
    before parallel implementation.
-   Agents must not overwrite one another's work.
-   The orchestrator must inspect the Git working tree before any edits.
-   Preserve existing user changes. Never reset, clean, or discard
    uncommitted work.

------------------------------------------------------------------------

# 4. Universal execution lifecycle for every sprint

Every sprint follows the same lifecycle.

## Stage A --- Discover and plan

1.  Inspect the repository, branch, working tree, project instructions
    and existing tests.
2.  Start the application using documented local development procedures
    where possible.
3.  Inventory relevant screens, routes, APIs, tables, storage buckets,
    models and configuration.
4.  Read the current bug tracker and previous sprint reports.
5.  Reproduce the issue or verify the feature.
6.  Identify dependencies, risks and files likely to change.
7.  Create a task plan with owners and acceptance criteria.

## Stage B --- Report and approval gate

Produce a short audit report containing: - Confirmed findings. -
Findings not reproduced. - Blocked checks and why. - Root causes. -
Proposed changes. - Files likely to change. - Tests required. - Risks
and rollback plan.

Stop for approval before high-impact changes identified in the sprint
instructions.

## Stage C --- Implement approved work

1.  Make small, scoped changes.
2.  Follow existing project conventions.
3.  Avoid unrelated refactors.
4.  Add or update automated tests.
5.  Record changed files and migration details.
6.  Keep configuration environment-aware.
7.  Preserve rollback capability.

## Stage D --- Verify independently

1.  Run targeted unit and integration tests.
2.  Run API and E2E tests.
3.  Run security tests where relevant.
4.  Run the full regression suite affected by the changes.
5.  Have an independent agent reproduce the original defect and verify
    the fix.
6.  Record exact commands, results, logs and evidence.
7.  Mark unresolved or untestable items as `BLOCKED`, never `PASSED`.

## Stage E --- Close sprint

Create: - `sprint_<N>_audit.md` - `sprint_<N>_implementation.md` -
`sprint_<N>_test_results.md` -
`sprint_<N>_independent_verification.md` - `sprint_<N>_summary.md`

Update the master issue tracker and roadmap. Recommend the next sprint,
but do not silently start a gated sprint.

------------------------------------------------------------------------

# 5. Sprint roadmap

## Sprint 1 --- Security and patient-data integrity

**Status at roadmap creation:** Initial audit reported complete;
remediation still requires execution and independent verification.

### Objective

Protect accounts, patient records, retinal images, screening results and
clinician access.

### Scope

-   Re-verify reported SEC-01 through SEC-08 and related privacy
    findings.
-   Enforce fail-closed authentication.
-   Validate JWTs correctly and consistently.
-   Fix clinician grant authorization and prevent BOLA.
-   Enforce clinician verification and patient authorization.
-   Prevent unauthorized reading or mutation of scans.
-   Move trusted prediction persistence to an appropriately protected
    server-side workflow.
-   Secure file storage and access policies.
-   Add appropriate API rate limits.
-   Generate grant codes with cryptographically secure randomness.
-   Restrict CORS to configured trusted origins.
-   Inspect repository history and current files for exposed secrets.
-   Rotate any real exposed credentials through the authorized owner.
-   Verify that logs and error responses do not expose secrets or
    medical information.

### Acceptance criteria

-   Unauthenticated requests cannot access protected resources.
-   Users cannot access another user's records.
-   Unverified clinicians cannot access protected patient data.
-   Grant codes are validated server-side and cannot be bypassed.
-   Clients cannot forge or arbitrarily modify trusted screening
    records.
-   Storage access is private and authorization-controlled.
-   Regression tests cover authorized and unauthorized cases.
-   Independent security review passes.

### Approval required

Credential rotation, destructive migrations, production database
changes, and changes to live access policies require explicit approval.

------------------------------------------------------------------------

## Sprint 2 --- ML pipeline validation and fixes

### Objective

Ensure the existing model and inference pipeline behave consistently and
produce reproducible technical results.

### Scope

1.  Verify actual model architecture and weights, including DenseNet121
    versus RETFound naming.
2.  Investigate reported training/validation/test leakage.
3.  Inspect original and augmented image relationships and duplicate
    images.
4.  Verify patient-level separation when patient identifiers are
    available.
5.  Ensure data augmentation is applied only to training data.
6.  Verify image decoding, RGB conversion, dimensions, resizing and
    normalization.
7.  Ensure training and inference preprocessing are consistent with the
    checkpoint.
8.  Verify disease-grade mapping and confidence calculations.
9.  Test blank, corrupted, unsupported, low-quality and non-retinal
    images.
10. Verify that inference failures return controlled errors, not
    fabricated predictions.
11. Reproduce model metrics on a valid, untouched test set where
    available.
12. Compare TensorFlow and TFLite only if both artifacts are available
    and relevant.
13. Verify the complete upload → preprocessing → inference → result API
    workflow.

### Acceptance criteria

-   Actual model identity is documented accurately.
-   Dataset leakage has been investigated and limitations documented.
-   Dataset split methodology is reproducible.
-   Preprocessing is consistent with the trained model.
-   Metrics are reproducible and include per-class results.
-   Invalid inputs are safely rejected or flagged by a validated method.
-   Prediction and class mapping are consistent across backend and app.
-   Independent ML QA approves the evidence.

### Approval required

Do not retrain, replace, convert, or deploy a model without explicit
approval. Preserve original datasets, checkpoints and results. Do not
claim clinical validity from internal test metrics alone.

------------------------------------------------------------------------

## Sprint 3 --- Patient and clinician workflows

### Objective

Make existing patient and clinician features work end to end.

### Patient workflow

-   Registration and login.
-   Profile management.
-   Dashboard and navigation.
-   Retinal image upload and preview.
-   Screening submission and progress state.
-   Screening result presentation.
-   History and record retrieval.
-   PDF report generation and download.
-   Consultation or clinician-review request where supported.

### Clinician workflow

-   Doctor registration and login.
-   Profile management and verification status.
-   Patient access requests.
-   Secure grant-code validation.
-   Authorized patient record access.
-   Retinal image viewing and inspection.
-   Screening result review.
-   Clinical notes and second opinions where implemented.
-   Access revocation.

### Integration and UX

-   Verify mobile-to-backend API contracts.
-   Verify database ownership and record relationships.
-   Fix broken actions and incomplete workflows.
-   Handle loading, empty, error, offline and expired-session states.
-   Ensure screening results are understandable and do not overclaim
    diagnosis.
-   Verify that PDF contents match actual saved records.

### Acceptance criteria

-   Patient and clinician journeys pass E2E tests.
-   Authorization is enforced throughout the workflow.
-   Retinal images and reports are displayed only to authorized users.
-   History and PDF reports are accurate.
-   Independent QA approves the workflows.

### Approval required

Do not use real patient records in testing. Any real clinical use
requires appropriate consent and authorization.

------------------------------------------------------------------------

## Sprint 4 --- Real hospitals, clinics and doctors in Sargodha

### Objective

Build a trustworthy provider directory and prepare a real
healthcare-provider onboarding pathway for Sargodha, Punjab, Pakistan.

### Provider research

-   Identify actual hospitals and eye clinics in Sargodha.
-   Identify ophthalmologists and retina specialists.
-   Verify names, qualifications and PMDC registration where possible.
-   Verify clinic/hospital affiliation, address, phone and official
    website.
-   Record source URLs and verification dates.
-   Prefer official sources and direct confirmation.
-   Mark information that cannot be confirmed as unverified.

### Provider directory

Create database-backed records for: - Hospitals. - Clinics. - Doctors. -
Specialties. - Qualifications. - Addresses and contact information. -
Verified operating hours. - Appointment information only where
confirmed. - Map/location data where reliable.

Support search and filters by location, facility and specialty.

### Provider onboarding

Use explicit statuses: - Publicly listed. - Contact pending. -
Identity/credentials under verification. - Verified. - Participation
accepted / onboarded. - Active. - Suspended.

Do not create accounts for doctors merely because their information is
public. Only authorized administrators can approve provider accounts.

### Patient-to-provider workflow

-   Browse local providers.
-   View provider profiles.
-   Contact the clinic or use a verified booking route.
-   Request clinician review where supported.
-   Share screening records only with explicit patient authorization.
-   Allow authorized clinicians to review shared images and reports.
-   Support access revocation and access history.

### Acceptance criteria

-   Provider records have traceable sources and verification dates.
-   Unverified records are clearly labeled.
-   Provider accounts require real identity verification and explicit
    participation.
-   Patient medical information is not shared automatically.
-   At least one provider is formally participating before claiming a
    partnership or pilot.

### Approval required

The swarm may research public information and prepare draft outreach
materials. It must not contact doctors, send invitations, make
appointments, claim partnerships, or disclose patient information
without human approval. Do not scrape or republish information in
violation of source terms or applicable law.

------------------------------------------------------------------------

## Sprint 5 --- UI/UX and accessibility

### Objective

Make the application consistent, understandable, responsive and
accessible.

### Scope

-   Patient dashboard.
-   Clinician dashboard.
-   Provider directory.
-   Screening and upload interface.
-   Prediction results.
-   Retinal image viewer.
-   History and reports.
-   Profile and settings.
-   Navigation and visual consistency.
-   Typography, spacing and color tokens.
-   Loading, empty and error states.
-   Mobile and tablet layouts.
-   Keyboard and screen-reader support.
-   Color contrast and touch targets.
-   WCAG 2.2 AA assessment where applicable.

### Acceptance criteria

-   Critical user journeys are clear and usable.
-   Supported device sizes are tested.
-   Accessibility defects are documented and prioritized.
-   Clinical language is understandable and appropriately cautious.
-   Independent UI/UX and accessibility review passes.

### Approval required

Do not perform a wholesale redesign or remove existing features without
approval. Preserve the established visual identity unless a change is
justified.

------------------------------------------------------------------------

## Sprint 6 --- Privacy and healthcare data protection

### Objective

Protect sensitive health information throughout collection, processing,
storage, sharing, retention and deletion.

### Scope

-   Inventory personal and medical data.
-   Map data flows between app, backend, database, storage and third
    parties.
-   Review patient consent and purpose limitation.
-   Review image and report access.
-   Review encryption in transit and at rest.
-   Review local device caches and downloads.
-   Review application logs and analytics.
-   Review third-party AI image processing and contractual terms.
-   Define retention and deletion behavior.
-   Verify account deletion and associated data handling.
-   Add access/audit history where appropriate.
-   Prepare incident and breach-response procedures.
-   Review applicable Pakistani legal and regulatory requirements with
    qualified counsel.

### Acceptance criteria

-   Data inventory and data-flow map exist.
-   Sensitive data is not exposed through logs or public storage.
-   Access and sharing require appropriate authorization.
-   Retention and deletion behavior is documented and tested.
-   Third-party processing has been reviewed.
-   Compliance claims are not made without evidence and qualified
    review.

### Approval required

No real patient data may be sent to a third-party service or used in a
pilot without appropriate legal, contractual, institutional and patient
approvals.

------------------------------------------------------------------------

## Sprint 7 --- Backend architecture and performance

### Objective

Make the application stable and responsive under its expected workload.

### Scope

-   Flask API performance.
-   Database query performance.
-   Gunicorn worker/thread configuration.
-   TensorFlow resource use.
-   TFLite deployment only if equivalence is established.
-   Image upload and transfer efficiency.
-   Memory and CPU management.
-   Inference concurrency.
-   Queue-based processing if justified.
-   Caching only where safe and useful.
-   Error handling and timeouts.
-   Load and stress testing.
-   Resource and latency benchmarks.

### Acceptance criteria

-   Performance is measured under documented conditions.
-   No unbounded resource growth in tested workloads.
-   Inference concurrency meets agreed targets.
-   No patient-data leakage through caches.
-   Optimizations preserve prediction correctness.
-   Independent performance verification passes.

### Approval required

Do not change production capacity, incur cloud costs, or replace the
inference runtime without approval.

------------------------------------------------------------------------

## Sprint 8 --- Production infrastructure and deployment

### Objective

Prepare repeatable, secure staging and production deployment.

### Scope

-   Docker build and startup.
-   Docker Compose configuration.
-   Environment variable validation.
-   Secret management.
-   Database migrations.
-   HTTPS and trusted origins.
-   CI/CD pipeline.
-   Health checks and readiness checks.
-   Logging and error monitoring.
-   Backup and restore procedures.
-   Rollback procedure.
-   Staging/production separation.
-   Dependency and container scanning.
-   Operational documentation.

### Acceptance criteria

-   Clean environment can build and start the application.
-   Required configuration is validated at startup.
-   No secrets are committed.
-   Migrations are repeatable and recoverable.
-   Health checks and monitoring work.
-   Backup restoration is tested.
-   Staging deployment is verified.

### Approval required

Production deployment, DNS changes, paid infrastructure, production
migrations and public release require explicit human approval.

------------------------------------------------------------------------

## Sprint 9 --- Supervised real-world provider pilot

### Objective

Evaluate the application in a controlled workflow with participating
Sargodha healthcare providers.

### Scope

-   Confirm participating facility and clinician.
-   Obtain institutional permission and required ethics approvals.
-   Confirm patient consent and information-sharing procedures.
-   Define the pilot protocol and clinical oversight.
-   Configure provider accounts and access.
-   Train participating staff.
-   Test patient onboarding.
-   Test image upload and clinician review.
-   Collect usability and workflow feedback.
-   Track incidents, errors and downtime.
-   Review performance and operational burden.
-   Document pilot outcomes and limitations.

### Acceptance criteria

-   A real provider has explicitly agreed to participate.
-   Required permissions and approvals are documented.
-   Patient consent and privacy controls are operational.
-   Clinical oversight and escalation procedures are defined.
-   Pilot findings are documented without overstating clinical
    effectiveness.

### Approval required

No autonomous recruitment, patient contact, clinical decision-making, or
real-patient data processing. The pilot must be supervised by
appropriately qualified healthcare professionals and authorized
institutions.

------------------------------------------------------------------------

## Sprint 10 --- Final production certification and launch

### Objective

Determine whether the application is ready for its intended release.

### Scope

-   Full regression suite.
-   Complete patient and clinician E2E tests.
-   Independent security retesting.
-   Privacy and data-deletion verification.
-   ML validation and limitations review.
-   Performance benchmarks.
-   Accessibility review.
-   Provider directory accuracy.
-   Backup restoration test.
-   Monitoring and incident response test.
-   Staging deployment verification.
-   Operational documentation.
-   Final risk register.
-   Launch approval.

### Acceptance criteria

-   No unresolved critical security or data-integrity defects.
-   No unresolved critical workflow failures.
-   ML evaluation and limitations are documented.
-   Privacy controls are verified.
-   Performance meets agreed targets.
-   Backup and rollback are tested.
-   Monitoring is operational.
-   Required clinical, institutional and regulatory approvals are
    obtained for the intended use.
-   An authorized human approves release.

**Passing software tests does not by itself establish clinical safety,
regulatory compliance, or fitness for diagnosis.**

------------------------------------------------------------------------

# 6. Cross-sprint issue tracking

Maintain one master tracker at `audit/master_bug_tracker.md`.

Each issue must contain:

  -----------------------------------------------------------------------
  Field                               Required content
  ----------------------------------- -----------------------------------
  ID                                  Stable unique identifier

  Sprint                              Sprint number

  Module                              Affected application area

  Severity                            Critical / High / Medium / Low /
                                      Informational

  Status                              Open / Reproduced / Approved / In
                                      Progress / Fixed / Regression
                                      Passed / Independently Verified /
                                      Blocked

  Evidence                            Logs, test output, screenshots or
                                      source reference

  Root cause                          Confirmed technical cause

  Owner                               One implementation owner

  Reviewer                            Independent reviewer

  Files changed                       Exact changed paths

  Tests                               Exact tests and results

  Risk                                Remaining risk

  Rollback                            Recovery method
  -----------------------------------------------------------------------

Never mark a defect `Independently Verified` based only on the
implementation agent's report.

------------------------------------------------------------------------

# 7. Autonomous execution policy

The orchestrator should continue automatically through tasks that are
safe, reversible and within the approved sprint scope.

## Allowed without additional approval

-   Repository inspection and documentation.
-   Read-only research using permitted public sources.
-   Test planning and test execution in isolated environments.
-   Synthetic test-data generation.
-   Reproducing defects locally.
-   Creating reports and issue trackers.
-   Implementing low-risk changes after the sprint's implementation
    stage has been approved.
-   Running regression tests.
-   Updating documentation.
-   Preparing draft provider profiles with source and verification
    labels.
-   Preparing draft outreach documents without sending them.

## Must stop and request human approval

-   Retraining, replacing or deploying ML models.
-   Destructive or irreversible database migrations.
-   Production database access or modification.
-   Credential rotation that requires account-owner action.
-   External emails, phone calls, messages or appointment bookings.
-   Creating or activating real doctor accounts.
-   Claiming a hospital or doctor partnership.
-   Collecting, uploading, sharing or processing real patient data.
-   Sending medical images to third-party AI services.
-   Clinical recommendations or patient triage decisions.
-   Paid services, cloud upgrades or purchases.
-   Production deployment, DNS changes or public launch.
-   Any action outside the approved sprint scope.

If approval is unavailable, continue other independent safe tasks and
mark the gated task `BLOCKED — HUMAN APPROVAL REQUIRED`.

------------------------------------------------------------------------

# 8. Fully automated orchestration instructions

When started with Antigravity `/teamwork`:

1.  Read this entire roadmap and the repository's existing agent
    instructions.
2.  Inspect the current Git branch and working tree.
3.  Identify which sprints are complete, in progress, blocked or not
    started using actual evidence.
4.  Read all existing audit and sprint reports.
5.  Do not repeat completed work unless independent verification is
    missing or the code has changed.
6.  Build a dependency graph for all remaining work.
7.  Create a task board with owners, dependencies, acceptance criteria
    and approval gates.
8.  Assign independent agents to research, implementation and
    verification.
9.  Run safe independent tasks in parallel.
10. Serialize work on shared files and shared database migrations.
11. Keep a durable execution log and update the master tracker.
12. After each sprint, generate the required reports and summarize
    changes.
13. Automatically proceed to the next sprint only when its dependencies
    are satisfied and the required approval gate has been granted.
14. Never interpret silence as approval.
15. If an agent fails, retry safely where appropriate, then report the
    failure. Do not invent successful results.
16. If the environment lacks a required tool, device, test account,
    dataset or service, record the limitation and continue other
    independent work.
17. At the end of each work session, leave a clear checkpoint: completed
    tasks, pending tasks, blockers, files changed, tests run and exact
    next action.

## Dependency guidance

The default order is:

-   Sprint 1 security is a prerequisite for workflows that depend on
    protected patient data.
-   Sprint 2 ML validation is a prerequisite for accepting
    prediction-related workflows.
-   Sprint 3 patient/clinician workflows depend on secure authorization
    and a verified inference contract.
-   Sprint 4 provider research can run in parallel with appropriate
    technical work; real provider onboarding depends on a safe provider
    workflow and explicit participation.
-   Sprint 5 UI/UX can overlap with workflow implementation, but final
    verification must use stable workflows.
-   Sprint 6 privacy review begins early and must be completed before
    real patient data is used.
-   Sprint 7 performance work follows stable, measurable inference
    behavior.
-   Sprint 8 staging deployment follows stable application and
    infrastructure changes.
-   Sprint 9 requires provider participation, required approvals,
    privacy safeguards and a stable staging system.
-   Sprint 10 follows successful completion of all mandatory
    workstreams.

The orchestrator may adjust parallelism where dependencies allow, but
must not bypass safety gates.

------------------------------------------------------------------------

# 9. Final project scorecard

At the end, report evidence-based status for:

1.  Functional completeness.
2.  E2E reliability.
3.  Authentication and authorization security.
4.  Patient-data privacy.
5.  ML pipeline reliability.
6.  Prediction evaluation quality.
7.  Patient experience.
8.  Clinician experience.
9.  Provider directory verification.
10. Accessibility.
11. Performance.
12. Production infrastructure.
13. Operational readiness.
14. Pilot readiness.

Use `NOT VERIFIED` when evidence is unavailable. Do not invent numerical
scores or treat untested areas as passing.

The final verdict must be one of:

-   `NOT READY`
-   `READY FOR INTERNAL TESTING`
-   `READY FOR SUPERVISED PILOT REVIEW`
-   `READY FOR APPROVED PRODUCTION RELEASE`

Only use the final verdict when its corresponding acceptance criteria
have been independently verified.

------------------------------------------------------------------------

# 10. First action for the swarm

Do not immediately launch all ten sprints as simultaneous code-editing
tasks.

Start by:

1.  Inspecting the current repository and Git state.
2.  Reading the Phase 1 audit and existing remediation reports.
3.  Checking whether Sprint 1 has actually been remediated.
4.  Checking whether Sprint 2 or Sprint 3 work has already started.
5.  Creating a verified project status and dependency plan.
6.  Presenting the first execution plan, owners, approval gates and safe
    parallel tasks.

Then begin the earliest eligible approved workstream.

**Final mission:** Automate the engineering and verification work as far
as possible while keeping human control over patient data, clinical
activity, external commitments, irreversible changes and production
release. Build a reliable diabetic retinopathy screening application
that can be responsibly evaluated with real healthcare providers in
Sargodha.
