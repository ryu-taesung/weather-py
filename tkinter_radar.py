import urllib.request
import xml.etree.ElementTree as ET
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import time

def get_radar_gif_url(zip_code):
    # Step 1: Get lat/lon from the zip code
    zip_lookup_url = f"https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList={zip_code}"
    with urllib.request.urlopen(zip_lookup_url) as response:
        xml_content = response.read().decode()

    # Parse the XML to extract lat/lon
    root = ET.fromstring(xml_content)
    lat_lon_list = root.find('.//latLonList').text

    # Step 2: Get the grid points using lat/lon
    grid_api_url = f"https://api.weather.gov/points/{lat_lon_list}"
    with urllib.request.urlopen(grid_api_url) as response:
        grid_json = json.loads(response.read().decode())
        radar_station = grid_json['properties']['radarStation']

    # Step 3: Construct the radar URL with a query string to prevent caching
    timestamp = int(time.time())
    radar_url = f"https://radar.weather.gov/ridge/standard/{radar_station}_loop.gif?{timestamp}"

    return radar_url

def fetch_and_display_gif():
    global frames, frame_index, frame_animation_id

    zip_code = zip_code_entry.get()
    radar_url = get_radar_gif_url(zip_code)
    with urllib.request.urlopen(radar_url) as response:
        image_data = response.read()

    # Use PIL to open the image
    image = Image.open(io.BytesIO(image_data))

    # If it's an animated GIF, handle the frames
    frames = []
    try:
        while True:
            frame = ImageTk.PhotoImage(image.copy())
            frames.append(frame)
            image.seek(len(frames))  # Seek to the next frame
    except EOFError:
        pass

    # Reset the frame index and start animation
    frame_index = 0
    animate_gif()

def animate_gif():
    global frames, frame_index, frame_animation_id

    if frames:
        frame = frames[frame_index]
        image_label.config(image=frame)
        image_label.image = frame
        frame_index = (frame_index + 1) % len(frames)
        frame_animation_id = root.after(200, animate_gif)

def update_gif_periodically():
    global frame_animation_id

    if frame_animation_id:
        root.after_cancel(frame_animation_id)
        frame_animation_id = None
    
    fetch_and_display_gif()
    root.after(180000, update_gif_periodically)  # Schedule the next update in 3 minutes (180,000 milliseconds)

# Set up the GUI
root = tk.Tk()
root.title("Weather Radar Viewer")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

zip_code_label = ttk.Label(frame, text="Enter ZIP code:")
zip_code_label.grid(row=0, column=0, padx=5, pady=5)

zip_code_entry = ttk.Entry(frame)
zip_code_entry.grid(row=0, column=1, padx=5, pady=5)

fetch_button = ttk.Button(frame, text="Fetch Radar", command=fetch_and_display_gif)
fetch_button.grid(row=0, column=2, padx=5, pady=5)

image_label = ttk.Label(frame)
image_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

# Global variables to manage frames and animation
frames = []
frame_index = 0
frame_animation_id = None

# Start the periodic update
root.after(180000, update_gif_periodically)  # Schedule the first update in 3 minutes

root.mainloop()

