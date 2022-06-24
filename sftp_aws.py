import pysftp
import config
import setup_rtd

class Transfer(object):
	def __init__(self, path):
		self.path = path
		self.db = config.database_connection_details['development']

	def upload(self, local_name, remote_name):
		cnopts = pysftp.CnOpts()
		cnopts.hostkeys = None
		with pysftp.Connection(host=self.db['ssh_host'], username=self.db['ssh_username'], private_key=self.db['ssh_private_key'], cnopts=cnopts) as conn:
			local_path, remote_path = setup_rtd.parameters['path'] + local_name, self.path + remote_name
			conn.put(local_path, remote_path)
