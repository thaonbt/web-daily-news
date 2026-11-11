# (1) Cào RSS $\rightarrow$ 
# (2) Gom dữ liệu thô $\rightarrow$ 
# (3) Gửi tới Gemini API tóm tắt $\rightarrow$ 
# (4) Biên tập file news.json & Render file index.html.

import os
import json
import feedparser
import markdown
from datetime import datetime
from google import genai

# 1. DANH SÁCH NGUỒN RSS (Ưu tiên Quốc tế > Việt Nam)
RSS_SOURCES = {
    # Nước ngoài / Quốc tế
    "Reuters World": "https://news.google.com/rss/search?q=when:24h+site:reuters.com/world&ceid=US:en&hl=en-US&gl=US",
    "Reuters Business": "https://news.google.com/rss/search?q=when:24h+site:reuters.com/business&ceid=US:en&hl=en-US&gl=US",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Financial Times": "https://www.ft.com/rss/home",
    "CoinDesk (Crypto)": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "TechCrunch (AI/Tech)": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Nikkei Asia": "https://info.asia.nikkei.com/rss",
    
    # Trong nước (Việt Nam)
    "VnExpress Thế Giới": "https://vnexpress.net/rss/the-gioi.rss",
    "VnExpress Kinh Doanh": "https://vnexpress.net/rss/kinh-doanh.rss",
    "VnExpress Khoa Học/Số Hóa": "https://vnexpress.net/rss/so-hoa.rss",
    "Tuổi Trẻ Thời Sự": "https://tuoitre.vn/rss/thoi-su.rss"
}

DATA_FILE = "news.json"

# def fetch_raw_news():
#     """Bóc tách tin thô từ các nguồn RSS trong 24h-48h qua"""
#     raw_articles = []
#     print("🔄 Đang cào dữ liệu từ các nguồn RSS...")
#     for source_name, url in RSS_SOURCES.items():
#         try:
#             feed = feedparser.parse(url)
#             for entry in feed.entries[:8]: # Lấy 8 bài mới nhất mỗi nguồn
#                 raw_articles.append({
#                     "source": source_name,
#                     "title": entry.title,
#                     "link": entry.link,
#                     "published": entry.get("published", datetime.now().strftime("%Y-%m-%d"))
#                 })
#         except Exception as e:
#             print(f"⚠️ Lỗi cào nguồn {source_name}: {e}")
#     return raw_articles

def fetch_raw_news():
    """Bóc tách tin thô từ các nguồn RSS trong 24h-48h qua"""
    raw_articles = []
    print("🔄 Đang cào dữ liệu từ các nguồn RSS...")
    
    # Kiểm tra xem RSS_SOURCES có tồn tại hoặc có dữ liệu không
    if 'RSS_SOURCES' not in globals() or not RSS_SOURCES:
        print("❌ Lỗi: Biến RSS_SOURCES chưa được định nghĩa hoặc đang trống!")
        return []

    for source_name, url in RSS_SOURCES.items():
        try:
            print(f"-> Đang kết nối tới [{source_name}]: {url}")
            feed = feedparser.parse(url)
            
            # Kiểm tra nếu feed bị lỗi phân tích (bozo)
            if feed.get('bozo') == 1:
                print(f"⚠️ Cảnh báo cấu trúc RSS tại {source_name}: {feed.get('bozo_exception')}")

            print(f"   Tìm thấy {len(feed.entries)} bài viết.")
            
            for entry in feed.entries[:8]: # Lấy 8 bài mới nhất mỗi nguồn
                raw_articles.append({
                    "source": source_name,
                    "title": getattr(entry, 'title', 'Không có tiêu đề'),
                    "link": getattr(entry, 'link', '#'),
                    "published": entry.get("published", datetime.now().strftime("%Y-%m-%d"))
                })
        except Exception as e:
            print(f"⚠️ Lỗi ngoại lệ khi cào nguồn {source_name}: {e}")
            
    return raw_articles

def generate_newsletter_with_gemini(raw_news):
    """Truyền dữ liệu thô + Prompt chuẩn Biên tập viên cho Gemini API"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chưa cài đặt GEMINI_API_KEY trong Environment Variable!")

    client = genai.Client(api_key=api_key)
    today_str = datetime.now().strftime("%d/%m/%Y")

    # Đóng gói dữ liệu thô dạng văn bản gọn nhẹ
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
Cần bao phủ các nhóm chủ đề theo 3 khu vực địa lý:
- Thế giới
- Châu Á
- Việt Nam

Tại mỗi khu vực địa lý, hãy quét 4 nhóm lĩnh vực trọng tâm:
1. Kinh tế - Tài chính & Thị trường đầu tư (Vĩ mô, Cổ phiếu, Giá vàng, Thị trường Tiền mã hóa/Crypto)
2. Chính trị - Xã hội
3. Văn hóa - Công nghệ (AI, Xu hướng công nghệ mới, Đời sống văn hóa - nghệ thuật)
4. Môi trường & Biến đổi khí hậu (Thiên tai, Đổi mới năng lượng, Chính sách khí hậu, Tín chỉ carbon)

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
### 1. Kinh tế - Tài chính & Thị trường đầu tư (Cổ phiếu, Vàng, Crypto)
- **[Tiêu đề tin]**
  - Tóm tắt: ...
  - Nguồn: [Tên Nguồn](link_url)

### 2. Chính trị - Xã hội
...
### 3. Văn hóa - Công nghệ
...
### 4. Môi trường & Biến đổi khí hậu
...

---

## II. CHÂU Á
(Cấu trúc tương tự)

---

## III. VIỆT NAM
(Cấu trúc tương tự)

---

## IV. ĐÁNH GIÁ NỔI BẬT (QUAN ĐIỂM BIÊN TẬP)
Tóm tắt ngắn gọn 3 - 4 dòng về bức tranh tổng thể và xu hướng dòng tiền/biến động đáng chú ý nhất của bản tin hôm nay.

DƯỚI ĐÂY LÀ DỮ LIỆU TIN TỨC THÔ ĐẦU VÀO:
{raw_text_payload}
"""

    print("🤖 Đang gửi dữ liệu tới Gemini API để chọn lọc & biên tập...")
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=system_prompt
    )
    return response.text

def save_to_history(markdown_content):
    """Lưu bản tin hôm nay vào file lịch sử JSON"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    # Thêm bản tin mới lên đầu danh sách
    history.insert(0, {
        "date": today_str,
        "content": markdown_content
    })
    
    # Giữ tối đa 30 bản tin gần nhất
    history = history[:30]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def build_html_page(markdown_content):
    """Chuyển đổi Markdown thành trang Web tĩnh HTML với Tailwind CSS"""
    html_body = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
    
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
        save_to_history(markdown_result)
        build_html_page(markdown_result)
    else:
        print("❌ Không lấy được tin tức thô nào từ các nguồn RSS.")