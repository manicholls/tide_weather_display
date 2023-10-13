import gc
import secrets
import time,ntptime
import json
from urllib import urequest
from ujson import load
import re
import sys
import machine

gc.enable()
gc.collect()

graphics = None
WIDTH = None
HEIGHT = None

# Length of time between updates in minutes.
# Frequent updates will reduce battery life!
UPDATE_INTERVAL = 30
weather_api_key = secrets.weather_api_key

def pad_num(num):
    # Add an extra 0 if the current minute is single digit.
    if len(str(num)) == 1:
        num = "0{0}".format(num)
        return num
    else:
        return num

def get_url(URL):
    try:
        socket = urequest.urlopen(URL)
        gc.collect()
        output = load(socket)
        socket.close()
        del socket  #clean up to relieve memory
        gc.collect()
        return(output)
    except Exception as e:
        print(e)
        print("Error getting {0}".format(URL))
        time.sleep(60)

def update():
    try:
        ntptime.settime()
        global current_weather
        global low_tide
        global high_tide
        global current_tide
        global current_state
        print("Updating...")
        current_weather = get_url("https://api.openweathermap.org/data/2.5/weather?lat=44.9169&appid={0}&lon=-62.3819&units=metric".format(weather_api_key))
        print("Got weather")
        #print(current_weather)
        # These URLs need to be (percent) URL encoded  https://www.w3schools.com/tags/ref_urlencode.ASP
        low_tide = get_url("http://influxdb.local:8086/query?db=tides_wlp&q=SELECT+bottom%28value%2C1%29+FROM+tides_wlp+WHERE+time+%3E%3D+now%28%29+and+time+%3C%3D+now%28%29%2B12h+tz%28%27America%2FHalifax%27%29")
        high_tide = get_url('http://influxdb.local:8086/query?db=tides_wlp&q=SELECT+top%28value%2C1%29+FROM+%22tides_wlp%22+WHERE+time+%3E%3D+now%28%29+and+time+%3C%3D+now%28%29%2B12h+tz%28%27America%2FHalifax%27%29')
        print("Got Low & High Tide")
        current_tide = get_url("http://influxdb.local:8086/query?db=tides_wlp&q=select+*+from+tides_wlp+where+time+%3E+now%28%29+and+time+%3C+now%28%29%2B15m%3B")
        current_state = get_url("http://influxdb.local:8086/query?db=tides_wlp&q=select+difference%28value%29+from+tides_wlp+where+time+%3E+now%28%29+and+time+%3C+now%28%29%2B30m%3B")
        print("Got tidal states")
        gc.collect()
    except Exception as e:
        print(e)
        gc.collect()
        print("Sleeping 15 seconds before restarting")
        time.sleep(15)
        machine.reset()

def draw():
    global current_weather
    global low_tide
    global high_tide
    global current_tide
    global current_state
    try:
        gc.collect()  # For good measure...
        #w, h = display.get_bounds()
        print(current_weather)
        current_temp = str("Current: {0}C           Feels like: {1}C".format(int(current_weather['main']['temp']),int(current_weather['main']['feels_like'])))
        curr_desc = str(current_weather['weather'][0]['description'])
        actual_time = time.localtime(time.time() + current_weather['timezone'])
        max_temp = str("High:      {0}C".format(int(current_weather['main']['temp_max'])))
        min_temp = str("Low:       {0}C".format(int(current_weather['main']['temp_min'])))
        humidity = str("Humidity: {0}%".format(current_weather['main']['humidity']))
        sunset = str("Sunset:   {0}:{1}".format(time.localtime((current_weather['sys']['sunset']) + current_weather['timezone'])[3],time.localtime((current_weather['sys']['sunset']) + current_weather['timezone'])[4]))
        wind = str("Wind: {0} km/h, gusting to {1} km/h".format(int(current_weather['wind']['speed']), int(current_weather['wind']['gust'])))
        print("Calculating tides")
        low_tide_str = str("Low Tide:           {0} {1}".format(re.search("(\d+-\d+-\d+)", low_tide['results'][0]['series'][0]['values'][0][0]).group(1),re.search("(\d+:\d+):\d+-", low_tide['results'][0]['series'][0]['values'][0][0]).group(1)))
        high_tide_str = str("High Tide:          {0} {1}".format(re.search("(\d+-\d+-\d+)", high_tide['results'][0]['series'][0]['values'][0][0]).group(1),re.search("(\d+:\d+):\d+-", high_tide['results'][0]['series'][0]['values'][0][0]).group(1)))
        current_tide_str = str("Current Tide:     {0} M".format(current_tide['results'][0]['series'][0]['values'][0][1]))

        if current_state['results'][0]['series'][0]['values'][0][1] >= 0:
            current_state_str = "The tide is currently rising"
        else:
            current_state_str = "The tide is currently falling"    
        
        gc.collect()
        graphics.set_pen(1)
        graphics.clear()
        graphics.set_backlight(1)
        graphics.set_pen(5)
        graphics.rectangle(0, 0, WIDTH, 50)    
        graphics.set_pen(3)
        graphics.text("Weather Forecast:   {0}".format(current_weather['name']), 10, 20, WIDTH - 140, 3)
        graphics.set_pen(3) #black
        graphics.text(current_temp, 10, 80, WIDTH, 3)
        
        graphics.text(max_temp, 10, 120, WIDTH, 3 ) #if graphics.measure_text(max_temp) < WIDTH else 2)
        graphics.text(min_temp, 10, 155, WIDTH, 3 ) #if graphics.measure_text(min_temp) < WIDTH else 2)
        graphics.text(humidity, 10, 185, WIDTH, 3)
        graphics.text(sunset, 10, 215, WIDTH, 3)
        graphics.text(wind, 10, 250, WIDTH, 3)

        graphics.set_pen(graphics.create_pen(0, 51, 204))
        graphics.rectangle(0, 280, WIDTH, 130)  
        graphics.set_pen(1)
        graphics.text(low_tide_str, 10, 290, WIDTH, 3)
        graphics.text(high_tide_str, 10, 320, WIDTH, 3)
        graphics.text(current_tide_str, 10, 350, WIDTH, 3)
        graphics.text(current_state_str, 10, 380, WIDTH, 3)
      

        graphics.set_pen(3)
        graphics.text(curr_desc, 400, 130, 20, 3)
        graphics.text("Last updated: {0}:{1}    Updated every {2} minutes".format(actual_time[3],pad_num(actual_time[4]), UPDATE_INTERVAL), 10, 430, WIDTH, 2)
        
        gc.collect()
        graphics.update()
        gc.collect()
    except Exception as e:
        print(e)
        gc.collect()
        print("Sleeping 15 seconds before restarting")
        time.sleep(15)
        machine.reset()