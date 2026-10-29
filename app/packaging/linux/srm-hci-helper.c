/*
 * srm-hci-helper – sendet Bluetooth-Werbedaten für Mould-King-Hubs (Stud Rail Master, Linux).
 *
 * Das einzige Teil des Programms mit dem Recht CAP_NET_RAW. Es kann nur Werbung einstellen,
 * senden und abschalten – nichts anderes. Das Hauptprogramm spricht über stdin/stdout:
 *
 *   Start:   srm-hci-helper <hci-nummer>      → "READY legacy" | "READY extended" | "ERR <grund>"
 *   D <hex>  Werbedaten (≤ 31 Byte) setzen, beim ersten Mal einschalten → "OK" | "ERR <grund>"
 *   X        Werbung aus → "OK"
 *   EOF      Werbung aus, Ende
 *
 * Bauen: cc -O2 -Wall -static -o srm-hci-helper srm-hci-helper.c
 * Gleiche HCI-Kommandos wie app/studrailmaster/radio/adv_linux.py.
 */
#include <errno.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define AF_BT 31
#define BTPROTO_HCI 1
#define SOL_HCI 0
#define HCI_FILTER 2
#define OGF_LE 0x08
#define INTERVAL 160 /* × 0,625 ms = 100 ms */
#define ADV_HANDLE 0x0E

struct sockaddr_hci {
    sa_family_t hci_family;
    unsigned short hci_dev;
    unsigned short hci_channel;
};

struct hci_filter {
    uint32_t type_mask;
    uint32_t event_mask[2];
    uint16_t opcode;
};

static int fd = -1;
static int extended = 0;
static int on = 0;

/* Kommando senden und auf Command Complete / Command Status warten; Rückgabe: HCI-Status oder -1 */
static int hci_cmd(uint16_t ocf, const uint8_t *params, uint8_t plen) {
    uint16_t opcode = (uint16_t)((OGF_LE << 10) | ocf);
    uint8_t buf[4 + 255];
    buf[0] = 0x01;
    buf[1] = opcode & 0xFF;
    buf[2] = opcode >> 8;
    buf[3] = plen;
    memcpy(buf + 4, params, plen);
    if (write(fd, buf, 4 + plen) < 0) return -1;
    for (int tries = 0; tries < 20; tries++) {
        struct pollfd p = {fd, POLLIN, 0};
        if (poll(&p, 1, 1000) <= 0) return -1;
        uint8_t ev[260];
        ssize_t n = read(fd, ev, sizeof(ev));
        if (n < 7 || ev[0] != 0x04) continue;
        if (ev[1] == 0x0E && (ev[4] | (ev[5] << 8)) == opcode) return ev[6];
        if (ev[1] == 0x0F && (ev[5] | (ev[6] << 8)) == opcode) return ev[3];
    }
    return -1;
}

static int set_params(void) {
    uint8_t lp[15] = {INTERVAL & 0xFF, INTERVAL >> 8, INTERVAL & 0xFF, INTERVAL >> 8,
                      0x03 /* ADV_NONCONN_IND */, 0x00, 0x00, 0, 0, 0, 0, 0, 0, 0x07, 0x00};
    int st = hci_cmd(0x0006, lp, sizeof(lp));
    if (st == 0) return 0;
    if (st != 0x0C && st != 0x01) return st;
    /* Controller ist im Extended-Modus: Extended-Parameter mit Legacy-PDU 0x0010 */
    extended = 1;
    uint8_t ep[25] = {ADV_HANDLE, 0x10, 0x00,
                      INTERVAL & 0xFF, INTERVAL >> 8, 0, INTERVAL & 0xFF, INTERVAL >> 8, 0,
                      0x07, 0x00, 0x00, 0, 0, 0, 0, 0, 0,
                      0x00, 0x7F, 0x01, 0x00, 0x01, 0x00, 0x00};
    return hci_cmd(0x0036, ep, sizeof(ep));
}

static int enable(int en) {
    if (extended) {
        uint8_t p[6] = {(uint8_t)en, 1, ADV_HANDLE, 0, 0, 0};
        return hci_cmd(0x0039, p, sizeof(p));
    }
    uint8_t p[1] = {(uint8_t)en};
    return hci_cmd(0x000A, p, 1);
}

static int set_data(const uint8_t *d, uint8_t len) {
    uint8_t p[35] = {0};
    int st;
    if (extended) {
        p[0] = ADV_HANDLE;
        p[1] = 0x03;
        p[2] = 0x01;
        p[3] = len;
        memcpy(p + 4, d, len);
        st = hci_cmd(0x0037, p, 4 + len);
    } else {
        p[0] = len;
        memcpy(p + 1, d, len);
        st = hci_cmd(0x0008, p, 32);
    }
    if (st == 0 && !on) {
        st = enable(1);
        on = st == 0;
    }
    return st;
}

static int hexval(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

int main(int argc, char **argv) {
    int dev = argc > 1 ? atoi(argv[1]) : 0;
    setvbuf(stdout, NULL, _IOLBF, 0);
    fd = socket(AF_BT, SOCK_RAW, BTPROTO_HCI);
    struct sockaddr_hci a = {AF_BT, (unsigned short)dev, 0};
    if (fd < 0 || bind(fd, (struct sockaddr *)&a, sizeof(a)) < 0) {
        printf("ERR socket: %s\n", strerror(errno));
        return 1;
    }
    struct hci_filter f = {1u << 4, {(1u << 0x0E) | (1u << 0x0F), 0}, 0};
    if (setsockopt(fd, SOL_HCI, HCI_FILTER, &f, sizeof(f)) < 0) {
        printf("ERR filter: %s\n", strerror(errno));
        return 1;
    }
    int st = set_params();
    if (st != 0) {
        if (errno == EPERM) printf("ERR permission\n");
        else printf("ERR params 0x%02X\n", st & 0xFF);
        return 1;
    }
    printf("READY %s\n", extended ? "extended" : "legacy");

    char line[256];
    while (fgets(line, sizeof(line), stdin)) {
        if (line[0] == 'X') {
            if (on && enable(0) == 0) on = 0;
            printf("OK\n");
        } else if (line[0] == 'D' && line[1] == ' ') {
            uint8_t d[31];
            int n = 0, bad = 0;
            for (char *p = line + 2; *p && *p != '\n'; p += 2) {
                int hi = hexval(p[0]), lo = p[1] ? hexval(p[1]) : -1;
                if (hi < 0 || lo < 0 || n >= 31) {
                    bad = 1;
                    break;
                }
                d[n++] = (uint8_t)(hi << 4 | lo);
            }
            if (bad || n == 0) printf("ERR data\n");
            else if ((st = set_data(d, (uint8_t)n)) != 0) printf("ERR hci 0x%02X\n", st & 0xFF);
            else printf("OK\n");
        } else {
            printf("ERR command\n");
        }
    }
    if (on) enable(0);
    close(fd);
    return 0;
}
