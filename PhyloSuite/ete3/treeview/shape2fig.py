import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtSvg import QSvgGenerator
import re
# from ete3.treeview.faces import
from ete3.treeview.CustomWidgets import QGraphicsLeftArrowItem, QGraphicsRightArrowItem, QGraphicsLeftTriangleItem, \
    QGraphicsRightTriangleItem, QGraphicsStarItem, QGraphicsStarItem2, QGraphicsTopTriangleItem, \
    QGraphicsBottomTriangleItem, \
    QGraphicsRoundRectItem, QGraphicsDiamondItem, QGraphicsLeftArrowItem2, QGraphicsRightArrowItem2

app = QApplication(sys.argv)

# Defining a scene rect of 400x200, with it's origin at 0,0.
# If we don't set this on creation, we can set it later with .setSceneRect
# scene = QGraphicsScene(0, 0, 50, 50)
# "circle": QGraphicsEllipseItem,
# "rectangle": QGraphicsRectItem,
# "round corner rectangle": QGraphicsRoundRectItem,
# "diamond": QGraphicsDiamondItem,
# "line": QGraphicsLineItem,
# "left arrow": QGraphicsLeftArrowItem,
# "right arrow": QGraphicsRightArrowItem,
# "left triangle": QGraphicsLeftTriangleItem,
# "right triangle": QGraphicsRightTriangleItem,
# "top trangle": QGraphicsTopTriangleItem,
# "bottom triangle": QGraphicsBottomTriangleItem
# Draw a rectangle item, setting the dimensions.

# Define the brush (fill).
# brush = QBrush(QColor("#679ebc"))
# rect.setBrush(brush)

# Define the pen (line)

def save(scene, imgName, w=None, h=None, dpi=300, \
         take_region=False, units="px"):
    ipython_inline = False
    if imgName == "%%inline":
        ipython_inline = True
        ext = "PNG"
    elif imgName == "%%inlineSVG":
        ipython_inline = True
        ext = "SVG"
    elif imgName.startswith("%%return"):
        try:
            ext = imgName.split(".")[1].upper()
        except IndexError:
            ext = 'SVG'
        imgName = '%%return'
    else:
        ext = imgName.split(".")[-1].upper()

    main_rect = scene.sceneRect()
    aspect_ratio = main_rect.height() / main_rect.width()

    # auto adjust size
    if not w and not h:
        units = "px"
        w = main_rect.width()
        h = main_rect.height()
        ratio_mode = Qt.KeepAspectRatio
    elif w and h:
        ratio_mode = Qt.IgnoreAspectRatio
    elif h is None :
        h = w * aspect_ratio
        ratio_mode = Qt.KeepAspectRatio
    elif w is None:
        w = h / aspect_ratio
        ratio_mode = Qt.KeepAspectRatio

    # Adjust to resolution
    if units == "mm":
        if w:
            w = w * 0.0393700787 * dpi
        if h:
            h = h * 0.0393700787 * dpi
    elif units == "in":
        if w:
            w = w * dpi
        if h:
            h = h * dpi
    elif units == "px":
        pass
    else:
        raise Exception("wrong unit format")

    x_scale, y_scale = w/main_rect.width(), h/main_rect.height()

    if ext == "SVG":
        svg = QSvgGenerator()
        targetRect = QRectF(0, 0, w, h)
        svg.setSize(QSize(w, h))
        svg.setViewBox(targetRect)
        svg.setTitle("Generated with PhyloSuite http://phylosuite.jushengwu.com/")
        svg.setDescription("Generated with PhyloSuite http://phylosuite.jushengwu.com/")

        if imgName == '%%return':
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            svg.setOutputDevice(buf)
        else:
            svg.setFileName(imgName)

        pp = QPainter()
        pp.begin(svg)
        scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
        pp.end()
        if imgName == '%%return':
            compatible_code = str(ba)
            print('from memory')
        else:
            compatible_code = open(imgName).read()
        # Fix a very annoying problem with Radial gradients in
        # inkscape and browsers...
        compatible_code = compatible_code.replace("xml:id=", "id=")
        compatible_code = re.sub('font-size="(\d+)"', 'font-size="\\1pt"', compatible_code)
        compatible_code = compatible_code.replace('\n', ' ')
        compatible_code = re.sub('<g [^>]+>\s*</g>', '', compatible_code)
        # End of fix
        if ipython_inline:
            from IPython.core.display import SVG
            return SVG(compatible_code)

        elif imgName == '%%return':
            return x_scale, y_scale, compatible_code
        else:
            open(imgName, "w").write(compatible_code)


    elif ext == "PDF" or ext == "PS":
        if ext == "PS":
            format = QPrinter.PostScriptFormat
        else:
            format = QPrinter.PdfFormat

        printer = QPrinter(QPrinter.HighResolution)
        printer.setResolution(dpi)
        printer.setOutputFormat(format)
        printer.setPageSize(QPrinter.A4)
        printer.setPaperSize(QSizeF(w, h), QPrinter.DevicePixel)
        printer.setPageMargins(0, 0, 0, 0, QPrinter.DevicePixel)

        #pageTopLeft = printer.pageRect().topLeft()
        #paperTopLeft = printer.paperRect().topLeft()
        # For PS -> problems with margins
        #print paperTopLeft.x(), paperTopLeft.y()
        #print pageTopLeft.x(), pageTopLeft.y()
        # print  printer.paperRect().height(),  printer.pageRect().height()
        #topleft =  pageTopLeft - paperTopLeft

        printer.setFullPage(True);
        printer.setOutputFileName(imgName);
        pp = QPainter(printer)
        targetRect =  QRectF(0, 0 , w, h)
        scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
    else:
        targetRect = QRectF(0, 0, w, h)
        ii= QImage(w, h, QImage.Format_ARGB32)
        ii.fill(QColor(Qt.white).rgb())
        ii.setDotsPerMeterX(dpi / 0.0254) # Convert inches to meters
        ii.setDotsPerMeterY(dpi / 0.0254)
        pp = QPainter(ii)
        pp.setRenderHint(QPainter.Antialiasing)
        pp.setRenderHint(QPainter.TextAntialiasing)
        pp.setRenderHint(QPainter.SmoothPixmapTransform)

        scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
        pp.end()
        if ipython_inline:
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            ii.save(buf, "PNG")
            from IPython.core.display import Image
            return Image(ba.data())
        elif imgName == '%%return':
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            ii.save(buf, "PNG")
            return x_scale, y_scale, ba.toBase64()
        else:
            ii.save(imgName)

    return w/main_rect.width(), h/main_rect.height()

