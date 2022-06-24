import socket
import ftplib
import io
import time
import os
import sys
import pandas as pd
import logging

logging.basicConfig(filename='/home/pi/rtd_global/main.txt',
                    format='%(levelname)s %(asctime)s :: %(message)s',
                    level=logging.DEBUG)

class sensor(object):

    def __init__(self, path):

        self.user = 'wisens-srv'
        self.password = 'wisens-srv'
        self.server = '192.168.69.1'

        self.ftp = None

        self.path = path

        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.server, 2221, timeout=10000)
            self.ftp.set_pasv(False)
            try:
                attempt = self.ftp.login(user=self.user, passwd=self.password)
                print(attempt)
                logging.debug(attempt)
            except:
                print(sys.exc_info()[0])
                pass
        except:
            print(sys.exc_info()[0])
            print("Timeout..")

    def file_received(self):
        files = self.ftp.nlst()
        if '..' in files:
            files.remove('..')
        if '.' in files:
            files.remove('.')
        return True if len(files) != 0 else False

    def download(self):
        if self.file_received():
            l_rec_files = []
            files = self.ftp.nlst()
            print(files)
            for file in files:
                attempt = self.ftp.sendcmd('TYPE i')
                print(attempt)
                if file not in os.listdir(self.path+'logs/raw/NKE'):
                    print('New file downloaded: \n' + file)
                    logging.debug('New file downloading: ' + file)
                    with open(self.path + 'logs/raw/NKE/'+file, 'wb') as download_file:
                        time.sleep(30)
                        with self.ftp.transfercmd('RETR ' + file) as data:
                            time.sleep(30)
                            while True:
                                f = data.recv(8192)
                                if not f:
                                    break
                                download_file.write(f)
                            print(self.ftp.voidresp())
                    logging.debug('Transfer completed')
                        
                   
                    l_rec_files.append(file)
                    self.ftp.delete(file) 
                else:
                    # command = """sudo mv /home/wisens-srv/{file} {path}sensor_repeated""".format(file=file, path=self.path)
                    # os.popen(command)
                    self.ftp.delete(file) 

                                       
            self.ftp.close()
            return l_rec_files
            
    def transfer(self):
        if self.file_received():
            l_rec_files = []
            files = self.ftp.nlst()
            print(len(files))
            for fil in files:                
                print(fil, fil not in os.listdir(self.path+'logs/raw/NKE'))
                if fil not in os.listdir(self.path+'logs/raw/NKE'):
                    time.sleep(10)
                    print('New file downloaded: \n' + fil)
                    try:
                        df = pd.read_csv('/home/wisens-srv/' + fil)
                        if '</WISENS>' in df['Timestamp(Standard)'].iloc[-1]:
                            command = """sudo mv /home/wisens-srv/{file} {path}logs/raw/NKE/"""
                            os.popen(command.format(file=fil, path=self.path))
                            time.sleep(10)
                            #logging.debug('Transfer completed')
                            l_rec_files.append(fil)
                            #self.ftp.delete(fil)
                        else:
                            self.transfer()
                    except:
                        time.sleep(10)
                        self.transfer()
                else:
                    # command = """sudo mv /home/wisens-srv/{file} {path}sensor_repeated""".format(file=fil, path=self.path)
                    # os.popen(command)
                    self.ftp.delete(fil) 
            
            self.ftp.close()
            return files

    def reconnect(self):
        try:
            time.sleep(2)
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.server, 2221, timeout=10000)
            try:
                attempt = self.ftp.login(user=self.user, passwd=self.password)
                logging.debug('ftp reconnected')
                print("ftp connected")
            except:
                print(sys.exc_info()[0])
                pass
        except:
            print("Timeout..")



