def Delta(t):
    HEAT_RATE = 1.2  # deg C / sec
    MAX_TEMP = 250
    COOL_RATE = 4

    # computed values
    HEAT_TIME = MAX_TEMP / HEAT_RATE
    COOL_TIME = MAX_TEMP / COOL_RATE

    if t < HEAT_TIME:
        return t * HEAT_RATE

    if t < HEAT_TIME + COOL_TIME:
        return MAX_TEMP - COOL_RATE * (t - HEAT_TIME)

    # indicates routine is over
    return -1
