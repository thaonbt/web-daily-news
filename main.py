# (1) Cào RSS $\rightarrow$ 
# (2) Gom dữ liệu thô $\rightarrow$ 
# (3) Gửi tới Gemini API tóm tắt $\rightarrow$ 
# (4) Biên tập file news.json & Render file index.html.

import os
import json
import time
import feedparser
import requests
import markdown
from datetime import datetime
from google import genai
from google.genai.errors import ServerError, ClientError

# 1. DANH SÁCH NGUỒN RSS (Ưu tiên Quốc tế > Việt Nam)
RSS_SOURCES = {
    # --- QUỐC TẾ & TOÀN CẦU (Châu Âu, Châu Mỹ, Vĩ mô) ---
    "Reuters World": "https://news.google.com/rss/search?q=when:24h+site:reuters.com/world&ceid=US:en&hl=en-US&gl=US",
    "Reuters Business": "https://news.google.com/rss/search?q=when:24h+site:reuters.com/business&ceid=US:en&hl=en-US&gl=US",
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Financial Times": "https://www.ft.com/rss/home",
    "Bloomberg Markets": "https://news.google.com/rss/search?q=when:24h+site:bloomberg.com/markets&ceid=US:en&hl=en-US&gl=US",
    "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",

    # --- CÔNG NGHỆ, AI & CRYPTO ---
    "TechCrunch (AI/Tech)": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Hacker News": "https://news.ycombinator.com/rss",
    "CoinDesk (Crypto)": "https://www.coindesk.com/arc/outboundfeeds/rss/",

    # --- VIỆT NAM (Kinh tế, Tài chính, Vĩ mô, Xã hội) ---
    "VnExpress Thế Giới": "https://vnexpress.net/rss/the-gioi.rss",
    "VnExpress Kinh Doanh": "https://vnexpress.net/rss/kinh-doanh.rss",
    "VnExpress Số Hóa": "https://vnexpress.net/rss/so-hoa.rss",
    "Tuổi Trẻ Thời Sự": "https://tuoitre.vn/rss/thoi-su.rss",
    "Cafef (Tài chính - Chứng khoán)": "https://cafef.vn/home.rss",
    "VnEconomy (Kinh tế & Chính sách)": "https://vneconomy.vn/rss/home.rss"
}

DATA_FILE = "news.json"

def fetch_raw_news():
    """Bóc tách tin thô từ các nguồn RSS/Atom, xử lý triệt để lỗi cấu trúc"""
    raw_articles = []
    print("🔄 Đang cào dữ liệu từ các nguồn...")
    
    if 'RSS_SOURCES' not in globals() or not RSS_SOURCES:
        print("❌ Lỗi: Biến RSS_SOURCES chưa được định nghĩa hoặc đang trống!")
        return []

    for source_name, url in RSS_SOURCES.items():
        try:
            print(f"-> Đang kết nối tới [{source_name}]: {url}")
            
            # Tải nội dung qua requests để kiểm soát tốt hơn các định dạng RSS/Atom
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8' 
            
            # Parse nội dung văn bản thô
            feed = feedparser.parse(response.text)
            
            # BChỉ in cảnh báo nếu không phải là Hacker News hoặc cảnh báo không ảnh hưởng nghiêm trọng (như CharacterEncodingOverride)
            if feed.get('bozo') == 1:
                exc = feed.get('bozo_exception')
                if source_name != "Hacker News" and not isinstance(exc, feedparser.CharacterEncodingOverride):
                    print(f"⚠️ Cảnh báo cấu trúc tại {source_name}: {exc}")
                
            print(f"   Tìm thấy {len(feed.entries)} bài viết.")
            
            # Duyệt qua các bài viết và trích xuất an toàn
            for entry in feed.get('entries', [])[:8]:
                title = getattr(entry, 'title', None) or entry.get('title', 'Không có tiêu đề')
                link = getattr(entry, 'link', None) or entry.get('link', '#')
                published = entry.get('published', entry.get('updated', datetime.now().strftime("%Y-%m-%d")))
                
                raw_articles.append({
                    "source": source_name,
                    "title": title,
                    "link": link,
                    "published": published
                })
        except Exception as e:
            print(f"⚠️ Lỗi ngoại lệ khi cào nguồn {source_name}: {e}")
            
    return raw_articles

