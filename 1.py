import feedparser
import requests
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

# إعدادات
PEXELS_API_KEY = "PCwqJJH8epOMqmKdeGzBPIgzk1npSkI39arGmpnEdshOewaUeRyCuyXY"
VIDEO_SIZE = (1280, 720)
FONT_PATH = "/content/TAHAR/3.ttf"  # استبدل بمسار الخط
FONT_SIZE = 55
TEXT_COLOR = "white"
DEFAULT_IMAGE = "/content/TAHAR/default_image.jpg"  # صورة افتراضية
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
def create_slide_images(news):
    if not os.path.exists("images"):
        os.makedirs("images")
    slide_images = []

    for i, item in enumerate(news):
        # تحميل الصورة الخلفية
        if item["image_url"]:
            try:
                response = requests.get(item["image_url"])
                img = Image.open(BytesIO(response.content)).convert("RGB")
                img = img.resize(VIDEO_SIZE)
            except Exception:
                img = Image.open(DEFAULT_IMAGE).resize(VIDEO_SIZE)
        else:
            img = Image.open(DEFAULT_IMAGE).resize(VIDEO_SIZE)

        # إضافة طبقة داكنة لتقليل الإضاءة
        overlay = Image.new("RGB", VIDEO_SIZE, color=(0, 0, 0))
        blended = Image.blend(img, overlay, alpha=0.8)

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
        y = (VIDEO_SIZE[1] - total_text_height) // 2

        for line in lines:
            text_width = draw.textlength(line, font=font)
            x = (VIDEO_SIZE[0] - text_width) // 2
            draw.text((x, y), line, fill=TEXT_COLOR, font=font)
            y += FONT_SIZE

        img_path = f"images/slide_{i}.png"
        blended.save(img_path)
        slide_images.append(img_path)

    return slide_images

# إنشاء الفيديو
def create_video(images, audio_files):
    clips = []
    for i, img_path in enumerate(images):
        audio_clip = AudioFileClip(audio_files[i])
        image_clip = ImageClip(img_path).set_duration(audio_clip.duration)
        image_clip = image_clip.set_audio(audio_clip)
        clips.append(image_clip)
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile("news_video.mp4", fps=1)

# تنفيذ البرنامج
rss_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
news = fetch_news(rss_url)
audio_files = create_audio(news)
images = create_slide_images(news)
create_video(images, audio_files)
print("Video created successfully.")
