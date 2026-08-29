const tabComponents = {
  Devices: DevicesTab,
};

createApp({
  setup() {
    const tabs = ref(["Devices"]);
    const activeTab = ref("Devices");
    return { tabs, activeTab, tabComponents };
  },
}).mount("#app");
