#! /usr/bin/env python
# coding=utf-8

# Author: Jukka Hautakorpi, Tuunix Oy
# Used with usb rfid reader that sends tag data as mimicing keyboard to worktime app api
# for example http://worktimeapp.tuunix.fi/
# Designed to be used with headless Raspberry pi zero W with some leds

# Required: Python, pip. Tested with Python 2.7.15rc1 on Linux
# 1. pip install requests
# 2. pip install click
# Configure your settings in settings.ini
# quit the program loop with q (enter)

import ConfigParser
import requests 
from urllib3.exceptions import InsecureRequestWarning
import click
import sys, time
import RPi.GPIO as GPIO


# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


redPin   = 11
greenPin = 13
bluePin  = 15

pwm = 0

stateRed = 0
stateGreen = 0
stateBlue = 0
colorslist = ['a', 's', 'd']

def setup():
	global pwm
	GPIO.setmode(GPIO.BOARD)       # GPIO Numbering of Pins is BOARD
	GPIO.setwarnings(False)
	GPIO.setup(redPin, GPIO.OUT)
	GPIO.output(redPin, GPIO.HIGH)
	GPIO.setup(greenPin, GPIO.OUT)
	GPIO.output(greenPin, GPIO.HIGH)
	GPIO.setup(bluePin, GPIO.OUT)
	GPIO.output(bluePin, GPIO.HIGH)

def redLed(state):
	GPIO.output(bluePin, GPIO.HIGH)
	GPIO.output(greenPin, GPIO.HIGH)
	if(state):
		GPIO.output(redPin, GPIO.LOW)
	else:
		GPIO.output(redPin, GPIO.HIGH)

def greenLed(state):
	GPIO.output(bluePin, GPIO.HIGH)
	GPIO.output(redPin, GPIO.HIGH)
	if(state):
		GPIO.output(greenPin, GPIO.LOW)
	else:
		GPIO.output(greenPin, GPIO.HIGH)

def blueLed(state):
	GPIO.output(redPin, GPIO.HIGH)
	GPIO.output(greenPin, GPIO.HIGH)
	if(state):
		GPIO.output(bluePin, GPIO.LOW)
	else:
		GPIO.output(bluePin, GPIO.HIGH)


def blink(times=1, ledFunction=redLed):
	global stateRed
	global stateGreen
	global stateBlue
	if (times == 1):
		ledFunction(0)
		time.sleep(0.5)
		ledFunction(1)
		time.sleep(0.5)
		ledFunction(0)
	else:
		for x in range(times):
			ledFunction(1)
			time.sleep(0.5)
			ledFunction(0)
			time.sleep(0.5)
	if(stateRed):
		stateRed = not stateRed
		toggleLed('red')
	elif(stateGreen):
		stateGreen = not stateGreen
		toggleLed('green')
	elif(stateBlue):
		stateBlue = not stateBlue
		toggleLed('blue')


def toggleLed(led):
	global stateRed
	global stateGreen
	global stateBlue
	if (led == 'a') or (led ==  'red'):
		stateRed = not stateRed
		if stateRed == 1:
			GPIO.output(redPin, GPIO.LOW)
		else: 
			GPIO.output(redPin, GPIO.HIGH)
	if (led == 's') or (led == 'green'):
		stateGreen = not stateGreen
		if stateGreen == 1:
			GPIO.output(greenPin, GPIO.LOW)
		else: 
			GPIO.output(greenPin, GPIO.HIGH)
	if (led == 'd') or (led == 'blue'):
		stateBlue = not stateBlue
		if stateBlue == 1:
			GPIO.output(bluePin, GPIO.LOW)
		else: 
			GPIO.output(bluePin, GPIO.HIGH)
	#print "a-red: %d s-green: %d d-blue: %d" %(stateRed, stateGreen, stateBlue)


#click.clear()

Config = ConfigParser.ConfigParser()
Config.read("settings.ini")
loop_active = True

def clearnString(txt):
	txt = txt.replace('?', '%3F')
	txt = txt.replace('&', '%26')
	txt = txt.strip();
	return txt

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def requestError():
	toggleLed('green')
	print "Request Failed, expection "
	blink(20, redLed)
	
api_url = ConfigSectionMap("basic")['api_url']
status_parameter = ConfigSectionMap("basic")['status_parameter']
toggle_parameter = ConfigSectionMap("basic")['toggle_parameter']
wait_time = ConfigSectionMap("basic")['wait_time']
leds_enabled = ConfigSectionMap("basic")['leds_enabled']
response_ok = ConfigSectionMap("basic")['response_ok']

setup()
##print "Will send requests to api url:  %s" % (api_url)
toggleLed('blue')
while loop_active:
	rfid_variable = clearnString(raw_input("Waiting input:"))
	if rfid_variable == 'q':
		loop_active = False
		GPIO.cleanup();
		print "Exit program"
	elif rfid_variable in colorslist:
		toggleLed(rfid_variable)
	elif rfid_variable == 'f':
		blink()
	elif len(rfid_variable) <= 1:
		blink(3, redLed)
	elif len(rfid_variable) > 3:
		toggleLed('blue')
		toggleLed('green')
		toggleLed('red')
		#yellow while loading request
		full_url = api_url + rfid_variable + toggle_parameter
		print "Sending query to  %s" % (full_url)
		try:
			response = requests.get(full_url, verify=False)
		except requests.exceptions.RequestException as e:  # This is the correct syntax
			requestError()

		toggleLed('blue')
		toggleLed('green')
		toggleLed('red')
		#back to blue
		response.encoding = 'utf-8'
		data = response.text
		print "Server responded: %s" % (data)
		if response_ok in data:
			print "Request OK "
			blink(3, greenLed)
		else:
			print "Request Failed "
			blink(5, redLed)

