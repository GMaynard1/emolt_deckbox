###########################################################################################
###### PROFILE PROCESSING
###########################################################################################

import pandas as pd
import os
import logging
from datetime import timedelta, datetime
import sys
sys.path.insert(1,'/home/pi/Desktop/')
import setup_rtd
import plot_profiles
from data_standardization import Standardize

logging.basicConfig(filename=setup_rtd.parameters['path'] + 'logs/main.log',
                    format='%(levelname)s %(asctime)s :: %(message)s',
                    level=logging.DEBUG)

class Load(object):
    def __init__(self):
        self.path = setup_rtd.parameters['path']
        self.checksalinity = False
        self.sensor = None
        self.l_merged = []

    def parse_profiles(self, data, file, sensor):
        l = []
        if sensor == 'Moana':
            file = file.split('/')[-1]
            moana, sn, num = file.split('.')[0].split('_')
        elif sensor == 'Lowell':
            lowell, sn, date, time = file.split('.')[0].split('_')
        din = data[data['PRESSURE'] < data['PRESSURE'].max() * 0.1]
        din = din.reset_index()
        din.loc[:, 'GAP'] = din['index'] - din['index'].shift(1)
        ldf = list(din['index'])
        lfiles = list(din[din['GAP'] > 10]['index'])

        lidx = [0]
        for i in range(len(lfiles) - 1):
            lt = ldf[ldf.index(lfiles[i]):ldf.index(lfiles[i + 1])]
            lidx.append(int(sum(lt) / len(lt)) + 1)
        lidx.append(len(data))

        c = 1
        for i in range(len(lidx) - 1):
            dn = data.iloc[lidx[i]:lidx[i + 1]]
            dn['DATETIME'] = pd.to_datetime(dn['DATETIME'])
            dn = dn[['DATETIME', 'TEMPERATURE', 'PRESSURE']]
            dn = dn[dn['PRESSURE'] > 0]
            if sensor == 'Moana':
                filename = '_'.join([moana, sn, str(c), num]) + '.csv' if c != 1 else '_'.join(
                    [moana, sn, num]) + '.csv'
            elif sensor == 'Lowell':
                dateti = dn.iloc[-1]['DATETIME']
                second, minute, hour, day, month, year = str(dateti.second), str(dateti.minute), str(dateti.hour), str(
                    dateti.day), str(dateti.month), str(dateti.year)
                if len(second) == 1:
                    second = '0' + second
                if len(minute) == 1:
                    minute = '0' + minute
                if len(hour) == 1:
                    hour = '0' + hour
                if len(day) == 1:
                    day = '0' + day
                if len(month) == 1:
                    month = '0' + month
                date = year + month + day
                time = hour + minute + second
                filename = '_'.join([lowell, sn, date, time]) + '.csv'
            else:
                filename = file
            self.l_merged.append(filename.split('.')[0])
            dn.to_csv(self.path + 'sensor/{sensor}/'.format(sensor=sensor) + filename, index=None)
            l.append([filename, dn])
            c += 1
        return l if len(l) > 1 else [[file, data]]

    def parse_segments(self, df):  # parse the dataframe into profiling down, fishing and profiling up
        df['DATETIME'] = pd.to_datetime(df['DATETIME'])
        df['DATEINT'] = (df['DATETIME'] - df['DATETIME'].min())
        df['DATEINT'] = df.apply(lambda row: row['DATEINT'].total_seconds(), axis=1)
        df['PRESSURE'] = df['PRESSURE'].astype(float)
        df['GAP_PRESSURE'] = abs(df['PRESSURE'] - df['PRESSURE'].quantile(0.9))

        # df['delta_time'] = df['DATETIME'].diff(periods=-1) / pd.offsets.Second(1)
        # df['vel'] = df['PRESSURE'].diff(periods=-1) / df['delta_time'] * 1000
        # df['vel_smooth'] = df['vel'].rolling(7, center=True, min_periods=1).mean()

        df['type'] = 3

        # True down and False up
        df['direction'] = df['PRESSURE'].shift(1) < df['PRESSURE']
        df['dir'] = df['direction'].rolling(10, center=True, min_periods=1).mean()

        # Direction and pressure
        df.loc[(df['dir'] > 0.5) & (df['GAP_PRESSURE'] > 0.5 * df['GAP_PRESSURE'].max()), 'dir'] = 1
        df.loc[(df['dir'] < 0.5) & (df['GAP_PRESSURE'] > 0.5 * df['GAP_PRESSURE'].max()), 'dir'] = 0

        df.loc[(df['dir'] == 1) & (df['GAP_PRESSURE'] > 0.5 * df['GAP_PRESSURE'].max()), 'direction'] = True
        df.loc[(df['dir'] == 0) & (df['GAP_PRESSURE'] > 0.5 * df['GAP_PRESSURE'].max()), 'direction'] = False

        std_bottom = df[(df['DATETIME'] > df['DATETIME'].quantile(0.1)) & (
                df['DATETIME'] < df['DATETIME'].quantile(0.9))]['PRESSURE'].std()

        nodown, noup = False, False
        if std_bottom < 0.2:
            # Smooth size to find the inflection point
            min_seg_size = 1
            max_down_pressure = df['PRESSURE'].iloc[:min_seg_size].max()
            while max_down_pressure < 0.9 * df['PRESSURE'].max():
                min_seg_size += 1
                max_down_pressure = df['PRESSURE'].iloc[:min_seg_size].max()

            if min_seg_size == 1:
                nodown = True

            min_seg_size = 1
            max_up_pressure = df['PRESSURE'].iloc[-min_seg_size:].max()
            while max_up_pressure < 0.9 * df['PRESSURE'].max():
                min_seg_size += 1
                max_up_pressure = df['PRESSURE'].iloc[-min_seg_size:].max()

            if min_seg_size == 1:
                noup = True

        else:
            # Smooth size to find the inflection point
            min_seg_size = 1
            max_down_pressure = df['PRESSURE'].iloc[:min_seg_size].max()
            while max_down_pressure < 0.5 * df['PRESSURE'].max():
                min_seg_size += 1
                max_down_pressure = df['PRESSURE'].iloc[:min_seg_size].max()

            min_seg_size = 1
            max_up_pressure = df['PRESSURE'].iloc[-min_seg_size:].max()
            while max_up_pressure < 0.5 * df['PRESSURE'].max():
                min_seg_size += 1
                max_up_pressure = df['PRESSURE'].iloc[-min_seg_size:].max()

        df.loc[:min_seg_size, 'direction'] = True
        df.loc[len(df) - min_seg_size:, 'direction'] = False

        lim_pressure = df[~df['direction']].iloc[0], df[df['direction']].iloc[-1]

        df.loc[:lim_pressure[0].name - 1, 'type'] = 2  # Profiling down
        df.loc[lim_pressure[1].name + 1:, 'type'] = 1  # Profiling up

        if nodown:
            df.loc[df['type'] == 2, 'type'] = 3

        if noup:
            df.loc[df['type'] == 1, 'type'] = 3

        gap_rows = (df['DATETIME'].iloc[-1] - df['DATETIME'].iloc[0]).total_seconds() / 60 / (len(df) - 1)
        if gap_rows > 25:
            df['type'] = 3

        return df

    def zip_file(self, filename, df):
        df.to_csv(self.path + 'merged/zip/' + filename + '.gz', compression='gzip', index=False)

