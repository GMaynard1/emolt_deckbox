import os


class Finder:
    def ping_net(self):
        command = """ ping -c 4 8.8.8.8 """
        result = os.popen(command.format())
        result = list(result)
        result = set([elem.strip() for elem in result])
        result = list(result)
        
        if len(result) == 0:
            return False
        else:
            con = [e for e in result if 'packets transmitted' in e][0]
        
        return True if int(con.split(', ')[1][0]) > 0 and 'error' not in con else False

class Connection(Finder):
    def wifi_check(self):
        return self.ping_net()

    # True if there is internet false otherwise
    def conn_type(self):
        return True if self.wifi_check() else False

