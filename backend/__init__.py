import time
from simple_pid import PID
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .gpio import initGPIO, setState, State
from .thermo import initThermo, temperature
from .profiles import Delta

initGPIO()
initThermo()

state = State.STANDBY
profile = 'delta'

setState(state)

sch = BackgroundScheduler()
sch.start()

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
pidData = []

TIME_RESOLUTION = 1


@app.get('/data')
async def data():
    return {"temp": tempData, "target": targetData, "pid": pidData}


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
    global state, tempData, targetData, pidData
    if state != State.STANDBY:
        raise Exception('Already running!')

    tempData = []
    targetData = []
    pidData = []
    state = State.COOL
    setState(state)

    pid = PID(1, 0.1, 0.05)
    startTime = time.time()

    sch.add_job(
        updateProfile,
        'interval',
        id='heat_cycle',
        seconds=TIME_RESOLUTION,
        args=(startTime, pid, Delta),
    )


@app.post('/stop')
async def stopProfile():
    global state, tempData, targetData, pidData
    state = State.STANDBY
    setState(state)

    tempData = []
    targetData = []
    pidData = []
    sch.remove_job('heat_cycle')


def updateProfile(startTime, pid, profile):
    global state, tempData, targetData, pidData
    temp = temperature()

    targetTemp = profile(time.time() - startTime)
    if (targetTemp == -1):
        stopProfile()
        return

    tempData.append(temp)
    targetData.append(targetTemp)

    pid.setpoint = targetTemp
    result = pid(temp)
    pidData.append(result)

    if result < temp:
        setState(State.HEAT)
    else:
        setState(State.COOL)
