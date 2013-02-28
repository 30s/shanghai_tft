import struct
from PyQt4.QtCore import *
from PyQt4.QtGui import *

IDX_ID = 0x00
IDX_WIDTH = 0x12
IDX_HEIGHT = 0x16
IDX_BITS = 0x1C
IDX_COMP = 0x1E

def get_bmp_info(filename):
    """
    param filename
    return a tuple of width, height, bits and compression
    """
    f = open(filename, 'rb')
    data = f.read(2)
    if data != 'BM':
        f.close()
        return (0, 0, 0, 0)
    f.seek(IDX_WIDTH)
    w = struct.unpack("I", f.read(4))[0]
    h = struct.unpack("I", f.read(4))[0]
    f.seek(IDX_BITS)
    b = struct.unpack("H", f.read(2))[0]
    f.seek(IDX_COMP)
    c = struct.unpack("I", f.read(4))[0]    
    f.close()
    if (b == 16 and c == 3) or b == 8:
        return (0, 0, 0, 0)
    return (w, h, b, c)

import Image

FLASH_IDX = {    
    # | flash type | image index | image data | font library |
    # 2MB, 4MB
    2:   [0x41000,  0x42000,  "./162.bin"],

    # 8MB
    8:   [0x3F0000, 0x400000, "./ASC_GB_TS_0_3_4M_LIB.bin"],

    # 16MB, 32MB, 64MB, 128MB, 256MB, 512MB, 1GB
    16:  [0x7F0000, 0x800000, "./ASC_GB_TS_0_4_8M_LIB.bin"],
    }


# IDX_IMG_IDX = 0x41000
# IDX_IMG_DAT = 0x42000
# LIB_PATH = "./162.bin"

def get_img_data(filename):
    """
    brief: Get the image data, gen image header too
    param filename: Image path
    return: image data
    """
    w, h, b, c = get_bmp_info(filename)
    if b == 1:
        return get_1_bits(w, h, filename)
    else:
        return get_16_bits(w, h, filename)
        
	
def get_1_bits(w, h, filename):
    data = ['\x00', '\x01']
    data.append(reverse_str(struct.pack("H", w)))
    data.append(reverse_str(struct.pack("H", h)))
    img = Image.open(filename)
    i = 0
    while i < h:
        j = 0
        pd = 0
        while j < w:
            pix = img.getpixel((j, i))            
            if pix == 0:
                pd |= (1 << (7 - (j % 8)))
            if j % 8 == 7:
                data.append(chr(pd))
                pd = 0
            j += 1
        if j % 8 != 0:
            data.append(chr(pd))
        i += 1
    return ''.join(data)

def get_16_bits(w, h, filename):
    data = ['\x00', '\x10']
    data.append(reverse_str(struct.pack("H", w)))
    data.append(reverse_str(struct.pack("H", h)))
    img = Image.open(filename)
#    print img
    i = 0
    while i < h:
        j = 0
        while j < w:
            pix = img.getpixel((j, i))
            pix = (pix[0]>>3, pix[1]>>2, pix[2]>>3)
            data.append(struct.pack("I", pix[2] | (pix[1] << 5) | (pix[0] << 11))[0:2]) 
            j += 1
        i += 1
    return ''.join(data)
    
def bin_gen(filename, imgs, flash):
    """
    brief: Generate the required bin file
    param filename: the bin file    
    param imgs: Image file paths
    """
    IDX_IMG_IDX = FLASH_IDX[flash][0]
    IDX_IMG_DAT = FLASH_IDX[flash][1]
    LIB_PATH    = FLASH_IDX[flash][2]

    f = open(LIB_PATH, 'rb')
    data = f.read()
    f.close()
    if len(data) > IDX_IMG_IDX:
#        print "char lib too big!"
        return False
    f = open(filename, 'wb')
    f.write(data)
    f.flush()
    data = struct.pack("I", IDX_IMG_DAT)
    lst = list(data)
    lst.reverse()
    data = ''.join(lst)
    f.write(data)
    f.flush()
    s = (IDX_IMG_DAT - IDX_IMG_IDX - len(data)) * '\xff'
    f.write(s)
    f.flush()
    data = get_img_data(imgs)
    f.write(data)
    f.flush()
    f.close()

