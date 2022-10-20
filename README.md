# Tide & Weather Display
A micropython project to display tide and weather information

For this project I've used a Raspberry Pi Pico W and a Waveshare 19804 - 2.8inch Touch Display Module For Raspberry Pi Pico


This project has a number of components:

- A script to parse tidal forecast information from the Canadian govt.
- An influxdb to hold the data
- The pico & display.

The first 2 components are due to the limited memory on the Pico.  Trying to pull
that information directly proved to be too much for the little device.

I'm not going to cover the setup of influxdb here.  Once you have an instance
available you can setup the tides.py file with your station id and run it via crontab.

For the pico, once you have the headers soldered and the display attached,
copy the main.py, secrets.py, st7789_4bit.py and nanoguilib folder to the Pi.

The nanoguilib is provided by waveshare and can originally be found here: https://www.waveshare.com/wiki/Pico-ResTouch-LCD-2.8

in main.py there's a few variables to update/adjust for your location.
