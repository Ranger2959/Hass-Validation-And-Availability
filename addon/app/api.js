// Loaded before all other local scripts: top-level `const` declarations
// cannot be repeated across classic <script> tags, so this file owns the
// shared Vue composition-API bindings for every later file.
const { createApp, ref, computed, onMounted, onBeforeUnmount } = Vue;

window.api = {
  async get(path) {
    const res = await fetch(`${window.APP_BASE}${path}`);
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      throw new Error(data?.detail || `Request failed (${res.status})`);
    }
    return res.json();
  },
  async post(path, body) {
    const res = await fetch(`${window.APP_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      throw new Error(data?.detail || `Request failed (${res.status})`);
    }
    return res.json();
  },
};
