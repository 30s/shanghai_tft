#
# [2011-12-25 23:40] V 1.1.0(alpha 1)
# * Show window maximized.
# * Different flash use different index and font libraries.
#   (when open bin, flash type auto detected)
#

import sip
sip.setapi('QVariant', 2)
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import os
import time
import threading
import shutil
import string
from BinGen import *
import qrc_resources


__version__ = u"Bin 生成工具 1.1.0(alpha 1)"


CAPS = [0x200000, 0x400000, 0x800000, 0x1000000, 0x2000000, 0x4000000, 0x8000000, 0x10000000, 0x20000000, 0x40000000]

class BinGentor(QDialog):
      
    def __init__(self, parent=None):
        super(BinGentor, self).__init__(parent, Qt.WindowMinMaxButtonsHint)        

        self.flash_box = QGroupBox(u"Flash")
        lbl_mem = QLabel(u"Flash 空间：")
        self.cbo_mem = QComboBox()
        self.cbo_mem.addItem("  2 M Bytes")
        self.cbo_mem.addItem("  4 M Bytes")
        self.cbo_mem.addItem("  8 M Bytes")
        self.cbo_mem.addItem(" 16 M Bytes")
        self.cbo_mem.addItem(" 32 M Bytes")
        self.cbo_mem.addItem(" 64 M Bytes")
        self.cbo_mem.addItem("128 M Bytes")
        self.cbo_mem.addItem("256 M Bytes")
        self.cbo_mem.addItem("512 M Bytes")
        self.cbo_mem.addItem("  1 G Bytes")
        self.flash = 2
        self.connect(self.cbo_mem, SIGNAL("currentIndexChanged (int)"), self.mem_changed)

        self.used = 0
        lbl_used = QLabel(u"空间使用率：")
        self.pro_used = QProgressBar()
        self.pro_used.setRange(0, 100)
        self.pro_used.setValue(
            (self.used + FLASH_IDX[self.flash][1]) * 1.0 / 
            CAPS[self.cbo_mem.currentIndex()] * 100)

        lbl_ph = QLabel("   ")
        
        fGrid = QGridLayout()
        fGrid.addWidget(lbl_mem, 0, 0)
        fGrid.addWidget(self.cbo_mem, 0, 1)
        fGrid.addWidget(lbl_ph, 0, 2)
        fGrid.addWidget(lbl_used, 1, 0)
        fGrid.addWidget(self.pro_used, 1, 1, 1, 2)
        self.flash_box.setLayout(fGrid)

        self.view_box = QGroupBox(u"图片预览")
        self.imageLabel = QLabel()
        lbl_link = QLabel("<a href=http://www.nuptech.com><font size=4 color=blue>www.nuptech.com</font></a>")
        lbl_link.setAlignment(Qt.AlignCenter)
        self.imageLabel.setMinimumSize(320, 240)
        self.imageLabel.setAlignment(Qt.AlignCenter)
        iGrid = QGridLayout()
        iGrid.addWidget(self.imageLabel, 0, 0, 15, 1)
#        iGrid.addWidget(lbl_link, 15, 0)
        self.view_box.setLayout(iGrid)
        self.connect(lbl_link, SIGNAL("linkActivated (const QString&)"), self.open_url)

        self.file_box = QGroupBox(u"图片列表")

        self.listWidget = QListWidget()

	btn_open = QPushButton(u"打开")
        btn_up = QPushButton(u"上移")
        btn_down = QPushButton(u"下移")
        btn_del = QPushButton(u"删除")
        btn_save = QPushButton(u"另存图片")
        btn_test = QPushButton(u"test")
        btn_gen = QPushButton(u"生成")        

        self.connect(btn_open, SIGNAL("clicked()"), self.open)
        self.connect(btn_up, SIGNAL("clicked()"), self.up)
        self.connect(btn_down, SIGNAL("clicked()"), self.down)
        self.connect(btn_del, SIGNAL("clicked()"), self.remove)
        self.connect(btn_save, SIGNAL("clicked()"), self.save)
        self.connect(btn_test, SIGNAL("clicked()"), self.test)
        self.connect(btn_gen, SIGNAL("clicked()"), self.generate)
        self.connect(self.listWidget, SIGNAL("itemClicked (QListWidgetItem *)"), self.show_me)

        mGrid = QGridLayout()
        mGrid.addWidget(self.listWidget, 0, 0, 8, 2)
        mGrid.addWidget(btn_open, 0, 2)
        mGrid.addWidget(btn_up, 1, 2)
        mGrid.addWidget(btn_down, 2, 2)
        mGrid.addWidget(btn_del, 3, 2)
        mGrid.addWidget(btn_save, 4, 2)