def draw_shape(shape, filename, pen_=6):
    scene = QGraphicsScene(-13, -13, 70, 70)
    pen = QPen(QColor("#d78d8e"))
    pen.setWidth(pen_)
    shape.setPen(pen)
    scene.addItem(shape)
    # master = QGraphicsRectItem(-13, -13, 70, 70)
    # scene.addItem(master)
    save(scene, filename)

def draw_shape2(shape, filename, pen_=6):
    br = shape.boundingRect()
    x, y, width, height = br.x(), br.y(), br.width(), br.height()
    scene = QGraphicsScene(x-1, y-1, width+2, height+2)
    pen = QPen(QColor("#d78d8e"))
    pen.setWidth(pen_)
    shape.setPen(pen)
    scene.addItem(shape)
    # master = QGraphicsRectItem(x-1, y-1, width+2, height+2)
    # scene.addItem(master)
    save(scene, filename)

rect = QGraphicsRectItem(0, 0, 50, 50)
circle = QGraphicsEllipseItem(0, 0, 50, 50)
round_rect = QGraphicsRoundRectItem(0, 0, 50, 50)
diamond = QGraphicsDiamondItem(50, 50)
diamond.setPos(0,0)
line = QGraphicsLineItem(0, 0, 50, 50)
left_arrow = QGraphicsLeftArrowItem(50, 50)
left_arrow.setPos(0,0)
right_arrow = QGraphicsRightArrowItem(50, 50)
right_arrow.setPos(0,0)
left_tri = QGraphicsLeftTriangleItem(50,50)
left_tri.setPos(0,0)
right_tri = QGraphicsRightTriangleItem(50,50)
right_tri.setPos(0,0)
top_tri = QGraphicsTopTriangleItem(50, 50)
top_tri.setPos(0,0)
bottom_tri = QGraphicsBottomTriangleItem(50,50)
bottom_tri.setPos(0,0)
star = QGraphicsStarItem(15)
star.setPos(0,0)
star2 = QGraphicsStarItem2(15)
star.setPos(0,0)
left_arrow2 = QGraphicsLeftArrowItem2(50, 30)
left_arrow2.setPos(0,0)
right_arrow2 = QGraphicsRightArrowItem2(50, 30)
right_arrow2.setPos(0,0)
# draw_shape(rect, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\rectangle.svg")
# draw_shape(circle, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\circle.svg")
# draw_shape(round_rect, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\round_rect.svg")
# draw_shape(diamond, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\diamond.svg")
# draw_shape(left_arrow, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\left_arrow.svg")
# draw_shape(right_arrow, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\right_arrow.svg")
# draw_shape(left_tri, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\left_tri.svg")
# draw_shape(right_tri, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\right_tri.svg")
# draw_shape(top_tri, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\top_tri.svg")
# draw_shape(bottom_tri, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\bottom_tri.svg")
# draw_shape(line, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\line.svg")
# draw_shape2(star, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\star.svg", pen_=3)
# draw_shape2(star2, r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\resourses\shape\star2.svg", pen_=2)

draw_shape(left_arrow2, r"D:\ZD\20220405\resourses\shape\left_arrow2.svg")
draw_shape(right_arrow2, r"D:\ZD\20220405\resourses\shape\right_arrow2.svg")

# view = QGraphicsView(scene)
# view.show()
# app.exec_()