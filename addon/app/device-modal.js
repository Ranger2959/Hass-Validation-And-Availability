const DeviceModal = {
  props: {
    device: { type: Object, required: true },
    areas: { type: Array, required: true },
  },
  emits: ["close", "refresh"],
  setup(props, { emit }) {
    const included = ref(!props.device.is_ignored);
    const originalIncluded = ref(!props.device.is_ignored);
    const areaSelect = ref(props.device.area_id || null);
    const originalArea = ref(props.device.area_id || null);
    const entitySelect = ref(props.device.monitored_entity || null);
    const saving = ref(false);
    const saveError = ref("");
    const canSave = computed(
      () =>
        (originalIncluded.value === false && included.value === true) ||
        (areaSelect.value !== null && entitySelect.value !== null)
    );

    const onKeydown = (e) => {
      if (e.key === "Escape") emit("close");
    };
    const openDevicePage = () => {
      window.location.href = `/config/devices/device/${props.device.id}`;
    };
    const onSave = async () => {
      saveError.value = "";
      saving.value = true;
      try {
        await window.api.post(`/api/devices/${props.device.id}/save`, {
          is_included: included.value,
          is_area_validated:
            areaSelect.value !== null && entitySelect.value !== null,
          area_id: areaSelect.value,
          update_area: areaSelect.value !== originalArea.value,
          monitored_entity_id: entitySelect.value,
        });
        props.device.is_ignored = !included.value;
        props.device.is_area_validated =
          areaSelect.value !== null && entitySelect.value !== null;
        if (areaSelect.value !== originalArea.value) {
          props.device.area_id = areaSelect.value;
          const area = props.areas.find(
            (a) => a.area_id === areaSelect.value
          );
          props.device.area_name = area ? area.name : "Unassigned";
        }
        originalIncluded.value = included.value;
        originalArea.value = areaSelect.value;
        emit("refresh");
        emit("close");
      } catch (err) {
        saveError.value = err.message;
      } finally {
        saving.value = false;
      }
    };
    onMounted(() => window.addEventListener("keydown", onKeydown));
    onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
    return {
      included,
      areaSelect,
      entitySelect,
      saving,
      saveError,
      canSave,
      openDevicePage,
      onSave,
    };
  },
  template: `
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click="$emit('close')">
          <div class="w-full max-w-md rounded-lg bg-white shadow-xl" @click.stop>
            <div class="flex items-center justify-between border-b border-gray-200 px-5 py-4">
              <h2 class="text-lg font-semibold">{{ device.name }}</h2>
              <button class="text-xl leading-none text-gray-400 hover:text-gray-600" @click="$emit('close')" aria-label="Close">&times;</button>
            </div>
            <dl class="px-5 py-4">
              <div class="flex justify-between gap-4 border-b border-gray-100 py-2 last:border-0">
                <dt class="shrink-0 text-gray-500">Device ID</dt>
                <dd class="break-all text-right font-medium">{{ device.id }}</dd>
              </div>
              <div class="flex justify-between gap-4 border-b border-gray-100 py-2 last:border-0">
                <dt class="shrink-0 text-gray-500">Integration</dt>
                <dd class="break-all text-right font-medium">{{ device.integration_name }}</dd>
              </div>
              <div class="flex justify-between gap-4 border-b border-gray-100 py-2 last:border-0">
                <dt class="shrink-0 text-gray-500">Floor</dt>
                <dd class="break-all text-right font-medium">{{ device.floor_name }}</dd>
              </div>
              <div class="flex items-center justify-between gap-4 border-b border-gray-100 py-2 last:border-0">
                <dt class="shrink-0 text-gray-500">Area</dt>
                <dd class="flex items-center gap-2">
                  <select v-model="areaSelect" class="max-w-[11rem] rounded-md border border-gray-300 bg-white px-2 py-1 text-sm">
                    <option :value="null">Unassigned</option>
                    <option v-for="a in areas" :key="a.area_id" :value="a.area_id">{{ a.name }}</option>
                  </select>
                </dd>
              </div>
              <div class="flex items-center justify-between gap-4 border-b border-gray-100 py-2 last:border-0">
                <dt class="shrink-0 text-gray-500">Entity Monitored</dt>
                <dd>
                  <select v-if="device.entities.length" v-model="entitySelect" class="max-w-[13rem] rounded-md border border-gray-300 bg-white px-2 py-1 text-sm">
                    <option :value="null"></option>
                    <option v-for="e in device.entities" :key="e.entity_id" :value="e.entity_id">{{ e.name }} [{{ e.entity_id }}]</option>
                  </select>
                  <span v-else class="text-sm text-red-600">No entities</span>
                </dd>
              </div>
              <div class="flex items-center justify-between gap-4 border-b border-gray-100 py-2 last:border-0">
                <dt class="shrink-0 text-gray-500">Included</dt>
                <dd class="text-right">
                  <input type="checkbox" v-model="included" class="h-4 w-4 accent-gray-900" />
                </dd>
              </div>
            </dl>
            <div v-if="saveError" class="px-5 py-2 text-sm text-red-600">{{ saveError }}</div>
            <div class="flex justify-between border-t border-gray-200 px-5 py-4">
              <button class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-500" @click="openDevicePage">Open Device Page</button>
              <button class="rounded-md bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-500 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500" :disabled="!canSave || saving" @click="onSave">{{ saving ? "Saving…" : "Save" }}</button>
            </div>
          </div>
        </div>
      `,
};
