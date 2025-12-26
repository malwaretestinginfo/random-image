import random
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

def get_google_images(query):
    """
    Search Google Images for the query and return a list of image URLs.
    This uses a basic scraper approach looking for thumbnails which is more robust against blocking than trying to parse the JS blobs.
    """
    url = f"https://www.google.com/search?tbm=isch&q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        images = []
        
        # Look for image tags. 
        # In the static/initial HTML load, Google often puts thumbnails in img tags.
        for img in soup.find_all('img'):
            src = img.get('src')
            # Filter out small UI icons or the Google logo if possible, 
            # though often gstatic images are the results.
            if src and src.startswith('http') and 'google' not in src: 
                # Some heuristics to skip branding if possible, but 'encrypted-tbn0' urls are good.
                pass
            
            if src and (src.startswith('http') or src.startswith('data:image')):
                images.append(src)
        
        # The first image is often the logo. Let's skip the first one if we have many.
        if len(images) > 1:
            return images[1:]
        return images
        
    except Exception as e:
        print(f"Error scraping images for '{query}': {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form.get('input_text')
        if not text or not text.strip():
            return render_template('index.html', error="Bitte geben Sie einen Text ein.")
        
        # Clean and split text
        words = text.split()
        
        # Need at least 1 word to pick from
        if not words:
             return render_template('index.html', error="Keine Wörter gefunden.")

        # Logic: Pick 3 random words from the text
        # If fewer than 3 words, reuse them.
        selected_words = []
        if len(words) >= 3:
            selected_words = random.sample(words, 3)
        else:
            # If we have 1 word, pick it 3 times? or just pick randomly 3 times
            for _ in range(3):
                selected_words.append(random.choice(words))
        
        final_images = []
        for word in selected_words:
            found_urls = get_google_images(word)
            
            # Use placeholder if empty
            picked_url = "https://via.placeholder.com/400x300?text=Bild+nicht+gefunden"
            
            if found_urls:
                # "aus den Top 10 Bildern" -> slice first 10
                top_10 = found_urls[:10]
                if top_10:
                    picked_url = random.choice(top_10)
            
            final_images.append(picked_url)
            
        return render_template('result.html', images=final_images, original_text=text)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
