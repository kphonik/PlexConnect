#!/usr/bin/env python

import re
import sys
import io
import urllib
import urllib2
import urlparse
import posixpath
import math
import ntpath



import ConfigParser

import os.path
import unicodedata
from Debug import *

try:
    from PIL import Image, ImageFilter, ImageFont, ImageDraw
    __isPILinstalled = True
except ImportError:
    dprint(__name__, 0, "No PIL/Pillow installation found.")
    __isPILinstalled = False
    
from Version import __VERSION__  # for {{EVAL()}}, display in settings page
import Settings, ATVSettings
import PlexAPI

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageFilter

class ImageBackground():
    options = {\
        'template' : 'Plex',\
        'title' : '',\
        'subtitle' : '',\
        'image' : 'blank.jpg',\
        'resolution' : '1080',\
        'font' : 'fonts/OpenSans/OpenSans-Light.ttf',\
        'titleSize' : '45',\
        'subtitleSize' : '35',\
        'titleColor' : 'ffffff',\
        'subtitleColor' : 'ffffff',\
        'anchorX' : 'right',\
        'anchorY' : 'top',\
        'offsetX' : '50',\
        'offsetY' : '20',\
        'lineheight' : '180',\
        'imageBlur' : None,\
        'layers' : []\
    }
    
    cfg = {}
    
    
    def __init__(self,opts):
        for opt in self.options:
            self.cfg[opt] = self.options[opt]
        if opts != None:
         for opt in opts:
            if self.cfg[opt] != opts[opt]:
                self.cfg[opt] = opts[opt]

                          
    def setOptions(self,opts):
        for opt in opts:
            if self.cfg[opt] != opts[opt]:
                self.cfg[opt] = opts[opt]
                
    def getRendersize(self, res):
        if str(res)=="poster":
            renderwidth = 512
            renderheight = 768
        elif str(res)=="16X9":
            renderwidth = 768
            renderheight = 432
        elif str(res)=="flow":
            renderwidth = 768
            renderheight= 256
        elif str(res)=="square":
            renderwidth = 768
            renderheight = 768
        else:
            renderwidth = 1280
            renderheight = 720
        return renderwidth, renderheight
        
    def fullHDtext(self,number):
        number = int(number)*1080/720
        return number
    
    def createFileHandle(self):
        cachefileStyle = normalizeString(self.cfg['template'])
        cachefileTitle = normalizeString(self.cfg['title'])
        cachefileSubtitle = normalizeString(self.cfg['subtitle'])
        cachefileRes = normalizeString(self.cfg['resolution'])
        
        sourcefile = remove_junk(str(self.cfg['image']))
        sourcefile = remove_junk(str(sourcefile))

        
        t1s = normalizeString(self.cfg['titleSize'])
        t1c = normalizeString(self.cfg['titleColor'])
        tax = normalizeString(self.cfg['anchorX'])
        tay = normalizeString(self.cfg['anchorY'])
        tox = normalizeString(self.cfg['offsetX'])
        toy = normalizeString(self.cfg['offsetY'])
        t2s = normalizeString(self.cfg['subtitleSize'])
        t2c = normalizeString(self.cfg['subtitleColor'])
        lh = normalizeString(self.cfg['lineheight'])
        ib = normalizeString(self.cfg['imageBlur'])
        
        # add layers
        layerrange = range(0, len(self.cfg['layers']))
        cachefileLayers = ""
        for layercounter in layerrange:
            if self.cfg['layers'][layercounter] != None:
                cachefileLayers = cachefileLayers+"+"+normalizeString(self.cfg['layers'][layercounter])
                
        # fix for extra long subtitles
        if len(cachefileSubtitle) > 30:
            cachefileSubtitle = cachefileSubtitle[0:30]
        cachefile = cachefileStyle+cachefileLayers+"+"+sourcefile+"+"+cachefileTitle+"+"+t1s+"+"+t1c+"+"+tax+"+"+tay+"+"+tox+"+"+toy+"+"+cachefileSubtitle+"+"+t2s+"+"+t2c+"+"+lh+"+"+ib+"+"+cachefileRes
        
        return cachefile


    def resizedMerge (self,background, stylepath):
        isatv2=0

        renderwidth, renderheight = self.getRendersize(self.cfg['resolution'])
        if str(renderheight) == "720":
            height = int(self.cfg['resolution'])
            if height == 720:
                isatv2 = 1
                width = 1920
                height = 1080
            elif height == 1080:
                width = 1920
        else:
            width = renderwidth
            height = renderheight
            
        im = Image.new("RGB", (width, height), "black")
        background = background.resize((width, height), Image.ANTIALIAS)
    
        # Blur BG
        if self.cfg['imageBlur'] != None and self.cfg['imageBlur'] != "" and self.cfg['imageBlur'] > 0:
            for i in range(0,int(self.cfg['imageBlur'])):
                background = background.filter(ImageFilter.BLUR)
        im.paste(background, (0, 0), 0)
        # Layers
        layerrange = range(0, len(self.cfg['layers']))
        for layercounter in layerrange:
            if self.cfg['layers'][layercounter] != None:
                layer = Image.open(stylepath+"/images/"+self.cfg['layers'][layercounter]+".png")
                layer = layer.resize((width, height), Image.ANTIALIAS)
                im.paste(layer, ( 0, 0),layer)
    
        if isatv2>0:
            im = im.resize((1280, 720), Image.ANTIALIAS)
        return im

    def textToImage(self, im, stylepath, index):
        if index == 1:
            if self.cfg['titleSize'] != None and self.cfg['titleSize'] != "":
                fontsize = int(self.cfg['titleSize'])
            else:
                fontsize = int(params[4]) / 24
            
            if self.cfg['titleColor'] != None and self.cfg['titleColor'] != "":
                if is_hex(str(self.cfg['titleColor'])):
                    textcolor = self.cfg['titleColor']
                    textcolor = tuple(int(textcolor[i:i+len(textcolor)/3], 16) for i in range(0, len(textcolor), len(textcolor)/3))
                else:
                    textcolor = self.cfg['titleColor']
            else: # Default Color
                textcolor = (255, 255, 255)
            
            text = unicode(urllib.unquote(self.cfg['title']), 'utf-8').replace('+',' ').strip()
                                
        elif index == 2:
            if self.cfg['subtitleSize'] != None and self.cfg['subtitleSize'] != "":
                fontsize = int(self.cfg['subtitleSize'])
            else:
                fontsize = int(params[4]) / 36
                
            if self.cfg['subtitleColor'] != None and self.cfg['subtitleColor'] != "":
                if is_hex(str(self.cfg['subtitleColor'])):
                    textcolor = self.cfg['subtitleColor']
                    textcolor = tuple(int(textcolor[i:i+len(textcolor)/3], 16) for i in range(0, len(textcolor), len(textcolor)/3))
                else:
                    textcolor = self.cfg['subtitleColor']
            else: # Default Color
                textcolor = (255, 255, 255)
                
            text = unicode(urllib.unquote(self.cfg['subtitle']), 'utf-8').replace('+',' ').strip()
                
        # TypeSpace
        draw = ImageDraw.Draw(im)
        font = stylepath+"/"+self.cfg['font']
        width, height = draw.textsize(text, ImageFont.truetype(font, int(fontsize)))
        renderwidth, renderheight = self.getRendersize(self.cfg['resolution'])

        # Anchor and Offset X
        if (self.cfg['anchorX'] != None and self.cfg['anchorX'] != "" ) or (self.cfg['offsetX'] != None and self.cfg['offsetX'] != ""):
            if self.cfg['anchorX'] == "right":
                offsetx = renderwidth - width - int(self.cfg['offsetX'])
            elif self.cfg['anchorX'] == "center":
                offsetx = (renderwidth - width) / 2
            elif self.cfg['anchorX'] == "left":
                offsetx = int(self.cfg['offsetX'])
            else:
                offsetx = 80
        else:
            offsetx = 80
        # Anchor and Offset Y
        if ( self.cfg['anchorY'] != None and self.cfg['anchorY'] != "" ) or ( self.cfg['offsetY'] != None and self.cfg['offsetY'] != "" ):
            if self.cfg['anchorY'] == "bottom":
                offsety = renderheight - int(self.cfg['offsetY'])
            elif self.cfg['anchorY'] == "middle":
                offsety = ( renderheight - height ) / 2
            elif self.cfg['anchorY'] == "top" or self.cfg['anchorY'] == "":
                offsety = int(self.cfg['offsetY'])
            else:
                offsety = 80
            # Subtitle
            
            if index > 1 and ( self.cfg['title'] != None and self.cfg['title'] != "" ):
                if self.cfg['titleSize'] != None or self.cfg['titleSize'] != "":
                    titlefontsize = int(self.cfg['titleSize'])
                else: # Default Size
                    titlefontsize = int(self.cfg['resolution']) / 24
                if self.cfg['lineheight'] != None and self.cfg['lineheight'] != "":
                    offsety = offsety + (titlefontsize * int(self.cfg['lineheight']) / 100)
                else:
                    offsety = offsety + (titlefontsize * 130 / 100)
        else:
            offsety = 80
        # Handle 1080 / atv3 Text
        if self.cfg['resolution'] == "1080":
            fontsize = self.fullHDtext(fontsize)
            offsetx = self.fullHDtext(offsetx)
            offsety = self.fullHDtext(offsety)
        # Write    
        draw.text((int(offsetx), int(offsety)), text , font=ImageFont.truetype(font, int(fontsize)), fill=textcolor)
        return im

    def generate(self):
    
    # Catch the Params
        cachepath = sys.path[0]+"/assets/fanartcache"
        stylepath = sys.path[0]+"/assets/thumbnails/"+self.cfg['template']
        cachefile = self.createFileHandle()
        
        dprint(__name__, 1, 'Check for Cachefile.')  # Debug
        # Already created?
        if os.path.isfile(cachepath+"/"+cachefile+".png"):
            dprint(__name__, 1, 'Cachefile  found.')  # Debug
            return cachefile+".png" # Bye Bye
        # No it's not
        else:
            dprint(__name__, 1, 'No Cachefile found. Generating Background.')  # Debug
            # Setup Background
            url = urllib.unquote(self.cfg['image'])
            if os.path.isfile(stylepath+"/images/"+url):
                dprint(__name__, 1, 'Fetching Template Image.'  )  # Debug
                background = Image.open(stylepath+"/images/"+url)
            elif url[0][0] != "/":
                try:
                    bgfile = urllib2.urlopen(url)
                except urllib2.URLError, e:
                    dprint(__name__, 1, 'error: {0}', str(e.code)+" "+e.msg+" // url:"+ url )  # Debug
                    background = Image.open(stylepath+"/images/blank.jpg")
                else:
                    dprint(__name__, 1, 'Fetting Remote Image.')  # Debug
                    output = open(cachepath+"/tmp.png",'wb')
                    output.write(bgfile.read())
                    output.close()
                    background = Image.open(cachepath+"/tmp.png")
                
            # Set Resolution and Merge Layers
            #if params[4] == "720":
            dprint(__name__, 1, 'Merging Layers.')  # Debug
            im = self.resizedMerge(background, stylepath)
            #else: # 1080
            # im = resizedMerge(background, params, fanartpath)
            # Setup Title Type Space
            dprint(__name__, 1, 'Add Text.')  # Debug
            if self.cfg['title'] != None and self.cfg['title'] != "":
                im = self.textToImage (im, stylepath, 1)
            # Setup Subtitle Type Space
            if self.cfg['subtitle'] != None and self.cfg['subtitle'] != "":
                im = self.textToImage (im, stylepath, 2)
            # Save to Cache
            im.save(cachepath+"/"+cachefile+".png")  
            dprint(__name__, 1, 'Cachefile  generated.')  # Debug
            return cachefile+".png"


