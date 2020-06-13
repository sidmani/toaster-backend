import spidev

spi = spidev.SpiDev()


def initThermo():
    spi.open(0, 0)
    spi.max_speed_hz = 7629
    spi.mode = 0


def temperature():
    b = spi.readBytes(4)
    return float((b[0] << 8) + (b[1])) / 4
