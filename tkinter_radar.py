import urllib.request
import xml.etree.ElementTree as ET
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import time
import json
import logging
import argparse

logger = logging.getLogger(__name__)

class WeatherRadarViewer(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Weather Radar Viewer")
        self.refresh_delay = 180000 # 3 minutes
        self.zip_code = None
        self.radar_url = None
        self.first_render = True
        self.populate_radar_urls()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        zip_code_label = ttk.Label(frame, text="Enter ZIP code:")
        zip_code_label.grid(row=0, column=0, padx=5, pady=5)

        self.zip_code_entry = ttk.Entry(frame, width=5)
        self.zip_code_entry.focus_set()
        self.zip_code_entry.bind('<Return>', lambda e: self.update_gif_periodically(force=True))
        self.zip_code_entry.bind('<KP_Enter>', lambda e: self.update_gif_periodically(force=True))
        self.zip_code_entry.grid(row=0, column=1, padx=5, pady=5)

        fetch_button = ttk.Button(frame, text="Fetch Radar", command=lambda: self.update_gif_periodically(force=True))
        fetch_button.grid(row=0, column=2, padx=5, pady=5)

        region_label = ttk.Label(frame, text="Or Select Region:")
        region_label.grid(row=0, column=3, padx=5, pady=5)
        self.selected_region = tk.StringVar(self)
        self.selected_region.set('')
        self.selected_region.trace('w', self.updated_region)
        region_dropdown = tk.OptionMenu(frame, self.selected_region, *self.radar_regions)
        region_dropdown.grid(row=0, column=4, padx=5, pady=5)

        #style = ttk.Style(self)
        #style.theme_use('classic')
        self.image_label = ttk.Label(frame, borderwidth=0, border=0)
        self.image_label.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky=(tk.N, tk.E, tk.S, tk.W))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(4, weight=1)

        self.frames = []
        self.frame_index = 0
        self.frame_animation_id = None
        self.image_label.bind("<Configure>", lambda event: self.handle_resize())
        self.image_label.bind('<Double-Button-1>', self.restore_image_dimensions)
        self.resize_await = None
        self.update_gif_timer = None
        self.settings_loaded = False
        self.load_settings()

    def updated_region(self, *args, **kwargs):
        if self.selected_region.get() != '':
            self.radar_url = self.radar_urls[self.radar_regions.index(self.selected_region.get())]
        else:
            self.radar_url = None 
        if self.settings_loaded and self.selected_region.get() != '':
            self.update_gif_periodically()

    def restore_image_dimensions(self, *args, **kwargs):
        self.first_render = True
        self.update_gif_periodically()
        self.geometry("")

    def load_settings(self):
        try:
            with open('settings.json', mode='r', encoding='utf-8') as file:
                settings = json.loads(file.read())
                self.selected_region.set(settings['regional_selection'])
                self.zip_code = settings['zip_code'] or ''
                self.zip_code_entry.delete(0,tk.END)
                self.zip_code_entry.insert(0,self.zip_code)
                self.radar_url = settings['radar_url']
        except:
            logging.debug("error loading settings.json")
        self.settings_loaded = True
        self.update_gif_periodically()

    def save_settings(self):
        with open('settings.json', mode='w', encoding='utf-8') as file:
            settings = {
                'zip_code': self.zip_code,
                'radar_url': self.radar_url,
                'regional_selection': self.selected_region.get(),
            }
            file.write(json.dumps(settings))

    def handle_resize(self):
        logging.debug("resize event")
        if self.resize_await:
            self.after_cancel(self.resize_await)
            self.resize_await = None
        self.resize_await = self.after(200, self.scale_image)

    def get_radar_gif_url(self, zip_code):
        logging.debug('zip lookup')
        if zip_code is None or zip_code == '':
            logging.debug('no zip')
            return ''

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
        force_lookup = kwargs.get('force')
        if self.radar_url is None or self.zip_code != self.zip_code_entry.get() or self.selected_region.get() == '':
            zip_code = self.zip_code_entry.get()
            if zip_code is None or zip_code == '' and self.selected_region.get() == '' :
                logging.debug('early return')
                return
            if zip_code is not None and force_lookup:
                self.radar_url = self.get_radar_gif_url(zip_code)
                self.zip_code = zip_code

        # Step 3: Construct the radar URL with a query string to prevent caching
        timestamp = int(time.time())
        no_cache_radar_url = f"{self.radar_url}?{timestamp}"
        logging.info(f"grabbed new image: {no_cache_radar_url}")

        try:
            with urllib.request.urlopen(no_cache_radar_url) as response:
                image_data = response.read()
        except:
            logging.debug("Error getting image")

        image = None
        try:
            # Use PIL to open the image
            image = Image.open(io.BytesIO(image_data))
        except:
            logging.debug("Corrupt image received")

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
        self.save_settings()
        self.after(200, self.animate_gif)

    def scale_image(self):
        if self.frames is None or len(self.frames) == 0:
            logging.debug('no frames')
            return
        if not self.first_render:
            self.update()
            width, height = ImageTk.getimage(self.frames[0]).size
            new_width = self.image_label.winfo_width()
            new_height = self.image_label.winfo_height()
            if new_height == height and new_width == width:
                logging.debug('no scaling needed')
                return
            logging.debug('scaling image')
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

    def update_gif_periodically(self, *args, **kwargs):
        force_lookup = False
        if kwargs.get('force'):
            force_lookup = True
            self.radar_url = None
            if self.selected_region.get() != '':
                self.selected_region.set('')
            self.zip_code = self.zip_code_entry.get() 
        if self.frame_animation_id:
            self.after_cancel(self.frame_animation_id)
            self.frame_animation_id = None
        if self.update_gif_timer:
            self.after_cancel(self.update_gif_timer)
            self.update_gif_timer = None
        #try:
        self.fetch_and_display_gif(force=force_lookup)
        #except:
        #    pass
        self.update_gif_timer = self.after(self.refresh_delay, self.update_gif_periodically)

    def populate_radar_urls(self):
        self.radar_regions = [
            '',
            'Pacific Northwest',
            'North Rockies',
            'Upper Mississippi Valley',
            'Central Great Lakes',
            'Northeast',
            'Pacific Southwest',
            'Southern Rockies',
            'Southern Plains',
            'Southern Mississippi Valley',
            'Southeast',
            'National',
            'Alaska',
            'Hawaii',
            'Guam',
            'Puerto Rico',
        ]

        self.radar_urls = [
            '',
            'https://radar.weather.gov/ridge/standard/PACNORTHWEST_loop.gif',
            'https://radar.weather.gov/ridge/standard/NORTHROCKIES_loop.gif',
            'https://radar.weather.gov/ridge/standard/UPPERMISSVLY_loop.gif',
            'https://radar.weather.gov/ridge/standard/CENTGRLAKES_loop.gif',
            'https://radar.weather.gov/ridge/standard/NORTHEAST_loop.gif',
            'https://radar.weather.gov/ridge/standard/PACSOUTHWEST_loop.gif',
            'https://radar.weather.gov/ridge/standard/SOUTHROCKIES_loop.gif',
            'https://radar.weather.gov/ridge/standard/SOUTHPLAINS_loop.gif',
            'https://radar.weather.gov/ridge/standard/SOUTHMISSVLY_loop.gif',
            'https://radar.weather.gov/ridge/standard/SOUTHEAST_loop.gif',
            'https://radar.weather.gov/ridge/standard/CONUS_loop.gif',
            'https://radar.weather.gov/ridge/standard/ALASKA_loop.gif',
            'https://radar.weather.gov/ridge/standard/HAWAII_loop.gif',
            'https://radar.weather.gov/ridge/standard/GUAM_loop.gif',
            'https://radar.weather.gov/ridge/standard/TJUA_loop.gif',
        ]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '-d', '--debug',
            help="Enable debug logging",
            action="store_const", dest='loglevel', const=logging.DEBUG,
            default=logging.WARNING,
    )
    parser.add_argument(
            '-v', '--verbose',
            help="Enable verbose logging",
            action="store_const", dest='loglevel', const=logging.INFO,
    )
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=args.loglevel)

    root = WeatherRadarViewer()
    root.mainloop()

