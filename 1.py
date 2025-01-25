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
VIDEO_SIZE = (1280, 720)
FONT_PATH = "/content/TAHAR/3.ttf"  # استبدل بمسار الخط
FONT_SIZE = 61
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
        y = (VIDEO_SIZE[1] - total_text_height) // 2

        for line in lines:
            text_width = draw.textlength(line, font=font)
            x = (VIDEO_SIZE[0] - text_width) // 2
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
def create_intro_slide():
    text = f"Welcome to Global Insight News\nToday's top stories for {datetime.now().strftime('%B %d, %Y')}."
    audio_path = "audio/intro.mp3"
    img_path = "images/intro.png"
    create_text_slide(text, audio_path, img_path)
    return img_path, audio_path

# إنشاء خاتمة الفيديو
def create_outro_slide():
    text = "Thank you for watching! Subscribe for more updates."
    audio_path = "audio/outro.mp3"
    img_path = "images/outro.png"
    create_text_slide(text, audio_path, img_path)
    return img_path, audio_path

# إنشاء صورة مع نصوص
def create_text_slide(text, audio_path, img_path):
    tts = gTTS(text=text, lang='en')
    tts.save(audio_path)

    img = Image.new("RGB", VIDEO_SIZE, color=(0, 0, 0))
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
    y = (VIDEO_SIZE[1] - total_text_height) // 2

    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (VIDEO_SIZE[0] - text_width) // 2
        draw.text((x, y), line, fill=TEXT_COLOR, font=font)
        y += FONT_SIZE

    # إضافة شعار القناة
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).resize((150, 150))
        img.paste(logo, (20, 20), logo)

    img.save(img_path)

# إنشاء الفيديو النهائي
def create_video_with_intro_outro(images, audio_files, first_news_title):
    intro_img, intro_audio = create_intro_slide()
    outro_img, outro_audio = create_outro_slide()

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

    # تجميع الفيديو بدون موسيقى خلفية
    video = concatenate_videoclips(clips, method="compose")

    sanitized_title = "".join(c for c in first_news_title if c.isalnum() or c in " _-").strip()
    video_filename = f"{sanitized_title}.mp4"

    video.write_videofile(video_filename, fps=1, codec="libx264", audio_codec="aac")
    print(f"Video saved as: {video_filename}")

# تنفيذ البرنامج
rss_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
news = fetch_news(rss_url)
audio_files = create_audio(news)
images = create_slide_images(news)
if news:
    create_video_with_intro_outro(images, audio_files, news[0]["title"])
else:
    print("No news found to create video.")
