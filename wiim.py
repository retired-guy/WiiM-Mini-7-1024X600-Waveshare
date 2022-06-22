#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from time import sleep
import requests
import textwrap
import re

import asyncio
import json
import sys
import time
import xmltodict
from datetime import datetime
from typing import Any, Optional, Sequence, Tuple, Union, cast
from random import randrange

from async_upnp_client.advertisement import SsdpAdvertisementListener
from async_upnp_client.aiohttp import AiohttpNotifyServer, AiohttpRequester
from async_upnp_client.client import UpnpDevice, UpnpService, UpnpStateVariable
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.const import NS, AddressTupleVXType, SsdpHeaders
from async_upnp_client.exceptions import UpnpResponseError
from async_upnp_client.profiles.dlna import dlna_handle_notify_last_change
from async_upnp_client.search import async_search as async_ssdp_search
from async_upnp_client.ssdp import SSDP_IP_V4, SSDP_IP_V6, SSDP_PORT, SSDP_ST_ALL
from async_upnp_client.utils import get_local_ip
from async_upnp_client.utils import CaseInsensitiveDict 

from PIL import Image,ImageFont,ImageDraw,ImageEnhance

###### I/O devices may be different on your setup #####
###### can optionally use numpy to write to fb ########
#h, w, c = 320, 480, 4
#fb = np.memmap('/dev/fb0', dtype='uint8',mode='w+',shape=(h,w,c))

fbw, fbh = 1024, 600         # framebuffer dimensions
fb = open("/dev/fb0", "wb") # framebuffer device

#######################################################

fonts = []
fonts.append( ImageFont.truetype('/usr/share/fonts/truetype/oswald/Oswald-Bold.ttf', 30) )
fonts.append( ImageFont.truetype('/usr/share/fonts/truetype/oswald/Oswald-Light.ttf', 30) )
fonts.append( ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 30) )
fonts.append( ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 144) )

## Red and Blue color channels are reversed from normal RGB on pi framebuffer
def swap_redblue(img):
  "Swap red and blue channels in image"
  try:
    r, g, b, a = img.split()
    return Image.merge("RGBA", (b, g, r, a))
  except:
    return img

## Paint image to screen at position
def blit(img, pos):

  size = img.size
  w = size[0]
  h = size[1]
  x = pos[0]
  y = pos[1]

  img = swap_redblue(img)
  try:
    fb.seek(4 * ((pos[1]) * fbw + pos[0]))
  except Exception as e:
    print("seek error: ", e)

  iby = img.tobytes()
  for i in range(h):
    try:
      fb.write(iby[4*i*w:4*(i+1)*w])
      fb.seek(4 * (fbw - w), 1)
    except Exception as e:
      break


## Display date and time when idle
def displaydatetime(large):

  if large:
    sec = datetime.now().second
    if sec not in {0,15,30,45}:
      return 

    dt = datetime.today().strftime('%a, %d %B %Y')
    tm = datetime.today().strftime('%H:%M')
    w = 1024
    h = 600
    color = '#000000'
  else:
    dt = datetime.today().strftime('%a, %d %B %Y   %H:%M')
    w = 474
    h = 50
    color = dcolor

  img = Image.new('RGBA',(w, h),color="black")
  draw = ImageDraw.Draw(img)

  if large:  
    x = randrange(10,600)
    y = randrange(10,300)
 
    draw.text((x,y), tm, tcolor,font=fonts[3])
    draw.text((x+35,y+192), dt,tcolor,font=fonts[2])

    blit(img,(0,0))
  else:
    draw.rounded_rectangle((0,0,w,h),fill=dcolor,radius=7)
    draw.text((10,0), dt, tcolor,font=fonts[1])

    buf = "%s/%s" % (reltime[3:],duration[3:])
    draw.text((320,0), buf, tcolor,font=fonts[1])
    blit(img,(550,550))


def clearscreen():
   img = Image.new('RGBA',size=(1024,600),color=(0,0,0,255))
   blit(img,(0,0))