def generate(PMS_uuid, url, authtoken, resolution, blurRadius, gradientTemplate, titleText, subtitleText, titleSize, subtitleSize, textColor, align, valign, offsetx, offsety, lineheight, blurStart, blurEnd, statusText):
    cachepath = sys.path[0]+"/assets/fanartcache"
    stylepath = sys.path[0]+"/assets/thumbnails/Plex"

    # Create cache filename
    id = re.search('/library/metadata/(?P<ratingKey>\S+)/art/(?P<fileId>\S+)', url)
    if id:
        # assumes URL in format "/library/metadata/<ratingKey>/art/fileId>"
        id = id.groupdict()
        cachefile = urllib.quote_plus(PMS_uuid +"_"+ id['ratingKey'] +"_"+ id['fileId'] +"_"+ resolution +"_"+ blurRadius) + titleText + subtitleText + gradientTemplate + ".png"
    else:
        fileid = posixpath.basename(urlparse.urlparse(url).path)
        cachefile = urllib.quote_plus(PMS_uuid +"_"+ fileid +"_"+ resolution +"_"+ blurRadius) + titleText + subtitleText + gradientTemplate + ".png"  # quote: just to make sure...
    
    # Already created?
    dprint(__name__, 1, 'Check for Cachefile.')  # Debug
    if os.path.isfile(cachepath+"/"+cachefile):
        dprint(__name__, 1, 'Cachefile  found.')  # Debug
        return "/fanartcache/"+cachefile
    
    # No! Request Background from PMS
    dprint(__name__, 1, 'No Cachefile found. Generating Background.')  # Debug
    try:
        dprint(__name__, 1, 'Getting Remote Image.')  # Debug
        xargs = {}
        if authtoken:
            xargs['X-Plex-Token'] = authtoken
        request = urllib2.Request(url, None, xargs)
        response = urllib2.urlopen(request).read()
        background = Image.open(io.BytesIO(response))
    except urllib2.URLError as e:
        dprint(__name__, 0, 'URLError: {0} // url: {1}', e.reason, url)
        return "/thumbnails/Plex/images/Background_blank_" + resolution + ".jpg"
    except urllib2.HTTPError as e:
        dprint(__name__, 0, 'HTTPError: {0} {1} // url: {2}', str(e.code), e.msg, url)
        return "/thumbnails/Plex/images/Background_blank_" + resolution + ".jpg"
    except IOError as e:
        dprint(__name__, 0, 'IOError: {0} // url: {1}', str(e), url)
        return "/thumbnails/Plex/images/Background_blank_" + resolution + ".jpg"
    
    blurRadius = int(blurRadius)
    
    # Get gradient template
    dprint(__name__, 1, 'Merging Layers.')  # Debug
    if resolution == '1080':
        width = 1920
        height = 1080
        blurStart = (1080/100) * int(blurStart)
        blurEnd = (1080/100) * int(blurEnd)
        blurRegion = (0, blurStart, 1920, blurEnd)
        # FT: get Background based on last Parameter
        layer = Image.open(stylepath + "/images/" + gradientTemplate + "_1080.png")
    else:
        width = 1280
        height = 720
        blurStart = (720/100) * int(blurStart)
        blurEnd = (720/100) * int(blurEnd)
        blurRegion = (0, blurStart, 1280, blurEnd)
        blurRadius = int(blurRadius / 1.5)
        layer = Image.open(stylepath + "/images/" + gradientTemplate + "_720.png")
    
    # Set background resolution and merge layers
    try:
        bgWidth, bgHeight = background.size
        dprint(__name__,1 ,"Background size: {0}, {1}", bgWidth, bgHeight)
        dprint(__name__,1 , "aTV Height: {0}, {1}", width, height)
    
        if bgHeight != height:
            background = background.resize((width, height), Image.ANTIALIAS)
            dprint(__name__,1 , "Resizing background")
        
        if blurRadius != 0:
            dprint(__name__,1 , "Blurring Lower Region")
            imgBlur = background.crop(blurRegion)
            imgBlur = imgBlur.filter(ImageFilter.GaussianBlur(blurRadius))
            background.paste(imgBlur, blurRegion)

        background.paste(layer, ( 0, 0), layer)

    except:
        dprint(__name__, 0, 'Error - Failed to modify image')
        return "/thumbnails/Plex/images/Background_blank_" + resolution + ".jpg"

    background = textToImage(stylepath, background, resolution, titleText, titleSize, textColor, align, valign, offsetx, offsety)

    if subtitleText != "":
        offsety = int(offsety) + int(lineheight)
        background = textToImage(stylepath, background, resolution, subtitleText, subtitleSize, textColor, align, valign, offsetx, offsety)

    # Handle 1080 / atv3 Text
    
    statusSize = 30
    statusX = 35
    statusY = 15

    if resolution == '1080':
        statusSize = fullHDtext(statusSize)
        statusX = fullHDtext(statusX)
        statusY = fullHDtext(statusY)
    
    if statusText != "":
            background = textToImage(stylepath, background, resolution, statusText, statusSize, textColor, "right", "top", statusX, statusY)


    try:
        # Save to Cache
        background.save(cachepath+"/"+cachefile)
    except:
        dprint(__name__, 0, 'Error - Failed to save image file')
        return "/thumbnails/Background_blank_" + resolution + ".jpg"
    
    dprint(__name__, 1, 'Cachefile  generated.')  # Debug
    return "/fanartcache/"+cachefile




