import os
import setup_rtd

def CreateEmptyDirectories(path):
    lrtd = ['gps', 'logs', 'merged', 'queued', 'sensor']
    llogs = ['gps', 'no_rtd', 'raw', 'sensor']
    lraw = ['Lowell', 'Moana', 'NKE']
    lmerged = ['eMOLT', 'Lowell', 'Moana', 'NKE', 'zip']
    leMOLT = ['Lowell', 'Moana']
    lsensor = ['Lowell', 'Moana', 'NKE', 'sensor_info']

    for rtd in lrtd:
        try:
            os.mkdir(path + rtd)
        except:
            pass

        if rtd == 'logs':
            for log in llogs:
                try:
                    os.mkdir(path + rtd + '/' + log)
                except:
                    pass
                if log == 'raw':
                    for raw in lraw:
                        try:
                            os.mkdir(path + rtd + '/' + log + '/' + raw)
                        except:
                            pass
        elif rtd == 'merged':
            for merged in lmerged:
                try:
                    os.mkdir(path + rtd + '/' + merged)
                except:
                    pass
                if merged == 'eMOLT':
                    for eMOLT in leMOLT:
                        try:
                            os.mkdir(path + rtd + '/' + merged + '/' + eMOLT)
                        except:
                            pass

        elif rtd == 'queued':
            for raw in lraw:
                try:
                    os.mkdir(path + rtd + '/' + raw)
                except:
                    pass


        elif rtd == 'sensor':
            for sensor in lsensor:
                try:
                    os.mkdir(path + rtd + '/' + sensor)
                except:
                    pass


path = setup_rtd.parameters['path']
CreateEmptyDirectories(path)

