from machine import Pin,SPI
import network
import time, ntptime
import urequests
from utime import sleep
import json
import secrets
import gc
gc.enable()
from nanoguilib.color_setup import ssd  # Create a display instance
from nanoguilib.nanogui import refresh
from nanoguilib.label import Label
from nanoguilib.writer import Writer, CWriter
from gui.fonts import freesans20
import uos
from nanoguilib.colors import *

#import utime
CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
wri = CWriter(ssd, freesans20, WHITE, BLACK, verbose=False)
wri.set_clip(True, True, False)

ssid = secrets.ssid
ssid_pass = secrets.ssid_pass
weather_api_key = secrets.weather_api_key

influxdb_url = "http://192.168.10.24:8086"


# These URLs need to be (percent) URL encoded  https://www.w3schools.com/tags/ref_urlencode.ASP
# Adjust the timezone in the queries to show the proper timezones for your location.
low_tide_query = "{0}/query?db=tides_wlp&q=SELECT+bottom%28value%2C1%29+FROM+tides_wlp+WHERE+time+%3E%3D+now%28%29+and+time+%3C%3D+now%28%29%2B12h+tz%28%27America%2FHalifax%27%29".format(influxdb_url)
high_tide_query = '{0}/query?db=tides_wlp&q=SELECT+top%28value%2C1%29+FROM+%22tides_wlp%22+WHERE+time+%3E%3D+now%28%29+and+time+%3C%3D+now%28%29%2B12h+tz%28%27America%2FHalifax%27%29'.format(influxdb_url)
current_tide_query = "{0}/query?db=tides_wlp&q=select+*+from+tides_wlp+where+time+%3E+now%28%29+and+time+%3C+now%28%29%2B15m%3B".format(influxdb_url)
current_state_query = "{0}/query?db=tides_wlp&q=select+difference%28value%29+from+tides_wlp+where+time+%3E+now%28%29+and+time+%3C+now%28%29%2B30m%3B".format(influxdb_url)
# Update this to be for your given location
weather_query = "https://api.openweathermap.org/data/2.5/weather?lat=44.97&appid={0}&lon=-62.07&units=metric".format(weather_api_key)

#How long to wait between screen changes.
screen_rotate_time = 45


def query_influxdb(query):
    gc.collect()
    response = urequests.get(query)
    return(response)

def display_text(text, x, y, colour):
    wri.setcolor(colour)
    width = wri.stringlen(text)
    if width >= 320:
        width = 319
    lbl_text = Label(wri, x, y, width)
    lbl_text.value(text)
    refresh(ssd)

def clear_display():
    refresh(ssd, True)

