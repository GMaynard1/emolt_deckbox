# set of functions used in generating plots in the wheelhouse
# with program running parallel with "getmatp.py" call "wxpage.py"
# where it plots the record and generates output file
# where it now includes the "getclim" function to post climatology
#updates on
import glob
import ftplib
import shutil
from shutil import copyfile
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import datetime
from datetime import datetime as dt
from pylab import *
import pandas as pd
from pandas import *
import time
import os
import numpy as np
#from gps import *
from time import *
import threading

def parse(datet):
    from datetime import datetime
    dt=datetime.strptime(datet,'%Y-%m-%dT%H:%M:%S')
    return dt

def parse2(datet):
    from datetime import datetime
    dt=datetime.strptime(datet,'%Y-%m-%d %H:%M:%S')
    return dt    
def gmt_to_eastern(times_gmt):
    import datetime
    times=[]
    eastern = pytz.timezone('US/Eastern')
    gmt = pytz.timezone('Etc/GMT')
    for i in range(len(times_gmt)):
        date = datetime.datetime.strptime(str(times_gmt[i]),'%Y-%m-%d %H:%M:%S')
        date_gmt=gmt.localize(date)
        easterndate=date_gmt.astimezone(eastern)
        times.append(easterndate)
    return times
def dm2dd(lat,lon):
    #converts lat, lon from decimal degrees,minutes to decimal degrees
    (a,b)=divmod(float(lat),100.)   
    aa=int(a)
    bb=float(b)
    lat_value=aa+bb/60.
    if float(lon)<0:
        (c,d)=divmod(abs(float(lon)),100.)
        cc=int(c)
        dd=float(d)
        lon_value=cc+(dd/60.)
        lon_value=-lon_value
    else:
        (c,d)=divmod(float(lon),100.)
        cc=int(c)
        dd=float(d)
        lon_value=cc+(dd/60.)
    return lat_value, -lon_value
def c2f(c):
    #convert Celsius to Fahrenheit
    f = c * 1.8 + 32
    return f
def getclim(yrday=str(int(dt.now().strftime('%j'))),var='Bottom_Temperature/BT_'): 
    # gets climatology of Bottom_Temperature, Surface_Temperature, Bottom_Salinity, or Surface_Salinity
    # as calculated by Chris Melrose from 30+ years of NEFSC CTD data on the NE Shelf provided to JiM in May 2018 
    # where "lat1", "lon1", and "yrday" are the position and yearday of interest (defaulting to today)
    # where "var" is the variable of interest (defaulting to Bottom_Temperature) 
    # inputdir='/net/data5/jmanning/clim/' # hardcoded directory name where you need to explode the "Data for Manning.zip"
    # assumes an indidividual file is stored in the "<inputdir>/<var>" directory for each yearday
    inputdir_csv='/home/pi/Desktop/towifi/'
    inputdir='/home/pi/clim/' # hardcoded directory name
    dflat=pd.read_csv(inputdir+'LatGrid.csv',header=None)
    dflon=pd.read_csv(inputdir+'LonGrid.csv',header=None)
    lat=np.array(dflat[0])   # gets the first col (35 to 45)
    lon=np.array(dflon.ix[0])# gets the first row (-75 to -65)
    clim=pd.read_csv(inputdir+var+yrday+'.csv',header=None) # gets bottom temp for this day of year
    files=(glob.glob(inputdir_csv+'*.csv'))
    files.sort(key=os.path.getmtime) # gets all the csv files in the towfi directory
    dfcsv=pd.read_csv(files[-1],sep=',',skiprows=8)
    [lat1,lon1]=dm2dd(float(dfcsv['lat'][0]),float(dfcsv['lon'][0]))
    idlat = np.abs(lat - lat1).argmin() # finds the neareast lat to input lat1
    idlon = np.abs(lon - lon1).argmin() # finds the neareast lon to input lon1
    return clim[idlon][idlat]

