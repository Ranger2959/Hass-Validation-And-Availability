const tabComponents = {
  Devices: DevicesTab,
  Settings: SettingsTab,
};

createApp({
  setup() {
    const tabs = computed(() => Object.keys(tabComponents));
    const activeTab = ref("Devices");
    return { tabs, activeTab, tabComponents };
  },
}).mount("#app");
