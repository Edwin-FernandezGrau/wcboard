# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 21:18:30 2021

@author: DELL
"""

import mediapipe as mp
import numpy as np
import time
import cv2
import streamlit as st
from PIL import ImageColor


st.set_page_config(layout="wide")

st.title("Webcam Board")
st.sidebar.text("Parametros")

numcam= st.sidebar.selectbox("Seleccione la camara",("Camara principal", "Camara Secundaria"))
reverse = st.sidebar.checkbox("Reverse",value = True)
tipo = st.sidebar.selectbox("Seleccione nitides ",("Superposición","Transparencia" ))

st.sidebar.subheader(" Selecciones colores")
color = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 01', '#00B7F9'), "RGB")
color2 = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 02', '#F99500'), "RGB")
color3 = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 03', '#F91200'), "RGB")
color4 = ImageColor.getcolor(st.sidebar.color_picker('Pick A Color 04', '#2BF900'), "RGB")

st.sidebar.write("----")
detcon = st.sidebar.slider('DETECTION CONFIDENCE', 0.5, 0.99, 0.85)
run = st.checkbox("Activar Camara")

if  numcam == "Camara principal":
    cval = 0
else :
    cval = 1
    
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

detector = handDetector(detectionCon=detcon)
ptime = 0
ctime = 0
xp, yp = 0, 0

cam = cv2.VideoCapture(cval) 
FRAME_WINDOW = st.image([])   
FRAME_WINDOW2 = st.sidebar.image([])   
board = np.zeros((480, 640, 3), np.uint8) 

pen_size = 3
color_pen = color
while run:
    # Lectura de imagen from webcam
    ret , frame = cam.read() 
    #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if reverse:
       frame = cv2.flip(frame, 1)
       #imgCanvas1= cv2.flip(board, 1)
    # Lectura de manos
    frame = detector.findHands(frame,draw=False)
    lmList = detector.findPosition(frame)
    
    #configuración para el espacio de colores
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
            
          # solo el indice arriba    - modo escritura
          elif finger[1] == True and finger[2] == False and finger[3] == False and finger[4] == False:
              
              cv2.circle(frame, (x1, y1), 7, (255, 0, 255), cv2.FILLED)
              if xp == 0 and yp == 0: #para la primera linea ni bien detecta el indice
                    xp, yp = x1, y1   
              cv2.line(frame, (xp, yp), (x1, y1), color_pen,pen_size,) #(30, 144, 255)
              cv2.line(board, (xp, yp), (x1, y1),  color_pen, pen_size,) 
              xp, yp = x1, y1 
          else:
              xp, yp = 0, 0
    
    if  tipo == "Superposición":
    
        imgGray = cv2.cvtColor(board, cv2.COLOR_BGR2GRAY) # pasamos a grises
        _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV) # a blanco y negro
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR) # invertimos para que el traso sea negro
        frame = cv2.bitwise_and(frame, imgInv) # pasamos el traso negro con la camara
        frame = cv2.bitwise_or(frame, board) #devolvemos la color original al traso posicionado en la camara          
 
    else :
       
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

    #encabeado con opcion de colores
    #cv2.putText(frame,"SETUP1", (115,18), cv2.FONT_HERSHEY_SIMPLEX, 0.40,color,1)
    #cv2.putText(frame,"SETUP2", (215,15), cv2.FONT_HERSHEY_PLAIN, 0.75,color2,1)
    #cv2.putText(frame,"SETUP3", (315,15), cv2.FONT_HERSHEY_PLAIN, 0.75,color3,1)
    #cv2.putText(frame,"SETUP4", (415,15), cv2.FONT_HERSHEY_PLAIN, 0.75,color4,1)
    cv2.putText(frame,"CLEAR ALL", (535,15), cv2.FONT_HERSHEY_PLAIN, 0.75,(250,250,250),1)
    
    
    
    cv2.rectangle(frame, (ini_an, ini_al)              , (ini_an + an, ini_al+ al)            , color,2)
    cv2.rectangle(frame, (ini_an + an + esp, ini_al)   , (ini_an + an*2 + esp, ini_al+ al)   , color2,2)
    cv2.rectangle(frame, (ini_an + 2*(an+esp), ini_al) , (ini_an + an*3 + esp*2, ini_al+ al) , color3,2)
    cv2.rectangle(frame, (ini_an + 3*(an+esp), ini_al) , (ini_an + an*4 + esp*3, ini_al+ al) , color4,2)
    
    #cv2.rectangle(frame, (600, 100) ,(625, 400) ,(0,0,0),2)
    
    ctime = time.time()
    fps  = 1/(ctime-ptime)
    ptime = ctime
    
    cv2.putText(frame,
                str(int(fps)),
                (620,465),
                cv2.FONT_HERSHEY_PLAIN,
                0.5,
                (250,250,250),
                1
                )
    
    FRAME_WINDOW.image(frame, 
                        #width = 980, #height = 1080,
                        channels="RGB",
                        use_column_width= True ,
                        )
    #FRAME_WINDOW2.image(frame)
    
   



















# import streamlit as st
# import cv2 as cv2

# st.set_page_config(layout="wide")
# st.title("Webcam Board")

# run = st.checkbox("Run")
# vf = cv.VideoCapture(1)

# stframe = st.empty()

# while run:
#     ret, frame = vf.read()
#     # if frame is read correctly ret is True
#     if not ret:
#         break
#     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     stframe.image(frame,use_column_width= True)

