import struct

def reverse_str(str):
    lst = list(str)
    lst.reverse()
    return ''.join(lst)


def get_imgs_from_bin(filename):
    flash = 2
    IDX_IMG_IDX = FLASH_IDX[flash][0]
    IDX_IMG_DAT = FLASH_IDX[flash][1]
    LIB_PATH    = FLASH_IDX[flash][2]

    try:
        f = open(filename, 'rb')

        # guess flash type
        types = FLASH_IDX.keys()
        types.sort()
        for i in types:
            flash = i
            IDX_IMG_IDX = FLASH_IDX[flash][0]
            IDX_IMG_DAT = FLASH_IDX[flash][1]
            LIB_PATH    = FLASH_IDX[flash][2]

            f.seek(IDX_IMG_IDX)
            if f.tell() != IDX_IMG_IDX:
                return False, 0
            data = f.read(4)
            if len(data) != 4:
                return False, 0
            if struct.unpack(">I", data)[0] == IDX_IMG_DAT:
                break
        else:
            return False, 0

        f.seek(IDX_IMG_IDX)
        addrs = []
        idx = 0
        while f.tell() < IDX_IMG_DAT:
            data = f.read(4)
            if len(data) != 4:
                return False, 0
            if data == "\xff\xff\xff\xff":
                break
            addrs.append(struct.unpack(">I", data)[0])
            if len(addrs) > 255:
                break
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.close()        
        return addrs, size - IDX_IMG_DAT
    except IOError:
        f.close()
        return False, 0

import os

GEN_IMG_FILES = []

def get_image_contents(filename, addr, idx):
    try:               
        imgname = filename.replace(".bin", "_%d" % idx)
        img = QImage()
        if img.load(imgname + ".bmp"):
            return img
        f = open(filename, 'rb')
        f.seek(addr + 1)
        b = ord(f.read(1))
        if b != 16 and b != 1:
            f.close()
            return
        w, h = struct.unpack("2H", reverse_str(f.read(2)) + reverse_str(f.read(2)))
#        print w, h
#        print "%x" % addr
        if b == 1:
#            print "mono"
            img = QImage(w, h, QImage.Format_Mono)
            img.fill(1)
            i = 0
            while i < h:
                j = 0
                pd = 0
                while j < w:
                    if j % 8 == 0:
#                        print i, j
                        pd = ord(f.read(1))
                    if pd & (1 << (7 - j % 8)):
                        img.setPixel(j, i, 0)
                    j += 1
                i += 1
        elif b == 16:
#            print "16"
            img = QImage(w, h, QImage.Format_RGB32)
            img.fill(1)
            i = 0
            while i < h:
                j = 0
                while j < w:
                    pd = f.read(2)
                    pd = [ord(pd[0]), ord(pd[1])]
                #                rgb = (pd[1] & 0xF8) | (((pd[1] << 5) & (pd[0] >> 3) & 0xFC) << 8) | (((pd[0] & 0x1F) << 3) << 16)
                    rgbs = [pd[1] & 0xF8, ((pd[1] << 5) | (pd[0] >> 3)) & 0xFC, (pd[0] & 0x1F) << 3]
                    clr = QColor(rgbs[0], rgbs[1], rgbs[2])
                    img.setPixel(j, i, clr.rgb())
                    j += 1
                i += 1
        f.close()
        img.save(imgname + ".bmp")
        GEN_IMG_FILES.append(imgname + ".bmp")
        return img
    except IOError:
        f.close()

def get_bin_size(filename, addr):
    f = open(filename, 'rb')
    f.seek(addr + 1)
    b = ord(f.read(1))
    if b != 16 and b != 1:
        f.close()
        return
    w, h = struct.unpack("2H", reverse_str(f.read(2)) + reverse_str(f.read(2)))
    f.close()
    if b == 16:
        return w * h * 2 + 6
    elif b == 1:
        bpl = 0
        if w % 8 == 0:
            bpl = w / 8
        else:
            bpl = w / 8 + 1
        return bpl * h + 6
#    elif b == 1:
        
