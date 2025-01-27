import feedparser
import requests
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
import os

# إعدادات
PEXELS_API_KEY = "PCwqJJH8epOMqmKdeGzBPIgzk1npSkI39arGmpnEdshOewaUeRyCuyXY"
YOUTUBE_VIDEO_SIZE = (1280, 720)  # فيديو يوتيوب
TIKTOK_VIDEO_SIZE = (1080, 1920)  # فيديو تيكتوك
FONT_PATH = "/content/TAHAR/3.ttf"  # استبدل بمسار الخط
FONT_SIZE = 55
TEXT_COLOR = "white"
DEFAULT_IMAGE = "/content/TAHAR/default_image.jpg"  # صورة افتراضية
LOGO_PATH = "/content/TAHAR/logo.png"  # شعار القناة
MAX_CHARS_PER_LINE = 40
MAX_LINES_PER_SLIDE = 8

# جلب الأخبار من RSS
def fetch_news(rss_url):
    feed = feedparser.parse(rss_url)
    news = []
    for entry in feed.entries[:5]:  # الحد الأقصى 5 أخبار
        news.append({
            "title": entry.title,
            "description": entry.description,
            "image_url": fetch_image_from_pexels(entry.title)
        })
    return news

# البحث عن صور من Pexels API
def fetch_image_from_pexels(query):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data["photos"]:
            return data["photos"][0]["src"]["large"]
    except Exception as e:
        print(f"Error fetching image: {e}")
    return None

# إنشاء ملفات الصوت
def create_audio(news):
    if not os.path.exists("audio"):
        os.makedirs("audio")
    audio_files = []
    for i, item in enumerate(news):
        text = f"{item['title']}. {item['description']}"
        tts = gTTS(text=text, lang='en')
        audio_path = f"audio/slide_{i}.mp3"
        tts.save(audio_path)
        audio_files.append(audio_path)
    return audio_files

# إنشاء صور الشرائح
def create_slide_images(news, video_size):
    if not os.path.exists("images"):
        os.makedirs("images")
    slide_images = []

    for i, item in enumerate(news):
        # تحميل الصورة الخلفية
        if item["image_url"]:
            try:
                response = requests.get(item["image_url"])
                img = Image.open(BytesIO(response.content)).convert("RGB")
                img = img.resize(video_size)
            except Exception:
                img = Image.open(DEFAULT_IMAGE).resize(video_size)
        else:
            img = Image.open(DEFAULT_IMAGE).resize(video_size)

        # إضافة طبقة داكنة لتقليل الإضاءة
        overlay = Image.new("RGB", video_size, color=(0, 0, 0))
        blended = Image.blend(img, overlay, alpha=0.6)

        draw = ImageDraw.Draw(blended)
        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except Exception as e:
            raise FileNotFoundError(f"خطأ في تحميل الخط: {e}")

        # تقسيم النص إلى أسطر
        text = f"{item['title']}\n\n{item['description']}"
        lines = []
        words = text.split()
        while words:
            line = ""
            while words and len(line) + len(words[0]) + 1 <= MAX_CHARS_PER_LINE:
                line += words.pop(0) + " "
            lines.append(line.strip())

        # تقليل الأسطر إذا تجاوزت الحد المسموح
        lines = lines[:MAX_LINES_PER_SLIDE]

        # حساب موضع النص لتوسيطه
        total_text_height = len(lines) * FONT_SIZE
        y = (video_size[1] - total_text_height) // 2

        for line in lines:
            text_width = draw.textlength(line, font=font)
            x = (video_size[0] - text_width) // 2
            draw.text((x, y), line, fill=TEXT_COLOR, font=font)
            y += FONT_SIZE

        # إضافة شعار القناة
        if os.path.exists(LOGO_PATH):
            logo = Image.open(LOGO_PATH).resize((150, 150))
            blended.paste(logo, (20, 20), logo)

        img_path = f"images/slide_{i}.png"
        blended.save(img_path)
        slide_images.append(img_path)

    return slide_images

# إنشاء مقدمة الفيديو
def create_intro_slide(video_size):
    text = f"Welcome to Global Insight News\nToday's top stories for {datetime.now().strftime('%B %d, %Y')}."
    audio_path = "audio/intro.mp3"
    img_path = "images/intro.png"
    create_text_slide(text, audio_path, img_path, video_size)
    return img_path, audio_path

# إنشاء خاتمة الفيديو
def create_outro_slide(video_size):
    text = "Thank you for watching! Subscribe for more updates."
    audio_path = "audio/outro.mp3"
    img_path = "images/outro.png"
    create_text_slide(text, audio_path, img_path, video_size)
    return img_path, audio_path

