import rockBlock
 
from rockBlock import rockBlockProtocol
'''    
    def main(self,ports):
        print ports
'''   
class MoExample(rockBlockProtocol):
    def __init__(self, ports,message):
        
    
        rb = rockBlock.rockBlock(ports, self)
        
        rb.sendMessage(message)      
        
        rb.close()
        
    def rockBlockTxStarted(self):
        print ("rockBlockTxStarted")
        
    def rockBlockTxFailed(self):
        print ("rockBlockTxFailed")
        
    def rockBlockTxSuccess(self,momsn):
        print ("rockBlockTxSuccess " + str(momsn))
        
if __name__ == '__main__':
    MoExample().main()