## Display artist, song title, album title
def displaymeta(data):

  img = Image.new('RGBA',size=(474,500),color='#000000')

  tw1 = textwrap.TextWrapper(width=40)
  tw2 = textwrap.TextWrapper(width=40)
  s = "\n"

  try:
    artist = data['upnp:artist']
  except:
    artist = ""

  try:
    quality = int(data['song:quality'])
  except:
    quality = 0

  try:
    actualQuality = data['song:actualQuality']
    mediatype = "FLAC"
  except:
    actualQuality = ""

  try:
    rate = int(data['song:rate_hz'])/1000.0
  except:
    rate = 0

  try:
    depth = int(data['song:format_s'])
    if actualQuality == "HD":
      depth = 16
    if depth > 24:
      depth = 24
  except:
    depth = 0


  try:
    title = data['dc:title']
  except:
    title = ""

  try:
    album = data['upnp:album']
  except:
    album = ""

  if album == "":
    try:
      album = data['dc:subtitle']
    except:
      pass

  try:
    mediatype = data['upnp:mediatype'].upper()
  except:
    if quality > 1 or len(actualQuality) > 0 :
      mediatype = "FLAC"
    else:
      mediatype = ""

  try:
    res = data['res']['#text']
    index = res.find('bitrate')
    if index > 0:
      bitrate = res[index+8:] + " kbps"
    else:
      try:
        br= int(data['song:bitrate']) / 1000.0
        bitrate = "%d kbps" % br
      except:
        bitrate = ""
  except:
    bitrate = ""

  draw = ImageDraw.Draw(img)
  draw.rounded_rectangle((3,5,469,495), outline=tcolor,width=1,radius=7)

  try:
    artist = s.join(tw2.wrap(artist)[:6])
    draw.text((20,10), artist, tcolor,font=fonts[1])
  except:
    pass

  try:
    album = s.join(tw2.wrap(album)[:6])
    draw.text((20,210), album, tcolor,font=fonts[1])
  except:
    pass

  if rate >0 and depth >0:
    buf = "%.d bits / %.1f kHz  %s" % (depth,rate,bitrate)
    draw.text((20,450), buf, tcolor, font=fonts[1])

  blit(img,(550,50))

  img = Image.new('RGBA',size=(1024,50),color="black")
  draw = ImageDraw.Draw(img)
  draw.rounded_rectangle((0,0,1024,50),fill=dcolor,radius=7)

  try:
    draw.text((10,0),  title[0:60], tcolor,font=fonts[0])
    buf = "%d/%d" % (currentTrack,numTracks)
    if currentTrack >0 and numTracks >0:
      draw.text((920,0),buf,tcolor,font=fonts[0])

    if quality > 0 or len(actualQuality) > 0:
      if quality == 1:
        buf = "HIGH"
      elif quality == 2:
        buf = "HiFi"
      else:
        buf = "Hi-Res"

      if quality==0 and len(actualQuality) > 0:
        buf = actualQuality

      font = fonts[1]

      w,h = font.getsize(buf) 

      draw.rounded_rectangle((800,4,826+w,44),outline=tcolor,width=1,radius=7)
      draw.text((812,2),buf,tcolor,font=font)
  except:
    pass

  blit(img,(0,0))

  displaydatetime(False)

## Get album cover and display
def getcoverart(url):

  try:

    img = Image.new('RGBA',size=(550,550),color="black")

    try:
      img2 = Image.open(requests.get(url, stream=True).raw)

      img2 = img2.resize((545,545))
      img2 = img2.convert('RGBA')

      ##### The Waveshare screen is quite bright, so let's dim the image a bit
      enhancer = ImageEnhance.Brightness(img2)
      img2 = enhancer.enhance(0.4)
      img.paste(img2,(0,5))
    except:
      pass

    blit(img,(0,50))
  except Exception as e:
    print(e)

## Init the screen
clearscreen()

items = {} 
art = ""
currentTrack=0
numTracks=0
dcolor = (69, 31, 12, 255)
tcolor = (100,100,100,255)
pprint_indent = 4

async def create_device(description_url: str) -> UpnpDevice:
    """Create UpnpDevice."""
    timeout = 60
    non_strict = True
    requester = AiohttpRequester(timeout)
    factory = UpnpFactory(requester, non_strict=non_strict)
    return await factory.async_create_device(description_url)


