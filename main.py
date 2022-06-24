###########################################################################################
###### MAIN SCRIPT
#recovery from 6/13/2022 version
#setup_rtd.py is on the desktop
#V 1.01
###########################################################################################
import sys
sys.path.insert(1,'/home/pi/Desktop/')
import time
import os
import serial
import pandas as pd
import numpy as np
from merge import *
from ftp_reader import *
from gps_reader import *
import serial.tools.list_ports as stlp

import paramiko
from pylab import mean, std
from connectivity import Connection
from sftp_aws import Transfer
from datetime import datetime
import datetime as dt
import logging
import setup_rtd
import paramiko
import ftplib
import warnings
import glob
import hrock
from hrock import MoExample
warnings.filterwarnings('ignore')

logging.basicConfig(filename=setup_rtd.parameters['path'] + 'logs/main.log',
                    format='%(levelname)s %(asctime)s :: %(message)s',
                    level=logging.DEBUG)
logging.debug('Start recording..')


class Profile(object):
    def __init__(self, sensor_type):
        self.vessel_name = setup_rtd.metadata['vessel_name']  # depending on the vessel
        self.l_sensors = sensor_type
        self.tow_num = len(os.listdir(setup_rtd.parameters['path'] + 'merged'))
        self.path = setup_rtd.parameters['path']
        self.gear = setup_rtd.metadata['gear_type']
        self.moana_SN = setup_rtd.metadata['moana_SN']
        self.transmitter= setup_rtd.metadata['transmitter']
        self.vessel_num = str(setup_rtd.metadata['vessel_num'])
    def main(self):
        device = self.list_ports('USB-Serial Controller D')
        gps = GPS(device, self.path)
        
        #print (device_trans)
        for sensor in self.l_sensors:
            # NKE necessary variable
            if sensor == 'NKE':
                ftp_conn = sensor(self.path)

            # Moana necessary variables
            elif sensor == 'Moana':
                d_moana_ini = {sn: os.listdir(self.path + 'logs/raw/Moana/' + sn) for sn in os.listdir(self.path + 'logs/raw/Moana/')}

            # Lowell necessary variable
            elif sensor == 'Lowell':
                l_lowell = os.listdir(self.path + 'logs/raw/Lowell')

        old_time = datetime.now()
        start_sync_time=0

        while True:
            curr_time = datetime.now()
            gps.add_df()
            
            
            #self.daily_report(curr_time)
            
            if (curr_time - old_time).total_seconds() / 60 > 5:
                logging.debug('Adding data to gps file')
                print('Adding data to gps file')
                gps.store_all_csv()
                if start_sync_time==0:     
                    self.sync_time()
                    start_sync_time+=1
                self.wifi()
                self.scp()
                self.daily_report(curr_time)
                old_time = curr_time
                stats = os.stat(self.path + 'gps/gps_merged.csv')
                if stats.st_size > 1728000:
                    gps.zip_file()

            for sensor in self.l_sensors:
                if sensor == 'NKE':
                    try:
                        if ftp_conn.file_received():
                            logging.debug('New file downloading: ')
                            l_rec_file = ftp_conn.transfer()
                            logging.debug('Downloading completed ' + l_rec_file[0])
                            logging.debug('Adding data to gps file')
                            print('Adding data to gps file')
                            gps.store_all_csv()
                            try:
                                self.connect_wireless(l_rec_file, sensor)
                            except:
                                pass
                            ldata = Merge().merge(l_rec_file, sensor, self.gear)  # set sensor type as WiFi or Bluetooth
                            self.cloud(ldata, sensor)

                            print('waiting...')
                            time.sleep(5)

                            ftp_conn = sensor(self.path)
                    except ftplib.all_errors:
                        ftp_conn.reconnect()

                elif sensor == 'Moana':
                    with open(self.path + 'status.txt') as f_ble:
                        d_moana = {sn: os.listdir(self.path + 'logs/raw/Moana/' + sn) for sn in os.listdir(self.path + 'logs/raw/Moana/')}
                        l_rec_file = []
                        if len(d_moana_ini) != len(d_moana):
                            sn_news = [sn for sn in d_moana if sn not in d_moana_ini]
                            for sn_new in sn_news:
                                if '1' in f_ble.readline():
                                    l_rec_file = [sn_new + '/' + file for file in d_moana[sn_new]]
                                    l_rec_file.sort()
                        else:
                            for sn in d_moana:
                                if len(d_moana_ini[sn]) != len(d_moana[sn]):
                                    if '1' in f_ble.readline():
                                        l_rec_file = [sn + '/' + file for file in d_moana[sn] if file not in d_moana_ini[sn]]
                                        l_rec_file.sort()

                        if len(l_rec_file) > 0:
                            print('New Moana sensor file completely transferred to the RPi')
                            logging.debug('Adding data to gps file')
                            print (l_rec_file)
                            self.moana_SN=l_rec_file[0].split('_')[2]
                            print('Adding data to gps file')
                            gps.store_all_csv()

                            try:
                                self.connect_wireless(l_rec_file, sensor)
                            except:
                                pass
                            ldata = Merge().merge(l_rec_file, sensor,
                                                  self.gear)  # set sensor type as WiFi or Bluetooth

                            leMOLT = [self.add_eMOLT_header(e[0], e[1], sensor) for e in ldata]  # creates files with eMOLT format
                            #print (data)
                            self.eMOLT_data_trans(leMOLT)
                            
                            # self.eMOLT_cloud(leMOLT)  # sends merged data to eMOLT endpoint
                            #self.cloud(ldata, sensor)
                            d_moana_ini = d_moana.copy()
                            os.system('sudo reboot')
                            print('waiting for the next profile...')

                elif sensor == 'Lowell':  # there are more than one type of sensor onboard
                    ln_lowell = os.listdir(self.path + 'logs/raw/Lowell')
                    if len(ln_lowell) > len(l_lowell):
                        print('New sensor data from Lowell logger')
                        n_lowell = [e for e in ln_lowell if e not in l_lowell]  # stores only new Lowell data
                        gps.store_all_csv()  # necessary to store any gps data between the 10 minutes gps gap
                        self.connect_wireless(n_lowell, 'Lowell')  # sends raw data to BDC endpoint
                        ldata = Merge().merge(n_lowell, sensor, self.gear)  # merges sensor data and GPS
                        
                        #leMOLT = [self.add_eMOLT_header(e[0], e[1], sensor) for e in ldata]  # creates files with eMOLT format
                        # self.eMOLT_cloud(leMOLT)  # sends merged data to eMOLT endpoint
                        self.cloud(ldata, sensor)  # sends merged data to BDC endpoint
                        print('waiting for the next profile...')

    def cloud(self, ldata, sensor):
        for filename, df in ldata:
            if len(df) < 2:
                print('Merged file is too small to be uploaded')
                continue
            conn_type = Connection().conn_type()
            if conn_type:  # wifi
                print('There is internet connection')
                Transfer('/home/ec2-user/rtd/vessels/{vess}/merged/{sensor}/'.format(
                    vess=self.vessel_name, sensor=sensor)).upload(
                    'merged/{sensor}/'.format(sensor=sensor) + filename, filename)
                print('Data transferred successfully to the AWS endpoint')
            else:
                logging.debug('There is no network available')
                print('There is no network available, merged data has not been uploaded, queued routine will try to upload the data later')
                df.to_csv(self.path + 'queued/{sensor}/'.format(sensor=sensor) + filename, index=False)
            self.tow_num += 1

    def connect_wireless(self, l_rec_file, sensor):
        conn_type = Connection().conn_type()
        if conn_type:
            data_gps = pd.read_csv(self.path + 'gps/gps_merged.csv')
            gps_name = 'gps' + datetime.utcnow().strftime('%y%m%d') + '.csv'
            data_gps.to_csv(self.path + 'logs/gps/' + gps_name, index=False)
            try:
                Transfer('/home/ec2-user/rtd/vessels/' + self.vessel_name + '/').upload('logs/gps/' + gps_name,
                                                                                        'gps/' + gps_name)
            except paramiko.ssh_exception.SSHException:
                logging.debug('GPS data was not uploaded')
                print('GPS data was not uploaded')

            for file in l_rec_file:
                Transfer('/home/ec2-user/rtd/vessels/' + self.vessel_name + '/').upload(
                    'logs/raw/{sensor}/'.format(sensor=sensor) + file, 'sensor/{sensor}/'.format(sensor=sensor) + file.split('/')[-1])

    def eMOLT_cloud(self, ldata):
        for filename, df in ldata:
            # print u
            session = ftplib.FTP('', '', '')
            file = open(filename, 'rb')
            session.cwd("/BDC")
            # session.retrlines('LIST')               # file to send
            session.storbinary("STOR " + filename.split('/')[-1], fp=file)  # send the file
            # session.close()
            session.quit()  # close file and FTP
            time.sleep(1)
            file.close()
            print(filename.split('/')[-1], 'uploaded in eMOLT endpoint')
        
    def add_eMOLT_header(self, filename, data, sensor):
        date_file = data['DATETIME'].iloc[-1]
        #date_file = datetime.strptime(date_file, '%Y-%m-%d %H:%M:%S')
        date_file = date_file.strftime('%Y%m%d_%H%M%S')
        logger_timerange_lim = setup_rtd.metadata['time_range']
        logger_pressure_lim = setup_rtd.metadata['Fathom'] * 1.8288  # convert from fathom to meter
        transmit = setup_rtd.metadata['transmitter']
        boat_type = setup_rtd.metadata['gear_type']
        vessel_num = str(setup_rtd.metadata['vessel_num'])
        vessel_name = setup_rtd.metadata['vessel_name']
        tilt = setup_rtd.metadata['tilt']
        if sensor == 'Lowell':
            MAC_FILTER = [setup_rtd.metadata['mac_addr']]
            MAC_FILTER[0] = MAC_FILTER[0].lower()
            new_filename = self.path + 'merged/eMOLT/{sensor}/'.format(sensor=sensor) + 'li_{SN}_{date}_{vessel}.csv'.format(SN=MAC_FILTER[0][-5:], date=date_file, vessel=vessel_name)
        elif sensor == 'Moana':
            MAC_FILTER = [self.moana_SN]
            new_filename = self.path + 'merged/eMOLT/{sensor}/'.format(sensor=sensor) + 'zt_{SN}_{date}_{vessel}.csv'.format(SN=MAC_FILTER[0][-5:], date=date_file, vessel=vessel_name)
        header_file = open(self.path + 'header.csv', 'w')
        header_file.writelines('Probe Type,{sensor}\nSerial Number,'.format(sensor=sensor) + MAC_FILTER[0][
                                                                     -5:] + '\nVessel Number,' + vessel_num + '\nVessel Name,' + vessel_name + '\nDate Format,YYYY-MM-DD\nTime Format,HH24:MI:SS\nTemperature,C\nDepth,m\n')  # create header with logger number
        header_file.close()
        
        # AFTER GETTING THE TD DATA IN A DATAFRAME
        data.rename(columns={'DATETIME': 'datet(GMT)', 'TEMPERATURE': 'Temperature (C)', 'PRESSURE': 'Depth (m)', 'LATITUDE': 'lat', 'LONGITUDE': 'lon'},
                    inplace=True)

        data['HEADING'] = 'DATA'  # add header DATA line
        data.reset_index(level=0, inplace=True)
        data.index = data['HEADING']
        data = data[['datet(GMT)', 'lat', 'lon', 'Temperature (C)', 'Depth (m)']]
        data.to_csv(self.path + 'merged/{sensor}/{file}'.format(sensor=sensor, file=filename[:-4]) + '_S1.csv')
        
        os.system('cat ' + self.path + 'header.csv ' + self.path + 'merged/{sensor}/{file}_S1.csv > '.format(sensor=sensor, file=filename[:-4]) + new_filename)
        os.system('rm ' + self.path + 'merged/{sensor}/{file}_S1.csv'.format(sensor=sensor, file=filename[:-4]))
        
        print('New file created as {file} to be sent to eMOLT endpoint'.format(file=new_filename))
        return new_filename, data
    
    def eMOLT_data_trans(self, lMOLT): 
        #print ('1')
        for filename, data in lMOLT:
            #print (data['Depth (m)'])
            dft=data.ix[(data['Depth (m)']>0.85*max(data['Depth (m)']))]
            #print (dft)
            meantemp=str(int(round(np.mean(dft['Temperature (C)'][0:-2]),2)*100)).zfill(4)
            #print ('meantemp'+meantemp)
            sdeviatemp=str(int(round(np.std(dft['Temperature (C)'][0:-2]),2)*100)).zfill(4)
            #print ('sdev'+sdeviatemp)
            time_delta = (dft['datet(GMT)'].iloc[-1] - dft['datet(GMT)'].iloc[0])
            total_seconds = time_delta.total_seconds()
            minutes = total_seconds/60
            timerange=str(int(minutes)).zfill(5) #logger time interval is 1.5 minutes put in hours
            print (timerange)
            meandepth=str(abs(int(round(mean(dft['Depth (m)'].values))))).zfill(3)
            rangedepth=str(abs(int(round(max(dft['Depth (m)'].values)-min(dft['Depth (m)'].values))))).zfill(3)
            print ('meandepth'+meandepth+'rangedepth'+rangedepth+'timerange'+timerange+'temp'+meantemp+'sdev'+sdeviatemp+' logger name'+self.moana_SN)
            data_gps = pd.read_csv(self.path + 'gps/gps_merged.csv')
                        #print (data_gps['LATITUDE'].iloc[-1])
            lat_1=str(data_gps['LATITUDE'].iloc[-1])[:8]
            lon_1=str(data_gps['LONGITUDE'].iloc[-1])[:8]
            daily_ave=''
            if 'f' in self.gear:
                try:    
                        print ("it is Fixed")
                        dft.set_index('datet(GMT)',inplace=True)
                        #dft.drop(['HEADING'])
                        
                        dft.index=pd.to_datetime(dft.index)
                        tsod=dft.resample('D',how=['count','mean','median','min','max','std'],loffset=dt.timedelta(hours=-12)) #creates daily averages,'-12' does not mean anything, only shows on datetime result 
                        
                        tsod=dft.resample('D',how=['mean'],loffset=dt.timedelta(hours=-12))
                        print (tsod)
                        if len(tsod)>5:
                                                #temp5=[str(i).rjust(4,'f') for i in tsod.iloc[-5:]['Temperature (C)']['mean']]
                            temp5=[str(int(round(float(i),2)*100)).zfill(4) for i in tsod.iloc[-6:-1]['Temperature (C)']['mean']]
                                                #tsod.ix[tsod['count']<minnumperday,['mean','median','min','max','std']] = 'NaN' # set daily averages to not-a-number if not enough went into it
                        else:
                            temp5=[str(int(round(float(i),2)*100)).zfill(4) for i in tsod.iloc[:-1]['Temperature (C)']['mean']]  
                            for i in temp5:
                                daily_ave+=i
                            print ('daily ave '+daily_ave)
                except:
                        daily_ave='' #add number '1' to the end of sending message to make logger serial number complete.   
            #print ("trans data")
            device_trans = self.list_ports('TTL232R-3V3 - TTL232R-3V3')
            if self.vessel_num =='99': # if vessel num is 99, this is a test  
                message=str(lat_1)+','+str(lon_1)+','+meandepth+rangedepth+timerange+meantemp+sdeviatemp+'eee'+self.moana_SN+daily_ave+'uc'
            else:
                message=str(lat_1)+','+str(lon_1)+','+meandepth+rangedepth+timerange+meantemp+sdeviatemp+'eee'+self.moana_SN+daily_ave+'u'
            print (message)
            MoExample (device_trans,message)
            print ('data transmitted by Rock ')
            
            #
            return
    def wifi(self):
      if not os.path.exists(self.path+'merged/uploaded_files'):
        os.makedirs(self.path+'merged/uploaded_files')      
      if not os.path.exists(self.path+'merged/uploaded_files/myfile.dat'):
          open(self.path+'merged/uploaded_files/myfile.dat','w').close()
      #software updates
      import time
      
      
      if 3>2:
            files=[]
            files.extend(sorted(glob.glob(self.path+'merged/eMOLT/Moana/*.csv')))
            #files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/error*')))
              
            with open(self.path+'merged/uploaded_files/myfile.dat') as f:
                content = f.readlines()        
            upfiles = [line.rstrip('\n') for line in open(self.path+'merged/uploaded_files/myfile.dat')]
            #print (upfiles)

            #f=open('../uploaded_files/myfile.dat', 'rw')
            dif_data=list(set(files)-set(upfiles))
            #print dif_data
            if dif_data==[]:
                
                time.sleep(1)
                return
            #print (dif_data)
            try:
                for u in dif_data:
                    import time
                    #print u
                    session = ftplib.FTP('66.114.154.52','huanxin','123321')
                    file = open(u,'rb') 
                    session.cwd("/Moanadata")  
                    #session.retrlines('LIST')               # file to send
                    #session.storbinary("STOR "+u.split('/')[-1], open(u, 'r'))   # send the file
                    session.storbinary("STOR " + u.split('/')[-1], fp=file)
                    #session.close()
                    session.quit()# close file and FTP
                    time.sleep(1)
                    file.close() 
                    #print u[24:]
                    #os.rename('C:/Program Files (x86)/Aquatec/AQUAtalk for AQUAlogger/DATA/'+u[:7]+'/'+u[8:], 'C:/Program Files (x86)/Aquatec/AQUAtalk for AQUAlogger/uploaded_files/'+u[8:])
                    #print u[24:]+' uploaded'
                    #os.rename(u[:7]+'/'+u[8:], "uploaded_files/"+u[8:]) 
                    time.sleep(1)                     # close file and FTP
                    f=open(self.path+'merged/uploaded_files/myfile.dat','a+')
                    #print 11111111111111111111111111111
                    #print 'u:'+u
                    f.writelines(u+'\n')
                    f.close()
                print ('all files are uploaded by ftp')
                #os.system('sudo ifdown wlan0')
                time.sleep(1500)
                return
            except:
                return
      else:
            #import time
            #print 'no wifi'
            time.sleep(1)
            
            return
    def scp(self):
      if not os.path.exists(self.path+'merged/uploaded_files'):
        os.makedirs(self.path+'merged/uploaded_files')      
      if not os.path.exists(self.path+'merged/uploaded_files/scp_myfile.dat'):
          open(self.path+'merged/uploaded_files/scp_myfile.dat','w').close()
      #software updates
      import time
      
      
      if 3>2:
            files=[]
            files.extend(sorted(glob.glob(self.path+'merged/eMOLT/Moana/*.csv')))
            #files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/error*')))
              
            with open(self.path+'merged/uploaded_files/scp_myfile.dat') as f:
                content = f.readlines()        
            upfiles = [line.rstrip('\n') for line in open(self.path+'merged/uploaded_files/scp_myfile.dat')]
            #print (upfiles)

            #f=open('../uploaded_files/myfile.dat', 'rw')
            dif_data=list(set(files)-set(upfiles))
            
            if dif_data==[]:
                
                time.sleep(1)
                return
            
            try:
                k=paramiko.RSAKey.from_private_key_file('/home/pi/.ssh/emolt_dev_pi-emolt-openssh')
                c=paramiko.SSHClient()
                c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                c.connect(hostname='73.114.111.175',port='1111',username='pi-emolt',pkey=k)
                
                sftp=c.open_sftp()
                for u in dif_data:
                    import time
                    #print (u)
                    sftp.put(u, '/home/pi-emolt/all_raw/'+u.split('/')[-1])
                    time.sleep(1)                     # close file and FTP
                    f=open(self.path+'merged/uploaded_files/scp_myfile.dat','a+')
                    #print 11111111111111111111111111111
                    #print ('u:'+u)
                    f.writelines(u+'\n')
                    f.close()
                print ('all files are uploaded by scp')
                sftp.close()
                #os.system('sudo ifdown wlan0')
                time.sleep(1500)
                return
            except:
                return
      else:
            #import time
            #print 'no wifi'
            time.sleep(1)
            
            return  

    def daily_report(self,curr_time):
                    if '12:11:00'<str(curr_time.time())<'12:28:00' or '22:45:00'<str(curr_time.time())<'22:59:00':
                        data_gps = pd.read_csv(self.path + 'gps/gps_merged.csv')
                        #print (data_gps['LATITUDE'].iloc[-1])
                        lat_1=str(data_gps['LATITUDE'].iloc[-1])[:8]
                        lon_1=str(data_gps['LONGITUDE'].iloc[-1])[:8]
                        device_trans = self.list_ports('TTL232R-3V3 - TTL232R-3V3')
                        message=str(lat_1)+','+str(lon_1)+',1111111111'
                        #print (message)
                        #print (device_trans)
                        MoExample (device_trans,message)
                        time.sleep(700)
                    else:
                        return
    def list_ports(self, desc):
        list_usb = []
        if sys.platform.startswith('linux'):
            list_usb = serial.tools.list_ports.comports()

        for port in list_usb:
            try:
                if port.description == desc:
                    return port.device
            except (OSError, serial.SerialException):
                print('GPS puck is not connected')
                pass
        return
    def sync_time(self):
        df=pd.read_csv(self.path + 'gps/gps_merged.csv')
        last_time=df['DATETIME'].iloc[-1]
        
        os.system('sudo timedatectl set-ntp 0')
        
        os.system("sudo timedatectl set-time '"+ str(last_time)+"'")
        os.system('sudo timedatectl set-ntp 1')
        time.sleep(1)
        return
        
        


# when power on
while True:
    try:
        print("RPi started recording the main routine.\n")
        Profile(setup_rtd.parameters['sensor_type']).main()
    except:
       print('Unexpected error:', sys.exc_info()[0])
       time.sleep(60)