def generate_newsletter_with_gemini(raw_news):
    """Gửi dữ liệu tới Gemini API với thời gian chờ giãn cách thông minh (Retry)"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ Chưa cài đặt GEMINI_API_KEY trong Environment Variable!")
        return None

    client = genai.Client(api_key=api_key)
    today_str = datetime.now().strftime("%d/%m/%Y")

    raw_text_payload = ""
    for idx, item in enumerate(raw_news, 1):
        raw_text_payload += f"{idx}. [{item['source']}] {item['title']} | Link: {item['link']} | Ngày: {item['published']}\n"

    system_prompt = f"""
Hãy đóng vai một Biên tập viên Tin tức Quốc tế & Trong nước chuyên nghiệp. Nhiệm vụ của bạn là thu thập, chọn lọc và tóm tắt các tin tức nổi bật nhất từ dữ liệu đầu vào.

### 1. QUY TẮC THỜI GIAN & LỌC TIN:
- Mốc thời gian tham chiếu: Ngày hôm nay {today_str}.
- Ưu tiên hàng đầu: Các tin tức cập nhật mới nhất trong vòng 24 giờ qua.
- Lọc bỏ tin cũ: Tuyệt đối LOẠI BỎ các tin đã diễn ra quá lâu. Chỉ giữ lại tin trong khoảng 3 ngày đến tối đa 1 tuần NẾU ĐÓ LÀ SỰ KIỆN CỰC KỲ HOT / CÓ TÁC ĐỘNG LỚN đang tiếp diễn.

### 2. PHẠM VI NỘI DUNG & ĐỊA LÝ:
Cần bao phủ các nhóm chủ đề theo 5 khu vực địa lý:
- Thế giới
- Châu Âu
- Châu Mỹ
- Châu Á
- Việt Nam

Tại mỗi khu vực địa lý, hãy quét 6 nhóm lĩnh vực trọng tâm:
1. Kinh tế - Tài chính, Tiêu dùng & Đầu tư (Vĩ mô, Cổ phiếu, Giá vàng, Crypto, Chi tiêu/Đầu tư công, Công nghiệp, CPI, GDP)
2. Chính trị, Pháp luật & Thuế (Chính sách nhà nước, Luật mới, Thuế, Quản lý vĩ mô)
3. Công nghệ thông tin, Hạ tầng viễn thông & AI (Xu hướng công nghệ, Chuyển đổi số, Viễn thông, Trí tuệ nhân tạo)
4. Việc làm, Xã hội & Đời sống văn hóa (Thị trường lao động, An sinh xã hội, Văn hóa - Nghệ thuật)
5. Xuất Nhập Khẩu & Thương mại quốc tế (Chuỗi cung ứng, Hiệp định thương mại, Hải quan, Logistics)
6. Môi trường & Biến đổi khí hậu (Thiên tai, Năng lượng sạch, Chính sách khí hậu, Tín chỉ carbon)

### 3. YÊU CẦU ĐỐI VỚI NỘI DUNG TIN TỨC:
- Chọn lọc 2 - 3 tin tức thực sự nổi bật/quan trọng nhất cho mỗi nhóm lĩnh vực.
- Thông tin phải mới, chính xác và có tính tác động lớn.
- Với mỗi tin tức, hãy tóm tắt ngắn gọn trong 2 - 4 câu (gồm: Sự việc gì đã xảy ra, nguyên nhân/bối cảnh chính, tác động hoặc hệ quả dự kiến).

### 4. YÊU CẦU VỀ NGUỒN (MANDATORY):
- Mỗi tin tức BẮT BUỘC phải kèm theo 1 - 2 đường link nguồn từ dữ liệu đầu vào.
- Định dạng link dạng Markdown rõ ràng: [Tên Nguồn](URL).

### 5. ĐỊNH DẠNG ĐẦU RA:
Trình bày kết quả chuẩn Markdown theo đúng cấu trúc sau (Không thêm lời dẫn đầu/cuối):

# BẢN TIN TỔNG HỢP NỔI BẬT {today_str}

---

## I. THẾ GIỚI
### 1. Kinh tế - Tài chính, Tiêu dùng & Đầu tư
- **[Tiêu đề tin]**
  - Tóm tắt: ...
  - Nguồn: [Tên Nguồn](link_url)

