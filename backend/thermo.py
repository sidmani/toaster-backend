import spidev

spi = spidev.SpiDev()


def initThermo():
    spi.open(0, 0)
    spi.max_speed_hz = 7629
    spi.mode = 0


def temperature():
    b = spi.readbytes(4)
    sign = -1 if (b[0] & 0x80) else 1
    return sign * float(((b[0] & 0x7f) << 6) + ((b[1] & 0xFC) >> 2)) / 4
