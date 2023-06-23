import numpy as np
    
timezone = {
            '2023-03-01':-7,
            '2023-05-01':-6,
            '2023-05-10':-6,
            '2023-06-08':-6,
            '2023-06-09':-6,
            '2023-06-13':-6,
            '2023-06-14':-6
         }

timeshift = { 
             '2023-03-01':-180,
             '2023-05-01':-164,
             '2023-05-10':-164,
             '2023-06-08':0,
             '2023-06-09':0,
             '2023-06-13':0,
             '2023-06-14':0
            }

def get_delta_time(day):
    """
    Get time difference between log and DAS data time

    Return: time difference in np.timedelta64. 

    Usage: 
    day = '2023-05-10'
    time_delta = get_delta_time(day)

    DAStime = log_time + time_delta

    """

    ts = timeshift[day]
    tz = timezone[day]

    delta_time = np.timedelta64(ts,'s')
    delta_time -= np.timedelta64(tz,'h')

    return delta_time

