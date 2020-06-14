from simple_pid import PID
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

pid = PID(1, 0.01, 1, setpoint=25)
pid.proportional_on_measurement = True
pid.output_limits = (-10, 10)


def pidLoop(pid):
    temp = temperature()
    result = pid(temp)
    p, i, d = pid.components
    addData(temp, pid.setpoint, p, i, d)
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
        if len(arr) > 200:
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


@app.post('/preheat')
async def preheat():
    global state
    state = State.PREHEAT
    pid.setpoint = 40


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


# @app.post('/run')
# async def startProfile():
#     # global state, tempData, targetData, pidData
#     # if state != State.STANDBY:
#     #     raise Exception('Already running!')

#     # tempData = []
#     # targetData = []
#     # pidData = []
#     # cool()

#     # pid = PID(1, 0.1, 0.05)
#     # startTime = time.time()

#     # sch.add_job(
#     #     updateProfile,
#     #     'interval',
#     #     id='heat_cycle',
#     #     seconds=TIME_RESOLUTION,
#     #     args=(startTime, pid, Delta),
#     # )


@app.post('/stop')
async def stop():
    global state
    standby()
    state = State.STANDBY
    pid.setpoint = 25
