import json
import re
import datetime as dt
from collections import defaultdict
import urllib.request

api_data = {}

req = urllib.request.urlopen('https://api.weather.gov/gridpoints/CTP/71,63/forecast')
if req.status != 200:
    print("weather.gov API currently unavailable.")
    print(req.status)
    print(req.reason)
    exit()
data = req.read()
api_data = json.loads(data)

# with open('sample.json', encoding="utf-8") as f:
#     raw_data = f.read();
#     api_data = json.loads(raw_data);

def get_day_of_week(date_string):
    date_object = dt.datetime.strptime(date_string, '%Y-%m-%d')
    return date_object.strftime("%A")

periods = defaultdict(lambda: {"day_of_week": None, 'high_temp': None, 'low_temp': None, 'day_forecast': None, 'night_forecast': None})
for period in api_data['properties']['periods']:
    forecast = period['detailedForecast']
    match = re.search(r'(?:(?:high near)|(?:low around))\s+(\d{2,3}).', forecast)
    period_date = period['startTime'].split('T')[0]
    periods[period_date]
    periods[period_date]['day_of_week'] = get_day_of_week(period_date)

    if match:
        #print(period_date, match.group(0))
        if 'high' in match.group(0):
            periods[period_date]['high_temp'] = match.group(1)
            periods[period_date]['day_forecast'] = period['shortForecast']
        if 'low' in match.group(0):
            periods[period_date]['low_temp'] = match.group(1)
            periods[period_date]['night_forecast'] = period['shortForecast']

print(f"{'Date':<12} {'Day':<10} {'High Temp':<10} {'Low Temp':<10} {'Day Forecast':<40} {'Night Forecast':<40}")
print("-" * (122 + 6))
for k,v in periods.items():
    print(f"{k:<12} {v['day_of_week']:<10} {v['high_temp'] if v['high_temp'] is not None else 'N/A':<10} {v['low_temp'] if v['low_temp'] is not None else 'N/A':<10} {v['day_forecast'][0:40] if v['day_forecast'] is not None else 'N/A':<40} {v['night_forecast'][0:40] if v['night_forecast'] is not None else 'N/A':<40}")