from Util import *

# You can add necessary functions here


class ReliableImpl:

    #  __init__: You can add variables to maintain your sliding window states.
    # 'reli' (self.reli) provides an interface to call functions of
    # class Reliable in ReliableImpl.
    # 'seqNum' indicates the initail sequence number in the SYN segment.
    # 'srvSeqNum' indicates the initial sequence number in the SYNACK segment.
    def __init__(self, reli=None, seqNum=None, srvSeqNum=None, longestAcked=None, largestSent=None, queue=None):
        super().__init__()
        self.reli = reli
        self.seqNum = seqNum
        self.srvAckNum = (srvSeqNum+1) % SeqNumSpace  # srvAckNum remains unchanged in this lab
        self.largestAcked = longestAcked
        self.largestSent = largestSent
        self.queue = queue

        pass

    # checksum: 16-bit Internet checksum (refer to RFC 1071 for calculation)
    # This function should return the value of checksum (an unsigned 16-bit integer).
    # You should calculate the checksum over 's', which is an array of bytes
    # (type(s)=<class 'bytes'>).
    # AUP = 1 << 16
    # def adder(num1,num2):
    #     result = num1 + num2
    #     return result if result < AUP else (result+1) % AUP

    # this does work but I chose to use the code provided for safety
    # @staticmethod
    # def checksum(s):
    #     q = [s[i: j] for i in range(len(s)) for j in range(i + 1, len(s) + 1) if len(s[i:j]) == 2] 
    #     sum1 = 0
    #     sum2 = 0
    #     for x in range(len(q)):
    #         if x % 2 == 0:
    #             c = int.from_bytes(q[x],"big", signed=False)
    #             sum1 = adder(sum1,c)
    #         if x % 2 == 1:
    #             d = int.from_bytes(q[x],"big", signed=False)
    #             sum2 = adder(sum2,c)

    #     print(hex(sum1))
    #     print(hex(sum2))

    #     return 0xFFFF - sum1

    @staticmethod
    def checksum(s):
        n=len(s)
        res = 0
        for i in range(0,n-1,2):
          res += s[i]*256+s[i+1]
        if (n & 1) == 1:
          res += s[n-1]*256
        while (res >> 16) > 0:
          res = (res & 0xFFFF)+(res >> 16)
        return (1 << 16)-1-res


    def checkIfAcked(seg):
        if seg.ack == 1:
            return 1
        return 0

    def checkInWrapRange(head, tail, index):
        if (head<=tail & (index<head | tail<=index)):
            return 0
        if (tail<head & (tail<=index & index < haed)):
            return 0
        return 1

    # recvAck: When an ACK or FINACK segment is received, the framework will
    # call this function to handle the segment.
    # The checksum will be verified before calling this function, so you
    # do not need to verify checksum again in this function.
    # Remember to call self.reli.updateRWND to update the receive window size.
    # Note that this function should return the reduction of bytes in flight
    # (a non-negative integer) so that class Reliable can update the bytes in flight.
    # 'seg' is an instance of class Segment (see Util.py)
    # 'isFin'=True means 'seg' is a FINACK, otherwise it is an ACK.
    def recvAck(self, seg, isFin):

        head1 = self.largestAcked+1
        tail1 = self.largestSent+2
        index1 = seg.ackNum

        if checkIfAcked(head1, tail1, index1) == 0:
            return 0

        bif = len(seg.payload)

        while ~(self.queue.empty()):
            if ~(checkIfAcked(self.queue[0])):
                break
            self.queue[0].reli.cancel()
            self.queue.get()

        self.reli.updateRWND(seg.rwnd)

        return bif

    # sendData: This function is called when a piece of payload should be sent out.
    # You can call Segment.pack in Util.py to encapsulate a segment and
    # call self.reli.setTimer (see Reliable.py) to set a Timer for retransmission.
    # Use self.reli.sendto (see Reliable.py) to send a segment to the receiver.
    # Note that this function should return the increment of bytes in flight
    # (a non-negative integer) so that class Reliable can update the bytes in flight.
    # 'payload' is an array of bytes (type(payload)=<class 'bytes'>).
    # 'isFin'=True means a FIN segment should be sent out.
    def sendData(self, payload, isFin):
        putIn = 0
        if isFin:
            putIn = 1

        checkSeg = Segment.pack(self.seqNum, self.srvAckNum, 0, 0, 0, putIn, 0, payload)
        cksum = checksum(checkSeg)
        mySeg = Segment.pack(self.seqNum, self.srvAckNum, 0, 0, 0, putIn, cksum, payload)        
        self.reli.sendto(mySeg)

        self.reli.setTimer(3,retransmission,[q[0]],{arg: 1}) # 5 seconds before retransmission
        self.seqNum = self.seqNum + len(q)

        return len(payload)

    # retransmission: A callback function for retransmission when you call
    # self.reli.setTimer.
    # In Python, you are allowed to modify the arguments of this function.
    def retransmission(self, seqNum):
        self.reli.setTimer(6, self.retransmission,send)
        self.reli.sendto(seqNum)
        pass