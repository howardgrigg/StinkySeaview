import requests
from flask import Flask, render_template, jsonify
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
import json
import random

app = Flask(__name__)

# Fun sayings for when it's NOT stinky (green state)
NOT_STINKY_SAYINGS = [
    "All good! Fresh as!",
    "Sweet as, bro! No stink today",
    "Looking mint out there!",
    "She'll be right! Air's choice",
    "No dramas here, mate",
    "Fresh air for the win!",
    "Smelling like roses today",
    "Windows wide open weather!",
    "Safe to hang the washing out",
    "BBQ weather - no worries!",
    "Take a deep breath, it's beautiful",
    "Clean as a whistle!",
    "Good as gold today",
    "Perfect for a beach walk",
    "Not even a whiff!",
    "Breathe easy, Seaview!",
    "The nose knows - it's all good",
    "Fresh vibes only today",
    "No pong in sight!",
    "Air quality: chef's kiss",
    "Seaview smelling sweet!",
    "All clear for outdoor activities",
    "No need to hold your breath",
    "Plants are loving this air",
    "Open those windows with confidence",
    "Taking the scenic route today!",
    "Dogs approve of this air quality",
    "Washing dried smell-free today",
    "Your neighbours can't blame you today",
    "Even better than usual!"
]

# Fun sayings for when it's STINKY (red state)
STINKY_SAYINGS = [
    "Close your windows! The stink is coming",
    "Who let rip? That's a bad one today",
    "Pōhehe alert! Hold your nose",
    "Not ideal out there, mate",
    "Maybe skip the outdoor run today",
    "The plant's having a moment",
    "Bring the washing in!",
    "Time to stay indoors, folks",
    "Yep, you're smelling that right",
    "Trust your nose on this one",
    "Air freshener sales going up today",
    "Not the day for a picnic",
    "The whiff is real today",
    "Warning: nostril situation ahead",
    "Seaview's trademark scent is back",
    "Someone forgot to turn off the smell",
    "Peak pongy conditions detected",
    "Windows: closed. Fans: on.",
    "That's not your cooking, promise",
    "Even the seagulls are complaining",
    "Breathing through your mouth recommended",
    "The gift that keeps on giving",
    "Eau de Seaview in full force",
    "Check the wind direction and run",
    "Your nose isn't broken, it's real",
    "Not a great day for the washing line",
    "The pong is strong with this one",
    "Indoor activities highly recommended",
    "Think of it as character building",
    "At least we're all in this together"
]

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sensor_data.json')
STINKY_THRESHOLD = 30  # Community guideline threshold (ppb)
MONITORING_PERIOD_MINS = 30 # Check for readings above threshold in the last 30 minutes

def load_sensor_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {DATA_FILE}. Returning empty list.")
                return [] # Return empty list if file is malformed
    return [] # Return empty list if file doesn't exist