class Merge(Load):
    def __init__(self):
        Load.__init__(self)

    def merge(self, l_rec_files, sensor, gear_type):
        num_hours = 146  # Number of hours taken from the GPS until now
        self.sensor = sensor
        ldata = []
        for file in l_rec_files:
            data, data_info = Standardize(sensor, file, self.path).data, Standardize(sensor, file, self.path).data_info
            #try:
            #    data_info.to_csv(self.path + 'sensor/sensor_info/' + file, index=None, header=True)
            #except ValueError:
            #    pass
            l_prof = self.parse_profiles(data, file, sensor)
            for filename, data in l_prof:
                data = data[data['PRESSURE'] > 0]
                if sensor == 'Moana':
                    try:
                        data = self.parse_segments(data)
                        
                        plot_profiles.Plotting(data)
                        
                    except:
                        pass

                elif sensor == 'Lowell':
                    data = data[data['PRESSURE'] > 2]  # uses eMOLT requirements to trim the bottom data
                    data.reset_index(drop=True, inplace=True)
                    data = data.iloc[10:-5]  # gets rid of the initial data due to the response delay
                    data.reset_index(drop=True, inplace=True)

                data = data[['DATETIME', 'TEMPERATURE', 'PRESSURE']] if 'SALINITY' not in data else data[
                    ['DATETIME', 'TEMPERATURE', 'PRESSURE', 'SALINITY']]

                GPS = pd.read_csv(self.path + 'gps/gps_merged.csv')
                GPS['DATETIME'] = pd.to_datetime(GPS['DATETIME'], format='%Y-%m-%d %H:%M:%S')
                GPS = GPS.sort_values(by=['DATETIME'])
                GPS = GPS[GPS['DATETIME'] > (datetime.utcnow() - timedelta(hours=num_hours))].reset_index(drop=True)

                logging.debug('Merging CTD file') if self.checksalinity else logging.debug('Merging TD file')

                print('Merging...')

                merged_data = self.merge_mobile(GPS, data) if 'l' in gear_type else self.merge_fixed(GPS, data)

                #print(merged_data)
                if len(merged_data) == 0: continue

                merged_data = merged_data[['DATETIME', 'TEMPERATURE', 'PRESSURE', 'SALINITY', 'LATITUDE',
                                           'LONGITUDE']] if 'SALINITY' in merged_data else merged_data[
                    ['DATETIME', 'TEMPERATURE', 'PRESSURE', 'LATITUDE', 'LONGITUDE']]
                merged_data['TEMPERATURE'] = round(merged_data['TEMPERATURE'], 1)
                merged_data['PRESSURE'] = round(merged_data['PRESSURE'], 1)
                #print (filename)
                #print (self.path)
                merged_data.to_csv(self.path + 'towifi/'+filename,
                                   index=None)

                self.zip_file(filename, merged_data)
                ldata.append([filename, merged_data])

        return ldata

    def merge_mobile(self, GPS, sensor):  # GPS and sensors are DataFrames
        time_s = sensor['DATETIME'].iloc[0] - timedelta(seconds=10)  # time starts
        time_e = sensor['DATETIME'].iloc[-1] + timedelta(seconds=5)  # time ends

        print('Starting sensor time:', time_s, 'and ending sensor time:', time_e)

        try:
            gps_before = GPS[GPS['DATETIME'] < time_s].index[-1]
            gps_after = GPS[GPS['DATETIME'] > time_e].index[0]
            # print(gps_before, gps_after)
            gps_profile = GPS.iloc[gps_before:gps_after + 1].reset_index(drop=True)
        except:
            print('GPS data missing for the sensor profile')
            return pd.DataFrame()

        if abs(gps_profile['DATETIME'].iloc[0] - sensor['DATETIME'].iloc[0]).total_seconds() / 60 > 60 or abs(
                gps_profile['DATETIME'].iloc[-1] - sensor['DATETIME'].iloc[-1]).total_seconds() / 60 > 60:
            print('Time difference between the first or last sensor point and the first or last GPS point is greater than 1h')
            return pd.DataFrame()

        sensor = pd.concat([gps_profile, sensor], sort=True, ignore_index=True).sort_values(
            by=['DATETIME']).reset_index(
            drop=True)

        sensor['LATITUDE'], sensor['LONGITUDE'] = sensor['LATITUDE'].interpolate(), sensor[
            'LONGITUDE'].interpolate()

        sensor = sensor.dropna().reset_index(drop=True)
        sensor = sensor.fillna(method='ffill')
        sensor = sensor.fillna(method='bfill')

        return sensor  # Merged mobile dataframe

    def merge_fixed(self, GPS, sensor):
        time1 = sensor.iloc[0]['DATETIME']
        time2 = sensor.iloc[-1]['DATETIME']
        print('Initial sensor time:', time1, 'and final sensor time:', time2)

        difi, diff = 10000, 10000
        lat1, lat2, lon1, lon2 = 200, 200, 200, 200  # set impossible location

        data1 = [GPS[(time1 > GPS['DATETIME'])].reset_index(drop=True),
                 GPS[(time1 < GPS['DATETIME'])].reset_index(drop=True)]

        if len(data1[0]) > 0:
            difi = (time1 - data1[0].iloc[-1].DATETIME).total_seconds()
        if len(data1[1]) > 0:
            diff = (data1[1].iloc[0].DATETIME - time1).total_seconds()

        dif_time = min(difi, diff)

        if dif_time / 60 < 10:
            if dif_time == difi:
                lat1, lon1 = data1[0].iloc[-1]['LATITUDE'], data1[0].iloc[-1]['LONGITUDE']
            else:
                lat1, lon1 = data1[1].iloc[0]['LATITUDE'], data1[1].iloc[0]['LONGITUDE']

        data2 = [GPS[(time2 > GPS['DATETIME'])].reset_index(drop=True),
                 GPS[(time2 < GPS['DATETIME'])].reset_index(drop=True)]

        if len(data2[0]) > 0:
            diff = (time2 - data2[0].iloc[-1].DATETIME).total_seconds()
        if len(data2[1]) > 0:
            difi = (data2[1].iloc[0].DATETIME - time2).total_seconds()

        dif_time = min(difi, diff)

        if dif_time / 60 < 10:
            if dif_time == difi:
                lat2, lon2 = data2[0].iloc[-1]['LATITUDE'], data2[0].iloc[-1]['LONGITUDE']
            else:
                lat2, lon2 = data2[1].iloc[0]['LATITUDE'], data2[1].iloc[0]['LONGITUDE']
        
        if lat1 == 200 and lon1 == 200:
            fixed_lat = lat2
            fixed_lon = lon2
        elif lat2 == 200 and lon2 == 200:
            fixed_lat = lat1
            fixed_lon = lon1
        else:
            fixed_lat = round((lat1 + lat2) / 2, 6)
            fixed_lon = round((lon1 + lon2) / 2, 6)

        if fixed_lat == 200 and fixed_lon == 200:
            return pd.DataFrame()

        sensor['LATITUDE'] = fixed_lat
        sensor['LONGITUDE'] = fixed_lon

        return sensor  # Merged fixed dataframe