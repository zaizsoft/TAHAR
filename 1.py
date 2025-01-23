import requests
from bs4 import BeautifulSoup
import feedparser
from gtts import gTTS
from moviepy.editor import *
import os
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
import re

# 1. Fetch the latest news from BBC News
def fetch_news():
    feed_url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    feed = feedparser.parse(feed_url)
    news_content = ""
    for entry in feed.entries[:1]:  # Get the first news article
        title = entry.title
        link = entry.link
        # Fetch the full article content
        response = requests.get(link)
        soup = BeautifulSoup(response.content, "html.parser")
        article_content = soup.find("article").get_text()  # Extract article text
        # Add title to news_content
        news_content += f"Welcome to Global Insight News. Today's top stories: {title}\n\n"
        # Split article_content into paragraphs
        paragraphs = article_content.split('\n\n')
        # Add first 5 paragraphs to news_content
        news_content += '\n\n'.join(paragraphs[:5]) + '\n\n'
    return news_content

# 2. Convert the news into an audio file and split it
def create_audio(news_content):
    # Generate individual audio for each slide's text
    slides_text = split_text_into_slides(news_content)
    for i, slide_text in enumerate(slides_text):
        # Skip empty slides to avoid the AssertionError
        if slide_text.strip():
            slide_audio = gTTS(text=slide_text, lang="en", slow=False)
            slide_audio.save(f"slide_{i}.mp3")

# 3. Create image slides from the news content
def create_slides(news_content):
    # Function to get text dimensions
    get_text_dims = lambda txt, fnt: (lambda bbox: (bbox[2] - bbox[0], bbox[3] - bbox[1]))(ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), txt, font=fnt))

    slides_text = split_text_into_slides(news_content)
    img_dims = (1280, 720)

    for idx, slide_text in enumerate(slides_text):
        # Create the slide
        img = Image.new("RGB", img_dims, color="white")
        d = ImageDraw.Draw(img)
        fnt = ImageFont.truetype("/content/TAHAR/3.ttf", 30)

        # Write the lines on the slide, limiting to 8 words per line
        y_pos = 100  # Start from the top of the slide with some margin
        lines = slide_text.split('\n')  # Get lines from slide_text
        for line in lines:
            words = line.split()
            wrapped_lines = []
            for i in range(0, len(words), 11):
                wrapped_lines.append(" ".join(words[i:i + 11]))

            for wrapped_line in wrapped_lines:
                txt_w, txt_h = get_text_dims(wrapped_line, fnt)
                x_pos = (img_dims[0] - txt_w) // 2
                d.text((x_pos, y_pos), wrapped_line, font=fnt, fill=(0, 0, 0))
                y_pos += txt_h + 20  # Add spacing between lines

        img.save(f"slide_{idx}.png")

# Helper function to split text into slides based on sentences
def split_text_into_slides(news_content):
    # Split the text into sentences using regex
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', news_content)

    # Group sentences into slides, aiming for 5 lines per slide
    slides_text = []
    current_slide = ""
    line_count = 0
    for sentence in sentences:
        current_slide += sentence
        line_count += 1
        if line_count >= 1 or sentence[-1] in ['.', '!', '?']:  # Create new slide after 3 lines or at end of sentence
            slides_text.append(current_slide)
            current_slide = ""
            line_count = 0

    # Add any remaining text to a final slide
    if current_slide:
        slides_text.append(current_slide)

    return slides_text

# 4. Combine the audio and images to create a video news presentation
def create_video():
    # Load audio and images
    image_clips = []
    for i in range(len(os.listdir('.')) - 1):
        if f"slide_{i}.png" in os.listdir('.'):
            try:  # Handle potential file not found errors
                audio_clip = AudioFileClip(f"slide_{i}.mp3")  # Use slide audio
                image_clip = ImageClip(f"slide_{i}.png").set_duration(audio_clip.duration)
                image_clip = image_clip.set_audio(audio_clip)
                image_clips.append(image_clip)
            except OSError as e:
                print(f"Error processing slide_{i}.mp3: {e}")  # Print error and continue

    # Concatenate images and add audio
    video = concatenate_videoclips(image_clips, method="compose")
    video.write_videofile("news_presentation.mp4", fps=1)  # Adjust fps as needed

if __name__ == "__main__":
    news_content = fetch_news()
    create_audio(news_content)
    create_slides(news_content)
    create_video()
