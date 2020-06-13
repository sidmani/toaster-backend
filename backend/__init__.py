import sched
import time
from simple_pid import PID
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .gpio import initGPIO, setState, State
from .thermo import initThermo, temperature
from .profiles import Delta

sch = sched.scheduler(time.time, time.sleep)

initGPIO()
initThermo()

state = State.STANDBY
profile = 'delta'

setState(state)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

tempData = []
targetData = []

TIME_RESOLUTION = 1


@app.get('/data')
async def data():
    return {"temp": tempData, "target": targetData}


@app.get('/temp')
async def getTemp():
    return {"temp": temperature()}


@app.get('/state')
async def getState():
    if state == State.STANDBY:
        return {"state": "standby"}
    return {"state": "running", "profile": profile}


@app.post('/run')
async def startProfile():
    global state, tempData, targetData
    if state != State.STANDBY:
        raise Exception('Already running!')

    tempData = []
    targetData = []
    state = State.COOL
    setState(state)

    pid = PID(1, 0.1, 0.05)
    sch.enter(TIME_RESOLUTION, 1, updateProfile, (TIME_RESOLUTION, pid, Delta))
    sch.run()


@app.post('/stop')
async def stopProfile():
    global state, tempData, targetData
    state = State.STANDBY
    setState(state)

    tempData = []
    targetData = []


def updateProfile(t, pid, profile):
    global targetTemp, tempData, targetData
    temp = temperature()

    targetTemp = profile(t)
    if (targetTemp == -1):
        state = State.STANDBY
        setState(state)
        tempData = []
        targetData = []
        return

    tempData.append(temp)
    targetData.append(targetTemp)

    pid.setpoint = targetTemp
    result = pid(temp)

    if result < temp:
        setState(State.HEAT)
    else:
        setState(State.COOL)

    sch.enter(TIME_RESOLUTION, 1, updateProfile, (t + TIME_RESOLUTION, pid, profile))
    sch.run()
