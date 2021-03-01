#include "Util.h"

void ErrorHandler(const char *err)
{
    fprintf(stderr, "%s\n", err);
    exit(0);
}

double get_current_time()
{
    struct timeval current_t;
    gettimeofday(&current_t, NULL);
    return current_t.tv_sec + 1.0 * current_t.tv_usec / 1000000;
}

void Free(void *p)
{
    if (p != NULL)
    {
        free(p);
        p = NULL;
    }
}

uint32_t rand32()
{
    uint32_t x;
    x = rand() & 0xff;
    x |= (rand() & 0xff) << 8;
    x |= (rand() & 0xff) << 16;
    x |= (rand() & 0xff) << 24;
    return x;
}

static void uint32AddrBytes(uint32_t x, char *buf)
{
    for (int i = 0; i < 4; i++)
        buf[i] = *(((char *)&x) + i);
}

static void uint16AddrBytes(uint16_t x, char *buf)
{
    for (int i = 0; i < 2; i++)
        buf[i] = *(((char *)&x) + i);
}

static void uint32ToBytes(uint32_t x, char *buf)
{
    x = htonl(x);
    uint32AddrBytes(x, buf);
}

static void uint16ToBytes(uint16_t x, char *buf)
{
    x = htons(x);
    uint16AddrBytes(x, buf);
}

Segment *segParse(Segment *seg, char *buf, size_t _len)
{
    seg->seqNum = ntohl(*(uint32_t *)buf);
    seg->ackNum = ntohl(*(uint32_t *)(buf + 4));
    seg->rwnd = ntohl(*(uint32_t *)(buf + 8));
    uint16_t flags = ntohs(*(uint16_t *)(buf + 12));
    seg->ack = ((flags & 4) == 4);
    seg->syn = ((flags & 2) == 2);
    seg->fin = ((flags & 1) == 1);
    seg->checksum = ntohs(*(uint16_t *)(buf + 14));
    seg->payload = buf + 16;
    seg->len = _len - 16;
    return seg;
}

size_t segPack(const Segment *seg, char *buf, size_t size)
{
    uint32ToBytes(seg->seqNum, buf);
    uint32ToBytes(seg->ackNum, buf + 4);
    uint32ToBytes(seg->rwnd, buf + 8);
    uint16ToBytes(seg->ack * 4 + seg->syn * 2 + seg->fin, buf + 12);
    uint16AddrBytes(seg->checksum, buf + 14);
    if (seg->payload != NULL && size - 16 >= seg->len)
        memcpy(buf + 16, seg->payload, seg->len);
    return seg->len + 16;
}

void segPrint(const Segment *seg)
{
    printf("%u,%u,%u,%u\n", seg->seqNum, seg->ackNum, seg->rwnd, seg->len);
    printf("%u,%u,%u\n", seg->ack, seg->syn, seg->fin);
    for (int i = 0; i < seg->len; i++)
        printf("%d ", seg->payload[i]);
    printf("\n");
}

void timerInit(Timer *timer, double timesec, void *(*_callback)(void *), void *_args)
{
    timer->timestamp = get_current_time() + timesec;
    timer->callback = _callback;
    timer->args = _args;
    timer->enable = true;
}

void timerCancel(Timer *timer)
{
    timer->enable = false;
}

void *timerRun(const Timer *timer)
{
    return timer->callback(timer->args);
}

int timerCmp(const void *lhs, const void *rhs)
{
    double a = ((Timer *)lhs)->timestamp, b = ((Timer *)rhs)->timestamp;
    if (a == b)
        return 0;
    return (a < b) ? 1 : -1;
}
