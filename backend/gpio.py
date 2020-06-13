import importlib.util
try:
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:
    import FakeRPi.GPIO as GPIO

RELAY = [27, 17, 18, 15, 14, 4, 3, 2]
LED = [13, 19, 26]


def initGPIO():
    GPIO.setmode(GPIO.BCM)
    for r in RELAY:
        GPIO.setup(r, GPIO.OUT)
        GPIO.output(r, True)