# إنشاء صورة مع نصوص
def create_text_slide(text, audio_path, img_path, video_size):
    tts = gTTS(text=text, lang='en')
    tts.save(audio_path)

    img = Image.new("RGB", video_size, color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except Exception as e:
        raise FileNotFoundError(f"خطأ في تحميل الخط: {e}")

    # تقسيم النص إلى أسطر
    lines = []
    words = text.split()
    while words:
        line = ""
        while words and len(line) + len(words[0]) + 1 <= MAX_CHARS_PER_LINE:
            line += words.pop(0) + " "
        lines.append(line.strip())

    total_text_height = len(lines) * FONT_SIZE
    y = (video_size[1] - total_text_height) // 2

    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (video_size[0] - text_width) // 2
        draw.text((x, y), line, fill=TEXT_COLOR, font=font)
        y += FONT_SIZE

    # إضافة شعار القناة
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).resize((150, 150))
        img.paste(logo, (20, 20), logo)

    img.save(img_path)

# إنشاء الفيديو النهائي
def create_video_with_intro_outro(images, audio_files, first_news_title, video_size, video_filename):
    intro_img, intro_audio = create_intro_slide(video_size)
    outro_img, outro_audio = create_outro_slide(video_size)

    clips = []

    # إضافة المقدمة
    intro_clip = ImageClip(intro_img).set_duration(AudioFileClip(intro_audio).duration)
    intro_clip = intro_clip.set_audio(AudioFileClip(intro_audio))
    clips.append(intro_clip)

    # إضافة الأخبار
    for i, img_path in enumerate(images):
        audio_clip = AudioFileClip(audio_files[i])
        image_clip = ImageClip(img_path).set_duration(audio_clip.duration)
        image_clip = image_clip.set_audio(audio_clip)
        clips.append(image_clip)

    # إضافة الخاتمة
    outro_clip = ImageClip(outro_img).set_duration(AudioFileClip(outro_audio).duration)
    outro_clip = outro_clip.set_audio(AudioFileClip(outro_audio))
    clips.append(outro_clip)

    # تجميع الفيديو
    video = concatenate_videoclips(clips, method="compose")

    sanitized_title = "".join(c for c in first_news_title if c.isalnum() or c in " _-").strip()

    video.write_videofile(video_filename, fps=24, codec="libx264", audio_codec="aac")
    print(f"Video saved as: {video_filename}")

# تنفيذ البرنامج
rss_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
news = fetch_news(rss_url)
audio_files = create_audio(news)

# فيديو اليوتيوب
images_youtube = create_slide_images(news, YOUTUBE_VIDEO_SIZE)
if news:
    create_video_with_intro_outro(images_youtube, audio_files, news[0]["title"], YOUTUBE_VIDEO_SIZE, f"{news[0]['title']}_youtube.mp4")

# فيديو التكتوك
images_tiktok = create_slide_images(news, TIKTOK_VIDEO_SIZE)
if news:
    create_video_with_intro_outro(images_tiktok, audio_files, news[0]["title"], TIKTOK_VIDEO_SIZE, f"{news[0]['title']}_tiktok.mp4")
else:
    print("No news found to create video.")

# صورة لليوتوب

import feedparser
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# إعدادات
PEXELS_API_KEY = "PCwqJJH8epOMqmKdeGzBPIgzk1npSkI39arGmpnEdshOewaUeRyCuyXY"  # مفتاح API من Pexels
THUMBNAIL_SIZE = (1280, 720)  # حجم الصورة المصغرة
FONT_PATH_TITLE = "/content/TAHAR/3.ttf"  # مسار الخط للعناوين
FONT_PATH_SUBTITLE = "/content/TAHAR/2.ttf"  # مسار الخط للنصوص الفرعية
DEFAULT_IMAGE = "/content/TAHAR/default_image.jpg"  # صورة افتراضية
LOGO_PATH = "/content/TAHAR/logo.png"  # شعار القناة
TITLE_FONT_SIZE = 100
SUBTITLE_FONT_SIZE = 50
TEXT_COLOR = "white"
BACKGROUND_GRADIENT = [(0, 0, 0), (50, 50, 50)]  # تدرج لوني للخلفية
BORDER_COLOR = (255, 0, 0)  # لون الحدود

# البحث عن صورة باستخدام Pexels API
def fetch_image_from_pexels(query):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1, "orientation": "landscape"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data["photos"]:
            return data["photos"][0]["src"]["large"]
    except Exception as e:
        print(f"Error fetching image from Pexels: {e}")
    return None

