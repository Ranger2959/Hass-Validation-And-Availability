const SettingsTab = {
  components: { CacheModal },
  setup() {
    const showCache = ref(false);
    return { showCache };
  },
  template: `
    <div class="overflow-x-auto rounded-lg border border-gray-300 bg-white">
      <div class="divide-y divide-gray-200">
        <div class="flex items-center justify-between gap-4 px-5 py-4">
          <div>
            <div class="text-sm font-medium">Cache</div>
            <div class="text-xs text-gray-500">Persistent device state (data.json)</div>
          </div>
          <button class="shrink-0 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50" @click="showCache = true">View</button>
        </div>
      </div>
    </div>
    <cache-modal v-if="showCache" @close="showCache = false" />
  `,
};
