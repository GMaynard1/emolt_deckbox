import pandas as pd
import setup_rtd
from datetime import timedelta

class Standardize(object):
    def __init__(self, sensor, filename, path):
        self.sensor = sensor
        self.filename = filename
        self.path = path
        self.data = pd.DataFrame()
        self.data_info = pd.DataFrame()
        if sensor == 'Moana':
            self.Moana()
        elif sensor == 'NKE':
            self.NKE()
        elif sensor == 'Lowell':
            self.Lowell()

    def Moana(self):
        try:
            self.data = pd.read_csv(self.path + 'logs/raw/Moana/' + self.filename)
            self.data['DATETIME'] = pd.to_datetime(self.data['DATETIME'])
        except:
            self.data_info = pd.read_csv(self.path + 'logs/raw/Moana/' + self.filename, nrows=8)
            self.data = pd.read_csv(self.path + 'logs/raw/Moana/' + self.filename, header=9)
            self.data['DATETIME'] = pd.to_datetime(self.data.Date + ' ' + self.data.Time, format='%Y-%m-%d %H:%M:%S')
            self.data.rename(columns={'Temperature C': 'TEMPERATURE', 'Depth Decibar': 'PRESSURE'}, inplace=True)
        self.data['TEMPERATURE'] = pd.to_numeric(self.data['TEMPERATURE'])
        self.data['PRESSURE'] = pd.to_numeric(self.data['PRESSURE'])
        self.data['TEMPERATURE'] = self.data.apply(lambda x: round(x['TEMPERATURE'], 4), axis=1)
        self.data['PRESSURE'] = self.data.apply(lambda x: round(x['PRESSURE'], 3), axis=1)

    def NKE(self):
        self.data = pd.read_csv(self.path + 'logs/raw/NKE/' + self.filename, error_bad_lines=False)
        checksalinity = "CH3:Salinity(PSU)" in self.data  # Check if there is salinity data present
        if checksalinity:
            self.data.rename(
                columns={'Timestamp(Standard)': 'DATETIME', 'CH1:Temperature(degC)': 'TEMPERATURE',
                         'CH2:Depth(dbar)': 'PRESSURE',
                         'CH3:Salinity(PSU)': 'SALINITY'},
                inplace=True)
        else:
            print('Temperature-Depth data available')
            self.data.rename(
                columns={'Timestamp(Standard)': 'DATETIME', 'CH0:Temperature(degC)': 'TEMPERATURE',
                         'CH1:Depth(dbar)': 'PRESSURE'},
                inplace=True)
        self.data, self.data_info = self.data[self.data.PRESSURE.notnull()].round(3), self.data[self.data.PRESSURE.isnull()]
        self.data['DATETIME'] = pd.to_datetime(self.data['DATETIME'], format='%Y-%m-%d %H:%M:%S')
        self.data['TEMPERATURE'] = pd.to_numeric(self.data['TEMPERATURE'])
        self.data['TEMPERATURE'] = self.data.apply(lambda x: round(x['TEMPERATURE'], 3), axis=1)
        self.data['PRESSURE'] = self.data.apply(lambda x: round(x['PRESSURE'], 3), axis=1)
        self.data.DATETIME -= timedelta(hours=setup_rtd.parameters['time_diff_nke'])

    def Lowell(self):
        self.data = pd.read_csv(self.path + 'logs/raw/Lowell/' + self.filename, sep=',')
        self.data.rename(columns={'Datetime': 'DATETIME', 'Temperature (C)': 'TEMPERATURE', 'Depth (m)': 'PRESSURE'},
                    inplace=True)  # BDC standards
        self.data['DATETIME'] = pd.to_datetime(self.data['DATETIME'])
        self.data['TEMPERATURE'] = pd.to_numeric(self.data['TEMPERATURE'])
        self.data['PRESSURE'] = pd.to_numeric(self.data['PRESSURE'])
        self.data['TEMPERATURE'] = self.data.apply(lambda x: round(x['TEMPERATURE'], 3), axis=1)
        self.data['PRESSURE'] = self.data.apply(lambda x: round(x['PRESSURE'], 3), axis=1)
        self.data = self.data[['DATETIME', 'TEMPERATURE', 'PRESSURE']]


