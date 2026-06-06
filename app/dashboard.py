DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mimir Agent Console</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
      background: #071018;
      color: #edf4f8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 12% 0%, #183452 0, transparent 34rem),
        radial-gradient(circle at 90% 10%, #332354 0, transparent 30rem),
        #071018;
    }
    .shell { max-width: 1280px; margin: 0 auto; padding: 32px 24px 48px; }
    header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 28px;
    }
    .eyebrow {
      color: #7dd3fc;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .18em;
      text-transform: uppercase;
    }
    h1 { margin: 6px 0; font-size: clamp(30px, 5vw, 54px); line-height: 1; }
    .subtitle { color: #91a4b2; margin: 0; max-width: 680px; }
    .online {
      border: 1px solid #28513b;
      border-radius: 999px;
      color: #86efac;
      padding: 8px 12px;
      font-size: 13px;
      white-space: nowrap;
      background: #0d281b;
    }
    .grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 12px; }
    .agent {
      min-height: 154px;
      padding: 16px;
      border: 1px solid #20303d;
      border-radius: 18px;
      background: rgba(12, 24, 34, .82);
      box-shadow: 0 16px 40px rgba(0, 0, 0, .16);
    }
    .agent.active { border-color: var(--agent-color); box-shadow: 0 0 0 1px var(--agent-color); }
    .avatar {
      width: 42px;
      height: 42px;
      display: grid;
      place-items: center;
      border-radius: 13px;
      color: #071018;
      background: var(--agent-color);
      font-weight: 900;
      font-size: 13px;
      margin-bottom: 14px;
    }
    .agent h2 { margin: 0 0 5px; font-size: 16px; }
    .role { color: #91a4b2; font-size: 12px; line-height: 1.45; }
    main { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, .7fr); gap: 18px; margin-top: 18px; }
    .panel {
      border: 1px solid #20303d;
      border-radius: 22px;
      background: rgba(8, 18, 27, .9);
      overflow: hidden;
    }
    .panel-title { padding: 18px 20px; border-bottom: 1px solid #20303d; font-weight: 750; }
    #conversation {
      height: 430px;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .message {
      max-width: 84%;
      padding: 12px 14px;
      border-radius: 15px;
      white-space: pre-wrap;
      line-height: 1.5;
      font-size: 14px;
    }
    .message.user { align-self: end; background: #164e63; }
    .message.agent { align-self: start; background: #162531; border: 1px solid #273b49; }
    form { display: flex; gap: 10px; padding: 16px; border-top: 1px solid #20303d; }
    input {
      width: 100%;
      border: 1px solid #2b4151;
      border-radius: 13px;
      padding: 13px 15px;
      background: #0b1720;
      color: #edf4f8;
      outline: none;
    }
    input:focus { border-color: #38bdf8; }
    button {
      border: 0;
      border-radius: 13px;
      padding: 0 18px;
      color: #041018;
      background: #7dd3fc;
      font-weight: 850;
      cursor: pointer;
    }
    button:disabled { opacity: .55; cursor: wait; }
    .activity { padding: 16px; }
    .event {
      padding: 12px 0;
      border-bottom: 1px solid #1c2d39;
      font-size: 13px;
    }
    .event strong { display: block; margin-bottom: 4px; }
    .event span { color: #8095a5; }
    .empty { color: #6f8494; font-size: 13px; }
    @media (max-width: 1000px) {
      .grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      main { grid-template-columns: 1fr; }
    }
    @media (max-width: 620px) {
      .shell { padding: 22px 14px 32px; }
      header { align-items: start; flex-direction: column; }
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .agent { min-height: 136px; }
      #conversation { height: 380px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <div class="eyebrow">Personal agent system</div>
        <h1>Mimir Console</h1>
        <p class="subtitle">One orchestrator. Six specialists. Send a request and watch Mimir route it.</p>
      </div>
      <div class="online">System online</div>
    </header>
    <section class="grid" id="agents"></section>
    <main>
      <section class="panel">
        <div class="panel-title">Conversation</div>
        <div id="conversation">
          <div class="message agent">Mimir is ready. Try: "Plan a three-day trip to Kyoto" or "Help me prepare an interview."</div>
        </div>
        <form id="chat-form">
          <input id="message" autocomplete="off" placeholder="Ask Mimir..." required>
          <button id="send" type="submit">Send</button>
        </form>
      </section>
      <aside class="panel">
        <div class="panel-title">Routing activity</div>
        <div class="activity" id="activity"><div class="empty">No tasks routed yet.</div></div>
      </aside>
    </main>
  </div>
  <script>
    const agentsNode = document.querySelector("#agents");
    const conversation = document.querySelector("#conversation");
    const activity = document.querySelector("#activity");
    const form = document.querySelector("#chat-form");
    const input = document.querySelector("#message");
    const send = document.querySelector("#send");
    let agents = [];

    function addMessage(text, kind) {
      const node = document.createElement("div");
      node.className = `message ${kind}`;
      node.textContent = text;
      conversation.appendChild(node);
      conversation.scrollTop = conversation.scrollHeight;
    }

    function setActive(route) {
      document.querySelectorAll(".agent").forEach((node) => {
        node.classList.toggle("active", node.dataset.id === route);
      });
    }

    function addEvent(response) {
      if (activity.querySelector(".empty")) activity.textContent = "";
      const node = document.createElement("div");
      node.className = "event";
      const title = document.createElement("strong");
      title.textContent = `Mimir -> ${response.agent}`;
      const detail = document.createElement("span");
      detail.textContent = response.metadata.role || "Orchestrator response";
      node.append(title, detail);
      activity.prepend(node);
    }

    async function loadAgents() {
      const response = await fetch("/api/agents");
      agents = await response.json();
      agentsNode.innerHTML = agents.map((agent) => `
        <article class="agent" data-id="${agent.id}" style="--agent-color:${agent.color}">
          <div class="avatar">${agent.icon}</div>
          <h2>${agent.name}</h2>
          <div class="role">${agent.role}</div>
        </article>
      `).join("");
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      addMessage(message, "user");
      input.value = "";
      send.disabled = true;
      try {
        const response = await fetch("/debug/chat", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            message,
            user_id: "dashboard-user",
            conversation_id: "dashboard"
          })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "Request failed");
        addMessage(result.reply, "agent");
        setActive(result.route);
        addEvent(result);
      } catch (error) {
        addMessage(`Request failed: ${error.message}`, "agent");
      } finally {
        send.disabled = false;
        input.focus();
      }
    });

    loadAgents().catch(() => {
      agentsNode.innerHTML = '<div class="empty">Could not load agents.</div>';
    });
  </script>
</body>
</html>
"""
