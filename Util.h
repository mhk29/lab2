#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include "Queue.h"

#define UDP_DATAGRAM_SIZE 1024
#define SEGMENT_SIZE (UDP_DATAGRAM_SIZE - 8) // UDP header: 8 bytes
#define PAYLOAD_SIZE (SEGMENT_SIZE - 16)
#define MAX_BAND (50 * 1024 * 1024 / 8)
#define MAX_DELAY 0.5
#define MAX_BDP ((int)(MAX_BAND * MAX_DELAY))
#define MAX_RTO 60.0
#define BUFFER_SIZE (10 * MAX_BDP / PAYLOAD_SIZE)

#define MIN(a, b) (((a) < (b)) ? (a) : (b))
#define MAX(a, b) (((a) > (b)) ? (a) : (b))

void ErrorHandler(const char *err);

double get_current_time();

void Free(void *p);

uint32_t rand32();

typedef struct Segment
{
    uint32_t seqNum, ackNum, rwnd;
    bool ack, syn, fin;
    uint16_t checksum;
    char *payload;
    uint16_t len;
} Segment;

Segment *segParse(Segment *seg, char *buf, size_t _len);
size_t segPack(const Segment *seg, char *buf, size_t size);
void segPrint(const Segment *seg);

typedef struct Timer
{
    double timestamp;
    bool enable;
    void *(*callback)(void *);
    void *args;
} Timer;

void timerInit(Timer *timer, double timesec, void *(*_callback)(void *), void *_args);
void timerCancel(Timer *timer);
void *timerRun(const Timer *timer);
int timerCmp(const void *lhs, const void *rhs);