#        mGrid.addWidget(btn_test, 5, 2)
        mGrid.addWidget(btn_gen, 7, 2)
        self.file_box.setLayout(mGrid)

	grid = QGridLayout()
	grid.addWidget(self.view_box, 0, 0, 6, 3)
	grid.addWidget(self.flash_box, 0, 3, 1, 3)
        grid.addWidget(self.file_box, 1, 3, 5, 3)
	self.setLayout(grid)

        self.bins = {}
        self.proDlg = None

        self.setWindowTitle(__version__)

    def test(self):        
        th = Test()
        del self.proDlg
        self.proDlg = QProgressDialog("", "test", 0, 1000)
        
        self.proDlg.setModal(True)
        self.proDlg.show()
        self.connect(th, SIGNAL("error(QString)"), self.error)
        th.test_run(1000, self)

    def error(self, type):
        self.proDlg.close()
        if type == "lib_1":
#            print "lib_1"
            QMessageBox.warning(self, "Bin", u"字库文件不存在！", u"我知道了")
        elif type == "lib_2":
            QMessageBox.warning(self, "Bin", u"Flash 字库文件太大！", u"我知道了")
        elif type == "lib_3":
            QMessageBox.warning(self, "Bin", u"创建 Bin 文件失败！", u"我知道了")
        elif type == "sav_except":
            QMessageBox.warning(self, "Bin", u"另存图片发生异常！", u"我知道了")
        elif type == "gen_except":
            QMessageBox.warning(self, "Bin", u"生成过程发生异常！", u"我知道了")

    def open(self):        
        settings = QSettings()        
        if not settings.value("path"):
            settings.setValue("path", ".")
        fnames = QFileDialog.getOpenFileNames(self, 
                          u"打开图片文件", settings.value("path"),
                          u"位图文件(*.bmp);;Bin 文件(*.bin)")
        if not fnames:
            return
        fmt_errs = []
        while not fnames.isEmpty():            
            fname = unicode(fnames.takeAt(0))
            settings.setValue("path", os.path.split(unicode(fname))[0])
            if fname.endswith(".bin"):
                self.open_bin(fname, fmt_errs)
                continue
            w, h, b, c = get_bmp_info(fname)
            if b == 0:
                fmt_errs.append(fname)
                continue
            elif b == 1:
                byte_line = 0
                if w % 8 == 0:
                    byte_line = w / 8
                else:
                    byte_line = w / 8 + 1
                self.used += (byte_line * h + 6)
            else:
                self.used += (w * h * 2 + 6)
            self.listWidget.addItem(fname)
        self.mem_changed(self.cbo_mem.currentIndex())
        if len(fmt_errs) != 0:
            QMessageBox.warning(self, "Bin", u"以下图片文件或Bin文件格式错误：\n" + u'\n'.join(fmt_errs), u"我知道了")            

    def open_bin(self, fname, fmt_errs):
        addrs, size = get_imgs_from_bin(fname)
        if addrs == False:
            fmt_errs.append(fname)
            return
        self.bins[fname] = addrs
        self.used += size
