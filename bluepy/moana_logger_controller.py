import datetime
import pathlib
from datetime import timezone
import os
import struct
import time
from inspect import stack
import bluepy
from bluepy import btle
import subprocess as sp


def utils_logger_is_moana(mac, info):
    return 'MOANA' in info


class LCBLEMoanaDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)
        self.buf = bytes()

    def handleNotification(self, c_handle, data):
        self.buf += data


class LoggerControllerMoana:

    UUID_W = btle.UUID('569a2001-b87f-490c-92cb-11ba5ea5167c')
    UUID_R = btle.UUID('569a2000-b87f-490c-92cb-11ba5ea5167c')
    UUID_S = btle.UUID('569a1101-b87f-490c-92cb-11ba5ea5167c')

    def _clear_buffers(self):
        self.dlg.buf = bytes()

    def __init__(self, mac, h=0):
        self.mac = mac
        self.h = h
        self.per = None
        self.svc = None
        self.c_r = None
        self.c_w = None
        self.dlg = LCBLEMoanaDelegate()
        self.sn = ''

    def _ble_tx(self, data):
        self.c_w.write(data, withResponse=True)

    def open(self):
        try:
            t_r = btle.ADDR_TYPE_RANDOM
            self.per = bluepy.btle.Peripheral(self.mac, iface=self.h,
                                              addrType=t_r)
            time.sleep(1.1)
            self.per.setDelegate(self.dlg)
            self.svc = self.per.getServiceByUUID(self.UUID_S)
            self.c_r = self.svc.getCharacteristics(self.UUID_R)[0]
            self.c_w = self.svc.getCharacteristics(self.UUID_W)[0]
            desc = self.c_r.valHandle + 1
            self.per.writeCharacteristic(desc, b'\x01\x00')
            self.per.setMTU(27)
            return True

        except (AttributeError, bluepy.btle.BTLEException) as ex:
            print('[ BLE ] can\'t connect: {}'.format(ex))

    def close(self):
        try:
            self.per.disconnect()
            self.per = None
        except AttributeError:
            pass

    def _wait_answer(self, exp_ans=''):

        # gets caller function
        cf = str(stack()[1].function)

        # 'file_get' is implemented somewhere else
        assert cf != 'file_get'

        # maps caller function to expected answer
        m = {
            'ping': b'ping_made_up_command',
            'auth': b'*Xa{"Authenticated":true}',
            'file_clear': b'*Vc{"ArchiveBit":false}',
            'time_sync': exp_ans.encode(),
            'file_info': exp_ans.encode(),
            'file_info_get_size': exp_ans.encode(),
            'file_crc': exp_ans.encode()
        }

        # -------------------------
        # waits for command answer
        # -------------------------

        till = time.perf_counter() + 2
        while 1:
            self.per.waitForNotifications(.1)
            if time.perf_counter() > till:
                break
            v = self.dlg.buf

            # fixed answers: auth, file_clear
            if v.endswith(m[cf]):
                break

            # variable answers: -> time_sync, file_info
            if exp_ans and exp_ans.encode() in v:
                break

    def ping(self):
        # made-up command, needed or Moana won't answer
        self._clear_buffers()
        self._ble_tx(b'...')
        self._wait_answer()
        return self.dlg.buf

    def auth(self) -> bool:
        for i in range(3):
            self._clear_buffers()
            self._ble_tx(b'*EA123')
            self._wait_answer()
            if self.dlg.buf == b'*Xa{"Authenticated":true}':
                return True
            time.sleep(2)

    def file_info(self):
        self._clear_buffers()
        self._ble_tx(b'*BF')
        self._wait_answer('ArchiveBit')
        # a: b'*004dF\x00{"FileName":"x.csv","FileSizeEstimate":907,"ArchiveBit":"+"}'
        a = self.dlg.buf.decode()

        try:
            i_colon = a.index(':') + 2
            i_comma = a.index(',') - 1
            file_name = a[i_colon:i_comma]
            self.sn = file_name.split('_')[1]
            self.dlg.buf = bytes()
            return file_name

        except (AttributeError, ValueError):
            # moana sometimes fails here
            pass

    def file_info_get_size(self):
        self._clear_buffers()
        self._ble_tx(b'*BF')
        self._wait_answer('ArchiveBit')
        # a: b'*004dF\x00{"FileName":"x.csv","FileSizeEstimate":907,"ArchiveBit":"+"}'
        a = self.dlg.buf.decode()

        try:
            size = int(a[a.index("FileSizeEstimate") + 18:a.index("ArchiveBit") + -2])
            return int(size)

        except (AttributeError, ValueError):
            # moana sometimes fails here
            pass

    def file_get(self, rm_demo=False):
        # --------------------------------------------
        # because it works with phones, the size of
        # Moana BLE notifications is 20 bytes
        # --------------------------------------------
        if rm_demo:
            sp.run('rm /home/kaz/Downloads/moana_demo/*', shell=True)

        data = bytes()
        marker_file_end = b'*0005D\x00'
        is_first_packet = True

        while 1:
            pre = len(self.dlg.buf)
            self._clear_buffers()
            self._ble_tx(b'*BB')
            while self.per.waitForNotifications(3):
                # accumulate till nothing more arrives
                pass
            post = len(self.dlg.buf)

            # lose header only of intermediate packets
            if is_first_packet:
                data += self.dlg.buf[0:]
                is_first_packet = False
            else:
                data += self.dlg.buf[7:]

            if self.dlg.buf[-7:] == marker_file_end:
                # reached file end
                break
            if pre == post:
                # detects timeouts
                break

        # data: b',"ArchiveBit":"+"}*0173D\x00Download Time...'
        k = data.index(b'*')
        self.dlg.buf = data[k:]
        return self.dlg.buf

    def file_clear(self):
        # delete senor file and stops advertising
        self._clear_buffers()
        self._ble_tx(b'*BC')
        self._wait_answer()
        return self.dlg.buf == b'*Vc{"ArchiveBit":false}'

    @staticmethod
    def file_save(data) -> str:
        if not data:
            return ''
        t = int(time.time())
        name = '/tmp/moana_{}.bin'.format(t)
        with open(name, 'wb') as f:
            f.write(data)
        return name

    # def file_crc(self):
    #     self._clear_buffers()
    #     self._ble_tx(b'*BZ')
    #     self._wait_answer('*Jz')
    #     crc = self.dlg.buf
    #     # crc: b'*Jzeb983b79
    #     # print('moana file remote crc ->', crc)
    #     if len(crc) == 11:
    #         return crc[-8:]

    def time_sync(self) -> bool:
        self._clear_buffers()
        # time() -> epoch seconds in UTC
        # src: www.tutorialspoint.com/python/time_time.htm
        epoch_s = str(int(time.time()))
        t = '*LT{}'.format(epoch_s).encode()
        self._ble_tx(t)
        self._wait_answer(epoch_s)
        return epoch_s.encode() in self.dlg.buf

    def file_cnv(self, name, moana_name, length):
        if not os.path.isfile(name):
            print('can\'t find {} to convert'.format(name))
            return False

        # find '\x03' byte
        with open(name, 'rb') as f:
            content = f.read()
            i = content.find(b'\x03')
        if i == 0:
            return

        # get first timestamp as integer and pivot
        # saves file w/ UTC times (local when tz=None)
        i_ts = int(struct.unpack('<i', content[i+1:i+5])[0])
        first_dt = datetime.datetime.fromtimestamp(i_ts, tz=timezone.utc)
        first_dt = first_dt.strftime('%Y%m%dT%H%M%S')

        if '_'.join(moana_name.split('_')[:2]) not in os.listdir('/home/pi/rtd_global/logs/raw/Moana/'):
            os.mkdir('/home/pi/rtd_global/logs/raw/Moana/{sensor_id}/'.format(sensor_id='_'.join(moana_name.split('_')[:2])))

        # use timestamps for file naming
        nm = '/' + self.file_info()
        nm = '/home/pi/rtd_global/logs/raw/Moana/{sensor_id}/'.format(sensor_id='_'.join(moana_name.split('_')[:2])) + nm
        fm = open(nm, 'w')
        fm.write('DATETIME,PRESSURE,TEMPERATURE\n')
        print('converting {}'.format(name))
        # print('    -> {}'.format(nt))
        # print('    -> {}'.format(np))

        # skip first timestamp
        j = i + 5

        # loop through data
        submerged = False
        while 1:
            if j + 6 > length:
                break
            line = content[j:j+6]
            i_last_ts = int(struct.unpack('<H', line[0:2])[0])
            i_ts += i_last_ts

            # saves file w/ UTC times (local when tz=None)
            # & removes the +00:00 part
            dt = datetime.datetime.fromtimestamp(i_ts, tz=timezone.utc)
            # todo > is next line needed?
            dt = dt.replace(tzinfo=None)
            press = int(struct.unpack('<H', line[2:4])[0])
            temp = int(struct.unpack('<H', line[4:6])[0])
            press = '{:4.2f}'.format((press / 10) - 10)
            temp = '{:4.2f}'.format((temp / 1000) - 10)
            j += 6
            dt = dt.isoformat('T', 'milliseconds')
            fm.write('{},{},{}\n'.format(dt, press, temp))
            # print('{} | {}\t{}'.format(dt, press, temp))

            # detect immersions
            p = int(float(press))
            threshold_meters = 2
            if not submerged and p > threshold_meters:
                submerged = True
                print('sub at', dt)
            elif submerged and p <= threshold_meters:
                submerged = False
                print('air at', dt)

        fm.close()

        # prefix: 'moana_0113_20211206T144237'
        prefix = 'moana_{}_{}'.format(self.sn, first_dt)
        return prefix


