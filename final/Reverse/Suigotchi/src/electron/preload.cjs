const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('suigotchi', Object.freeze({
  snapshot: () => ipcRenderer.invoke('pet:snapshot'),
  care: (action) => ipcRenderer.invoke('pet:care', action),
  check: () => ipcRenderer.invoke('pet:check'),
  reset: () => ipcRenderer.invoke('pet:reset'),
}));
