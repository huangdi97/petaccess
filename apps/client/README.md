# PetAccess legacy uni-app x client — DO NOT BUILD / DO NOT RELEASE

**Status: `LEGACY_REFERENCE_ONLY`.**

This directory is retained only as historical source material from the pre-v0.10 multi-client phase. It is **not** the canonical Consumer implementation and **must not** be used for Android screenshots, Human Visual Acceptance, release artifacts, product demos, or new feature work.

## Canonical runtime

- Consumer UI / business presentation: `apps/client-h5`
- Windows shell: `apps/client-h5/src-tauri`
- Android shell: `apps/client-h5/src-tauri`
- Android release workflow: `.github/workflows/release-ci.yml`

The v0.10-R1 architecture explicitly converged on **Vue Consumer + Tauri 2 for Windows/Android**, so that Rule / Reality / Evidence / Contribution semantics and UI are not reimplemented independently on each platform.

## Why this directory is frozen

The code here predates the current Consumer Discovery UI and the v0.10 RealityReport contribution model. It contains historical shortcuts that are unacceptable as current product truth, including:

- map markers derived from synthetic coordinate offsets rather than canonical place coordinates;
- legacy Observation / quick-verification contribution flows;
- historical fixed proximity buckets;
- a separate, simplified UI that no longer matches the canonical Consumer information architecture.

Those behaviors are useful forensic evidence of the old architecture, but they must not re-enter the production path.

## Allowed use

- historical comparison;
- migration archaeology;
- reading old platform-adapter ideas when designing a future non-Tauri client.

## Forbidden use

- HBuilderX Android build for current PetAccess;
- shipping an APK from this directory;
- using these pages as UI references;
- adding new product features here;
- copying legacy Observation behavior back into the canonical Consumer.

For Android development, build/run **`apps/client-h5/src-tauri`** instead.
