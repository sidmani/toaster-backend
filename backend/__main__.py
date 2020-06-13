from .gpio import initGPIO, setLED
from .thermo import initThermo, temperature

initGPIO()
initThermo()

setLED(0, True)

while(True):
    print(temperature())