def save_sensor_data(data):
    # Ensure the data directory exists before trying to write the file
    data_dir = os.path.dirname(DATA_FILE)
    os.makedirs(data_dir, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_stinky():
    data = load_sensor_data()
    if not data or 'sensors' not in data or not data['sensors']:
        return False # No data, so not stinky

    now = datetime.now()
    # Check if the scraped data itself is too old to be relevant
    scrape_time = datetime.fromisoformat(data.get('scrape_time', datetime.min.isoformat()))
    if now - scrape_time > timedelta(minutes=MONITORING_PERIOD_MINS * 2): # Allow some buffer
        print("Warning: Scraped data is too old. Considering as not stinky.")
        return False

    time_threshold = now - timedelta(minutes=MONITORING_PERIOD_MINS)

    for sensor in data['sensors']:
        try:
            reading_time = datetime.fromisoformat(sensor.get('timestamp', datetime.min.isoformat()))
            latest_reading = sensor.get('latest_reading', 0)
            average_60_minutes = sensor.get('average_60_minutes', 0)

            # If any sensor has a recent reading above the threshold, it's stinky
            if reading_time > time_threshold:
                if latest_reading > STINKY_THRESHOLD or average_60_minutes > STINKY_THRESHOLD:
                    return True
        except ValueError:
            # Malformed data for one sensor shouldn't stop checks for others
            print(f"Error: Malformed data for sensor {sensor.get('sensor_id')}. Skipping.")
            continue
    
    return False

def scrape_data():
    print(f"[{datetime.now()}] Scraping data for all sensors...")
    all_sensor_data = []
    base_url = "https://www.wellingtonwater.co.nz/your-water-2/topic/wastewater-2/wastewater-treatment-plants/seaview-wastewater-treatment-plant/seaview-wastewater-treatment-plant-odour-monitors/showdata/?DataSource="

    for sensor_id in range(1, 5):
        url = f"{base_url}{sensor_id}"
        print(f"Scraping sensor {sensor_id} from {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            json_response = response.json()
            html_content = json_response.get("HTML", "")
            
            if not html_content:
                print(f"Error: 'HTML' content not found for sensor {sensor_id}.")
                continue

            soup = BeautifulSoup(html_content, 'html.parser')

            sensor_name_tag = soup.find('h3')
            sensor_name = sensor_name_tag.get_text(strip=True) if sensor_name_tag else f"Sensor {sensor_id}"

            # Extract historical data from canvas chart
            historical_timestamps = []
            historical_readings = []
            canvas = soup.find('canvas', id='hydrogenSulfideChart')
            if canvas:
                try:
                    import html as html_module
                    timestamps_raw = canvas.get('data-chart-formatted-reading-times', '')
                    readings_raw = canvas.get('data-dataset-one', '')
                    if timestamps_raw and readings_raw:
                        historical_timestamps = json.loads(html_module.unescape(timestamps_raw))
                        historical_readings = json.loads(html_module.unescape(readings_raw))
                except Exception as e:
                    print(f"Error extracting historical data for sensor {sensor_id}: {e}")
            
            latest_reading_value_tag = soup.find('h1', string=lambda text: text and 'ppb' in text.lower())
            latest_reading_value_str = latest_reading_value_tag.get_text(strip=True) if latest_reading_value_tag else "0 ppb"
            latest_reading = float(latest_reading_value_str.lower().replace(' ppb', ''))

            latest_reading_update_tag = soup.find('p', string=lambda text: text and 'latest reading' in text.lower())
            latest_reading_update_str = latest_reading_update_tag.get_text(strip=True) if latest_reading_update_tag else ""

            iso_timestamp = datetime.now().isoformat() # Default to now
            timestamp_part = ""
            if "updated at" in latest_reading_update_str.lower():
                # Extract timestamp from format: "Latest reading (updated at 25 Nov 2025, 09:07)"
                timestamp_part = latest_reading_update_str.split("(updated at")[1].strip(")").strip()

            if timestamp_part: # Only try to parse if the part is not empty
                try:
                    reading_time = datetime.strptime(timestamp_part, '%d %b %Y, %H:%M')
                    iso_timestamp = reading_time.isoformat()
                except ValueError:
                    print(f"Could not parse timestamp for sensor {sensor_id}: '{timestamp_part}'. Using current time.")
            
            # Find paragraph containing "Average last 60 minutes" and extract the value from the strong tag
            avg_60_mins = 0.0
            for p_tag in soup.find_all('p'):
                if 'average last 60 minutes' in p_tag.get_text().lower():
                    avg_60_mins_strong = p_tag.find('strong')
                    if avg_60_mins_strong:
                        avg_60_mins_str = avg_60_mins_strong.get_text(strip=True)
                        avg_60_mins = float(avg_60_mins_str.lower().replace(' ppb', '').strip())
                    break

            # Find paragraph containing "Wind direction" and extract the value from the strong tag
            wind_direction = "N/A"
            for p_tag in soup.find_all('p'):
                if 'wind direction' in p_tag.get_text().lower():
                    wind_direction_strong = p_tag.find('strong')
                    if wind_direction_strong:
                        wind_direction = wind_direction_strong.get_text(strip=True)
                    break

            all_sensor_data.append({
                'sensor_id': sensor_id,
                'sensor_name': sensor_name,
                'latest_reading': latest_reading,
                'timestamp': iso_timestamp,
                'average_60_minutes': avg_60_mins,
                'wind_direction': wind_direction,
                'historical_timestamps': historical_timestamps,
                'historical_readings': historical_readings,
            })
            
            print(f"Successfully scraped sensor {sensor_id}.")

        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Error fetching data for sensor {sensor_id}: {e}")
        except json.JSONDecodeError as e:
            print(f"[{datetime.now()}] Error decoding JSON for sensor {sensor_id}: {e}")
        except Exception as e:
            print(f"[{datetime.now()}] An unexpected error occurred during scraping for sensor {sensor_id}: {e}")

    # Add a top-level scrape time to the saved data for checking freshness
    final_data = {
        "sensors": all_sensor_data,
        "scrape_time": datetime.now().isoformat()
    }
    
    save_sensor_data(final_data)
    print(f"[{datetime.now()}] Completed scraping for all sensors. Total readings: {len(all_sensor_data)}.")

@app.route('/')
def index():
    stinky_status = is_stinky()
    sensor_data = load_sensor_data() # Load the comprehensive data

    # Pick a random saying based on stinky status
    if stinky_status:
        saying = random.choice(STINKY_SAYINGS)
    else:
        saying = random.choice(NOT_STINKY_SAYINGS)

    # Pass all relevant data to the template
    return render_template('index.html', stinky=stinky_status, sensor_data=sensor_data, saying=saying)

@app.route('/api/stinky')
def api_stinky():
    stinky_status = is_stinky()
    sensor_data = load_sensor_data()

    # Pick a random saying based on stinky status
    if stinky_status:
        message = random.choice(STINKY_SAYINGS)
    else:
        message = random.choice(NOT_STINKY_SAYINGS)

    # Get last update time
    last_updated = None
    if sensor_data and sensor_data.get('scrape_time'):
        last_updated = sensor_data['scrape_time']

    return jsonify(stinky=stinky_status, message=message, last_updated=last_updated)

@app.route('/api/widget')
def api_widget():
    stinky_status = is_stinky()
    sensor_data = load_sensor_data()

    # Pick a random saying based on stinky status
    if stinky_status:
        saying = random.choice(STINKY_SAYINGS)
    else:
        saying = random.choice(NOT_STINKY_SAYINGS)

    # Get last update time
    last_update = "Unknown"
    if sensor_data and sensor_data.get('scrape_time'):
        last_update = sensor_data['scrape_time'].replace('T', ' ')[:19]

    # Background color based on status
    bg_color = '#d9534f' if stinky_status else '#5cb85c'
    answer_text = 'YES 😷' if stinky_status else 'NO ✅'

    # Return minimal HTML with inline styles for widget embedding
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seaview Stinky Widget</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: {bg_color};
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            text-align: center;
        }}
        .title {{
            font-size: 1.2rem;
            font-weight: 500;
            margin-bottom: 1rem;
            opacity: 0.95;
        }}
        .answer {{
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 1rem;
            line-height: 1;
        }}
        .saying {{
            font-size: 1.5rem;
            font-weight: 500;
            line-height: 1.3;
            margin-bottom: 1.5rem;
        }}
        .update {{
            font-size: 0.85rem;
            opacity: 0.9;
            margin-top: auto;
        }}
    </style>
</head>
<body>
    <div class="title">Is Seaview Stinky?</div>
    <div class="answer">{answer_text}</div>
    <div class="saying">{saying}</div>
    <div class="update">Updated: {last_update}</div>
</body>
</html>"""

    return html

# Schedule data scraping
scheduler = BackgroundScheduler()
# Run scrape_data immediately on startup, then every 15 minutes
scheduler.add_job(func=scrape_data, trigger="interval", minutes=15, id='scrape_job', next_run_time=datetime.now())
scheduler.start()


if __name__ == '__main__':
    # This block now only runs for direct execution, not with Gunicorn
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
