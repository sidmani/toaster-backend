import importlib.util
from enum import Enum


class State(Enum):
    STANDBY = 0
    HEAT = 1
    COOL = 2


try:
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:
    import FakeRPi.GPIO as GPIO

RELAY = [27, 17, 18, 15, 14, 4, 3, 2]
LED = [13, 19, 26]

TOP_ELEMENT = RELAY[1]
BOTTOM_ELEMENT = RELAY[3]
FAN = RELAY[2]
LIGHT = RELAY[0]


def initGPIO():
    GPIO.setmode(GPIO.BCM)
    for r in RELAY:
        GPIO.setup(r, GPIO.OUT)
        GPIO.output(r, True)

    for l in LED:
        GPIO.setup(l, GPIO.OUT)
        GPIO.output(l, False)


def clearLEDs():
    for l in LED:
        GPIO.output(l, False)


def clearRelays():
    for r in RELAY:
        GPIO.output(r, True)


def heat():
    # set the red LED
    GPIO.output(LED[0], True)

    # enable both heating elements
    GPIO.output(TOP_ELEMENT, False)
    GPIO.output(BOTTOM_ELEMENT, False)

    # enable the fan
    GPIO.output(FAN, False)


def cool():
    # set center LED
    GPIO.output(LED[1], True)

    # enable fan
    GPIO.output(FAN, False)


def standby():
    # set 3rd LED
    GPIO.output(LED[2], True)


def setState(s):
    clearLEDs()
    clearRelays()

    if s == State.STANDBY:
        standby()
    elif s == State.HEAT:
        heat()
    elif s == State.COOL:
        cool()