### 2. Chính trị, Pháp luật & Thuế
...
### 3. Công nghệ thông tin, Hạ tầng viễn thông & AI
...
### 4. Việc làm, Xã hội & Đời sống văn hóa
...
### 5. Xuất Nhập Khẩu & Thương mại quốc tế
...
### 6. Môi trường & Biến đổi khí hậu
...

---

## II. CHÂU ÂU
(Cấu trúc tương tự)

---

## III. CHÂU MỸ
(Cấu trúc tương tự)

---

## IV. CHÂU Á
(Cấu trúc tương tự)

---

## V. VIỆT NAM
(Cấu trúc tương tự)

---

## VI. ĐÁNH GIÁ NỔI BẬT (QUAN ĐIỂM BIÊN TẬP)
Tóm tắt ngắn gọn 3 - 4 dòng về bức tranh tổng thể và xu hướng dòng tiền/biến động đáng chú ý nhất của bản tin hôm nay.

DƯỚI ĐÂY LÀ DỮ LIỆU TIN TỨC THÔ ĐẦU VÀO:
{raw_text_payload}
"""

    max_retries = 3
    delays = [30, 60, 120]  # Giãn cách thời gian chờ để vượt qua các đợt bận kéo dài

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🤖 Đang gửi dữ liệu tới Gemini API (Lần thử {attempt}/{max_retries})...")
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=system_prompt
            )
            return response.text
        except (ServerError, ClientError, Exception) as e:
            print(f"⚠️ Gặp sự cố khi gọi Gemini: {e}")
            if attempt < max_retries:
                wait_time = delays[attempt - 1]
                print(f"⏳ Server đang quá tải. Đang chờ {wait_time} giây trước khi tự động thử lại...")
                time.sleep(wait_time)
            else:
                print("❌ Đã thử lại tối đa nhưng không thành công do quá tải.")
                return None

def save_to_history(markdown_content):
    """Lưu bản tin hôm nay vào file lịch sử JSON (giữ tối đa 30 bản tin)"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    history = [item for item in history if item.get("date") != today_str]
    history.insert(0, {"date": today_str, "content": markdown_content})
    history = history[:30]
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print("✅ Đã cập nhật vào news.json thành công!")

