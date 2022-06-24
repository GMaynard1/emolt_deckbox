import pandas as pd
import serial
import os
from datetime import datetime, timedelta


class GPSException(Exception):
    pass
    #print('GPS disconnected')

class GPS(object):

    def __init__(self, portID, path):
        self.s = None
        self.portID = portID
        self.autoSession = True
        self.df = pd.DataFrame()
        self.df_total = pd.DataFrame()
        self.line = []
        self.path = path

        try:
            self.s = serial.Serial(self.portID, 4800, timeout=None)

        except (Exception):
            print('Check GPS status')
            raise GPSException()

    def _ensureConnectionStatus(self):
        if (self.s == None or self.s.isOpen() == False):
            raise GPSException()

    def store_csv(self, path):
        self._ensureConnectionStatus()
        if len(self.df) != 0:
            self.df.to_csv(path, index=False, columns=['date', 'DATETIME', 'LATITUDE', 'latd', 'LONGITUDE', 'lond'], header=True)
    
    def store_all_csv(self):
        self._ensureConnectionStatus()
        if len(self.df_total != 0):
            gps = pd.DataFrame()
            gps['ti'], gps['da'] = self.df_total['DATETIME'].astype(float).astype(int).astype(str), self.df_total['date'].astype(str)
            gps['ti'] = gps.apply(lambda x: ((6 - len(x['ti'])) * '0' + x['ti']), axis=1)
            gps['da'] = gps.apply(lambda x: ((6 - len(x['da'])) * '0' + x['da']), axis=1)
            gps['ti'] = gps.da + ' ' + gps.ti
            gps['ti'] = pd.to_datetime(gps['ti'], format='%d%m%y %H%M%S')
            gps['DATETIME'] = self.df_total['DATETIME'].astype(float)
            self.df_total['LATITUDE'], self.df_total['LONGITUDE'] = self.df_total['LATITUDE'].astype(float), self.df_total[
                'LONGITUDE'].astype(float)
            gps['LATITUDE'] = self.df_total.apply(lambda x: round(int(x['LATITUDE'] / 100) + (x['LATITUDE'] / 100 % 1) * 100 / 60, 6) if x['latd'] == 'N' else -round(int(x['LATITUDE'] / 100) + (x['LATITUDE'] / 100 % 1) * 100 / 60, 6), axis=1)
            gps['LONGITUDE'] = self.df_total.apply(lambda x: round(int(x['LONGITUDE'] / 100) + (x['LONGITUDE'] / 100 % 1) * 100 / 60, 6) if x['lond'] == 'E' else -round(int(x['LONGITUDE'] / 100) + (x['LONGITUDE'] / 100 % 1) * 100 / 60, 6), axis=1)
            gps.set_index('ti', inplace=True)

            # surface = gps.resample('10T').mean().reset_index()
            gps = gps.resample('30S').mean().reset_index()  # Resamples data in 30 seconds interval
            gps['DATETIME'], gps['date'] = gps['DATETIME'].astype(float).astype(int).astype(str), gps['ti'].dt.date
            gps['DATETIME'] = gps.apply(lambda x: ((6 - len(x['DATETIME'])) * '0' + x['DATETIME']), axis=1)

            # gps['date'] = gps.apply(lambda x: ((6 - len(x['date'])) * '0' + x['date']), axis=1)
            gps['DATETIME'] = gps.date.astype(str) + ' ' + gps.DATETIME
            gps['DATETIME'] = pd.to_datetime(gps['DATETIME'], format='%Y-%m-%d %H%M%S')

            # surface['DATETIME'], surface['date'] = surface['DATETIME'].astype(float).astype(int).astype(str), self.df_total[
                # 'date'].astype(str)
            # surface['DATETIME'] = surface.apply(lambda x: ((6 - len(x['DATETIME'])) * '0' + x['DATETIME']), axis=1)
            # surface['date'] = surface.apply(lambda x: ((6 - len(x['date'])) * '0' + x['date']), axis=1)
            # surface['DATETIME'] = surface.date + ' ' + surface.DATETIME
            # surface['DATETIME'] = pd.to_datetime(surface['DATETIME'], format='%d%m%y %H%M%S')

            if os.path.isfile(self.path + 'gps/gps_merged.csv'):
                gps.to_csv(self.path + 'gps/gps_merged.csv', index=None, columns=['DATETIME', 'LATITUDE', 'LONGITUDE'], header=False, mode='a')
                # surface.to_csv('/home/pi/rtd_fixed/surface_data/surface.csv', index=None, columns=['DATETIME', 'LATITUDE', 'LONGITUDE'], header=False, mode='a')
            else:
                gps.to_csv(self.path + 'gps/gps_merged.csv', index=None, columns=['DATETIME', 'LATITUDE', 'LONGITUDE'], header=True)
                # surface.to_csv('/home/pi/rtd_fixed/surface_data/surface.csv', index=None, columns=['DATETIME', 'LATITUDE', 'LONGITUDE'], header=True)
            self.df_total = pd.DataFrame()

    def get_splitted_line(self):
        self._ensureConnectionStatus()
        try:
            self.line = self.s.readline().decode('utf-8').strip().split(',')
        except:
            # print("Unicode error: waiting till it finds GPS data...\n")
            self.get_splitted_line()

    def length(self):
        self._ensureConnectionStatus()
        return True if len(self.line) == 13 else False

    def id(self):
        self._ensureConnectionStatus()
        if self.length():
            return True if self.line[0] == '$GPRMC' else False

    def status(self):
        self._ensureConnectionStatus()
        if self.length():
            if self.line[2] == 'A':
                #print("GPS signal found")
                return True
            else:
                #print(datetime.utcnow())
                #print(self.line)
                #print("GPS signal not found")
                return False

    def close(self):
        self._ensureConnectionStatus()
        if self.s != None:
            self.s.close()
            self.s = None

    def add_df(self):
        self._ensureConnectionStatus() 
        self.get_splitted_line()
        if self.length() and self.id() and self.status():
            id, times, state, LATITUDE, latd, LONGITUDE, lond, _, _, date, _, _, _ = self.line
            #print (times)
            #print ('date is' +date)
            self.df = self.df.append(pd.DataFrame([[id, times, state, LATITUDE, latd, LONGITUDE, lond, 0, 0, date, 0, 0, 0]],
                                        columns=['id', 'DATETIME', 'state', 'LATITUDE', 'latd', 'LONGITUDE', 'lond', 'a', 'b',
                                                 'date', 'c', 'd', 'e']), ignore_index=True)
            self.df_total = self.df_total.append(pd.DataFrame([[id, times, state, LATITUDE, latd, LONGITUDE, lond, 0, 0, date, 0, 0, 0]],
                                        columns=['id', 'DATETIME', 'state', 'LATITUDE', 'latd', 'LONGITUDE', 'lond', 'a', 'b',
                                                 'date', 'c', 'd', 'e']), ignore_index=True)

    def print_line(self):
        self._ensureConnectionStatus()
        return self.line

    def reset_df(self):
        self.df_total = pd.DataFrame()

    def zip_file(self):
        df = pd.read_csv(self.path + 'gps/gps_merged.csv')
        df['DATETIME'] = pd.to_datetime(df['DATETIME'])
        df[df['DATETIME'] <= (datetime.now() - timedelta(days=7))].to_csv(self.path + 'logs/gps' + (datetime.now() - timedelta(days=7)).strftime('%d%m%y') + '.gz', compression='gzip', index=False)
        df = df[df['DATETIME'] > (datetime.now() - timedelta(days=7))]
        df.to_csv(self.path + 'gps/gps_merged.csv', index=False)
