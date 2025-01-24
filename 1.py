import feedparser
import re
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os

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

def create_audio(slides):
    """Converts each slide into an audio file and saves it in 'audio' folder."""
    if not os.path.exists("audio"):
        os.makedirs("audio") 
    for i, slide_text in enumerate(slides):
        tts = gTTS(text=slide_text, lang='en')  
        tts.save(f"audio/slide_{i}.mp3") 

def create_slides_images(slides):
    """Creates images for the slides with the news text and saves them in 'images' folder."""
    if not os.path.exists("images"):
        os.makedirs("images")
    for i, slide_text in enumerate(slides):
        img = Image.new('RGB', (1280, 720), color='white')
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Regular.ttf", 30)  
        d.text((100, 100), slide_text, font=font, fill=(0, 0, 0))
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
create_audio(slides)
create_slides_images(slides)
create_video(slides)
print("Video created successfully.")
