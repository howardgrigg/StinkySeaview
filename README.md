# Is Seaview Stinky?

A fun web application and API to check the odour status at Seaview Wastewater Treatment Plant based on real-time sensor data from Wellington Water.

## Features

### 🎨 Interactive Web Interface
*   **Hero Section**: Large, bold YES/NO answer with fun random sayings (60 different messages!)
*   **Historical Graphs**: Four interactive line charts showing ~7 days of odour data (readings every 30 minutes)
*   **Real-time Data**: Displays current readings, 60-minute averages, and wind direction for all 4 sensors
*   **Smart Scaling**: Charts automatically adjust to show data clearly with consistent Y-axis across all sensors
*   **Threshold Line**: Red dashed line at 30 ppb (community guideline) on all graphs
*   **Mobile Responsive**: Works great on phones, tablets, and desktop

### 🔔 API Endpoints
*   **`/api/stinky`**: Returns JSON with current stinky status: `{"stinky": true/false}`
*   **`/api/widget`**: Returns standalone HTML widget perfect for phone widgets and embedding

### 📊 Data Collection
*   **Auto-scraping**: Fetches data from Wellington Water every 15 minutes
*   **4 Sensors Monitored**:
  - #1 Seaview WWTP - South End
  - #2 Seaview WWTP - North End
  - #3 Meachen St
  - #4 Hutt Park
*   **Historical Data**: Captures ~336 data points per sensor (7 days)
*   **Persistent Storage**: Data saved locally in `./data` directory

### 🎯 Smart Threshold Detection
*   **Threshold**: 30 ppb (community guideline)
*   **Monitoring Window**: Checks last 30 minutes of readings
*   **Logic**: Triggers if ANY sensor's latest reading OR 60-minute average exceeds 30 ppb

### 🎲 Fun Random Sayings
*   30 sayings for "not stinky" (green) - e.g., "Sweet as, bro! No stink today"
*   30 sayings for "stinky" (red) - e.g., "Close your windows! The stink is coming"
*   Kiwi-flavored and community-friendly
*   Different message on each page refresh

## Setup and Running

### Prerequisites

*   Docker and Docker Compose installed on your system.

### Important Note for macOS Users

Port 5000 is commonly used by macOS Control Center (AirPlay Receiver). If you encounter a "port already in use" error, either:
- Disable AirPlay Receiver in System Settings > General > AirDrop & Handoff
- Use a different port (the docker-compose.yml uses port 5001 by default)

## Quick Start with Docker Compose (Recommended)

The easiest way to run the application:

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

The application will be accessible at `http://localhost:5001`.

**Benefits of using Docker Compose:**
- Data persistence: Sensor data is saved in the local `./data` directory
- Automatic restart: Container restarts automatically if it crashes
- Simple management: Easy to start, stop, and rebuild

## Alternative: Manual Docker Commands

### Build the Docker Image

Navigate to the `seaview-stinky` directory and build the Docker image:

```bash
docker build -t seaview-stinky .
```

### Run the Docker Container

Once the image is built, you can run the container. The application inside the container runs on port 5000 by default, but you can map this to any port on your host machine.

**To run on host port 5001 (recommended):**
```bash
docker run -p 5001:5000 --name seaview-stinky-app seaview-stinky
```
The application will be accessible at `http://localhost:5001`.

**To run on a different host port (e.g., 5005):**
```bash
docker run -p 5005:5000 --name seaview-stinky-app seaview-stinky
```
The application will then be accessible at `http://localhost:5005`.

### Stopping and Managing the Container

```bash
# Stop the container
docker stop seaview-stinky-app

# Start the container
docker start seaview-stinky-app

# Remove the container
docker rm seaview-stinky-app

# View logs
docker logs -f seaview-stinky-app
```

## Using the Application

### Web Interface

Open `http://localhost:5001` in your browser to see:

1. **Hero Section** (top 1/3):
   - Large YES/NO answer
   - Fun random saying
   - Updates on each refresh

