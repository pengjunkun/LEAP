#!/usr/bin/env python

import math, optparse, random, socket, sys, time
import dpkt


class Ping(object):
    def __init__(self, count = 5, wait = 1):
        # usage = '%prog [OPTIONS] <host>'
        # self.op = optparse.OptionParser(usage=usage)
        # self.op.add_option('-c', dest='count', type='int', default=sys.maxint,
        #                    help='Total number of queries to send')
        # self.op.add_option('-i', dest='wait', type='float', default=1,
        #                    help='Specify packet interval timeout in seconds')

        self.dict["count"] = count
        self.dict["wait"] = wait

    def gen_ping(self):
        pass

    def open_sock(self):
        pass

    def print_header(self):
        pass

    def print_reply(self, buf):
        pass

    def main(self, host): # argv=None):
        # if not argv:
        #     argv = sys.argv[1:]
        # opts, args = self.op.parse_args(argv)
        # print(opts)
        # if not args:
        #     self.op.error('missing host')
        # elif len(args) > 1:
        #     self.op.error('only one host may be specified')

        # host = args[0]
        # opts.ip = socket.gethostbyname(host)
        self.dict["ip"] = socket.gethostbyname(host)
        sock = self.open_sock()

        sent = rcvd = rtt_max = rtt_sum = rtt_sumsq = 0
        rtt_min = 0xffff
        try:
            self.print_header()
            for ping in self.gen_ping():
                try:
                    start = time.time()
                    sock.send(ping)
                    buf = sock.recv(0xffff)
                    rtt = time.time() - start

                    if rtt < rtt_min: rtt_min = rtt
                    if rtt > rtt_max: rtt_max = rtt
                    rtt_sum += rtt
                    rtt_sumsq += rtt * rtt

                    self.print_reply(buf, rtt)
                    rcvd += 1
                except socket.timeout:
                    pass
                sent += 1
                time.sleep(self.dict["wait"])
        except KeyboardInterrupt:
            pass

        print '\n--- %s ping statistics ---' % self.dict["ip"]
        print '%d packets transmitted, %d packets received, %.1f%% packet loss' % \
              (sent, rcvd, (float(sent - rcvd) / sent) * 100)
        rtt_avg = rtt_sum / sent
        if rtt_min == 0xffff: rtt_min = 0
        print 'round-trip min/avg/max/std-dev = %.3f/%.3f/%.3f/%.3f ms' % \
              (rtt_min * 1000, rtt_avg * 1000, rtt_max * 1000,
               math.sqrt((rtt_sumsq / sent) - (rtt_avg * rtt_avg)) * 1000)

        return rtt_avg*1000


class ICMPPing(Ping):
    dict = {}
    def __init__(self):
        Ping.__init__(self)
        # self.op.add_option('-p', dest='payload', type='string',
        #                    default='hello world!',
        #                    help='Echo payload string')
        self.dict["payload"] = "hello world!"

    def open_sock(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)
        sock.connect(( self.dict["ip"], 1))
        sock.settimeout(self.dict["wait"])
        return sock

    def gen_ping(self):
        for i in xrange(self.dict["count"]):
            icmp = dpkt.icmp.ICMP(
                type=8, data=dpkt.icmp.ICMP.Echo(id=random.randint(0, 0xffff),
                                                 seq=i, data=self.dict["payload"]))
            yield str(icmp)

    def print_header(self):
        print 'PING %s: %d data bytes' % (self.dict["ip"], len(self.dict["payload"]))

    def print_reply(self, buf, rtt):
        ip = dpkt.ip.IP(buf)
        if sys.platform == 'darwin':
            # XXX - work around raw socket bug on MacOS X
            ip.data = ip.icmp = dpkt.icmp.ICMP(buf[20:])
            ip.len = len(ip.data)
        print '%d bytes from %s: icmp_seq=%d ip_id=%d ttl=%d time=%.3f ms' % \
              (len(ip.icmp), self.dict["ip"], ip.icmp.echo.seq, ip.id, ip.ttl,
               rtt * 1000)


if __name__ == '__main__':
    p = ICMPPing()
    p.main("biadu.com")