# def calculate_moana_file_crc(data: bytes):
#
#     # ---------------------------------------------------------------------
#     # Moana CRC is weird, downloading the same file gives slightly
#     # different values every time, so let's consider a CRC match of
#     # 24 MSb, that is 3 MSB, that is the first 6 digits of the
#     # calculation good enough (just a 16-bit CRC DETECTS 99% of errors)
#     # src: https://barrgroup.com/embedded-systems/how-to/crc-math-theory
#     # ---------------------------------------------------------------------
#
#     checksum = np.uint32(0)
#     for c in data:
#         checksum = np.uint32(checksum) ^ c
#         checksum = np.uint32(checksum) << 1
#         if np.uint32(checksum) & 0x80000000:
#             checksum = np.uint32(checksum) | 1
#
#     # sometimes needs these couple adjusts
#     checksum -= 0x104
#     if checksum > 0xFFFFFFFF:
#        checksum -= 0x100000000
#
#     s = '{:08x}'.format(checksum)
#     # print('moana file local crc ->', s)
#     return s
#
#
# def compare_moana_file_crc(a: bytes, b):
#     # a: b'*Jz2b983b40'
#     # b: '2b983b40'
#     print('moana: comparing local crc vs remote crc', a, b)
#     if not a or not b:
#         return
#     if len(a) != len(b) != 8:
#         return
#     # 24-bit CRC is enough (detects 99% errors)
#     rv = a.decode()[:6] == b[:6]
#     return rv