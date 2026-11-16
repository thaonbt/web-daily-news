// Hiển thị news.json. HTML đã được render + sanitize ở main.py (markdown-it-py + nh3),
// nên trang này không cần thư viện bên thứ ba. CSP trong index.html chỉ cho phép script từ 'self'.
const STALE_AFTER_HOURS = 36;
const $ = (id) => document.getElementById(id);
const fmt = new Intl.DateTimeFormat("vi-VN", {
  timeZone: "Asia/Ho_Chi_Minh", dateStyle: "short", timeStyle: "short",
});

// Hỗ trợ cả định dạng cũ (mảng [{date, content}]) lẫn mới ({editions, last_run}).
function normalize(raw) {
  if (Array.isArray(raw)) return { last_run: null, editions: raw };
  return { last_run: raw.last_run || null, editions: raw.editions || [] };
}

function renderInto(el, edition) {
  if (edition.html) {
    el.innerHTML = edition.html;
    el.querySelectorAll("a").forEach((a) => {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    });
  } else {
    // Edition chưa có html (chưa qua main.py mới): hiện markdown thô bằng textContent, không chèn HTML.
    const pre = document.createElement("pre");
    pre.textContent = edition.content || "";
    el.replaceChildren(pre);
  }
}

function labelOf(e) {
  const when = e.generated_at ? fmt.format(new Date(e.generated_at)) : e.date;
  return e.label ? `${e.label} · ${when}` : `Ngày ${e.date}`;
}

function show(editions, idx, tabs) {
  renderInto($("content"), editions[idx]);
  tabs.forEach((b, i) => b.setAttribute("aria-selected", String(i === idx)));
}

function setBanner(text) {
  const el = $("banner");
  el.textContent = text;
  el.style.display = text ? "block" : "none";
}

async function init() {
  let data;
  try {
    const res = await fetch("news.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    data = normalize(await res.json());
  } catch (err) {
    $("meta").textContent = "";
    setBanner("Không tải được dữ liệu bản tin. Vui lòng thử lại sau.");
    return;
  }

  const { editions, last_run } = data;
  if (!editions.length) {
    $("meta").textContent = "";
    setBanner("Chưa có bản tin nào.");
    return;
  }

  const latest = editions[0];
  $("meta").textContent = latest.generated_at
    ? `Cập nhật lần cuối: ${fmt.format(new Date(latest.generated_at))} (giờ Việt Nam)`
    : `Bản tin ngày ${latest.date}`;

  // Banner: lần chạy gần nhất lỗi -> đang hiện bản cũ; hoặc dữ liệu quá cũ (Actions ngừng chạy).
  if (last_run && last_run.status === "failed") {
    setBanner(`Lần cập nhật gần nhất (${fmt.format(new Date(last_run.at))}) không thành công. ` +
              `Đang hiển thị bản tin gần nhất còn lưu.`);
  } else if (latest.generated_at &&
             Date.now() - new Date(latest.generated_at).getTime() > STALE_AFTER_HOURS * 3600e3) {
    setBanner("Bản tin này đã khá cũ; hệ thống có thể chưa chạy được lịch cập nhật mới.");
  }

  const nav = $("tabs");
  const buttons = editions.map((e, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.textContent = (i === 0 ? "Mới nhất · " : "Trước đó · ") + labelOf(e);
    b.addEventListener("click", () => show(editions, i, buttons));
    nav.appendChild(b);
    return b;
  });
  if (editions.length < 2) nav.style.display = "none";

  show(editions, 0, buttons);
}

init();
