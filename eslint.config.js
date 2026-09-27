import pluginVue from "eslint-plugin-vue";
import { defineConfigWithVueTs, vueTsConfigs } from "@vue/eslint-config-typescript";

export default defineConfigWithVueTs(
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/coverage/**",
      "packages/api-client/**",
      "playwright-out/**",
      "test-results/**",
      "apps/client/**",
      ".venv/**",
      // Local agent scratch dir — never app source; prevents the project
      // service from choking on transient scripts written there.
      ".tmp/**",
      "**/*.d.ts",
      // Tauri build outputs: cargo fingerprints/gen are machine-written JS, not
      "apps/client-h5/src-tauri/**",
      // Android acceptance tooling (CDP driver) — machine-run automation, not
      // app source; belongs to no app tsconfig and predates the project-service
      // allowlist (baseline lint already refused it).
      "scripts/android_acceptance/cdp_journey.cjs",
    ],
  },
  pluginVue.configs["flat/essential"],
  vueTsConfigs.recommended,
  {
    languageOptions: {
      parserOptions: {
        projectService: {
          allowDefaultProject: [
            "vite.config.*",
            "apps/admin/vite.config.ts",
            "apps/client-h5/vite.config.ts",
            "playwright.config.*",
            "playwright.visual.config.ts",
            "playwright.ui-audit.config.ts",
            // These root-level tooling files belong to no app tsconfig, so the
            // typed rules can only reach them through the default project. That
            // project has a hard cap of 8 files before typescript-eslint starts
            // refusing outright — 10 files here is not a performance problem,
            // and pretending otherwise by dropping one from linting is worse.
            "tests/e2e/*.ts",
            "tests/visual/*.ts",
            "tests/ui-audit/*.ts",
            "scripts/*.mjs",
            "eslint.config.js",
          ],
          maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 30,
        },
      },
    },
  },
  {
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
  {
    files: ["tests/e2e/**/*.ts"],
    rules: {
      "@typescript-eslint/no-unsafe-assignment": "off",
    },
  },
);
