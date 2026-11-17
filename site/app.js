// Hiển thị news.json. HTML đã được render + sanitize ở main.py (markdown-it-py + nh3),
// nên trang này không cần thư viện bên thứ ba. CSP trong index.html chỉ cho phép script từ 'self'.
const STALE_AFTER_HOURS = 36;
const SLOT_NAMES = { morning: "sáng", midday: "trưa" };
const $ = (id) => document.getElementById(id);
const fmt = new Intl.DateTimeFormat("vi-VN", {
  timeZone: "Asia/Ho_Chi_Minh", dateStyle: "short", timeStyle: "short",
});

// Hỗ trợ cả định dạng cũ (mảng [{date, content}]) lẫn mới ({editions, last_run}).
function normalize(raw) {
  if (Array.isArray(raw)) return { last_run: null, editions: raw };
  return { last_run: raw.last_run || null, editions: raw.editions || [] };
}

// "2026-11-16" -> "16/11/2026"
function dateVN(e) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(e.date || "");
  return m ? `${m[3]}/${m[2]}/${m[1]}` : (e.date || "");
}

// Phiên: "16/11/2026 sáng" / "16/11/2026 trưa" (edition cũ không có slot: "Ngày 13/11/2026").
function labelOf(e) {
  const slot = SLOT_NAMES[e.slot];
  return slot ? `${dateVN(e)} ${slot}` : `Ngày ${dateVN(e)}`;
}

// Một "tin" là <li> có <strong> (tiêu đề) và <ul> lồng bên trong (Tóm tắt, Nguồn).
function storyItems(root) {
  return [...root.querySelectorAll("li")].filter(
    (li) => li.querySelector(":scope > strong") && li.querySelector(":scope > ul"),
  );
}

function hrefsOf(node) {
  return [...node.querySelectorAll("a[href]")].map((a) => a.getAttribute("href").split("#")[0]);
}

// Làm mờ tin đã xuất hiện ở bản trước: coi là cùng một tin khi dùng chung ít nhất một link nguồn.
// Trả về {fresh, seen} hoặc null nếu không có bản trước để so sánh.
function markSeen(el, previous) {
  if (!previous || !previous.html) return null;
  const prevDoc = new DOMParser().parseFromString(previous.html, "text/html"); // không thực thi script
  const prevLinks = new Set(hrefsOf(prevDoc));
  let seen = 0;
  const stories = storyItems(el);
  for (const li of stories) {
    if (!hrefsOf(li).some((h) => prevLinks.has(h))) continue;
    li.classList.add("seen");
    const badge = document.createElement("span");
    badge.className = "seen-badge";
    badge.textContent = "Đã có ở bản trước";
    li.querySelector(":scope > strong").after(badge);
    seen += 1;
  }
  return { fresh: stories.length - seen, seen };
}

function renderInto(el, edition, previous) {
  const stats = $("stats");
  stats.textContent = "";
  if (!edition.html) {
    // Edition chưa có html (chưa qua main.py mới): hiện markdown thô bằng textContent, không chèn HTML.
    const pre = document.createElement("pre");
    pre.textContent = edition.content || "";
    el.replaceChildren(pre);
    return;
  }
  el.innerHTML = edition.html;
  el.querySelectorAll("a").forEach((a) => {
    a.target = "_blank";
    a.rel = "noopener noreferrer";
  });
  const result = markSeen(el, previous);
  if (result) {
    stats.textContent = `${result.fresh} tin mới · ${result.seen} tin đã có ở bản trước (${labelOf(previous)})`;
  }
}

// editions[0] là bản mới nhất; bản "trước" của editions[i] là editions[i + 1].
function show(editions, idx, tabs) {
  renderInto($("content"), editions[idx], editions[idx + 1]);
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

  // Banner: lần chạy gần nhất lỗi -> đang hiện bản cũ; hoặc dữ liệu quá cũ (trigger ngừng chạy).
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
