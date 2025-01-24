import feedparser
import re
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def fetch_news(rss_url):
    """Fetches news content from an RSS feed."""
    feed = feedparser.parse(rss_url)
    news_content = ""
    for entry in feed.entries:
        news_content += entry.title + ". " + entry.description
    return news_content

def split_into_slides(text):
    """Splits the text into slides based on sentences and line breaks,
    ensuring each line has 7 words or less."""
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    slides = []
    current_slide = ""
    for sentence in sentences:
        words = sentence.split()
        # Split sentence into lines with max 7 words:
        lines = [' '.join(words[i:i + 7]) for i in range(0, len(words), 7)] 
        current_slide += '\n'.join(lines) + '\n' # Add lines to slide with line breaks
        
        # Check if the slide is too long (more than 8 lines):
        if current_slide.count('\n') >= 8:  
            slides.append(current_slide.strip())
            current_slide = ""
            
    slides.append(current_slide.strip())  # Add the last slide
    slides = [slide for slide in slides if slide]  
    return slides

def add_intro_and_outro(slides):
    """Adds an introduction and conclusion slide."""
    # مقدمة الفيديو مع التاريخ الحالي
    today = datetime.now().strftime("%Y-%m-%d")
    intro_slide = f"Welcome to Global Insight News.\nToday's top stories:\n{today}"
    slides.insert(0, intro_slide)
    
    # النص الختامي
    outro_slide = "don't forget to subscribe to the channel"
    slides.append(outro_slide)
    return slides

def create_audio(slides):
    """Converts each slide into an audio file and saves it in 'audio' folder."""
    if not os.path.exists("audio"):
        os.makedirs("audio") 
    for i, slide_text in enumerate(slides):
        tts = gTTS(text=slide_text, lang='en' if i != len(slides) - 1 else 'en')  # اللغة الإنجليزية للمقدمة والنصوص، والعربية للنهاية
        tts.save(f"audio/slide_{i}.mp3") 

def create_slides_images(slides):
    """Creates images for the slides with the news text and saves them in 'images' folder."""
    if not os.path.exists("images"):
        os.makedirs("images")
    for i, slide_text in enumerate(slides):
        # إنشاء صورة فارغة مع خلفية بيضاء
        img = Image.new('RGB', (1280, 720), color='white')
        d = ImageDraw.Draw(img)
        
        # استخدام الخط المخصص
        font_path = "/content/TAHAR/3.ttf"  # تحديد مسار الخط
        font_size = 38
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"Error loading font: {e}")
            return
        
        # حساب أبعاد النص باستخدام دالة multiline_textbbox
        text_bbox = d.multiline_textbbox((0, 0), slide_text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        
        # حساب إحداثيات توسيط النص
        position = ((1280 - text_width) // 2, (720 - text_height) // 2)
        
        # رسم النص في الصورة مع تحديد المحاذاة والتعبئة
        d.multiline_text(position, slide_text, font=font, fill="black", align="center")
        
        # حفظ الصورة
        img.save(f"images/slide_{i}.png")  

def create_video(slides):
    """Creates a video from the images and audio."""
    image_clips = []
    for i in range(len(slides)):
        audio_clip = AudioFileClip(f"audio/slide_{i}.mp3") 
        image_clip = ImageClip(f"images/slide_{i}.png").set_duration(audio_clip.duration)
        image_clip = image_clip.set_audio(audio_clip)
        image_clips.append(image_clip)
    video = concatenate_videoclips(image_clips, method="compose")
    video.write_videofile("news_video.mp4", fps=1)

# Main execution
rss_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
news_content = fetch_news(rss_url)
slides = split_into_slides(news_content)
slides = add_intro_and_outro(slides)  # إضافة المقدمة والنهاية
create_audio(slides)
create_slides_images(slides)
create_video(slides)
print("Video created successfully.")
