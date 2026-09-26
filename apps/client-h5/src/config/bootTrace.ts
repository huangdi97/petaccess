/**
 * Debug-only boot-stage trace (forensic deliverable F06).
 *
 * Emits "PETACCESS_BOOT=<stage>" console lines so the startup chain
 * (INDEX_LOADED -> VUE_CREATED -> ROUTER_READY -> APP_SHELL_MOUNTED ->
 * HOME_READY) is observable in logcat / devtools.
 *
 * SECURITY: gated at build time by VITE_BOOT_TRACE=1. Production builds
 * without that flag constant-fold `enabled` to false and add no console
 * output, so no stage or content leaks in production bundles.
 */
const enabled = import.meta.env.VITE_BOOT_TRACE === "1";

export function bootStage(stage: string): void {
  if (enabled) {
    console.info(`PETACCESS_BOOT=${stage}`);
  }
}