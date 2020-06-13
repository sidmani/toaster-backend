import sched
import time
from simple_pid import PID
from fastapi import FastAPI
from .gpio import initGPIO, setState, State
from .thermo import initThermo, temperature
from .profiles import Delta

sch = sched.scheduler(time.time, time.sleep)

initGPIO()
initThermo()

state = State.STANDBY
setState(state)

app = FastAPI()

targetTemp = 0

TIME_RESOLUTION = 0.5


@app.get('/temperature')
def getTemperature():
    return {"t": temperature()}


@app.post('/run')
def startProfile():
    if state != State.STANDBY:
        raise Exception('Already running!')

    state = State.COOL
    setState(state)

    pid = PID(1, 0.1, 0.05)
    sch.enter(TIME_RESOLUTION, 1, updateProfile, (TIME_RESOLUTION, pid))


def updateProfile(t, pid):
    temp = temperature()
    if (temp == -1):
        state = State.STANDBY
        setState(state)

    pid.setpoint = Delta(t)
    result = pid(temp)
    if result < temp:
        setState(State.HEAT)
    else:
        setState(State.COOL)

    sch.enter(TIME_RESOLUTION, 1, updateProfile, (t + TIME_RESOLUTION, pid))