# جلب الأخبار من RSS
def fetch_bbc_headlines(rss_url="http://feeds.bbci.co.uk/news/world/rss.xml"):
    feed = feedparser.parse(rss_url)
    headlines = [entry.title for entry in feed.entries[:5]]
    return "\n".join(f"- {headline}" for headline in headlines)

# دالة لإنشاء صورة مصغرة احترافية
def create_advanced_thumbnail(title, subtitle, output_path="advanced_thumbnail.png"):
    # البحث عن صورة باستخدام العنوان
    image_url = fetch_image_from_pexels(title)

    # تحميل الصورة الخلفية أو استخدام صورة افتراضية
    if image_url:
        try:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content)).convert("RGB")
            img = img.resize(THUMBNAIL_SIZE)
        except Exception:
            img = Image.open(DEFAULT_IMAGE).resize(THUMBNAIL_SIZE)
    else:
        img = Image.open(DEFAULT_IMAGE).resize(THUMBNAIL_SIZE)

    # إضافة تدرج لوني
    gradient = Image.new("RGB", THUMBNAIL_SIZE, color=BACKGROUND_GRADIENT[0])
    draw_gradient = ImageDraw.Draw(gradient)
    for y in range(THUMBNAIL_SIZE[1]):
        r = int(BACKGROUND_GRADIENT[0][0] + (BACKGROUND_GRADIENT[1][0] - BACKGROUND_GRADIENT[0][0]) * (y / THUMBNAIL_SIZE[1]))
        g = int(BACKGROUND_GRADIENT[0][1] + (BACKGROUND_GRADIENT[1][1] - BACKGROUND_GRADIENT[0][1]) * (y / THUMBNAIL_SIZE[1]))
        b = int(BACKGROUND_GRADIENT[0][2] + (BACKGROUND_GRADIENT[1][2] - BACKGROUND_GRADIENT[0][2]) * (y / THUMBNAIL_SIZE[1]))
        draw_gradient.line([(0, y), (THUMBNAIL_SIZE[0], y)], fill=(r, g, b))

    blended = Image.blend(img, gradient, alpha=0.7)

    # إضافة النصوص
    draw = ImageDraw.Draw(blended)
    try:
        title_font = ImageFont.truetype(FONT_PATH_TITLE, TITLE_FONT_SIZE)
        subtitle_font = ImageFont.truetype(FONT_PATH_SUBTITLE, SUBTITLE_FONT_SIZE)
    except Exception as e:
        raise FileNotFoundError(f"خطأ في تحميل الخط: {e}")

    # إضافة شعار القناة
    logo_height = 0
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).resize((150, 150))
        blended.paste(logo, (20, 20), logo)
        logo_height = logo.size[1] + 30  # ارتفاع الشعار + مسافة إضافية

    # رسم العنوان الرئيسي
    title_bbox = title_font.getbbox(title)
    title_width, title_height = title_bbox[2] - title_bbox[0], title_bbox[3] - title_bbox[1]
    title_x = (THUMBNAIL_SIZE[0] - title_width) // 2
    title_y = logo_height + 20  # الموضع الرأسي (أسفل الشعار)
    draw.text((title_x, title_y), title, fill=TEXT_COLOR, font=title_font)

    # رسم النص الفرعي
    lines = subtitle.split("\n")
    subtitle_y = title_y + title_height + 30  # بدء النص الفرعي بعد العنوان الرئيسي بمسافة إضافية
    for line in lines:
        subtitle_bbox = subtitle_font.getbbox(line)
        subtitle_width, subtitle_height = subtitle_bbox[2] - subtitle_bbox[0], subtitle_bbox[3] - subtitle_bbox[1]
        subtitle_x = (THUMBNAIL_SIZE[0] - subtitle_width) // 2
        draw.text((subtitle_x, subtitle_y), line, fill=TEXT_COLOR, font=subtitle_font)
        subtitle_y += subtitle_height + 15  # زيادة المسافة بين الأسطر

    # إضافة الحدود
    draw.rectangle([0, 0, THUMBNAIL_SIZE[0] - 1, THUMBNAIL_SIZE[1] - 1], outline=BORDER_COLOR, width=10)

    # حفظ الصورة المصغرة
    blended.save(output_path)
    print(f"Advanced thumbnail saved as: {output_path}")

# استخدام الدالة
headlines = fetch_bbc_headlines()
create_advanced_thumbnail(
    title="Breaking News: Top 5 Stories",
    subtitle=headlines,
    output_path="bbc_youtube_thumbnail.png"
)
