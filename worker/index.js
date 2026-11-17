// Cloudflare Worker của web-daily-news. Hai việc:
//  1. Phục vụ site tĩnh trong ./site (qua binding ASSETS).
//  2. Mỗi Cron Trigger gọi API workflow_dispatch của GitHub để chạy workflow đúng giờ.
//
// Cấu hình (wrangler.jsonc): GITHUB_REPO, WORKFLOW_FILE, GITHUB_REF.
// Secret (không để trong repo): GH_DISPATCH_TOKEN - fine-grained PAT chỉ cho repo này, quyền Actions: read and write.

// Biểu thức cron (UTC) -> phiên. Phải khớp "triggers.crons" trong wrangler.jsonc.
const SLOT_BY_CRON = {
  "17 22 * * *": "morning", // 05:17 ICT
  "17 4 * * *": "midday",   // 11:17 ICT
};

const RETRY_DELAYS_MS = [0, 5_000, 20_000];

async function dispatchWorkflow(env, slot) {
  const url = `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${env.WORKFLOW_FILE}/dispatches`;
  const init = {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "web-daily-news-cron", // GitHub API bắt buộc có User-Agent
      "Content-Type": "application/json",
    },
    // force=false: nếu phiên này đã có edition thì main.py bỏ qua, nên gọi trùng không tốn quota Gemini.
    body: JSON.stringify({ ref: env.GITHUB_REF, inputs: { slot, force: "false" } }),
  };

  let lastError;
  for (const delay of RETRY_DELAYS_MS) {
    if (delay) await new Promise((resolve) => setTimeout(resolve, delay));
    try {
      const res = await fetch(url, init);
      if (res.status === 204) {
        console.log(`Đã kích hoạt workflow, phiên ${slot}`);
        return;
      }
      const detail = (await res.text()).slice(0, 300);
      lastError = new Error(`GitHub trả HTTP ${res.status}: ${detail}`);
      // 401/403/404/422 (sai token, hết quyền, sai tên workflow/ref): thử lại cũng vô ích.
      if (res.status < 500 && res.status !== 429) break;
    } catch (err) {
      lastError = err; // lỗi mạng: thử lại
    }
  }
  throw lastError;
}

export default {
  // Throw khi thất bại để Cloudflare ghi nhận lần chạy lỗi (xem Observability > Logs).
  async scheduled(event, env) {
    const slot = SLOT_BY_CRON[event.cron];
    if (!slot) throw new Error(`Cron không xác định: ${event.cron}`);
    if (!env.GH_DISPATCH_TOKEN) throw new Error("Thiếu secret GH_DISPATCH_TOKEN");
    await dispatchWorkflow(env, slot);
  },

  // Mọi request HTTP đều trả về file tĩnh; Worker không có endpoint nào để gọi GitHub từ bên ngoài.
  fetch(request, env) {
    return env.ASSETS.fetch(request);
  },
};
