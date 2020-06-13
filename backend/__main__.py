from .gpio import initGPIO, setState, State
from .thermo import initThermo, temperature

initGPIO()
initThermo()

setState(State.HEAT)
