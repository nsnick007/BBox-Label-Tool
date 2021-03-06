#-------------------------------------------------------------------------------
#
#-------------------------------------------------------------------------------
from __future__ import division
try:
    import Tkinter as tk # this is for python2
    import tkMessageBox
except:
    from tkinter import *
    import tkinter as tk # this is for python3
    import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256
CLASS_NUM = 0

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("物体検出用ラベリングツール")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "画像パス:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "読み込み", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)
        self.Convert2YoloBtn = Button(self.frame, text = 'Convert', command = self.convert2Yolo)
        self.Convert2YoloBtn.grid(row = 0, column = 3)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row = 1, column = 1, rowspan = 5, sticky = W+N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 1, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 2, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 4, column = 2, sticky = W+E+N)
        

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 5, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< 前へ', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='次へ >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "例:")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            if TryParseInt(s) == False:
                tkMessageBox.showerror("Error!", message = "フォルダ名は数値を使用してください。")
                return
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPEG'))
        self.image_convert(self.imageList, ".JPEG", ".png")
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        self.image_convert(self.imageList, ".jpg", ".png")
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpeg'))
        self.image_convert(self.imageList, ".jpeg", ".png")
        self.imageList = []
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.png'))

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        if not os.path.exists(self.imageDir):
            os.mkdir(self.imageDir)
        self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        # load example bboxes
        self.egDir = os.path.join(r'./Examples', '%03d' %(self.category))
        if not os.path.exists(self.egDir):
            os.mkdir(self.egDir)
        filelist = glob.glob(os.path.join(self.egDir, '*.JPEG'))

        if len(self.imageList) == 0:
            print('No images found in the specified dir!')
            tkMessageBox.showerror("Error!", message = "画像ファイルを指定のフォルダに格納してください。")
            return

        self.tmp = []
        self.egList = []
        random.shuffle(filelist)
        for (i, f) in enumerate(filelist):
            if i == 3:
                break
            im = Image.open(f)
            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])

        self.loadImage()
        print('%d images loaded from %s' %(self.total, s))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))
        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    tmp = [int(t.strip()) for t in line.split()]
                    self.bboxList.append(tuple((tmp[1], tmp[2], tmp[3], tmp[4])))
                    tmpId = self.mainPanel.create_rectangle(tmp[1], tmp[2], \
                                                            tmp[3], tmp[4], \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(tmp[1], tmp[2], tmp[3], tmp[4]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def image_convert(self, imageList, from_format, to_format):
        if len(imageList) != 0:
            for image_path in imageList:
                img = Image.open(image_path)
                os.remove(image_path)
                img.save(image_path.replace(from_format, to_format))

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            for bbox in self.bboxList:
                f.write(str(CLASS_NUM) + ' ')
                f.write(' '.join(map(str, bbox)) + '\n')
        print('Image No. %d saved' %(self.cur))


    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        if len(self.imageList) != 0:
            self.saveImage()
            if self.cur > 1:
                self.cur -= 1
                self.loadImage()

    def nextImage(self, event = None):
        if len(self.imageList) != 0:
            self.saveImage()
            if self.cur < self.total:
                self.cur += 1
                self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def convert2Yolo(self):
        #we have to make pair foder images and labels.
        print("convert")
        pair_images = []
        pair_labels = []
        import uuid
        guid = str(uuid.uuid4())
        print(self.imageList)
        for image_path in self.imageList:            
            #image
            img = Image.open(image_path)
            w, h = img.size
            if os.path.exists((os.path.join("Converted", guid))) == False:
                os.mkdir(os.path.join("Converted", guid))
            if os.path.exists((os.path.join("Converted", guid, "images"))) == False:
                os.mkdir(os.path.join("Converted", guid, "images"))
            import shutil
            converted_path = os.path.join("Converted", guid, "images", os.path.basename(image_path))
            shutil.copyfile(image_path, converted_path)

            #label
            if os.path.exists((os.path.join("Converted", guid, "labels"))) == False:
                os.mkdir(os.path.join("Converted", guid, "labels"))
            label_path = image_path.replace("Images","Labels").replace(".png",".txt")
            _line = []
            f = open(label_path,'r')
            line = f.readline()
            if len(line) != 0:
                l = line.replace('\r\n','').replace('\n','').replace('\r','').split(" ")
                _line.append(l)
            while line:
                line = f.readline()
                if len(line) == 0:
                    break
                l = line.replace('\r\n','').replace('\n','').replace('\r','').split(" ")
                _line.append(l)
            f.close()
            for l in _line:
                b = (float(l[1]), float(l[3]), float(l[2]), float(l[4]))
                bb = convert((w,h), b)
                _write_file = open(os.path.join("Converted", guid, "labels", os.path.basename(label_path)), 'a')
                _write_file.write(str(l[0]) + " " + " ".join([str(a) for a in bb]) + "\n")
                _write_file.close()
        zip_directory(os.path.join("Converted", guid))
        print("converted!!")

def TryParseInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

#元のbox
#xmin xmax ymin ymax
#学習データセット作成
#xmin ymin xmax ymax
def convert(size, box):
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)

def zip_directory(path):
    import zipfile
    zip_targets = []
    base = os.path.basename(path)
    zipfilepath = os.path.abspath('%s.zip' % base)
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filepath == zipfilepath:
                continue
            arc_name = os.path.relpath(filepath, os.path.dirname(path))
            print(filepath, arc_name)
            zip_targets.append((filepath, arc_name))
        for dirname in dirnames:
            filepath = os.path.join(dirpath, dirname)
            arc_name = os.path.relpath(filepath, os.path.dirname(path)) + os.path.sep
            print(filepath, arc_name)
            zip_targets.append((filepath, arc_name))
    zip = zipfile.ZipFile(zipfilepath, 'w')
    for filepath, name in zip_targets:
        zip.write(filepath, name)
    zip.close()



if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