def centre_text(text):
    return(int(110-(len(text)//2)))

def temp_colour(temp):
    try:
        value = int(temp)
        if value <= 0:
            return(BLUE)
        if value >0 and value <=24:
            return(GREEN)
        if value >= 25:
            return(LIGHTRED)
    except:
        return("WHITE")

def pad_num(num):
    # Add an extra 0 if the current minute is single digit.
    if len(str(num)) == 1:
        num = "0{0}".format(num)
        return num
    else:
        return num


if __name__=='__main__':
    clear_display()

    display_text("Connecting to",2, 2, WHITE)
    display_text(ssid,20, 2, WHITE)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, ssid_pass)

    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
      if wlan.status() < 0 or wlan.status() >= 3:
        break
      max_wait -= 1
      clear_display()
      display_text('waiting for connection...',2, 2, RED)
      time.sleep(1)

    # Handle connection error
    if wlan.status() != 3:
       clear_display()
       raise RuntimeError('network connection failed',2, 2)
    else:
      clear_display()
      display_text('connected',2, 2, YELLOW)
      status = wlan.ifconfig()
      display_text( "IP: {0}".format(status[0]), 20, 2, WHITE )
      display_text( "SN: {0}".format(status[1]), 40, 2, WHITE )
      display_text( "GW: {0}".format(status[2]), 60, 2, WHITE )
      display_text( "DNS: {0}".format(status[3]), 80, 2, WHITE )
      sleep(1)


    while True:
        try:
            clear_display()
            display_text("Updating Data",2, 2, YELLOW)
            ntptime.settime()
            try:
                display_text("Getting Low Tide Data",20, 2, GREY)
                low_tide = query_influxdb(low_tide_query)
                low_tide_time = low_tide.json()['results'][0]['series'][0]['values'][0][0]
                low_tide_measurement = low_tide.json()['results'][0]['series'][0]['values'][0][1]
                ltm_string = "{0} M".format(low_tide_measurement)
                del low_tide
                display_text("Getting Low Tide Data",20, 2, GREEN)
            except:
                ltm_string = ""
                display_text("Getting Low Tide Data",20, 2, RED)


            try:
                display_text("Getting High Tide Data",40, 2, GREY)
                high_tide = query_influxdb(high_tide_query)
                high_tide_time = high_tide.json()['results'][0]['series'][0]['values'][0][0]
                high_tide_measurement = high_tide.json()['results'][0]['series'][0]['values'][0][1]
                htm_string = "{0} M".format(high_tide_measurement)
                del high_tide
                display_text("Getting High Tide Data",40, 2, GREEN)
            except:
                display_text("Getting High Tide Data",40, 2, RED)
                high_tide_time = ""
                htm_string = ""

            try:
                display_text("Getting Current Tide Data",60, 2, GREY)
                current_tide = query_influxdb(current_tide_query)
                current_tide_time = current_tide.json()['results'][0]['series'][0]['values'][0][0]
                current_tide_measurement = current_tide.json()['results'][0]['series'][0]['values'][0][1]
                ctm_string = "{0} M".format(current_tide_measurement)
                del current_tide
                display_text("Getting Current Tide Data",60, 2, GREEN)
            except:
                display_text("Getting Current Tide Data",60, 2, RED)
                current_tide_time = ""
                ctm_string = ""

            try:
                display_text("Getting Current Forecast Data",80, 2, GREY)
                current_temp = query_influxdb(weather_query)
                current_temp_string = int(current_temp.json()['main']['temp'])
                feels_like = int(current_temp.json()['main']['feels_like'])
                temp_max = int(current_temp.json()['main']['temp_max'])
                temp_min = int(current_temp.json()['main']['temp_min'])
                curr_desc = current_temp.json()['weather'][0]['description']
                curr_wind = int(current_temp.json()['wind']['speed'])
                wind_gust = int(current_temp.json()['wind']['gust'])
                pressure = current_temp.json()['main']['pressure']
                humidity = current_temp.json()['main']['humidity']
                UTC_OFFSET = current_temp.json()['timezone']
                sunset = (current_temp.json()['sys']['sunset'] + UTC_OFFSET)

                try:
                    del current_temp
                except:
                    pass
                display_text("Getting Current Forecast Data",80, 2, GREEN)
            except:
                print(current_temp.json()['main'])
                curr_desc = ""
                curr_wind = ""
                temp_max = ""
                temp_min = ""
                pressure = ""
                humidity = ""
                wind_gust = ""
                current_temp_string = ""
                UTC_OFFSET = "-10800" # Hard code current if we can't retrieve it.
                sunset = ""
                display_text("Getting Current Forecast Data",80, 2, RED)


            display_text("Analyzing Data",120, 2, GREY)
            try:
                current_state_results = query_influxdb(current_state_query)
                if current_state_results.json()['results'][0]['series'][0]['values'][0][1] >= 0:
                    current_state = "rising"
                else:
                    current_state = "falling"
                current_state_string = "The tide is currently {0}".format(current_state)
                display_text("Analyzing Data",120, 2, GREEN)
            except:
                current_state_string = "unknown"
                display_text("Analyzing Data",120, 2, RED)


            display_text("Update Completed!",140, 2, GREEN)
            gc.collect()
            sleep(1)
            clear_display()
            i = 0
            #Refresh data at ~10 minute intervals
            while i <= 600:
                actual_time = time.localtime(time.time() + UTC_OFFSET)  # Refresh time
                #Screen 1
                display_text("Tidal Forecast - {0}:{1}".format(actual_time[3],pad_num(actual_time[4])),2, 40, YELLOW)
                display_text("Current Tide         {0}".format(ctm_string),32, 2, WHITE)


                display_text(current_state_string,60, 2, WHITE)

                display_text("Low Tide               {0}".format(ltm_string),100, 2, GREEN)
                display_text(low_tide_time.replace("T","    "),130, 2, GREEN)


                display_text("High Tide              {0}".format(htm_string),180, 2, MAGENTA)
                display_text(high_tide_time.replace("T","    "),210, 2, MAGENTA)

                sleep(screen_rotate_time)
                clear_display()

                #Screen 2
                actual_time = time.localtime(time.time() + UTC_OFFSET) # Refresh Time
                display_text("Today's Weather - {0}:{1}".format(actual_time[3],pad_num(actual_time[4])),2, 30, YELLOW)

                display_text("Temp: {0}C  Feels Like: {1}C".format(current_temp_string, feels_like),32, 2, temp_colour(feels_like))
                display_text("Low/High : {0}C / {1}C".format(temp_min,temp_max),60, 2, temp_colour(temp_min))
                display_text("Current Conditions : {0}".format(curr_desc),90, 2, WHITE)
                display_text("Wind: {0} m/s, Gusting to {1} m/s".format(curr_wind, wind_gust),120, 2, WHITE)
                display_text("Humidity: {0}%".format(humidity),150, 2, WHITE)
                display_text("Pressure: {0} hPa".format(pressure),180, 2, WHITE)
                display_text("Sunset: {0}:{1}".format(time.localtime(sunset)[3],time.localtime(sunset)[4] ), 210, 2, WHITE)
                sleep(screen_rotate_time)
                clear_display()
                i += screen_rotate_time

        except Exception as e:
            clear_display()
            display_text(str(e), 2, 0, WHITE)
            display_text("reset in 10 sec",22, 0, RED)
            time.sleep(10)
            machine.reset()
