const fs = require("node:fs");
const path = require("node:path");

const DEBUG_URL = "http://127.0.0.1:9222";
const APP_URL = "http://127.0.0.1:8501";
const OUTPUT_DIR = path.resolve(__dirname, "..", "screenshots");

function connect(webSocketDebuggerUrl) {
  const socket = new WebSocket(webSocketDebuggerUrl);
  let nextId = 1;
  const pending = new Map();

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (!message.id || !pending.has(message.id)) return;
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) reject(new Error(message.error.message));
    else resolve(message.result);
  });

  return new Promise((resolve, reject) => {
    socket.addEventListener("error", reject, { once: true });
    socket.addEventListener("open", () => {
      resolve({
        close: () => socket.close(),
        send(method, params = {}) {
          const id = nextId++;
          socket.send(JSON.stringify({ id, method, params }));
          return new Promise((commandResolve, commandReject) => {
            pending.set(id, { resolve: commandResolve, reject: commandReject });
          });
        },
      });
    }, { once: true });
  });
}

async function capture(name, width, height, deviceScaleFactor = 1) {
  const response = await fetch(`${DEBUG_URL}/json/new?${encodeURIComponent(APP_URL)}`, { method: "PUT" });
  if (!response.ok) throw new Error(`Chrome target creation failed: ${response.status}`);
  const target = await response.json();
  const client = await connect(target.webSocketDebuggerUrl);

  try {
    await client.send("Page.enable");
    await client.send("Emulation.setDeviceMetricsOverride", {
      width,
      height,
      deviceScaleFactor,
      mobile: width <= 640,
    });
    await client.send("Page.navigate", { url: APP_URL });
    await new Promise((resolve) => setTimeout(resolve, 12000));
    const result = await client.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
    });
    fs.writeFileSync(path.join(OUTPUT_DIR, name), Buffer.from(result.data, "base64"));
  } finally {
    client.close();
    await fetch(`${DEBUG_URL}/json/close/${target.id}`);
  }
}

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  await capture("dashboard-desktop.png", 1440, 1100);
  await capture("dashboard-mobile.png", 390, 844, 2);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