#        print size
        for i in range(len(addrs)):
            self.listWidget.addItem(fname.replace(".bin", "_%d" % i))

    def showImage(self):
        if self.image.isNull():
            return
        size = self.imageLabel.frameSize()
        lw, lh = size.width(), size.height()
        iw, ih = self.image.width(), self.image.height()
        factor = 1.0
        if (iw > lw) or (ih > lh):
            factor = (lw * 1.0 / iw)
            if factor > (lh * 1.0 / ih):
                factor = (lh * 1.0 / ih)
        width = self.image.width() * factor
        height = self.image.height() * factor
        image = self.image.scaled(width, height, Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(QPixmap.fromImage(image))

    def get_image(self, fname):
        split = fname.rsplit("_")
        bname = split[0]+".bin" 
        bidx = string.atoi(split[1])
        return get_image_contents(bname, self.bins[bname][bidx], bidx)        

    def show_me(self, item):
        self.image = QImage()
        fname = unicode(item.text())
        if fname.endswith(".bmp"):
            self.image.load(fname)
        else:
            if not self.image.load(fname):
                self.imageLabel.setText(u"正在生成预览...")
                self.imageLabel.repaint()
                self.image = self.get_image(fname)
        if self.image == None:
            self.imageLabel.setText(u"生成预览失败!")
        else:
            self.showImage()

    def mem_changed(self, index):
        if (index == 0) or (index == 1):
            self.flash = 2
        elif (index == 2):
            self.flash = 8
        else:
            self.flash = 16

        if self.used > (CAPS[self.cbo_mem.currentIndex()] - FLASH_IDX[self.flash][1]):
            QMessageBox.warning(self, "Bin", u"Flash 空间已满，请删除一些图片！", u"我知道了")
            self.pro_used.setValue(0)
        self.pro_used.setValue(
            (self.used + FLASH_IDX[self.flash][1]) * 1.0 / 
            CAPS[self.cbo_mem.currentIndex()] * 100)

    def remove(self):
        row = self.listWidget.currentRow()
        item = self.listWidget.item(row)
        if item is None:
            return
        item = self.listWidget.takeItem(row)
        fname = unicode(item.text())
        if fname.endswith(".bmp"):
            w, h, b, c = get_bmp_info(fname)
            if b == 1:
                byte_line = 0
                if w % 8 == 0:
                    byte_line = w / 8
                else:
                    byte_line = w / 8 + 1
                    self.used += (byte_line * h + 6)
            else:
                self.used -= (w * h * 2 + 6)
        else:
            split = fname.rsplit("_")
            bname = split[0]+".bin"            
            num = get_bin_size(bname, self.bins[bname][string.atoi(split[1])])
            self.used -= num
        self.mem_changed(self.cbo_mem.currentIndex())        
        del item
        self.imageLabel.clear()

    def up(self):
        row = self.listWidget.currentRow()
        if row >= 1:
            item = self.listWidget.takeItem(row)
            self.listWidget.insertItem(row - 1, item)
            self.listWidget.setCurrentItem(item)

    def down(self):
        row = self.listWidget.currentRow()
        if row < self.listWidget.count() - 1:
            item = self.listWidget.takeItem(row)
            self.listWidget.insertItem(row + 1, item)
            self.listWidget.setCurrentItem(item)

    def generate(self):
        num = self.listWidget.count()
        if num == 0:
            QMessageBox.information(None, "Bin", u"图片列表中没有图片", u"确定")            
            return
        if num > 255:
            QMessageBox.warning(self, "Bin", u"图片不能超过 255 张！", u"我知道了")
            return
        if self.used > CAPS[self.cbo_mem.currentIndex()]:
            QMessageBox.warning(self, "Bin", u"Flash 空间已满，请删除一些图片！", u"我知道了")
            return
        settings = QSettings()        
        if not settings.value("savePath"):
            settings.setValue("savePath", ".")
        fname = QFileDialog.getSaveFileName(self, 
                          u"Bin文件", settings.value("savePath"),
                          u"Bin文件(*.bin)")
        if not fname:
            return
        settings.setValue("savePath", os.path.split(unicode(fname))[0])
        del self.proDlg
        self.proDlg = QProgressDialog(u"", u"停止", 0, num)
        self.proDlg.setWindowTitle(u"生成 Bin 文件")
        self.proDlg.setAutoClose(False)
        self.proDlg.setAutoReset(False)
        self.proDlg.setModal(True)
        self.proDlg.show()
        print unicode(fname)
        self.disco()
        self.wthread = Worker()
        self.connect(self.wthread, SIGNAL("error(QString)"), self.error)
        self.wthread.generate(self, unicode(fname), num, self.flash)


    def save(self):
        num = self.listWidget.count()
        if num == 0:
            QMessageBox.information(None, "Bin", u"图片列表中没有图片", u"确定")
            return
        settings = QSettings()        
        if not settings.value("saveListPath"):
            settings.setValue("saveListPath", ".")
        dname = QFileDialog.getExistingDirectory(
            self, u"选择文件夹", settings.value("saveListPath"))
        if not dname:
            return
        settings.setValue("saveListPath", unicode(dname))
        del self.proDlg
        self.proDlg = QProgressDialog(u"", u"停止", 0, num)
        self.proDlg.setWindowTitle(u"另存图片")
        self.proDlg.setAutoClose(False)
        self.proDlg.setAutoReset(False)
        self.proDlg.setModal(True)
        self.proDlg.show()
        self.disco()
        self.sthread = Saver()
        self.connect(self.sthread, SIGNAL("error(QString)"), self.error)
        self.sthread.savelist(self, num, unicode(dname))

    def open_url(self, url):
        os.system(u"start explorer " + unicode(url))

    def disco(self):
        attrs = dir(self)
        if "wthread" in attrs:
            self.disconnect(self.wthread, SIGNAL("error(QString)"), self.error)
        if "sthread" in attrs:
            self.disconnect(self.sthread, SIGNAL("error(QString)"), self.error)

class Test(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)

    def __del__(self):
        self.wait()

    def test_run(self, num, dlg):
        self.num = num
        self.dlg = dlg
        self.start()

    def run(self):
        for i in range(0, self.num):
#            self.dlg.proDlg.setValue(i)
#            if self.dlg.proDlg.wasCanceled():
#                self.emit(SIGNAL("error(QString)"), "sav_cancel")
#                return
            print i
#        item = self.dlg.listWidget.item(0)
#        print unicode(item.text())
#        self.dlg.proDlg.setLabelText(u"所有图片另存到目录：" )
#        self.dlg.proDlg.setCancelButtonText(u"确定")    
#        self.emit(SIGNAL("error(QString)"), "lib_1")
#
class Worker(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)

    def __del__(self):
        self.wait()

    def generate(self, dlg, filename, num, flash):
        self.dlg = dlg
        self.fname = filename
        self.num = num
        self.flash = flash
        self.start()

    def run(self):
        IDX_IMG_IDX = FLASH_IDX[self.flash][0]
        IDX_IMG_DAT = FLASH_IDX[self.flash][1]
        LIB_PATH    = FLASH_IDX[self.flash][2]
        data = None
        try:
            f = open(LIB_PATH, 'rb')
            data = f.read()
            f.close()
        except IOError:
            print "lib_1 in run"
            self.emit(SIGNAL("error(QString)"), "lib_1")
            return
        if len(data) > IDX_IMG_IDX:
            self.emit(SIGNAL("error(QString)"), "lib_2")
            return
        f = None
        try:
            f = open(self.fname, 'wb')
        except IOError:
            self.emit(SIGNAL("error(QString)"), "lib_3")
            f.close()
            return            
        f.write(data)
        f.flush()
        s = (IDX_IMG_DAT - len(data)) * '\xff'
        f.write(s)
        f.flush()
	idxs = [IDX_IMG_DAT]
        i = 0
        try:
            while i < self.num :
                item = self.dlg.listWidget.item(i)
                filename = unicode(item.text())
                print filename
                self.dlg.proDlg.setLabelText(filename)
                data = None
                if not filename.endswith(".bmp"):
                    split = filename.rsplit("_")
                    bname = split[0]+".bin"            
                    bidx = self.dlg.bins[bname][string.atoi(split[1])]
                    num = get_bin_size(bname, bidx)
                    bf = open(bname, "rb")
                    bf.seek(bidx)
                    data = bf.read(num)
    #                print len(data)
                else:
    #		print filename
                    data = get_img_data(filename)
                f.write(data)
                f.flush()
                idxs.append(idxs[i] + len(data))
                i += 1        
                self.dlg.proDlg.setValue(i)
                if self.dlg.proDlg.wasCanceled():
                    f.close()
                    self.emit(SIGNAL("error(QString)"), "gen_cancel")
                    return
        except Exception:
            print "gen exception"
            f.close()
            self.emit(SIGNAL("error(QString)"), "gen_except")
            return
        f.seek(IDX_IMG_IDX)
        for idx in idxs[:-1]:
            f.write(struct.pack(">I", idx))
        f.flush()
        f.close()
        self.dlg.proDlg.setLabelText(u"生成成功！")
        self.dlg.proDlg.setCancelButtonText(u"确定")

class Saver(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)

    def __del__(self):
        self.wait()

    def savelist(self, dlg, num, dname):
        self.dlg = dlg
        self.dname = dname
        self.num = num
        self.start()

    def run(self):        
        i = 0
        try:
            while i < self.num:
                item = self.dlg.listWidget.item(i)
                nf = self.dname + "\IMG_" + str(i) + ".bmp"
                fname = unicode(item.text())
                print fname, nf
                self.dlg.proDlg.setLabelText(fname + u" 另存为 " + nf)
                if not fname.endswith(".bmp"):
                    self.dlg.get_image(fname)
                    fname += ".bmp"
                shutil.copy(fname, nf)
                i += 1
                self.dlg.proDlg.setValue(i)            
                if self.dlg.proDlg.wasCanceled():
                    self.emit(SIGNAL("error(QString)"), "sav_cancel")
                    return
        except Exception:
            self.emit(SIGNAL("error(QString)"), "sav_except")
            return
        self.dlg.proDlg.setLabelText(u"所有图片另存到目录：" + self.dname + " !")
        self.dlg.proDlg.setCancelButtonText(u"确定")    
        
def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("Qtrac Ltd.")
    app.setOrganizationDomain("qtrac.eu")
    app.setApplicationName("Image Changer")
    app.setWindowIcon(QIcon(":/icon.ico"))
    form = BinGentor()
    form.showMaximized()
    app.exec_()
#    form.disco()
    for i in GEN_IMG_FILES:
        os.remove(i)

main()
