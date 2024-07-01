import urllib.request
import xml.etree.ElementTree as ET
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import time

class WeatherRadarViewer(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Weather Radar Viewer")
        self.refresh_delay = 180000 # 3 minutes
        self.zip_code = None
        self.radar_url = None
        self.first_render = True

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        zip_code_label = ttk.Label(frame, text="Enter ZIP code:")
        zip_code_label.grid(row=0, column=0, padx=5, pady=5)

        self.zip_code_entry = ttk.Entry(frame)
        self.zip_code_entry.focus_set()
        self.zip_code_entry.bind('<Return>', lambda e: self.update_gif_periodically())
        self.zip_code_entry.bind('<KP_Enter>', lambda e: self.update_gif_periodically())
        self.zip_code_entry.grid(row=0, column=1, padx=5, pady=5)

        fetch_button = ttk.Button(frame, text="Fetch Radar", command=self.update_gif_periodically)
        fetch_button.grid(row=0, column=2, padx=5, pady=5)

        #style = ttk.Style(self)
        #style.theme_use('classic')
        self.image_label = ttk.Label(frame)
        self.image_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.N, tk.E, tk.S, tk.W))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

        self.frames = []
        self.frame_index = 0
        self.frame_animation_id = None
        self.image_label.bind("<Configure>", lambda event: self.handle_resize())
        self.resize_await = None
        self.update_gif_timer = None

    def handle_resize(self):
        #print("resize event")
        if self.resize_await:
            self.after_cancel(self.resize_await)
            self.resize_await = None
        self.resize_await = self.after(200, self.update_gif_periodically)

    def get_radar_gif_url(self, zip_code):
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

        self.zip_code = zip_code
        radar_url = f"https://radar.weather.gov/ridge/standard/{radar_station}_loop.gif"

        return radar_url

    def fetch_and_display_gif(self, *args, **kwargs):
        if self.radar_url is None or self.zip_code != self.zip_code_entry.get():
            zip_code = self.zip_code_entry.get()
            if zip_code is None or zip_code == '':
                return
            self.radar_url = self.get_radar_gif_url(zip_code)

        # Step 3: Construct the radar URL with a query string to prevent caching
        timestamp = int(time.time())
        no_cache_radar_url = f"{self.radar_url}?{timestamp}"
        print(f"grabbed new image: {no_cache_radar_url}")

        with urllib.request.urlopen(no_cache_radar_url) as response:
            image_data = response.read()

        # Use PIL to open the image
        image = Image.open(io.BytesIO(image_data))

        # If it's an animated GIF, handle the frames
        self.frames = []
        try:
            while True:
                frame = ImageTk.PhotoImage(image.copy())
                self.frames.append(frame)
                image.seek(len(self.frames))  # Seek to the next frame
        except EOFError:
            pass

        # Reset the frame index and start animation
        self.frame_index = 0
        self.scale_image()
        self.first_render = False
        self.after(200, self.animate_gif)

    def scale_image(self):
        if not self.first_render:
            self.update()
            # print(self.image_label.winfo_width(),self.image_label.winfo_height())
            new_width = self.image_label.winfo_width() - 4 # subtract the mystery 4 pixels so it doesn't keep expanding
            new_height = self.image_label.winfo_height() - 4
            for i in range(len(self.frames)):
                img = ImageTk.getimage(self.frames[i])
                resized_image = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.frames[i] = ImageTk.PhotoImage(image=resized_image)

    def animate_gif(self):
        if self.frames:
            frame = self.frames[self.frame_index]
            self.image_label.config(image=frame)
            self.image_label.image = frame
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.frame_animation_id = self.after(200, self.animate_gif)

    def update_gif_periodically(self):
        if self.frame_animation_id:
            self.after_cancel(self.frame_animation_id)
            self.frame_animation_id = None
        if self.update_gif_timer:
            self.after_cancel(self.update_gif_timer)
            self.update_gif_timer = None
        self.fetch_and_display_gif()
        self.update_gif_timer = self.after(self.refresh_delay, self.update_gif_periodically)

if __name__ == "__main__":
    root = WeatherRadarViewer()
    root.mainloop()

