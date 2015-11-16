#!/usr/bin/python
import os
import sys
from subprocess import call

DEBUG = 1

# rw: 1-READ, 2-WRITE
# bs: string value of bs parameter
#
# read stat file of disk and extract ratio of sector per milli-second
# of various IO size
def get_factor(file, device, rw, dd_bs, dd_count):
    if (rw == 1): # READ
        # READ test needs actual device to generate physical IO.
        # File reading can happen on buffered file in memory.
        # parm_if = "/dev/" + device
        parm_if = "./big"
        parm_of = "/dev/null"
        parm_flag = "iflag=direct,dsync"
        io_count_idx = 0
        sector_idx = 2
        tick_idx = 3
        # drop buffer/cache to read disk data
        command = "echo 3 | sudo tee /proc/sys/vm/drop_caches" + "dd"+" if="+parm_if+" of="+parm_of+" "+parm_flag+" bs="+str(dd_bs)+" count="+str(dd_count)
    else: # WRITE
        parm_if = "/dev/zero"
        parm_of = "./big"
        parm_flag = "oflag=direct,dsync conv=fsync"
        io_count_idx = 4
        sector_idx = 6
        tick_idx = 7
        command = "dd"+" if="+parm_if+" of="+parm_of+" "+parm_flag+" bs="+str(dd_bs)+" count="+str(dd_count)

    file.seek(0)
    line = file.read()
    io_count_before = int(line.split()[io_count_idx])
    sector_before = int(line.split()[sector_idx])
    ticks_before = int(line.split()[tick_idx])

    if (DEBUG == 1):
        print command
        os.system(command)
    else:
        os.system(command + " 2> /dev/null")
        
    file.seek(0)
    line = file.read()
    io_count_after = int(line.split()[io_count_idx])
    sector_after = int(line.split()[sector_idx])
    ticks_after = int(line.split()[tick_idx])

    if (DEBUG == 1):
        print 'io:{0}-{1}={2}'.format(io_count_before, io_count_after, io_count_after-io_count_before)
        print 'sectors:{0}-{1}={2}'.format(sector_before, sector_after, sector_after-sector_before)
        print 'ms:{0}-{1}={2}'.format(ticks_before, ticks_after, ticks_after-ticks_before)
        print 'sector-per-io={0}'.format((sector_after - sector_before) / (io_count_after - io_count_before))
        print 'sector-per-ms={0}'.format((sector_after - sector_before) / (ticks_after - ticks_before))

    assert sector_after != sector_before
    assert ticks_after != ticks_before
    return round((sector_after - sector_before) / float(ticks_after - ticks_before), 2)

device_opt = sys.argv[1]
f = open("/sys/block/" + device_opt + "/stat", "r")
bs_sizes =  [  1,   2,   4,   8,  16,  32,  64,  128, 256, 512, 1024, 2048, 4096]
counts   =  [  5,   5,   5,   5,   3,   3,   3,    3,   3,   1,    1,    1,    1]    
read_factors = []
write_factors = []
for i in range(0, len(bs_sizes)):
    write_factors.append(get_factor(f, device_opt, 2, bs_sizes[i]*1024, counts[i]*1024))
    read_factors.append(get_factor(f, device_opt, 1, bs_sizes[i]*1024, counts[i]*1024))
print "READ-sector/ms:{0}".format(read_factors)
print "WRITE-sector/ms:{0}".format(write_factors)
f.close
