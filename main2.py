# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 15:36:03 2021

@author: DELL
"""
import mediapipe as mp
import numpy as np
import time
import cv2
import streamlit as st
from PIL import ImageColor
import cv2
import av
import logging
import queue

from streamlit_webrtc import (
    AudioProcessorBase,
    RTCConfiguration,
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

st.set_page_config(layout="wide")

st.title("Webcam Board")
st.sidebar.text("Parametros")
st.sidebar.subheader(" Selecciones colores")
color = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 01', '#00B7F9'), "RGB")
color2 = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 02', '#F99500'), "RGB")
color3 = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 03', '#F91200'), "RGB")
color4 = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 04', '#2BF900'), "RGB")

st.sidebar.write("----")

logger = logging.getLogger(__name__)

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.80, trackCon=0.5 ):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands( self.mode,self.maxHands,self.detectionCon,self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4,8,12,16,20]
               
    def findHands(self,frame,draw=True):
         #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
         self.results = self.hands.process(frame)  
    
         # si encuentra manos
         if self.results.multi_hand_landmarks:
            # por cada mano
            for handLms in self.results.multi_hand_landmarks:
                if draw: # si queremos dibujar
                    self.mpDraw.draw_landmarks(frame,handLms, self.mpHands.HAND_CONNECTIONS)
                
         return frame


    def findPosition(self,frame, handNo=0,draw = True): #draw = True
        self.lmList = []
        if self.results.multi_hand_landmarks:
           myHand = self.results.multi_hand_landmarks[handNo]
       
           for id, lm in enumerate(myHand.landmark):
               h,w,c = frame.shape
               cx ,cy = int(lm.x*w),int(lm.y*h)
               self.lmList.append([id,cx,cy])
               
        return self.lmList

    
    def fingersUp(self):
        fingers = []
        
        # Thumb
        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 fingers
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers




def app_sendonly_video():
    """A sample to use WebRTC in sendonly mode to transfer frames
    from the browser to the server and to render frames via `st.image`."""
    webrtc_ctx = webrtc_streamer(
        key="video-sendonly",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True},
    )

    image_place = st.empty()
    detector = handDetector(detectionCon=0.85)
    #detector = handDetector(detectionCon=detcon)
    ptime = 0
    ctime = 0
    xp, yp = 0, 0
    board = np.zeros((480, 640, 3), np.uint8)
    pen_size = 3
    #color,color2,color3,color4 = (250,250, 250),(250,250, 250),(250,250, 250),(250,250, 250)
    color_pen = color
    while True:
        if webrtc_ctx.video_receiver:
            try:
                video_frame = webrtc_ctx.video_receiver.get_frame()
            except queue.Empty:
                logger.warning("Queue is empty. Abort.")
                break

            img_rgb = video_frame.to_ndarray(format="rgb24")
            img_rgb = cv2.flip(img_rgb,1)
            frame = detector.findHands(img_rgb,draw=True)
            lmList = detector.findPosition(frame)
            al,an, esp = 20,75,30
            ini_an, ini_al = 80,5
            
            if len(lmList) != 0: # si algun dedo arriba
                  x1, y1 = lmList[8][1:]
                  x2, y2 = lmList[12][1:]
                  finger = detector.fingersUp()
            
                # si la mano abierta - modo borrado
                  if finger[0]  and finger[1] and finger[2] and finger[3] and finger[4] :
                      if xp == 0 and yp == 0:
                          xp, yp = x1, y1
                      cv2.line(board, (xp, yp), (x1, y1), (0, 0, 0), 55)
                      cv2.circle(frame, (x1, y1),20, (250,250, 250), cv2.FILLED)
                      xp, yp = 0, 0
                     
                  #si dos dedos arriba  - modo no escrituaa
                  elif finger[1] and finger[2]  and finger[0] and finger[3] == False and finger[4] == False:     
                    xp, yp = 0, 0
                    cv2.rectangle(frame, (x2-5, y2-5),(x2+5, y2+5), (255, 0, 255), cv2.FILLED)
                    
                    #seleccion de colores disponibles 
                    if y2 <= ini_al + al :
                        if  ini_an < x2 < ini_an + an :
                            cv2.rectangle(frame, (ini_an, ini_al) , (ini_an + an, ini_al+ al) , color, cv2.FILLED)
                            color_pen = color
                            
                        elif  ini_an + an + esp < x2 < ini_an + 2*an + esp :
                            cv2.rectangle(frame, (ini_an + an + esp, ini_al) , (ini_an + an*2 + esp, ini_al+ al) , color2,cv2.FILLED)
                            color_pen = color2
                            
                        elif  ini_an + 2*(an+esp) < x2 < ini_an + 3*an + 2*esp :
                            cv2.rectangle(frame, (ini_an + 2*(an+esp), ini_al) , (ini_an + an*3 + esp*2, ini_al+ al) , color3,cv2.FILLED)
                            color_pen = color3
                        
                        elif  ini_an + 3*(an+esp) < x2 < ini_an + 4*an + 3*esp :
                            cv2.rectangle(frame, (ini_an + 3*(an+esp), ini_al) , (ini_an + an*4 + esp*3, ini_al+ al) , color4,cv2.FILLED)
                            color_pen = color4     
                                   
                    xp, yp = 0, 0    
                    
                  elif finger[1] == True and finger[2] == False and finger[3] == False and finger[4] == False:
                  
                      cv2.circle(frame, (x1, y1), 7, (255, 0, 255), cv2.FILLED)
                      if xp == 0 and yp == 0: #para la primera linea ni bien detecta el indice
                            xp, yp = x1, y1   
                      cv2.line(frame, (xp, yp), (x1, y1), color_pen,pen_size,) #(30, 144, 255)
                      cv2.line(board, (xp, yp), (x1, y1),  color_pen, pen_size,) 
                      xp, yp = x1, y1 
                  else:
                     xp, yp = 0, 0
                     
            frame = cv2.addWeighted(frame, 0.5, board, 0.6, 0) 
            cv2.putText(frame,"BLID",
                (600,465),cv2.FONT_HERSHEY_PLAIN,
                0.5, (250,250,250), 1)
    
            cv2.putText(frame,
                        "SETUP",
                        (5,15),
                        cv2.FONT_HERSHEY_PLAIN,
                        0.75,
                        (250,250,250),
                        1
                        )
            
            cv2.putText(frame,"CLEAR ALL", (535,15), cv2.FONT_HERSHEY_PLAIN, 0.75,(250,250,250),1)
            cv2.rectangle(frame, (ini_an, ini_al)              , (ini_an + an, ini_al+ al)            , color,2)
            cv2.rectangle(frame, (ini_an + an + esp, ini_al)   , (ini_an + an*2 + esp, ini_al+ al)   , color2,2)
            cv2.rectangle(frame, (ini_an + 2*(an+esp), ini_al) , (ini_an + an*3 + esp*2, ini_al+ al) , color3,2)
            cv2.rectangle(frame, (ini_an + 3*(an+esp), ini_al) , (ini_an + an*4 + esp*3, ini_al+ al) , color4,2)
            
            image_place.image(frame, use_column_width= True )
        else:
            logger.warning("AudioReciver is not set. Abort.")
            break

app_sendonly_video()