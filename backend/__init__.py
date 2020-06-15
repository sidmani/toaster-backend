import time
from simple_pid import PID
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .gpio import initGPIO, heat, cool, standby, fan, light
from .thermo import initThermo, temperature
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

pid = PID(4.8, 0.047, 5, setpoint=23)
pid.proportional_on_measurement = True
armed = False


def pidLoop(pid):
    temp = temperature()
    result = pid(temp)
    p, i, d = pid.components
    addData(temp, pid.setpoint, p, i, d)

    if not armed:
        return

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


def addData(temp, target, p, i, d):
    def add(arr, x):
        arr.append(x)
        if len(arr) > 600:
            arr.pop(0)

    add(tempData, temp)
    add(targetData, target)
    add(pidData_p, p)
    add(pidData_i, i)
    add(pidData_d, d)


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
    return {"temp": temperature()}


@app.get('/state')
async def getState():
    if state == State.STANDBY:
        return {"state": "standby"}
    elif state == State.PREHEAT:
        return {"state": "preheat"}
    return {"state": "running", "profile": "delta"}


class PreheatTemp(BaseModel):
    temp: float


@app.post('/preheat')
async def preheat(data: PreheatTemp):
    global state, armed
    armed = True
    pid.reset()
    state = State.PREHEAT
    pid.setpoint = data.temp


class PIDModel(BaseModel):
    p: float
    i: float
    d: float


@app.post('/pid_set')
async def setPID(req: PIDModel):
    global pid
    pid.Kp = req.p
    pid.Ki = req.i
    pid.Kd = req.d


@app.get('/pid')
async def getPID():
    return {"p": pid.Kp, "i": pid.Ki, "d": pid.Kd}


@app.post('/run')
async def startProfile():
    global pid, armed, state
    armed = True
    startTime = time.time()
    state = State.PROFILE
    pid.reset()
    sch.add_job(
        setProfileTarget,
        'interval',
        id='profile',
        seconds=1,
        args=(pid, startTime),
    )


def setProfileTarget(pid, startTime):
    global state
    elapsed = time.time() - startTime
    if elapsed < 310:
        pid.setpoint = 245
    else:
        if pid.setpoint != 23:
            light(True)
            pid.setpoint = 23
            pid.reset()
            return

        temp = temperature()
        if temp < 50:
            sch.remove_job('profile')
            state = State.STANDBY
            standby()
        elif temp < 140:
            fan(True)


@app.post('/stop')
async def stop():
    global state, armed

    try:
        sch.remove_job('profile')
    except Exception:
        pass

    pid.reset()
    standby()
    state = State.STANDBY
    pid.setpoint = 23
    armed = False
