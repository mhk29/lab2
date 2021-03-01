#pragma once

#include "Util.h"

typedef struct ReliableImpl ReliableImpl;
#include "Reliable.h"

struct ReliableImpl
{
    Reliable *reli;
    uint32_t seqNum, srvAckNum;

    // Variables for maintaining sliding window
};

ReliableImpl *reliImplCreate(Reliable *_reli, uint32_t _seqNum, uint32_t _srvSeqNum);
void reliImplClose(ReliableImpl *reliImpl);
uint16_t reliImplChecksum(const char *buf, ssize_t len);
uint32_t reliImplRecvAck(ReliableImpl *reliImpl, const Segment *seg, bool isFin);
uint32_t reliImplSendData(ReliableImpl *reliImpl, char *payload, uint16_t payloadlen, bool isFin);
void *reliImplRetransmission(void *args);
