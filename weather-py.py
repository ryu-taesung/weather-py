import json
import re
import datetime as dt
from collections import defaultdict
import urllib.request

api_data = {}

req = urllib.request.urlopen('https://api.weather.gov/gridpoints/CTP/71,63/forecast')
data = req.read()
#print(data)
#encoding = req.info().get_content_charset('utf-8')
api_data = json.loads(data) #data.decode(encoding))

print(api_data['properties']['updated'])


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

# for k,v in periods.items():
#     print(k, v['high_temp'], v['low_temp'])

print(f"{'Date':<12} {'Day':<10} {'High Temp':<10} {'Low Temp':<10} {'Day Forecast':<20} {'Night Forecast':<20}")
print("-" * 85)
for k,v in periods.items():
    print(f"{k:<12} {v['day_of_week']:<10} {v['high_temp'] if v['high_temp'] is not None else 'N/A':<10} {v['low_temp'] if v['low_temp'] is not None else 'N/A':<10} {v['day_forecast'] if v['day_forecast'] is not None else 'N/A':<20} {v['night_forecast'] if v['night_forecast'] is not None else 'N/A':<20}")