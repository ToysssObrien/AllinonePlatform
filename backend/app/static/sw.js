self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  event.waitUntil((async () => {
    const allClients = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const client of allClients) {
      if ("focus" in client) {
        await client.focus();
      }
      client.postMessage({
        type: "notification:open-chat",
        chatId: data.chatId || null,
        accountId: data.accountId || null
      });
      return;
    }
    if (self.clients.openWindow) {
      await self.clients.openWindow("/#/conversations");
    }
  })());
});
