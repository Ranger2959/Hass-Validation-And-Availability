const DevicesTab = {
  components: { DeviceModal },
  setup() {
    const devices = ref([]);
    const areas = ref([]);
    const showIgnored = ref(false);
    const search = ref("");
    const loading = ref(true);
    const error = ref("");
    const selected = ref(null);

    const visibleDevices = computed(() => {
      const q = search.value.trim().toLowerCase();
      const list = showIgnored.value
        ? [...devices.value]
        : devices.value.filter((d) => !d.is_ignored);
      if (!q) {
        return list;
      }
      return list.filter((d) =>
        [d.name, d.integration_name, d.floor_name, d.area_name].some(
          (f) => f && f.toLowerCase().includes(q)
        )
      );
    });

    const rowClass = (d) =>
      d.is_area_mismatched
        ? "bg-red-100 hover:bg-red-200"
        : d.is_ignored
          ? "bg-gray-100 hover:bg-gray-200"
          : d.is_area_validated && d.monitored_entity
            ? "bg-green-100 hover:bg-green-200"
            : "bg-yellow-100 hover:bg-yellow-200";

    const totalDevices = computed(() => devices.value.length);
    const ignoredCount = computed(() =>
      devices.value.filter((d) => d.is_ignored).length
    );
    const validatedCount = computed(() =>
      devices.value.filter((d) => d.is_area_validated).length
    );
    const areaMismatchCount = computed(() =>
      devices.value.filter((d) => d.is_area_mismatched).length
    );

    const refreshDevices = async () => {
      try {
        devices.value = await window.api.get("/api/devices");
      } catch (err) {
        error.value = err.message || "Failed to load devices";
      }
    };

    onMounted(async () => {
      try {
        const [devicesList, areasList] = await Promise.all([
          window.api.get("/api/devices"),
          window.api.get("/api/areas").catch(() => null),
        ]);
        devices.value = devicesList;
        if (areasList) {
          areas.value = areasList;
        }
      } catch (err) {
        error.value = err.message || "Failed to load devices";
      } finally {
        loading.value = false;
      }
    });

    return {
      devices,
      areas,
      showIgnored,
      search,
      loading,
      error,
      selected,
      totalDevices,
      ignoredCount,
      validatedCount,
      areaMismatchCount,
      visibleDevices,
      refreshDevices,
      rowClass,
    };
  },
  template: `
    <div class="mb-3 text-sm text-gray-600">
      <div>Total Devices: {{ totalDevices }}</div>
      <div>Ignored Devices: {{ ignoredCount }}</div>
      <div>Area Validated Devices: {{ validatedCount }}</div>
      <div :class="{ 'text-red-600': areaMismatchCount }">
        Area Mismatch: {{ areaMismatchCount }}
      </div>
    </div>
    <div class="mb-2 flex items-center gap-3">
      <input v-model="search" type="search" placeholder="Search by name, integration, or floor/area…" class="min-w-0 max-w-[40vw] flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm" />
      <label class="flex shrink-0 cursor-pointer items-center gap-2 text-sm text-gray-700">
        <span>Show Ignored</span>
        <input type="checkbox" v-model="showIgnored" class="h-4 w-4 accent-gray-900" />
      </label>
    </div>
    <div class="overflow-x-auto rounded-lg border border-gray-300 bg-white">
      <table class="w-full border-collapse">
        <thead>
          <tr>
            <th class="bg-gray-900 px-4 py-3 text-left text-white">Device Name</th>
            <th class="bg-gray-900 px-4 py-3 text-left text-white">Integration</th>
            <th class="bg-gray-900 px-4 py-3 text-left text-white">Floor/Area</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading" class="odd:bg-white even:bg-gray-100">
            <td colspan="3" class="border-b border-gray-300 px-4 py-3">Loading devices…</td>
          </tr>
          <tr v-else-if="error" class="odd:bg-white even:bg-gray-100 text-red-600">
            <td colspan="3" class="border-b border-gray-300 px-4 py-3">{{ error }}</td>
          </tr>
          <tr v-else-if="!visibleDevices.length" class="odd:bg-white even:bg-gray-100">
            <td colspan="3" class="border-b border-gray-300 px-4 py-3">No devices found</td>
          </tr>
          <tr v-for="device in visibleDevices" v-else :key="device.id"
              class="cursor-pointer"
              :class="[rowClass(device), { 'text-gray-400 italic': device.is_ignored }]"
              @click="selected = device">
            <td class="border-b border-gray-300 px-4 py-3">{{ device.name }}</td>
            <td class="border-b border-gray-300 px-4 py-3">{{ device.integration_name }}</td>
            <td class="border-b border-gray-300 px-4 py-3">{{ device.floor_name }} / {{ device.area_name }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <device-modal v-if="selected" :device="selected" :areas="areas" @close="selected = null" @refresh="refreshDevices" />
  `,
};
