import pandas as pd
import setup_rtd
from connectivity import Connection
from datetime import datetime
from sftp_aws import Transfer
import os
import logging

logging.basicConfig(filename=setup_rtd.parameters['path'] + 'logs/queued.log',
                    format='%(levelname)s %(asctime)s :: %(message)s',
                    level=logging.DEBUG)
logging.debug('Running..')

queued_wifi = os.listdir(setup_rtd.parameters['path'] + 'queued/Moana/')
logging.debug('unsent:'+str(len(queued_wifi)))

if len(queued_wifi) > 0:
    server_name = ''
    server_id = 1
    conn_type = Connection().conn_type()
    print(conn_type)
    
    for elem in queued_wifi:
        print(elem)
        df_queue = pd.read_csv(setup_rtd.parameters['path'] + 'queued/Moana/' + elem, error_bad_lines=False)
        #print(df_queue)
        df_queue.DATETIME = pd.to_datetime(df_queue.DATETIME)
        diff = (datetime.now() - df_queue.DATETIME.max()).total_seconds() / 3600
        logging.debug('Time difference:')
        logging.debug(str(diff))
        if diff <= 1200:
            metadata = ','.join(elem.split('_')) + '\n'
            if conn_type == 1 or conn_type == 2:  # wifi or gsm
                Transfer('/home/ec2-user/rtd/vessels/{vessel}/'.format(vessel=setup_rtd.parameters['vessel_name'])).upload(
                    'queued/Moana' + elem, 'merged/Moana/' + elem)
                os.remove(setup_rtd.parameters['path'] + 'queued/Moana/' + elem)
        else:
            df_queue.to_csv(setup_rtd.parameters['path'] + 'logs/no_rtd/' + elem, index=None)
            os.remove(setup_rtd.parameters['path'] + 'queued/Moana/' + elem)

