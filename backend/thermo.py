from apscheduler.schedulers.background import BackgroundScheduler
import spidev

spi = spidev.SpiDev()
sch = BackgroundScheduler()
sch.start()
currentTmp = 0


def initThermo():
    spi.open(0, 0)
    spi.max_speed_hz = 7629
    spi.mode = 0


def read_temperature():
    b = spi.readbytes(4)
    return float(((b[0] & 0x7f) << 6) + ((b[1] & 0xFC) >> 2)) / 4


def update_temperature(prevArr):
    global currentTmp
    if len(prevArr) == 5:
        prevArr.pop(0)

    prevArr.append(read_temperature())
    currentTmp = sum(prevArr) / len(prevArr)


def temperature():
    return currentTmp


tempLog = []
sch.add_job(
    update_temperature,
    'interval',
    id='temperature',
    seconds=0.2,
    args=(tempLog,)
)
