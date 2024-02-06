import json
import re
import datetime as dt
import urllib.request
from collections import defaultdict
from typing import Dict, Any

# Constants
API_URL = 'https://api.weather.gov/gridpoints/CTP/71,63/forecast'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'

# Compile regex pattern for efficiency
TEMP_PATTERN = re.compile(r'(?:(?:high near)|(?:low around))\s+(-?\d{1,3})[\.,]')


def fetch_weather_data(url: str) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url) as req:
            data = req.read()
            return json.loads(data)
    except urllib.error.HTTPError as e:
        print("Error: weather.gov API currently unavailable.")
        print("Status:", e.code)
        print("Reason:", e.reason)
        #raise
    except urllib.error.URLError as e:
        print("URL Error:", e.reason)
        #raise


def process_weather_data(api_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    periods = defaultdict(lambda: {"day_of_week": None, 'high_temp': None, 'low_temp': None, 'day_forecast': None, 'night_forecast': None})
    for period in api_data['properties']['periods']:
        forecast = period['detailedForecast']
        match = TEMP_PATTERN.search(forecast.lower())
        period_date = period['startTime'].split('T')[0]
        period_time_start = period['startTime'].split('T')[1]
        before_dawn = True if int(period_time_start[0:2]) < 6 else False

        if before_dawn:
            current_date = dt.datetime.strptime(period_date, DATE_FORMAT)
            new_date = current_date - dt.timedelta(days=1)
            period_date = new_date.strftime(DATE_FORMAT)

        periods[period_date]['day_of_week'] = get_day_of_week(period_date)

        if match:
            if 'high' in match.group(0):
                periods[period_date]['high_temp'] = match.group(1)
                periods[period_date]['day_forecast'] = period['shortForecast']
            if 'low' in match.group(0):
                periods[period_date]['low_temp'] = match.group(1)
                periods[period_date]['night_forecast'] = period['shortForecast']

    return periods


def get_day_of_week(date_string: str) -> str:
    date_object = dt.datetime.strptime(date_string, DATE_FORMAT)
    return date_object.strftime("%A")[0:3]


def display_weather_report(periods: Dict[str, Dict[str, str]]):
    header = f"{'Date':<12} {'Day':<4} {'High':<4} {'Low':<4} {'Day Forecast':<49} {'Night Forecast':<49}"
    divider = "-" * (len(header) + 4)
    print(header)
    print(divider)
    for k, v in periods.items():
        print(f"{k:<12} {v['day_of_week']:<4} {v['high_temp'] if v['high_temp'] is not None else 'N/A':<4} {v['low_temp'] if v['low_temp'] is not None else 'N/A':<4} {v['day_forecast'][0:49] if v['day_forecast'] is not None else 'N/A':<49} {v['night_forecast'][0:49] if v['night_forecast'] is not None else 'N/A':<49}")


if __name__ == '__main__':
    api_data = fetch_weather_data(API_URL)
    periods = process_weather_data(api_data)
    display_weather_report(periods)
