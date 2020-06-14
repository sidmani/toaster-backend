import time
from simple_pid import PID
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .gpio import initGPIO, heat, cool, standby
from .thermo import initThermo, temperature
from .profiles import Delta
from enum import Enum


class State(Enum):
    STANDBY = 0
    PREHEAT = 1
    PROFILE = 2


initGPIO()
initThermo()
state = State.STANDBY
standby()

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

MAX_LEN = 200

def addData(temp, target, pid):
    tempData.append(temp)
    targetData.append(target)
    pidData.append(pid)

    if len(tempData) > MAX_LEN:
        tempData.pop(0)

    if len(targetData) > MAX_LEN:
        targetData.pop(0)

    if len(pidData) > MAX_LEN:
        pidData.pop(0)


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
    elif state == State.PREHEAT:
        return {"state": "preheat"}
    return {"state": "running", "profile": "delta"}


@app.post('/preheat')
async def preheat():
    global state
    state = State.PREHEAT

    try:
        sch.remove_job('heat_cycle')
    except Exception:
        pass

    pid = PID(1, 0.1, 0.05)
    pid.setpoint = 40
    sch.add_job(
        preheatHandler,
        'interval',
        id='heat_cycle',
        seconds=TIME_RESOLUTION,
        args=(pid,),
    )


def preheatHandler(pid):
    temp = temperature()
    result = pid(temp)
    addData(temp, 40, result)
    if (result > temp):
        heat()
    else:
        cool()


@app.post('/run')
async def startProfile():
    global state, tempData, targetData, pidData
    if state != State.STANDBY:
        raise Exception('Already running!')

    tempData = []
    targetData = []
    pidData = []
    cool()

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
    global tempData, targetData, pidData

    tempData = []
    targetData = []
    pidData = []
    standby()
    try:
        sch.remove_job('heat_cycle')
    except Exception:
        pass


# def updateProfile(startTime, pid, profile):
#     global state, tempData, targetData, pidData
#     temp = temperature()

#     targetTemp = profile(time.time() - startTime)
#     if (targetTemp == -1):
#         stopProfile()
#         return

#     tempData.append(temp)
#     targetData.append(targetTemp)

#     pid.setpoint = targetTemp
#     result = pid(temp)
#     pidData.append(result)

#     if temp < result:
#         heat()
#     else:
#         cool()
