/** Real privacy-rights transactions; no local fake success. */
import { computed, onMounted, ref } from "vue";
import { client, platformStorage, session } from "@petaccess/client-core";
import { presentDescription } from "../errors";

export function usePrivacyRights() {
  const cleared = ref(false);
  const loading = ref(true);
  const exportBusy = ref(false);
  const deletionBusy = ref(false);
  const rightsError = ref("");
  const deletionStatus = ref<"none" | "submitted" | string>("none");
  const deletionRequestedAt = ref<string | null>(null);
  const confirmDeletion = ref(false);
  const signedIn = computed(() => session.signedIn);

  function clearLocalData() {
    platformStorage.remove("pa_token");
    session.logout();
    cleared.value = true;
  }

  async function loadRightsStatus() {
    loading.value = true;
    rightsError.value = "";
    try {
      await session.restore();
      if (!session.signedIn) return;
      const row = await client.accountDeletionRequest();
      deletionStatus.value = row.status;
      deletionRequestedAt.value = row.requested_at;
    } catch (error) {
      rightsError.value = presentDescription(error);
    } finally {
      loading.value = false;
    }
  }

  async function exportData() {
    if (!session.signedIn || exportBusy.value) return;
    exportBusy.value = true;
    rightsError.value = "";
    try {
      const payload = await client.exportMyData();
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: "application/json;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `petaccess-data-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      rightsError.value = presentDescription(error);
    } finally {
      exportBusy.value = false;
    }
  }

  async function submitDeletionRequest() {
    if (!session.signedIn || deletionBusy.value) return;
    deletionBusy.value = true;
    rightsError.value = "";
    try {
      const row = await client.requestAccountDeletion();
      deletionStatus.value = row.status;
      deletionRequestedAt.value = row.requested_at;
      confirmDeletion.value = false;
    } catch (error) {
      rightsError.value = presentDescription(error);
    } finally {
      deletionBusy.value = false;
    }
  }

  onMounted(loadRightsStatus);

  return {
    cleared,
    loading,
    exportBusy,
    deletionBusy,
    rightsError,
    deletionStatus,
    deletionRequestedAt,
    confirmDeletion,
    signedIn,
    clearLocalData,
    loadRightsStatus,
    exportData,
    submitDeletionRequest,
  };
}
