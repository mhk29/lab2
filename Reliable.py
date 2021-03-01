import time
import heapq
import select
import socket
import random
import threading
from ReliableImpl import ReliableImpl
from queue import Queue
from collections import deque
from Util import *


SYNSENT = 0
CONNECTED = 1
FINWAIT = 2
CLOSED = 3


class Reliable:
    def __init__(self, hport=10000):
        self.__dst = (None, None)
        self.__buf = Queue(maxsize=BufferSize)
        self.__skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__skt.bind(('', hport))

        self.status = CLOSED
        self.bytesInFly = 0
        self.rwnd = MaxBDP
        # self.cwnd = 3*BlockSize
        self.cwnd = MaxBDP

        self.timerHeap = []
        self.handlerThread = None
        self.reliImpl = None

    def __del__(self):
        self.__skt.close()

    def getskt(self):
        return self.__skt

    def connect(self, ip='127.0.0.1', rport=7090, n=None):
        self.__dst = (ip, rport)

        self.__skt.settimeout(1)
        if n is None:
            seqNum = random.randint(0, (1 << 32)-1)
        else:
            seqNum = n % SeqNumSpace

        self.status = SYNSENT
        synretry = 0
        while self.status != CONNECTED:
            temp = Segment.pack(seqNum, 0, 0, 0, 1, 0, 0, b'')
            self.sendto(Segment.pack(seqNum, 0, 0, 0, 1, 0, ReliableImpl.checksum(temp), b''))

            try:
                seg_str = self.recvfrom()
            except Exception as e:
                if synretry > 60:
                    self.status = CLOSED
                    return -1
                synretry += 1
                continue
            if ReliableImpl.checksum(seg_str) != 0:
                continue

            seg = Segment(seg_str)
            if seg.syn and seg.ack and seg.ackNum == (seqNum+1) % SeqNumSpace:
                self.status = CONNECTED

        self.__skt.settimeout(None)
        self.reliImpl = ReliableImpl(self, seqNum, seg.seqNum)
        self.handlerThread = Handler(self, self.reliImpl)
        self.handlerThread.start()
        return 0

    def close(self):
        self.send(None)
        if self.handlerThread is not None:
            self.handlerThread.join()

    def getPayload(self):
        return self.__buf.get(block=False)  # raise exception if queue is empty

    def send(self, payload):
        return self.__buf.put(payload)  # block if queue is full

    def recvfrom(self):
        (seg, addr) = self.__skt.recvfrom(SegmentSize)
        return seg

    # Followings are APIs that you may need to use in ReliableImpl
    # sendto: Send a well-formed segment to the destination.
    # 'seg_str' should be an array of bytes (type(seg_str)=<class 'bytes'>) and
    # should not contain UDP header
    def sendto(self, seg_str):
        return self.__skt.sendto(seg_str, self.__dst)

    # updateRWND: Update the receive window size.
    # 'rwnd' means the bytes of the receive window.
    def updateRWND(self, rwnd):
        self.rwnd = rwnd
        return self.rwnd

    # setTimer: Set a timer. Its usage is similar to threading.Timer,
    # but we implement our own Timer in this lab (See Util.py).
    # The function 'callback' will be called with 'args' as arguments
    # after 'timesec' seconds.
    def setTimer(self, timesec, callback, args):
        timer = Timer(timesec, callback, args)
        heapq.heappush(self.timerHeap, timer)
        return timer


class Handler(threading.Thread):
    def __init__(self, reli=None, reliImpl=None):
        super().__init__()
        self.reli = reli
        self.reliImpl = reliImpl

    def run(self):
        inputs = [self.reli.getskt()]
        outputs = [self.reli.getskt()]
        while self.reli.status != CLOSED:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for skt in readable:
                seg_str = self.reli.recvfrom()
                if ReliableImpl.checksum(seg_str) != 0:
                    continue
                seg = Segment(seg_str)
                if self.reli.status == CONNECTED:
                    if seg.ack and not seg.syn and not seg.fin:
                        self.reli.bytesInFly -= self.reliImpl.recvAck(seg, False)
                elif self.reli.status == FINWAIT:
                    if seg.ack and not seg.syn and not seg.fin:
                        self.reli.bytesInFly -= self.reliImpl.recvAck(seg, False)
                    elif seg.ack and seg.fin:
                        self.reli.bytesInFly -= self.reliImpl.recvAck(seg, True)
                        self.reli.status = CLOSED

            for skt in writable:
                if self.reli.status != CONNECTED or self.reli.bytesInFly >= min(self.reli.rwnd, self.reli.cwnd):
                    continue

                try:
                    payload = self.reli.getPayload()
                except Exception as e:
                    continue
                if payload is None:
                    self.reli.bytesInFly += self.reliImpl.sendData(b'', True)
                    self.reli.status = FINWAIT
                else:
                    self.reli.bytesInFly += self.reliImpl.sendData(payload, False)

            timestamp = time.time()
            while len(self.reli.timerHeap) > 0:
                timer = self.reli.timerHeap[0]
                if timestamp < timer.timestamp:
                    break
                heapq.heappop(self.reli.timerHeap)
                if timer.enable:
                    timer.run()
