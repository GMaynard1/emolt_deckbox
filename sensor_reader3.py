import os
import time
from pathlib import Path
from bluepy import btle
from mat.ble.bluepy.moana_logger_controller import LoggerControllerMoana
import sys
sys.path.insert(1,'/home/pi/Desktop/')
import setup_rtd

path = setup_rtd.parameters['path']
#macs = [setup_rtd.metadata['mac_addr']]
macs = setup_rtd.metadata['mac_addr']
def just_delete_file_n_time_sync():
    print('reaching moana to time sync {}...'.format(mac))
    lc = LoggerControllerMoana(mac)
    if not lc.open():
        print('connection error')
        return

    lc.auth()
    if not lc.time_sync():
        print('error time sync')
    if not lc.file_clear():
        print('error file_clear')
    lc.close()


def full_demo(mac):
    lc = LoggerControllerMoana(mac)
    if not lc.open():
        # print('connection error')
        return

    lc.auth()

    name_csv_moana = lc.file_info()

    print('Status file changed to 0')

    g = open(path + 'status.txt', 'w')
    g.write('0')
    g.close()

    print('downloading file {}...'.format(name_csv_moana))
    data = lc.file_get()

    name_bin_local = lc.file_save(data)
    if name_bin_local:
        print('saved as {}'.format(name_csv_moana))

        name_csv_local = lc.file_cnv(name_bin_local, name_csv_moana, len(data))

        if name_csv_local:
            print('conversion OK')
        else:
            print('conversion error')

    # we are doing OK
    lc.time_sync()

    # comment next 2 -> repetitive download tests
    # uncomment them -> re-run logger
    time.sleep(1)
    if not lc.file_clear():
        print('error file_clear')

    time.sleep(20)
    g = open(path + 'status.txt', 'w')
    g.write('1')
    g.close()
    print('Status file changed to 1')
    lc.close()


# scanner = btle.Scanner().withDelegate(LCBLEMoanaDelegate())
# devices = scanner.scan(10
# the name that the scan searches for
scanName = "ZT-MOANA"
print('reaching moana {}...'.format(macs))

while True:
    for mac in macs:
        print (mac)
        full_demo(mac)
        time.sleep(5)


