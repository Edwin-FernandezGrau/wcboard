# -*- coding: utf-8 -*-
"""
Created on Sun Aug 15 20:26:06 2021

@author: DELL
"""
import av
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pydub
import streamlit as st
from aiortc.contrib.media import MediaPlayer
from typing import List, NamedTuple

import mediapipe as mp
import time
from PIL import ImageColor

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal 

from streamlit_webrtc import (
    AudioProcessorBase,
    RTCConfiguration,
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)



############################################

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
               
    def findHands(self,frame,draw=False):
         #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
         self.results = self.hands.process(frame)  
    
         # si encuentra manos
         if self.results.multi_hand_landmarks:
            # por cada mano
            for handLms in self.results.multi_hand_landmarks:
                if draw: # si queremos dibujar
                    self.mpDraw.draw_landmarks(frame,handLms, self.mpHands.HAND_CONNECTIONS)
                
         return frame


    def findPosition(self,frame, handNo=0): #draw = True
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

###############################################################

def app_video_filters():
    """ Video transforms with OpenCV """
    
    class OpenCVVideoProcessor(VideoProcessorBase):
        type: Literal["noop", "cartoon", "edges", "rotate"]

        def __init__(self) -> None:
            self.type = "noop"

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")

            if self.type == "noop":
                pass
            elif self.type == "cartoon":
                detector = handDetector()
                img = cv2.flip(img,1)
                img = detector.findHands(img,draw=True)
            elif self.type == "edges":
                pass
            elif self.type == "rotate":
               pass

            return av.VideoFrame.from_ndarray(img, format="bgr24")

    webrtc_ctx = webrtc_streamer(
        key="object-detection",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=OpenCVVideoProcessor,
        async_processing=True,
    )

    if webrtc_ctx.video_processor:
        webrtc_ctx.video_processor.type = st.radio(
            "Select transform type", ("noop", "cartoon", "edges", "rotate")
        )
        
        
app_video_filters()        
        
        