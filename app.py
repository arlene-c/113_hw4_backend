"""
Flask Backend Service for Weather-Based Outfit Recommendations
Hosted on Render.com
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')
UNSPLASH_BASE_URL = 'https://api.unsplash.com/search/photos'


# Outfit recommendation logic
def get_outfit_recommendation(weather_data, preferences):
    """
    Generate outfit recommendations based on weather and user preferences
    """
    temp = weather_data['main']['temp']
    condition = weather_data['weather'][0]['main']
    mood = preferences.get('mood', 'casual')
    style = preferences.get('style_preference', 'casual')
    color_pref = preferences.get('color_preference', 'neutral')
    
    # Initialize outfit components
    outfit = {
        'top': '',
        'bottom': '',
        'outerwear': '',
        'footwear': '',
        'accessories': []
    }
    
    # Temperature-based recommendations
    if temp < 50:  # Cold
        outfit['top'] = 'Thermal long-sleeve shirt or sweater'
        outfit['bottom'] = 'Jeans or warm pants'
        outfit['outerwear'] = 'Heavy coat or parka'
        outfit['footwear'] = 'Boots'
        outfit['accessories'] = ['Scarf', 'Gloves', 'Beanie']
    elif temp < 65:  # Cool
        outfit['top'] = 'Long-sleeve shirt or light sweater'
        outfit['bottom'] = 'Chinos or jeans'
        outfit['outerwear'] = 'Light jacket or cardigan'
        outfit['footwear'] = 'Sneakers or loafers'
        outfit['accessories'] = ['Light scarf']
    elif temp < 75:  # Mild
        outfit['top'] = 'T-shirt or button-down shirt'
        outfit['bottom'] = 'Chinos or casual pants'
        outfit['outerwear'] = 'Optional light jacket'
        outfit['footwear'] = 'Sneakers or casual shoes'
        outfit['accessories'] = ['Sunglasses']
    elif temp < 85:  # Warm
        outfit['top'] = 'Breathable t-shirt or polo'
        outfit['bottom'] = 'Shorts or light pants'
        outfit['outerwear'] = 'None needed'
        outfit['footwear'] = 'Sandals or canvas shoes'
        outfit['accessories'] = ['Sunglasses', 'Hat']
    else:  # Hot
        outfit['top'] = 'Light, breathable tank or t-shirt'
        outfit['bottom'] = 'Shorts'
        outfit['outerwear'] = 'None'
        outfit['footwear'] = 'Sandals'
        outfit['accessories'] = ['Sunglasses', 'Sun hat', 'Sunscreen']
    
    # Weather condition adjustments
    if condition in ['Rain', 'Drizzle', 'Thunderstorm']:
        outfit['outerwear'] = 'Waterproof jacket or raincoat'
        outfit['accessories'].append('Umbrella')
        outfit['footwear'] = 'Waterproof boots or shoes'
    elif condition == 'Snow':
        outfit['outerwear'] = 'Insulated winter coat'
        outfit['accessories'].extend(['Warm hat', 'Gloves', 'Scarf'])
        outfit['footwear'] = 'Winter boots'
    
    # Mood-based adjustments
    if mood == 'professional':
        outfit['top'] = outfit['top'].replace('t-shirt', 'dress shirt').replace('T-shirt', 'Button-down shirt')
        outfit['bottom'] = 'Dress pants or skirt'
        outfit['footwear'] = 'Dress shoes or heels'
    elif mood == 'adventurous':
        outfit['footwear'] = 'Hiking boots or athletic shoes'
        outfit['accessories'].append('Backpack')
    elif mood == 'cozy':
        outfit['top'] = 'Soft sweater or hoodie'
        outfit['accessories'].append('Comfort scarf')
    
    # Color palette based on preference
    color_palettes = {
        'neutral': ['Navy', 'Beige', 'White', 'Gray'],
        'warm': ['Burgundy', 'Mustard', 'Rust', 'Cream'],
        'cool': ['Navy', 'Teal', 'Silver', 'Ice Blue'],
        'vibrant': ['Red', 'Emerald', 'Royal Blue', 'Yellow']
    }
    
    color_palette = color_palettes.get(color_pref, color_palettes['neutral'])
    
    # Style tips
    style_tips = generate_style_tips(temp, condition, mood)
    
    return {
        'outfit': outfit,
        'color_palette': color_palette,
        'style_tips': style_tips
    }


def generate_style_tips(temp, condition, mood):
    """Generate helpful styling tips"""
    tips = []
    
    if temp < 65:
        tips.append("Layer your clothing for temperature flexibility")
    
    if condition in ['Rain', 'Drizzle']:
        tips.append("Choose water-resistant fabrics")
    
    if temp > 75:
        tips.append("Opt for breathable, moisture-wicking materials")
    
    if mood == 'professional':
        tips.append("Keep accessories minimal and polished")
    
    return ' | '.join(tips) if tips else "Dress comfortably and confidently!"


def search_unsplash_image(query, orientation='portrait'):
    """
    Search Unsplash for outfit-related images
    Returns image URL or None if not found
    """
    if not UNSPLASH_ACCESS_KEY:
        return None
    
    try:
        params = {
            'query': query,
            'per_page': 1,
            'orientation': orientation,
            'content_filter': 'high'
        }
        headers = {
            'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
        }
        
        response = requests.get(UNSPLASH_BASE_URL, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                return {
                    'url': data['results'][0]['urls']['regular'],
                    'thumb': data['results'][0]['urls']['small'],
                    'photographer': data['results'][0]['user']['name'],
                    'photographer_url': data['results'][0]['user']['links']['html']
                }
        return None
    except Exception as e:
        print(f"Unsplash API error: {str(e)}")
        return None


def get_outfit_images(outfit):
    """
    Fetch Unsplash images for each outfit component
    """
    images = {}
    
    # Search queries for each outfit piece
    search_queries = {
        'top': f"{outfit['top']} fashion flatlay",
        'bottom': f"{outfit['bottom']} fashion flatlay",
        'outerwear': f"{outfit['outerwear']} fashion flatlay" if outfit['outerwear'] and outfit['outerwear'] != 'None needed' else None,
        'footwear': f"{outfit['footwear']} fashion flatlay",
        'outfit_complete': f"complete outfit flatlay fashion minimal aesthetic"
    }
    
    for key, query in search_queries.items():
        if query:
            image_data = search_unsplash_image(query)
            if image_data:
                images[key] = image_data
    
    return images


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'outfit-recommendation-service'
    }), 200


@app.route('/api/outfit-recommendation', methods=['POST'])
def outfit_recommendation():
    """
    Main endpoint for outfit recommendations
    Expects JSON body with: location, mood, style_preference, color_preference
    """
    try:
        # Parse request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'location' not in data:
            return jsonify({
                'error': 'Location is required'
            }), 400
        
        location = data['location']
        preferences = {
            'mood': data.get('mood', 'casual'),
            'style_preference': data.get('style_preference', 'casual'),
            'color_preference': data.get('color_preference', 'neutral')
        }
        
        # Fetch weather data from OpenWeather API
        weather_params = {
            'q': location,
            'appid': OPENWEATHER_API_KEY,
            'units': 'imperial'  # Use Fahrenheit
        }
        
        weather_response = requests.get(OPENWEATHER_BASE_URL, params=weather_params)
        
        if weather_response.status_code != 200:
            return jsonify({
                'error': 'Unable to fetch weather data. Please check the location.'
            }), 400
        
        weather_data = weather_response.json()
        
        # Extract relevant weather information
        weather_info = {
            'temperature': round(weather_data['main']['temp']),
            'condition': weather_data['weather'][0]['main'],
            'description': weather_data['weather'][0]['description'],
            'humidity': weather_data['main']['humidity'],
            'wind_speed': round(weather_data['wind']['speed'])
        }
        
        # Generate outfit recommendation
        recommendation = get_outfit_recommendation(weather_data, preferences)
        
        # Fetch outfit images from Unsplash
        outfit_images = get_outfit_images(recommendation['outfit'])
        
        # Combine response
        response = {
            'location': location,
            'weather': weather_info,
            'outfit': recommendation['outfit'],
            'outfit_images': outfit_images,
            'color_palette': recommendation['color_palette'],
            'style_tips': recommendation['style_tips']
        }
        
        return jsonify(response), 200
        
    except requests.RequestException as e:
        return jsonify({
            'error': 'Failed to connect to weather service'
        }), 503
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Use PORT from environment variable (Render provides this)
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)