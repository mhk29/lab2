import os
import sys
import time

UDPDatagramSize = 1024
SegmentSize = UDPDatagramSize - 8
PayloadSize = SegmentSize-16
MaxBandwidth = int(50*1024*1024/8)  # 50Mbps
MaxDelay = 0.5  # 500ms
MaxRTO = 60
MaxBDP = int(MaxBandwidth*MaxDelay)
SeqNumSpace = (1 << 32)
HalfSeqNumSpace = (1 << 31)
BufferSize = int(10*MaxBDP/PayloadSize)


def ErrorHandler(msg):
    print(msg, file=sys.stderr)
    os._exit(1)


def intToBytes(x, n=4):  # big-endian
    b = [0]*n
    for i in range(0, n):
        b[n-1-i] = x % 256
        x = int(x / 256)
    return bytes(b)


def bytesToInt(b):
    x = 0
    for i in range(0, len(b)):
        x = x*256+b[i]
    return x


class Segment:

    def __init__(self, seg):
        self.seqNum = bytesToInt(seg[:4])
        self.ackNum = bytesToInt(seg[4:8])
        self.rwnd = bytesToInt(seg[8:12])
        flags = bytesToInt(seg[12:14])
        self.ack = ((flags & 4) == 4)
        self.syn = ((flags & 2) == 2)
        self.fin = ((flags & 1) == 1)
        self.checksum = bytesToInt(seg[14:16])
        self.payload = seg[16:]

    @staticmethod
    def pack(seqNum, ackNum, rwnd, ack, syn, fin, checksum, payload):
        return intToBytes(seqNum)+intToBytes(ackNum)+intToBytes(rwnd) +\
            bytes([0, ack*4+syn*2+fin])+intToBytes(checksum, 2)+payload

    def Print(self):
        print(self.seqNum, self.ackNum, self.rwnd)
        print(self.ack, self.syn, self.fin)


class Timer:

    def __init__(self, timesec, callback, args):
        self.timestamp = time.time()+timesec
        self.enable = True
        self.__callback = callback
        self.__args = args

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def cancel(self):
        self.enable = False

    def run(self):
        return self.__callback(*self.__args)
