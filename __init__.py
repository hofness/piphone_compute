#!/bin/python

# piphone_compute - A DIY Cellphone element based on Raspberry Pi
# uses tons of Adafruit stuff  https://www.adafruit.com/
# (Raspberry Pi ), (PiTFT), (modem 808), (power supply)
# 
# Prerequisite tutorials: aside from the basic Raspbian setup and PiTFT setup
# http://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi
#
# by Alex Hofmann () modified from piphone.py except numeriCallBack, adafruit pitft calls, and modem calls
# based on piphone.py by David Hunt (dave@davidhunt.ie) 
# which is based on cam.py by Phil Burgess / Paint Your Dragon for Adafruit Industries.
# using pygbutton UI by AL Stegwart ()
# BSD license, above text must be referenced with redistribution see copyright.txt

import atexit
from datetime import datetime, timedelta
import errno
import fnmatch
import io
import os
from subprocess import call  
import sys  # so that i can quit if desired to run other things
import threading
from time import sleep

import pygame
import pygame.display  # just to be verbose
from pygame.locals import *
import serial

import cPickle as pickle
import pygbutton  # button UI class by AL Stegwart


sys.path.insert(0, os.path.abspath('..'))  # to grab button UI class

# UI callbacks -------------------------------------------------------------
# These are defined before globals because they're referenced by items in
# the global buttons[] list.

def numericCallback(n):  # Pass 1 (next setting) or -1 (prev setting)
    global screenMode
    global numberstring
    global phonecall
    if n < 10 and screenMode == 0:
        numberstring = numberstring + str(n)
    elif n == 10 and screenMode == 0:
        numberstring = numberstring[:-1]
    elif n == 12:
        if phonecall == 0:
            if screenMode == 0:
                if len(numberstring) > 0:
                    print("Calling " + numberstring);
                    serialport.write("AT\r")
                    response = serialport.readlines(None)
                    serialport.write("ATD " + numberstring + ';\r')
                    response = serialport.readlines(None)
                    print response
                    phonecall = 1
                    screenMode = 1
        else:
            print("Hanging Up...")
            serialport.write("AT\r")
            response = serialport.readlines(None)
            serialport.write("ATH\r")
            response = serialport.readlines(None)
            print response
            phonecall = 0
            screenMode = 0
        if len(numberstring) > 0:
            numeric = int(numberstring)
            v[dict_idx] = numeric



# Global stuff -------------------------------------------------------------

screen_width = 240  # set screen size here
screen_height = 320

busy = False
threadExited = False
phonecall = 1
screenMode = 0
screenModePrior = -1  # Prior screen mode (for detecting changes)
iconPath = 'icons'  # Subdirectory containing UI bitmaps (PNG format)
numeric = 0  # number from numeric keypad      
numberstring = ""  # phone values
dict_idx = "Interval"
v = { "Pulse": 100,
    "Interval": 3000,
    "Images": 150}

# Initialization -----------------------------------------------------------

# Init framebuffer/touchscreen environment variables
print "setting pi values..."
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb1') # see adafruit tutorial on this
os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')
# check these on the pi --

# Init pygame and screen
print "Initting..."
pygame.init()
pygame.display.set_caption('PiPhone')  # name where we are
DISPLAYSURFACE = pygame.display.set_mode((screen_width, screen_height))  # pygbutton requirement

print "Setting Mouse invisible..."
pygame.mouse.set_visible(True)  # if not debuging set to false

print "Setting fullscreen..."
# check the display out for debugging
info = pygame.display.list_modes()
bestmode = pygame.display.mode_ok((screen_width, screen_height), FULLSCREEN, 0)
print "display modes: ", info
print "display modes: ", bestmode

screen = pygame.display.set_mode([screen_width, screen_height])

print "loading background.."
img = pygame.image.load("icons/PiPhone.png")
if img is None: 
    screen.fill(0)
if img:
    screen.blit(img, ((240 - img.get_width()) / 2, (320 - img.get_height()) / 2))
    pygame.display.update()
# sleep(1) # delay

print "Initialising Modem.."
serialport = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5)
serialport.write("AT\r")
response = serialport.readlines(None)
serialport.write("ATE0\r")
response = serialport.readlines(None)
serialport.write("AT\r")
response = serialport.readlines(None)
print response
# check these on pi