def create_pic():

      tit='Temperature and Angle'

      if not os.path.exists('/home/pi/Desktop/Pictures'):
        os.makedirs('/home/pi/Desktop/Pictures')


   

      if not os.path.exists('../uploaded_files'):
        os.makedirs('../uploaded_files')
      n=0  
      
      try:
            files=[]
            files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/*T.txt')))
            if not os.path.exists('../uploaded_files/mypicfile.dat'):
                open('../uploaded_files/mypicfile.dat','w').close() 
            #print files  
            with open('../uploaded_files/mypicfile.dat','r') as f:
                content = f.readlines()
                f.close()
            upfiles = [line.rstrip('\n') for line in open('../uploaded_files/mypicfile.dat','r')]
            #open('../uploaded_files/mypicfile.dat').close()

            #f=open('../uploaded_files/myfile.dat', 'rw')
            dif_data=list(set(files)-set(upfiles))
            if dif_data==[]:
                print 'no new file was found'
                time.sleep(15)
                pass
            

    ##################################
    ##################################
            dif_data.sort(key=os.path.getmtime)
            fn=dif_data[-1]
            print 'fn: '+fn
            if 3>2:           
            
                fn2=fn.split(')')[0]+')_MA.txt'
                print fn
                print fn2
                if not os.path.exists('/home/pi/Desktop/Pictures/'+fn.split('(')[1].split('_')[0]):
                    os.makedirs('/home/pi/Desktop/Pictures/'+fn.split('(')[1].split('_')[0])
                df=pd.read_csv(fn,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)#creat a new Datetimeindex
                df2=pd.read_csv(fn2,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)
                df['yd']=df.index.dayofyear+df.index.hour/24.+df.index.minute/60./24.+df.index.second/60/60./24.-1.0 #creates a yrday0 field
                df2['yd']=df2.index.dayofyear+df2.index.hour/24.+df2.index.minute/60./24.+df2.index.second/60/60./24.-1.0
                print len(df2),len(df)
                try: 
                    index_good=np.where(abs(df2['Az (g)'])<2) #Attention : If you want to use the angle, change the number under 1.
                    print index_good[0][3],index_good[0][-3]
                    index_good_start=index_good[0][3]
                    index_good_end=index_good[0][-3]
                    #print 'index_good_start:'+index_good_start+' index_good_end:'+index_good_end
                except:
                    
                    #os.remove(new_file_path+').lid')
                    #os.remove(new_file_path+')_MA.txt')
                    #os.remove(new_file_path+')_T.txt')
                    print "no good data"
                    pass
                #df.rename(index=str,columns={"Temperature (C)":"Temperature"}) #change name
                meantemp=round(np.mean(df['Temperature (C)'][index_good_start:index_good_end]),2)
                fig=plt.figure()
                ax1=fig.add_subplot(211)
                ax2=fig.add_subplot(212)
                #df['depth'].plot()
                ax2.plot(df2.index,df2['Az (g)'],'b',label='Angle')
                #ax2.plot(df2.index[index_good_start:index_good_end],df2['Az (g)'][index_good_start:index_good_end],'red',linewidth=4,label='in the water')
                ax2.legend()
                #df['temp'].plot()

                ax1.plot(df.index,df['Temperature (C)'],'b')
                #ax1.plot(df.index[index_good_start:index_good_end],df['Temperature (C)'][index_good_start:index_good_end],'red',linewidth=4,label='in the water')
                ax1.set_ylabel('Temperature (Celius)')
                ax1.legend(['temp','in the water'])
                #print 2222222222222222222222222222222222222222222
                try:    
                        if max(df.index)-min(df.index)>Timedelta('0 days 04:00:00'):
                            ax1.xaxis.set_major_locator(dates.HourLocator(interval=(max(df.index)-min(df.index)).seconds/3600/6))# for hourly plot
                            ax1.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
                            ax2.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
                            
                        else: 
                            ax1.xaxis.set_major_locator(dates.MinuteLocator(interval=(max(df.index)-min(df.index)).seconds/60/6))# for minutely plot
                            ax1.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
                            ax2.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
                except:
                    print 'too less data'

                ax1.text(0.9, 0.15, 'mean temperature in the water='+str(round(meantemp*1.8+32,1))+'F',
                            verticalalignment='bottom', horizontalalignment='right',
                            transform=ax1.transAxes,
                            color='green', fontsize=15)    
                #ax1.xaxis.set_major_formatter(dates.DateFormatter('%D %H:%M'))
                ax1.set_xlabel('')
                
                #ax1.set_ylim(int(np.nanmin(df['Temperature (C)'].values)),int(np.nanmax(df['Temperature (C)'].values)))
                #ax1.set_xticklabels([])
                ax1.grid()
                ax12=ax1.twinx()
                ax12.set_title(tit)
                ax12.set_ylabel('Fahrenheit')
                ax12.set_xlabel('')
                #ax12.set_xticklabels([])
                ax12.set_ylim(np.nanmin(df['Temperature (C)'].values)*1.8+32,np.nanmax(df['Temperature (C)'].values)*1.8+32)



                ax2=fig.add_subplot(212)
                
                ax2.plot(df2.index,df2['Az (g)'].values)
                ax2.invert_yaxis()
                ax2.set_ylabel('Angle')
                #ax2.set_xlabel(df2.index[0])
                ax2.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
                ax2.grid()
                ax2.set_ylim(-1,1)
                ax22=ax2.twinx()
                ax22.set_ylabel('Angle')
                #ax22.set_ylim(np.nanmin(df['depth'].values)/1.8288,np.nanmax(df['depth'].values)/1.8288)
                ax22.set_ylim(1,-1)
                ax22.invert_yaxis()

     
                plt.gcf().autofmt_xdate()    
                ax2.set_xlabel('GMT TIME '+df.index[0].strftime('%m/%d/%Y %H:%M:%S')+' - '+df.index[-1].strftime('%m/%d/%Y %H:%M:%S'))
                
                plt.savefig('/home/pi/Desktop/Pictures/'+fn.split('(')[1].split('_')[0]+'/'+fn.split('(')[0][-2:]+fn.split('(')[1][:-6]+'.png')
                plt.close()
                print 'picture is saved'
            upfiles.extend(dif_data)
            f=open('uploaded_files/mypicfile.dat','r').close()
            f=open('../uploaded_files/mypicfile.dat','w+')
            [f.writelines(i+'\n') for i in upfiles]
            f.close()
            print ' All Pictures are Generated'
                   
            return 
       
      except:
            print 'something wrong'
            
            return 


def p_create_pic():

      tit='Temperature and Depth'
      
      if not os.path.exists('/home/pi/Desktop/Pictures'):
        os.makedirs('/home/pi/Desktop/Pictures')

      if not os.path.exists('uploaded_files'):
        os.makedirs('uploaded_files')
      n=0  
      if 'r' in open('/home/pi/Desktop/mode.txt').read():
        file='control_file.txt'
        mode='real'
      else:
        file='test_control_file.txt'
        mode='test'
      print (1)
      try:
            files=[]
            files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/*.csv')))
            
            if not os.path.exists('uploaded_files/mypicfile.dat'):
                open('uploaded_files/mypicfile.dat','w').close() 
            
            with open('uploaded_files/mypicfile.dat','r') as f:
                content = f.readlines()
                f.close()
            
            upfiles = [line.rstrip('\n') for line in open('uploaded_files/mypicfile.dat','r')]
            dif_data=list(set(files)-set(upfiles))
           
            if dif_data==[]:
                print  'Standby. When the program detects a probe haul, machine will reboot and show new data.'
                import time
                time.sleep(14)
                
                return
            

    ##################################
    ##################################
            dif_data.sort(key=os.path.getmtime)
            print (2)
            for fn in dif_data:          
            
                fn2=fn
                              
                if not os.path.exists('/home/pi/Desktop/Pictures/'+fn.split('/')[-1].split('_')[2]):
                    os.makedirs('/home/pi/Desktop/Pictures/'+fn.split('/')[-1].split('_')[2])
                df=pd.read_csv(fn,sep=',',skiprows=8,parse_dates={'datet':[1]},index_col='datet',date_parser=parse2)#creat a new Datetimeindex
                if mode=='real':
                    df=df.ix[(df['Depth (m)']>0.85*mean(df['Depth (m)']))]
                    df=df.ix[3:-2] # delete this line if cannot get plot
                    if len(df)>1000:
                        df=df.ix[5:-5]
                        df=df.iloc[::(len(df)/960+1),:] #Plot at most 1000 data
                else:
                    if len(df)>1000:
                        df=df.iloc[::(len(df)/960+1),:]
                df2=df
                df2['Depth (m)']=[x*(-0.5468) for x in df2['Depth (m)'].values]
                #change to -0.5468 if you want to show negtive depth on Pic
                if len(df2)<5:
                    continue
                print (3)
                meantemp=round(np.mean(df['Temperature (C)']),2)
                fig=plt.figure(figsize=(7,4))#figsize?
                ax1=fig.add_subplot(211)
                ax2=fig.add_subplot(212)
                time_df2=gmt_to_eastern(df2.index)
                time_df=gmt_to_eastern(df.index)
     
                ax1.plot(time_df,df['Temperature (C)']*1.8+32,'b',)
                #ax1.set_xlim(time_df[1],time_df[-2])
                #ax1.set_ylim(np.nanmin(df['Temperature (C)'].values)*1.8+30,np.nanmax(df['Temperature (C)'].values)*1.8+36)
                ax1.set_ylabel('Temperature (Fahrenheit)')
                ax1.legend(['temp','in the water'])
                
                try:    
                        if max(df.index)-min(df.index)>Timedelta('0 days 04:00:00'):
                            ax1.xaxis.set_major_locator(dates.DateLocator(interval=(max(df.index)-min(df.index)).seconds/3600/12))# for hourly plot
                            ax2.xaxis.set_major_locator(dates.DateLocator(interval=(max(df.index)-min(df.index)).seconds/3600/12))# for hourly plot
                        else:
                            ax1.xaxis.set_major_locator(dates.DateLocator(interval=(max(df.index)-min(df.index)).seconds/3600/4))# for hourly plot
                            ax2.xaxis.set_major_locator(dates.DateLocator(interval=(max(df.index)-min(df.index)).seconds/3600/4))# for hourly plot
                except:
                    print ' '
                
                clim=getclim()# extracts climatological values at this place and yearday
                
                if isnan(clim):
                    txt='mean temperature ='+str(round(c2f(meantemp),1))+'F (No Climatology here.)'
                else:    
                    txt='mean temperature ='+str(round(c2f(meantemp),1))+'F Climatology ='+str(round(c2f(clim),1))+'F'
                ax1.text(0.95, 0.01,txt,
                            verticalalignment='bottom', horizontalalignment='right',
                            transform=ax1.transAxes,
                            color='red', fontsize=14)
                
                ax1.grid()
                ax12=ax1.twinx()
                ax12.set_title(tit)
                #ax12.set_ylabel('Fahrenheit')
                ax12.set_ylabel('Temperature (Celius)')
                #ax12.set_xlabel('')
                ax12.set_ylim(np.nanmin(df['Temperature (C)'].values),np.nanmax(df['Temperature (C)'].values)+0.01)

                ax2.plot(time_df2,df2['Depth (m)'],'b',label='Depth',color='green')
                ax2.legend()
                ax2.invert_yaxis()
                ax2.set_ylabel('Depth(Fathom)')
                ax2.set_ylim(np.nanmin(df2['Depth (m)'].values)*1.05,np.nanmax(df2['Depth (m)'].values)*0.95)
                #ax2.set_xlim(time_df2[1],time_df2[-2])
                ax2.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
                ax2.grid()
                
                ax22=ax2.twinx()
                ax22.set_ylabel('Depth(feet)')
                ax22.set_ylim(round(np.nanmax(df2['Depth (m)'].values)*6*0.95,1),round(np.nanmin(df2['Depth (m)'].values)*6*1.05,1))        
                ax22.invert_yaxis()

                plt.gcf().autofmt_xdate()    
                ax2.set_xlabel('TIME '+time_df[0].astimezone(pytz.timezone('US/Eastern')).strftime('%m/%d/%Y %H:%M:%S')+' - '+time_df[-1].astimezone(pytz.timezone('US/Eastern')).strftime('%m/%d/%Y %H:%M:%S'))
                plt.savefig('/home/pi/Desktop/Pictures/'+fn.split('/')[-1].split('_')[2]+'/'+fn.split('/')[-1].split('_')[-1].split('.')[0]+'.png')
                plt.close()

            a=open('uploaded_files/mypicfile.dat','r').close()
            
            a=open('uploaded_files/mypicfile.dat','a+')
            
            [a.writelines(i+'\n') for i in dif_data]
            a.close()

            print 'New data successfully downloaded. Plot will appear.'
            return 
       
      except:
          print 'the new csv file cannot be plotted, skip it'
          a=open('uploaded_files/mypicfile.dat','a+')
            
          [a.writelines(i+'\n') for i in dif_data]
          a.close()
          return
                            
             
def wifi():
      if not os.path.exists('../uploaded_files'):
        os.makedirs('../uploaded_files')
      if not os.path.exists('/home/pi/for_update/Desktop'):
        os.makedirs('/home/pi/for_update/Desktop')
      if not os.path.exists('/home/pi/for_update/mat_modules'):
        os.makedirs('/home/pi/for_update/mat_modules')      
      if not os.path.exists('../uploaded_files/myfile.dat'):
          open('../uploaded_files/myfile.dat','w').close()
      #software updates
      import time
      session1 = ftplib.FTP('66.114.154.52','huanxin','123321')
      session1.cwd("/updates/Desktop")
      files_Desktop=session1.nlst()
      #print files_Desktop
      for a in files_Desktop:
          file = open('/home/pi/for_update/Desktop/'+a,'wb')
          session1.retrbinary('RETR '+a,file.write)
          file.close()
          time.sleep(1)
          if os.stat('/home/pi/for_update/Desktop/'+a).st_size>=4:
              copyfile('/home/pi/for_update/Desktop/'+a,'/home/pi/Desktop/'+a)           
          
      time.sleep(1)
      session1.cwd("/updates/mat_modules")
      
      files_mat_modules=session1.nlst()
      
      for b in files_mat_modules:
          file = open('/home/pi/for_update/mat_modules/'+b,'wb')
          session1.retrbinary('RETR '+b,file.write)
          file.close()
          time.sleep(1)
          if os.stat('/home/pi/for_update/mat_modules/'+b).st_size>=4:
              copyfile('/home/pi/for_update/mat_modules/'+b,'/home/pi/Desktop/mat_modules/'+b)
          
          if os.path.exists("mat_modules/"+b+'c'):
              os.remove("mat_modules/"+b+'c')
              
      session1.quit()
      time.sleep(3)
      
      
      
      if 3>2:
            files=[]
            files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/*.csv')))
            files.extend(sorted(glob.glob('/home/pi/Desktop/towifi/error*')))
            #print files  
            with open('../uploaded_files/myfile.dat') as f:
                content = f.readlines()        
            upfiles = [line.rstrip('\n') for line in open('../uploaded_files/myfile.dat')]
            

            #f=open('../uploaded_files/myfile.dat', 'rw')
            dif_data=list(set(files)-set(upfiles))
            #print dif_data
            if dif_data==[]:
                print ''
                time.sleep(1)
                return
         
            for u in dif_data:
                import time
                #print u
                session = ftplib.FTP('66.114.154.52','huanxin','123321')
                file = open(u,'rb') 
                session.cwd("/Matdata")  
                #session.retrlines('LIST')               # file to send
                session.storbinary("STOR "+u[24:], open(u, 'r'))   # send the file
                #session.close()
                session.quit()# close file and FTP
                time.sleep(1)
                file.close() 
                print u[24:]
                #os.rename('C:/Program Files (x86)/Aquatec/AQUAtalk for AQUAlogger/DATA/'+u[:7]+'/'+u[8:], 'C:/Program Files (x86)/Aquatec/AQUAtalk for AQUAlogger/uploaded_files/'+u[8:])
                print u[24:]+' uploaded'
                #os.rename(u[:7]+'/'+u[8:], "uploaded_files/"+u[8:]) 
                time.sleep(3)                     # close file and FTP
                f=open('../uploaded_files/myfile.dat','a+')
                #print 11111111111111111111111111111
                #print 'u:'+u
                f.writelines(u+'\n')
                f.close()
                
            #upfiles.extend(dif_data)
            #f=open('../uploaded_files/myfile.dat','w')
            #[f.writelines(i+'\n') for i in upfiles]
            #f.close()
            print 'all files are uploaded'
            #os.system('sudo ifdown wlan0')
            time.sleep(1500)
            return

       
      else:
            #import time
            #print 'no wifi'
            time.sleep(1)
            
            return

def judgement(boat_type,ma_file,t_file):
    valid='no'
    try:
        df=pd.read_csv(t_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)#creat a new Datetimeindex
        df2=pd.read_csv(ma_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse2)
        index_good=np.where(abs(df2['Az (g)'])<0.2)
        index_better=[]
        for e in range(len(index_good[0][:-1])):
                            if index_good[0][e+1]-index_good[0][e]>1:
                                index_better.append(index_good[0][e+1])
        print index_good,index_better
        if index_better==[]:
            index_better=[index_good[0][0]]

        index_good_start=index_better[-1]
        index_good_end=index_good[0][-1]+1
        print 'index_good_start:'+str(index_good_start)+' index_good_end:'+str(index_good_end)
        if boat_type=='fixed':
            if index_good_end-index_good_start<60:  #100 means 200 minutes
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end
            else:
                valid='yes'
                return valid,index_good_start,index_good_end,
        else:
            if index_good_end-index_good_start<3:  #12 means 24 minutes
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end 
            else:
                valid='yes'
                return valid,index_good_start,index_good_end           


    except:
        print 'data not in the sea'
        return valid,index_good_start,index_good_end

def judgement2(boat_type,s_file,logger_timerange_lim,logger_pressure_lim):
    valid='no'
    try:
        df=pd.read_csv(s_file,sep=',',skiprows=0,parse_dates={'datet':[0]},index_col='datet',date_parser=parse)#creat a new Datetimeindex
        
        index_good_start=1
        index_good_end=len(df)-1
       
        if boat_type<>'mobile':
            index_good=np.where(abs(df['Depth (m)'])>logger_pressure_lim)
            if len(index_good[0])<logger_timerange_lim:  #100 means 150 minutes
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end
            else:
                valid='yes'
                return valid,index_good_start,index_good_end
        else:
            index_good=np.where(abs(df['Depth (m)'])>logger_pressure_lim)#make sure you change it before on the real boat
            if len(index_good[0])<logger_timerange_lim or len(df)>1440:  #make sure the good data is long enough,and total data is not more than one day  
                print 'too less data, not in the sea'
                return valid,index_good_start,index_good_end
            else:
                valid='yes'
                return valid,index_good[0][0],index_good[0][-1]           


    except:
        print 'data not in the sea'
        return valid,index_good_start,index_good_end


 
def gps_compare(lat,lon,mode): #check to see if the boat is in the harbor
    
    harbor_range=0.5 #box size of latitude and longitude, unit: seconds/10
    if mode=='test':
        file2='/home/pi/Desktop/test_harborlist.txt'
    else:
        file2='/home/pi/Desktop/harborlist.txt'
    df2=pd.read_csv(file2,sep=',')

    indice_lat=[i for i ,v in enumerate(abs(np.array(df2['lat'])-lat)<harbor_range) if v]
    indice_lon=[i for i ,v in enumerate(abs(np.array(df2['lon'])-lon)<harbor_range) if v]
    harbor_point_list=[i for i, j in zip(indice_lat,indice_lon) if i==j]

    return harbor_point_list




















        
