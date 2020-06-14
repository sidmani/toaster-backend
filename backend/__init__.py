import time
from simple_pid import PID
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .gpio import initGPIO, heat, cool, standby
from .thermo import initThermo, temperature_avg
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

pid = PID(1, 0.005, 0.2, setpoint=0)
pid.proportional_on_measurement = True


def pidLoop(pid):
    temp = temperature_avg()
    result = pid(temp)
    p, i, d = pid.components
    addData(temp, 40, p, i, d)
    if (result > 0):
        heat()
    else:
        cool()


sch.add_job(
    pidLoop,
    'interval',
    id='heat_cycle',
    seconds=1,
    args=(pid,),
)

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
pidData_p = []
pidData_i = []
pidData_d = []

MAX_LEN = 200


def addData(temp, target, p, i, d):
    def add(arr, x):
        arr.append(x)
        if len(arr) > MAX_LEN:
            arr.pop(0)

    add(tempData, temp)
    add(targetData, target)
    add(pidData_p, p)
    add(pidData_i, i)
    add(pidData_d, d)


TIME_RESOLUTION = 1


@app.get('/data')
async def data():
    return {
        "temp": tempData,
        "target": targetData,
        "p": pidData_p,
        "i": pidData_i,
        "d": pidData_d,
    }


@app.get('/temp')
async def getTemp():
    return {"temp": temperature_avg()}


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
    pid.setpoint = 40


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
    standby()
    pid.setpoint = 0


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