print "generating buttons..."# print buttons
exitbutton = pygbutton.PygButton((5, 290, 35, 25), 'exit')  # button construct
onebutton = pygbutton.PygButton((30, 60, 60, 60), normal='icons/1.png')
twobutton = pygbutton.PygButton((90, 60, 60, 60), normal='icons/2.png')
threebutton = pygbutton.PygButton((150, 60, 60, 60), normal='icons/3.png')
fourbutton = pygbutton.PygButton((30, 110, 60, 60), normal='icons/4.png')
fivebutton = pygbutton.PygButton((90, 110, 60, 60), normal='icons/5.png')
sixbutton = pygbutton.PygButton((150, 110, 60, 60), normal='icons/6.png')
sevenbutton = pygbutton.PygButton((30, 160, 60, 60), normal='icons/7.png')
eightbutton = pygbutton.PygButton((90, 160, 60, 60), normal='icons/8.png')
ninebutton = pygbutton.PygButton((150, 160, 60, 60), normal='icons/9.png')
zerobutton = pygbutton.PygButton((90, 210, 60, 60), normal='icons/0.png')
starbutton = pygbutton.PygButton((30, 210, 60, 60), normal='icons/star.png')
hashbutton = pygbutton.PygButton((150, 210, 60, 60), normal='icons/hash.png')
delbutton = pygbutton.PygButton((150, 260, 60, 60), normal='icons/del2.png')
callbutton = pygbutton.PygButton((90, 260, 60, 60), normal='icons/call.png')

hangbutton = pygbutton.PygButton((90, 260, 60, 60), normal='icons/hang.png')

# Main loop ----------------------------------------------------------------

def main():
    
    allButtons = (exitbutton, onebutton, twobutton, threebutton, fourbutton, fivebutton, sixbutton, sevenbutton, eightbutton, ninebutton, zerobutton, starbutton, hashbutton, delbutton, callbutton) 
    for b in allButtons:
        b.draw(DISPLAYSURFACE)
    
    screenMode = 0
    
    print "mainloop.."

    while True: # main game loop
        for event in pygame.event.get(): # event handling loop
            screen_change = 0
            if 'click' in exitbutton.handleEvent(event):
                print "exiting"
                pygame.display.quit()         
                pygame.quit()
                sys.exit()
                
            if 'click' in onebutton.handleEvent(event):
                print "1"
                screenMode = 0
                numericCallback(1) 
                screen_change = 1   
            
            if 'click' in twobutton.handleEvent(event):
                screenMode = 0
                numericCallback(2) 
                screen_change = 1       

            if 'click' in threebutton.handleEvent(event):
                screenMode = 0
                numericCallback(3) 
                screen_change = 1
                    
            if 'click' in fourbutton.handleEvent(event):
                screenMode = 0
                numericCallback(4) 
                screen_change = 1
                    
            if 'click' in fivebutton.handleEvent(event):
                screenMode = 0
                numericCallback(5) 
                screen_change = 1
                    
            if 'click' in sixbutton.handleEvent(event):
                screenMode = 0
                numericCallback(6) 
                screen_change = 1
                    
            if 'click' in sevenbutton.handleEvent(event):
                screenMode = 0
                numericCallback(7) 
                screen_change = 1
                    
            if 'click' in eightbutton.handleEvent(event):
                screenMode = 0
                numericCallback(8) 
                screen_change = 1
                    
            if 'click' in ninebutton.handleEvent(event):
                screenMode = 0
                numericCallback(9) 
                screen_change = 1
                    
            if 'click' in zerobutton.handleEvent(event):
                screenMode = 0
                numericCallback(0) 
                screen_change = 1
                    
            if 'click' in delbutton.handleEvent(event):
                screenMode = 0
                numericCallback(10) 
                screen_change = 1
                    
            if 'click' in starbutton.handleEvent(event):
                screenMode = 0
                numericCallback("*") 
                screen_change = 1
                    
            if 'click' in hashbutton.handleEvent(event):
                screenMode = 0
                numericCallback("#") 
                screen_change = 1
                    
            if 'click' in callbutton.handleEvent(event):
                screenMode = 0
                numericCallback(12) 
                screen_change = 1
            
            
            if screenMode == 0 :
                myfont = pygame.font.SysFont(None, 50) # use default sys font to avoid conflicts
                screen.blit(img, (0, 0), (0,0, 240, 50))# only replace screen under text changes
                label = myfont.render(numberstring, 1, (255, 255, 255))
                screen.blit(label, (10, 2))
                screenMode = 1# debug calling
    
            else:
                myfont = pygame.font.SysFont(None, 30)
                screen.blit(img, (0, 0), (0,0, 240, 50))
                label = myfont.render("Calling: " + numberstring + " ...", 1, (255, 255, 255)) # put calling on main text line
                screen.blit(label, (10, 2))

            pygame.display.update()
        
if __name__ == '__main__':
    main()
  