2. **Graphs Section** (bottom 2/3):
   - 4 interactive line charts
   - Hover to see exact values
   - 7 days of historical data
   - Current conditions displayed

### API Endpoints

#### Status API
```bash
# Get current stinky status as JSON
curl http://localhost:5001/api/stinky

# Response
{"stinky": false}
```

#### Widget API
```bash
# Get standalone HTML widget
curl http://localhost:5001/api/widget

# Returns full HTML page with:
# - Hero section
# - Inline styles
# - Perfect for embedding in phone widgets
```

**Using the Widget on Your Phone:**

For iOS (Scriptable):
```javascript
let req = new Request("http://your-ip:5001/api/widget")
let html = await req.loadString()
let webview = new WebView()
await webview.loadHTML(html)
```

For Android (KWGT/Tasker):
- Add web view component
- Point to `http://your-ip:5001/api/widget`
- Set auto-refresh for live updates

**Note:** Replace `localhost` with your server's IP address or use a service like ngrok for external access.

## Configuration

### Thresholds and Timing

Edit `app/app.py` to adjust:

```python
STINKY_THRESHOLD = 30  # ppb - community guideline threshold
MONITORING_PERIOD_MINS = 30  # Check last 30 minutes of readings
```

### Customizing Sayings

Add your own fun sayings in `app/app.py`:

```python
NOT_STINKY_SAYINGS = [
    "Your custom saying here!",
    # ... add more
]

STINKY_SAYINGS = [
    "Your custom stinky warning here!",
    # ... add more
]
```

## Technical Details

### Tech Stack
- **Backend**: Flask (Python 3.9)
- **Web Scraping**: BeautifulSoup, Requests
- **Scheduling**: APScheduler
- **Frontend**: Vanilla JavaScript, Chart.js with annotation plugin
- **Server**: Gunicorn WSGI
- **Container**: Docker with docker-compose

### Data Structure

Sensor data is stored in `data/sensor_data.json`:

```json
{
  "sensors": [
    {
      "sensor_id": 1,
      "sensor_name": "#1 Seaview WWTP - South End",
      "latest_reading": 8.03,
      "timestamp": "2025-11-25T09:17:00",
      "average_60_minutes": 9.29,
      "wind_direction": "East-Northeast (69.0°)",
      "historical_timestamps": ["18 Nov 2025, 09:30", ...],
      "historical_readings": [7.98, 5.04, ...]
    }
  ],
  "scrape_time": "2025-11-24T20:49:46"
}
```

### Chart Behavior

- **Y-axis scaling**: `max(actual_max × 1.1, 35)` ensures:
  - Always 10% headroom above highest reading
  - Minimum of 35 ppb to keep threshold visible
  - All 4 charts use the same scale for comparison

- **Threshold line**: Red dashed line at 30 ppb (community guideline)

- **Update frequency**: Data refreshes every 15 minutes via background scheduler

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 5001
lsof -i :5001

# Use a different port
docker run -p 5002:5000 --name seaview-stinky-app seaview-stinky
```

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Data Not Updating
```bash
# Check if scraper is running
docker logs seaview-stinky-app | grep "Scraping"

# Manually trigger scrape
docker exec seaview-stinky-app python -c "from app import scrape_data; scrape_data()"
```

## Development

### Project Structure
```
seaview-stinky/
├── app/
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   └── templates/
│       └── index.html      # Main web interface
├── data/                   # Sensor data storage (auto-created)
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Docker Compose setup
└── README.md             # This file
```

### Making Changes

1. Edit files in `app/`
2. Rebuild container: `docker-compose up -d --build`
3. Check logs: `docker-compose logs -f`

## Credits

Data sourced from [Wellington Water](https://www.wellingtonwater.co.nz/your-water-2/topic/wastewater-2/wastewater-treatment-plants/seaview-wastewater-treatment-plant/seaview-wastewater-treatment-plant-odour-monitors/)

Built with ❤️ for the Seaview community