# HELPERS

def isPILinstalled():
    return __isPILinstalled

def purgeFanart():
    folder = sys.path[0]+"/assets/fanartcache"
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e



def normalizeString(text):
    text = urllib.unquote(str(text)).replace(' ','+')
    text = unicodedata.normalize('NFKD',unicode(text,"utf8")).encode("ascii","ignore")  # Only ASCII CHARS
    text = re.sub(r'\W+', '+', text) # No Special Chars  
    return text


def textToImage(stylepath, im, resolution, textToWrite, fontsize, color, align, valign, offsetX, offsetY):
    # Set Font
    font = stylepath + "/fonts/font.ttf"

    # Set Color From Hex Value
    if is_hex(color):
        textcolor = color
        textcolor = tuple(int(textcolor[i:i+len(textcolor)/3], 16) for i in range(0, len(textcolor), len(textcolor)/3))
    
    else: # Default Color
        textcolor = (255, 255, 255)

    # Handle 1080 / atv3 Text

    if resolution == '1080':
        layerWidth = 1920
        layerHeight = 1080
        fontsize = fullHDtext(fontsize)
        offsetX = fullHDtext(offsetX)
        offsetY = fullHDtext(offsetY)
    else:
        layerWidth = 1280
        layerHeight = 720
        fontsize = int(fontsize)
        offsetX = int(offsetX)
        offsetY = int(offsetY)

    # Text & TypeSpace
    text = unicode(urllib.unquote(textToWrite), 'utf-8').replace('+',' ').strip()
    draw = ImageDraw.Draw(im)
    width, height = draw.textsize(text, ImageFont.truetype(font, fontsize))


    # Anchor and Offset X
    if align == "right":
        offsetx = layerWidth - width - offsetX
    elif align == "center":
        offsetx = (layerWidth - width ) / 2
    elif align == "left":
        offsetx = int(offsetX)

    # Anchor and Offset Y
    if valign == "bottom":
        offsety = layerHeight - offsetY
    elif valign == "middle":
        offsety = (layerHeight - height ) / 2
    elif valign == "top":
        offsety = int(offsetY)



    # Write
    dprint(__name__,1 ,"Text: {0} size: {1} offsetX: {2} offsetY: {3} font: {4} color: {5}", text, fontsize,offsetx,offsety, font, textcolor)

    draw.text((int(offsetx), int(offsety)), text , font=ImageFont.truetype(font, fontsize), fill=textcolor)
    return im



def fullHDtext(number):
    number = int(number)*1080/720
    return number

def is_hex(s):
    hex_digits = set("0123456789abcdefABCDEF")
    for char in s:
        if not (char in hex_digits):
            return False
    return True

    
def fullHDtext(number):
    number = int(number)*1080/720
    return number

def is_hex(s):
    hex_digits = set("0123456789abcdefABCDEF")
    for char in s:
        if not (char in hex_digits):
            return False
    return True
    
def remove_junk(url):
    temp = urllib.unquote(str(url))
    temp = temp.split('/')[-1]
    temp = temp.split('?')[0]
    temp = temp.split('&')[0]
    return temp
    




if __name__=="__main__":
    url = "http://thetvdb.com/banners/fanart/original/95451-23.jpg"
    res = generate('uuid', url, 'authtoken', '1080')
    res = generate('uuid', url, 'authtoken', '720')
    dprint(__name__, 0, "Background: {0}", res)