def get_latest_from_history():
    """Lấy nội dung bản tin thành công gần nhất từ news.json khi AI gặp lỗi"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                if history and len(history) > 0:
                    return history[0].get("content")
        except Exception:
            pass
    return None

def build_html_page(markdown_content, is_fallback=False):
    """Chuyển đổi Markdown thành trang Web tĩnh HTML với Tailwind CSS (có nút chuyển hướng nhanh tới Actions)"""
    html_body = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
    
    warning_banner = ""
    if is_fallback:
        warning_banner = """
        <div class="bg-amber-50 border-l-4 border-amber-400 p-4 mb-6 rounded-r-lg shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div class="flex items-start">
                <div class="flex-shrink-0 pt-0.5">
                    <svg class="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-amber-700 font-medium">
                        ⚠️ Hệ thống AI đang quá tải tạm thời. Bản tin hiển thị bên dưới là kho lưu trữ gần nhất.
                    </p>
                </div>
            </div>
            <a href="https://github.com/thaonbt/web-daily-news/actions/workflows/update_news.yml" target="_blank" class="whitespace-nowrap inline-flex items-center justify-center px-4 py-2 border border-amber-300 text-sm font-medium rounded-md text-amber-800 bg-amber-100 hover:bg-amber-200 transition shadow-xs">
                🚀 Bấm để chạy lại ngay
            </a>
        </div>
        """

    html_document = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bản Tin Tổng Hợp 24/7</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .prose h1 {{ font-size: 1.875rem; font-weight: 800; color: #1d4ed8; margin-bottom: 1.5rem; text-align: center; }}
        .prose h2 {{ font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }}
        .prose h3 {{ font-size: 1.125rem; font-weight: 600; color: #2563eb; margin-top: 1.25rem; margin-bottom: 0.5rem; }}
        .prose ul {{ list-style-type: disc; padding-left: 1.25rem; margin-bottom: 1rem; }}
        .prose li {{ margin-bottom: 0.5rem; }}
        .prose a {{ color: #2563eb; text-decoration: underline; font-weight: 500; }}
        .prose a:hover {{ color: #1d4ed8; }}
        .prose strong {{ color: #0f172a; }}
        .prose hr {{ margin-top: 2rem; margin-bottom: 2rem; border-color: #cbd5e1; }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 font-sans leading-relaxed">
    <div class="max-w-4xl mx-auto px-4 py-8">
        <header class="bg-white p-6 rounded-2xl shadow-sm mb-8 border border-slate-100 text-center">
            <span class="bg-blue-100 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">AI Daily Newsletter</span>
            <p class="text-slate-400 text-xs mt-3">Tự động cập nhật 24/7 bởi Python & Gemini AI</p>
        </header>

        {warning_banner}

        <main class="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 prose max-w-none">
            {html_body}
        </main>

        <footer class="text-center text-slate-400 text-xs mt-10 mb-6">
            <p>© {datetime.now().year} International & Local News Aggregator. Powered by GitHub Pages.</p>
        </footer>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_document)
    print("✅ Đã tạo file index.html thành công!")

def build_html_page(markdown_content, is_fallback=False):
    """Chuyển đổi Markdown thành trang Web tĩnh HTML với Tailwind CSS (có hỗ trợ hiển thị cảnh báo lỗi)"""
    html_body = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
    
    # Tạo banner cảnh báo nếu là bản tin lấy từ lịch sử do lỗi API
    warning_banner = ""
    if is_fallback:
        warning_banner = """
        <div class="bg-amber-50 border-l-4 border-amber-400 p-4 mb-6 rounded-r-lg shadow-sm">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-amber-700 font-medium">
                        ⚠️ Hệ thống AI đang quá tải (Lỗi 503). Đang tạm thời hiển thị bản tin lưu trữ gần nhất. Bản tin mới sẽ được cập nhật ở lần chạy tiếp theo.
                    </p>
                </div>
            </div>
        </div>
        """

    html_document = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bản Tin Tổng Hợp 24/7</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .prose h1 {{ font-size: 1.875rem; font-weight: 800; color: #1d4ed8; margin-bottom: 1.5rem; text-align: center; }}
        .prose h2 {{ font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }}
        .prose h3 {{ font-size: 1.125rem; font-weight: 600; color: #2563eb; margin-top: 1.25rem; margin-bottom: 0.5rem; }}
        .prose ul {{ list-style-type: disc; padding-left: 1.25rem; margin-bottom: 1rem; }}
        .prose li {{ margin-bottom: 0.5rem; }}
        .prose a {{ color: #2563eb; text-decoration: underline; font-weight: 500; }}
        .prose a:hover {{ color: #1d4ed8; }}
        .prose strong {{ color: #0f172a; }}
        .prose hr {{ margin-top: 2rem; margin-bottom: 2rem; border-color: #cbd5e1; }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 font-sans leading-relaxed">
    <div class="max-w-4xl mx-auto px-4 py-8">
        <header class="bg-white p-6 rounded-2xl shadow-sm mb-8 border border-slate-100 text-center">
            <span class="bg-blue-100 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">AI Daily Newsletter</span>
            <p class="text-slate-400 text-xs mt-3">Tự động cập nhật 24/7 bởi Python & Gemini AI</p>
        </header>

        {warning_banner}

        <main class="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 prose max-w-none">
            {html_body}
        </main>

        <footer class="text-center text-slate-400 text-xs mt-10 mb-6">
            <p>© {datetime.now().year} International & Local News Aggregator. Powered by GitHub Pages.</p>
        </footer>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_document)
    print("✅ Đã tạo file index.html thành công!")

if __name__ == "__main__":
    raw_news = fetch_raw_news()
    if raw_news:
        markdown_result = generate_newsletter_with_gemini(raw_news)
        if markdown_result:
            save_to_history(markdown_result)
            build_html_page(markdown_result, is_fallback=False)
        else:
            print("⚠️ Lấy bản tin cũ từ lịch sử do gọi API thất bại.")
            # Lấy bản tin mới nhất trong lịch sử ra để hiển thị kèm cảnh báo
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if history:
                        build_html_page(history[0]["content"], is_fallback=True)
    else:
        print("❌ Không lấy được tin tức thô nào từ các nguồn RSS.")