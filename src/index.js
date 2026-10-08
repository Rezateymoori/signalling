export class SignalingRoom {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.sessions = new Map();
  }

  async fetch(request) {
    if (request.headers.get("Upgrade") !== "websocket") {
      return new Response("DirectChat Signaling Worker is running.", { status: 200 });
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    const url = new URL(request.url);
    const userId = url.searchParams.get("user");

    if (!userId) {
      server.close(1008, "Missing user");
      return new Response(null, { status: 400 });
    }

    server.accept();
    this.sessions.set(userId, server);

    server.addEventListener("message", event => {
      try {
        const msg = JSON.parse(event.data);
        const target = msg.to;
        if (target && this.sessions.has(target)) {
          this.sessions.get(target).send(JSON.stringify({
            ...msg,
            from: userId
          }));
        }
      } catch (_) {}
    });

    const cleanup = () => {
      if (this.sessions.get(userId) === server) {
        this.sessions.delete(userId);
      }
    };

    server.addEventListener("close", cleanup);
    server.addEventListener("error", cleanup);

    server.send(JSON.stringify({ type: "connected", user: userId }));
    return new Response(null, { status: 101, webSocket: client });
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({ ok: true, service: "DirectChat Signaling" });
    }

    if (url.pathname === "/ws") {
      const roomId = url.searchParams.get("room") || "global";
      const id = env.SIGNALING_ROOM.idFromName(roomId);
      return env.SIGNALING_ROOM.get(id).fetch(request);
    }

    return new Response("DirectChat Signaling Worker", { status: 200 });
  }
};