def service_from_device(device: UpnpDevice, service_name: str) -> Optional[UpnpService]:
    """Get UpnpService from UpnpDevice by name or part or abbreviation."""
    for service in device.all_services:
        part = service.service_id.split(":")[-1]
        abbr = "".join([c for c in part if c.isupper()])
        if service_name in (service.service_type, part, abbr):
            return service

    return None

async def pollingloop(description_url: str, service_names: Any) -> None:
    """Subscribe to service(s) and output updates."""
    global reltime,duration,numTracks,currentTrack

    device = await create_device(description_url)

    # start notify server/event handler
    source = (get_local_ip(device.device_url), 0)
    server = AiohttpNotifyServer(device.requester, source=source)
    await server.async_start_server()

    # gather all wanted services
    if "*" in service_names:
        service_names = device.services.keys()

    services = []

    for service_name in service_names:
        service = service_from_device(device, service_name)
        if not service:
            print(f"Unknown service: {service_name}")
            sys.exit(1)
        services.append(service)

    stop_invoked = False
    newTrack = True
    stop_action = services[0].action("Stop")
    info_action = services[0].action("GetTransportInfo")
    media_action = services[0].action("GetMediaInfo")
    position_action = service.action("GetPositionInfo")

    ##### Polling loop
    while True:
  
          ##### Get the current transport state 
          result = await info_action.async_call(InstanceID=0,Channel="Master")
          state = result["CurrentTransportState"]
          if state in ["STOPPED","PAUSED","PAUSED_PLAYBACK","TRANSITIONING","NO_MEDIA_PRESENT"]:
            playing = False
            newTrack = True
          else:
            playing = True


          if playing == False:
            #### Make sure we're really stopped
            #if state in ["PAUSED","PAUSED_PLAYBACK"]:
              #### Wiim Mini won't turn off optical output LED with Pause, so send hard Stop
              ####   to turn it off so that RME DAC will switch to USB input
              #result = await stop_action.async_call(InstanceID=0,Channel="Master")

            displaydatetime(True)
          else:
 
            #### Get the position of current track
            result = await position_action.async_call(InstanceID=0,Channel="Master")
            reltime = result["RelTime"]
            duration = result["TrackDuration"]
            currentTrack = result["Track"]

            h, m, s = reltime.split(':')
            if int(h)+int(m)+int(s) < 2:
              newTrack = True
              #### Get the track count in current queue
              res = await media_action.async_call(InstanceID=0,Channel="Master")
              numTracks = res["NrTracks"]

            displaydatetime(False)

            try:
              meta = result["TrackMetaData"]

              ### Convert the grubby XML to JSON, because XML stinks!
              ### First fix incorrect & in XML
              xml = meta.replace("& ","&#38; ")
              items = xmltodict.parse(xml)["DIDL-Lite"]["item"]

              if newTrack == True or numTracks == 0:
                #print(json.dumps(items,indent=4))
                newTrack = False
                try:
                  displaymeta(items)
                except:
                  pass

                try:
                  arttmp = items["upnp:albumArtURI"]
                  if isinstance(arttmp, dict):
                    art = art["#text"]
                  else:
                    art = arttmp

                  getcoverart(art)

                except:
                  pass

            except Exception as e:
              print("Error:", e)

          await asyncio.sleep(1)


async def search() -> None:
    """Discover WiiM device"""

    global wiim_description_url

    timeout = 5
    ### Search for service type unique to WiiM  
    service_type = "urn:schemas-wiimu-com:service:PlayQueue:1" 
    wiim_description_url = ""

    source, target = (
            "0.0.0.0",
            0,
        ), (SSDP_IP_V4, SSDP_PORT)


    async def on_response(headers: CaseInsensitiveDict) -> None:
        global wiim_description_url
        for key, value in headers.items():
          if key == "LOCATION":
            wiim_description_url = value
            break

    await async_ssdp_search(
        service_type=service_type,
        source=source,
        target=target,
        timeout=timeout,
        async_callback=on_response,
    )

    return(wiim_description_url)

async def async_main() -> None:
    """Async main."""

    service = ["AVTransport"]

    ### SSDP search for the WiiM 
    wiim_description_url = await search()
    print(wiim_description_url)

    if wiim_description_url == "":
      print("Can't find WiiM Mini!")
      sys.exit(1)

    await pollingloop(wiim_description_url, service)

def main() -> None:
    """Set up async loop and run the main program."""
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(async_main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()

