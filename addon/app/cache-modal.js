const CacheModal = {
  emits: ["close"],
  setup(props, { emit }) {
    const content = ref("");
    const loading = ref(true);
    const error = ref("");
    const onKeydown = (e) => {
      if (e.key === "Escape") emit("close");
    };
    const loadData = async () => {
      loading.value = true;
      error.value = "";
      try {
        const data = await window.api.get("/api/cache");
        content.value = JSON.stringify(data, null, 2);
      } catch (err) {
        error.value = err.message;
      } finally {
        loading.value = false;
      }
    };
    onMounted(() => {
      window.addEventListener("keydown", onKeydown);
      loadData();
    });
    onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
    return { content, loading, error };
  },
  template: `
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click="$emit('close')">
      <div class="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-lg bg-white shadow-xl" @click.stop>
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <h2 class="text-lg font-semibold">data.json</h2>
          <button class="text-xl leading-none text-gray-400 hover:text-gray-600" @click="$emit('close')" aria-label="Close">&times;</button>
        </div>
        <div v-if="error" class="px-5 py-3 text-sm text-red-600">{{ error }}</div>
        <pre v-else class="min-h-0 flex-1 overflow-auto bg-gray-900 px-5 py-4 text-xs leading-relaxed text-gray-100">{{ loading ? "Loading…" : content }}</pre>
      </div>
    </div>
  `,
};
