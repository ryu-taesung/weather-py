import json
import re
import datetime as dt
from collections import defaultdict
import urllib.request

api_data = {}

def get_day_of_week(date_string):
    date_object = dt.datetime.strptime(date_string, '%Y-%m-%d')
    return date_object.strftime("%A")[0:3]

try:
    with urllib.request.urlopen('https://api.weather.gov/gridpoints/CTP/71,63/forecast') as req:
        data = req.read()
        # with open('forecast_overnight.json') as f:
        #     data = f.read()
        api_data = json.loads(data)
        periods = defaultdict(lambda: {"day_of_week": None, 'high_temp': None, 'low_temp': None, 'day_forecast': None, 'night_forecast': None})
    for period in api_data['properties']['periods']:
        forecast = period['detailedForecast']
        match = re.search(r'(?:(?:high near)|(?:low around))\s+(-?\d{1,3})[\.,]', forecast.lower())
        period_date = period['startTime'].split('T')[0]
        period_time_start = period['startTime'].split('T')[1]
        before_dawn = period_time_start.startswith('00')
        if before_dawn:
            current_date = dt.datetime.strptime(period_date, '%Y-%m-%d')
            new_date = current_date - dt.timedelta(days=1)
            period_date = new_date.strftime('%Y-%m-%d')
        
        periods[period_date]['day_of_week'] = get_day_of_week(period_date)

        if match:
            #print(period_date, match.group(0))
            if 'high' in match.group(0):
                periods[period_date]['high_temp'] = match.group(1)
                periods[period_date]['day_forecast'] = period['shortForecast']
            if 'low' in match.group(0):
                periods[period_date]['low_temp'] = match.group(1)
                periods[period_date]['night_forecast'] = period['shortForecast']

    print(f"{'Date':<12} {'Day':<4} {'High':<4} {'Low':<4} {'Day Forecast':<49} {'Night Forecast':<49}")
    print("-" * (122 + 6))
    for k,v in periods.items():
        print(f"{k:<12} {v['day_of_week']:<4} {v['high_temp'] if v['high_temp'] is not None else 'N/A':<4} {v['low_temp'] if v['low_temp'] is not None else 'N/A':<4} {v['day_forecast'][0:49] if v['day_forecast'] is not None else 'N/A':<49} {v['night_forecast'][0:49] if v['night_forecast'] is not None else 'N/A':<49}")
except urllib.error.HTTPError as e:
    # Handle HTTP errors here
    print("Error: weather.gov API currently unavailable.")
    print("Status:", e.code)
    print("Reason:", e.reason)
except urllib.error.URLError as e:
    # This catches other URL errors (like network issues)
    print("URL Error:", e.reason)
    
