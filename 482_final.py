# -*- coding: utf-8 -*-
"""482 Final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1a6dPY4_NXxVJAA4eePDiEmpCSCK_z8lg
"""

from psutil import virtual_memory
ram_gb = virtual_memory().total / 1e9
print('Your runtime has {:.1f} gigabytes of available RAM\n'.format(ram_gb))

if ram_gb < 20:
  print('To enable a high-RAM runtime, select the Runtime > "Change runtime type"')
  print('menu, and then select High-RAM in the Runtime shape dropdown. Then, ')
  print('re-execute this cell.')
else:
  print('You are using a high-RAM runtime!')

import numpy as np
import cv2 
import matplotlib.pyplot as plt
import math
import datetime as dt
from scipy.signal import convolve2d

# from google.colab.patches import cv2_imshow
# google=True

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
# face_cascade = cv2.CascadeClassifier('haarcascade_fullbody.xml')

def detect_face(img):
    new_img = img.copy()

    face_rects = face_cascade.detectMultiScale(img, minNeighbors=5, minSize=(30,30))
      
    for (x,y,w,h) in face_rects:
      cv2.rectangle(new_img, (x,y), (x+w, y+h), (255,255,255), 10)


    return new_img, face_rects

def meanShift(dst, track_windows, check, interval):#, term_crit
  new_windows = []

  for (x1,y1,x2,y2) in track_windows:
    highest = (np.sum(dst[y1:y2, x1:x2]), (x1,y1,x2,y2))
    # print(f'first: {highest[0]}')
    #x1,x2,y1,y2
    borders = [(check,check,0,0),
              (-check,-check,0,0),
              (0,0,check,check),
              (0,0,-check,-check),
              (check,check,check,check),
              (-check,-check,-check,-check),
              (check,check,-check,-check),
              (-check,-check,check,check)]
    
    intervals = check//interval
    for border in borders:
      for i in range(1, (intervals)+1):
        x_1 = x1+(border[0]//intervals)*i
        x_2 = x2+(border[1]//intervals)*i
        y_1 = y1+(border[2]//intervals)*i
        y_2 = y2+(border[3]//intervals)*i

        if x_1 > dst.shape[1] or x_1 < 0:
          continue
        if x_2 > dst.shape[1] or x_2 < 0:
          continue
        if y_1 > dst.shape[1] or y_1 < 0:
          continue
        if y_2 > dst.shape[0] or y_2 < 0:
          continue

        
        clus = np.sum(dst[y_1:y_2, x_1:x_2])
        # print(f'coor: {(x_1,y_1,x_2,y_2)}')
        # print(f'new clus: {clus}')
        if clus > highest[0]:
          highest = (clus, (x_1,y_1,x_2,y_2))
      
    new_windows.append(highest[1])

  return new_windows

def MS(video, save=True):
  frames = []
  cap = cv2.VideoCapture(f'{video}.mp4')
  ret,frame = cap.read()
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fps =  int(cap.get(cv2.CAP_PROP_FPS))
  frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

  #How many seconds until detecting if face still there
  sec = 1
  t = dt.datetime.now()

  frame, faces = detect_face(frame)

  roi = frame[0:frame.shape[0], 0:frame.shape[1]]
  hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
  roi_hist = cv2.calcHist([hsv_roi],[0],None, [180], [0,180])
  cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

  track_windows = []
  for (x,y,w,h) in faces:
    track_windows.append((int(x),int(y),int(x+w),int(y+h)))
    roi = frame[y:y+h, x:x+w]
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    roi_hist = cv2.calcHist([hsv_roi],[0],None, [180], [0,180])
    cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
  



  while True: 

    if (dt.datetime.now() -t).seconds / 10 >= 1:
      t = dt.datetime.now()
      percent = ((cap.get(cv2.CAP_PROP_POS_FRAMES)/frame_count)*100)
      print(f'\rProcessing Video - {percent :.2f}%', end='', flush=True)

    ret,frame = cap.read()

    if ret == True:
      hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
      dst = cv2.calcBackProject([hsv], [0], roi_hist, [0,180], 1)
      
      #MeanShift
      track_windows = meanShift(dst, track_windows, 30, 1)#, term_crit
      for (x1,y1,x2,y2) in track_windows:
        frame = cv2.rectangle(frame, (x1,y1), (x2, y2), (0,0,255), 5)

      # cv2_imshow(frame)
      frames.append(frame)


      if int(cap.get(cv2.CAP_PROP_POS_FRAMES))%(fps*sec) == 0 or  track_windows==[]:
        frame, faces = detect_face(frame)

        # roi = frame[0:frame.shape[0], 0:frame.shape[1]]
        # hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # roi_hist = cv2.calcHist([hsv_roi],[0],None, [180], [0,180])
        # cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

        track_windows = []
        for (x,y,w,h) in faces:
          track_windows.append((int(x),int(y),int(x+w),int(y+h)))
          roi = frame[y:y+h, x:x+w]
          hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
          roi_hist = cv2.calcHist([hsv_roi],[0],None, [180], [0,180])
          cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
    else:
      break

  if save == True:
    video = cv2.VideoWriter(f'processed/{video}-{sec}-MS.mp4', cv2.VideoWriter_fourcc(*'MP4V'), fps, (width,height))
    for frame in frames:
      video.write(frame)

    video.release()
  cap.release()
  cv2.destroyAllWindows()
  print(f'\rProcessing Video - 100%', end='', flush=True)

def Lucas_Kanade(frame1, frame2,  track_windows):
    img1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    Gx = np.reshape(np.asarray([[-1, 1], [-1, 1]]), (2, 2))  # for image 1 and image 2 in x direction
    Gy = np.reshape(np.asarray([[-1, -1], [1, 1]]), (2, 2))  # for image 1 and image 2 in y direction
    Gt1 = np.reshape(np.asarray([[-1, -1], [-1, -1]]), (2, 2))  # for 1st image
    Gt2 = np.reshape(np.asarray([[1, 1], [1, 1]]), (2, 2))  # for 2nd image


    Ix = (convolve2d(img1, Gx) + convolve2d(img2, Gx)) / 2 #smoothing in x direction

    Iy = (convolve2d(img1, Gy) + convolve2d(img2, Gy)) / 2 #smoothing in y direction
    It1 = convolve2d(img1, Gt1) + convolve2d(img2, Gt2)   #taking difference of two images using gaussian mask of all -1 and all 1

    u = np.ones(Ix.shape)
    v = np.ones(Ix.shape)
    status=np.zeros(track_windows.shape[0]) # this will tell change in x,y
    A = np.zeros((2, 2))
    B = np.zeros((2, 1))

    new_track_windows=np.zeros_like(track_windows)

    for a,i in enumerate(track_windows):

        x, y = i

        A[0, 0] = np.sum((Ix[y - 1:y + 2, x - 1:x + 2]) ** 2)

        A[1, 1] = np.sum((Iy[y - 1:y + 2, x - 1:x + 2]) ** 2)
        A[0, 1] = np.sum(Ix[y - 1:y + 2, x - 1:x + 2] * Iy[y - 1:y + 2, x - 1:x + 2])
        A[1, 0] = np.sum(Ix[y - 1:y + 2, x - 1:x + 2] * Iy[y - 1:y + 2, x - 1:x + 2])
        Ainv = np.linalg.pinv(A)

        B[0, 0] = -np.sum(Ix[y - 1:y + 2, x - 1:x + 2] * It1[y - 1:y + 2, x - 1:x + 2])
        B[1, 0] = -np.sum(Iy[y - 1:y + 2, x - 1:x + 2] * It1[y - 1:y + 2, x - 1:x + 2])
        prod = np.matmul(Ainv, B)

        u[y, x] = prod[0]
        v[y, x] = prod[1]

        new_track_windows[a]=[np.int32(x+u[y,x]),np.int32(y+v[y,x])]
        if np.int32(x+u[y,x])==x and np.int32(y+v[y,x])==y:    # this means that there is no change(x+dx==x,y+dy==y) so marking it as 0 else
            status[a]=0
        else:
            status[a]=1 # this tells us that x+dx , y+dy is not equal to x and y

    um=np.flipud(u)
    vm=np.flipud(v)

    new_points = new_track_windows[status==1] #status will tell the position where x and y are changed so for plotting getting only that points
    old_points = track_windows[status==1]

    try:
      tracking =  new_points.reshape(len(new_points)//2, 4)
      
      for points in tracking:
        x1, y1 = points[0], points[1]
        x2, y2 =  points[2],points[3]
        frame2 = cv2.rectangle(frame2, (x1,y1), (x2, y2), (0,0,255), 5)

    except:
      pass

    # draw the tracks
    for i, (new, old) in enumerate(zip(new_points, old_points)):
        a, b = new.ravel()
        c, d = old.ravel()
        frame2 = cv2.line(frame2, (a, b), (c, d), (0,255,0), 2)
        frame2 = cv2.circle(frame2, (a, b), 5, (255,0,0), -1)
 
    return frame2,  new_points

def check_points(frame, track_windows):
  check = False
  try:
    tracking =  track_windows.reshape(len(track_windows)//2, 4)
    
    for points in tracking:
      x1, y1 = track_windows[0], track_windows[1]
      x2, y2 =  track_windows[2], track_windows[3]
      if x1 > frame.shape[1] or x1 < 0:
        check = True
        break
      if x2 > frame.shape[1] or x2 < 0:
        check = True
        break
      if y1 > frame.shape[1] or y1 < 0:
        check = True
        break
      if y2 > frame.shape[0] or y2 < 0:
        check = True
        break
  except:
    check = True
  
  if check or track_windows.size == 0:
    _, faces = detect_face(frame)
    track_windows = []
    for (x,y,w,h) in faces:
      track_windows.append((int(x),int(y),int(x+w),int(y+h)))
    track_windows = np.array(track_windows).reshape(2*len(track_windows),2)
  
  return check, track_windows

def LK(video, save = True):
  frames = []
  cap = cv2.VideoCapture(f'{video}.mp4')
  ret,frame = cap.read()
  width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fps =  int(cap.get(cv2.CAP_PROP_FPS))
  frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

  t = dt.datetime.now()

  frame1, faces = detect_face(frame)
  track_windows = []
  for (x,y,w,h) in faces:
    track_windows.append((int(x),int(y),int(x+w),int(y+h)))

  track_windows = np.array(track_windows).reshape(len(track_windows)*2,2)
  while True: 

    if (dt.datetime.now() -t).seconds / 10 >= 1:
      t = dt.datetime.now()
      percent = ((cap.get(cv2.CAP_PROP_POS_FRAMES)/frame_count)*100)
      print(f'\rProcessing Video - {percent :.2f}%', end='', flush=True)

    ret,frame2 = cap.read()

    if ret == True:
      check, track_windows = check_points(frame2, track_windows)

      frame, track_windows = Lucas_Kanade(frame1, frame2, track_windows)

      check, track_windows = check_points(frame2, track_windows)
      
      frames.append(frame)
      frame1 = frame2.copy()
      
    else:
      break

  if save == True:
    video = cv2.VideoWriter(f'processed/{video}-LK.mp4', cv2.VideoWriter_fourcc(*'MP4V'), fps, (width,height))
    for frame in frames:
      video.write(frame)

    video.release()
  cap.release()
  cv2.destroyAllWindows()
  print(f'\rProcessing Video - 100%', end='', flush=True)

# #'face', 'dance', 'manKid', 'market', 'people', 'rollarSkaters',
# videos = ['rollarSkaters2', 'study', 'walk', 'workingMan', 'protest2', 'protest1']
# for video in videos:
#   print(f'\n{video}')
#   print('MeanShift:')
#   MS(video)
#   print('\nLucas Kanade:')
#   LK(video)

# from google.colab import files
# files.download('processed/face-1-MS.mp4') 
# files.download('processed/face-LK.mp4')
# files.download('processed/dance-1-MS.mp4') 
# files.download('processed/dance-LK.mp4')
# files.download('processed/manKid-1-MS.mp4') 
# files.download('processed/manKid-LK.mp4') 
# files.download('processed/market-1-MS.mp4') 
# files.download('processed/market-LK.mp4')
# files.download('processed/people-1-MS.mp4') 
# files.download('processed/people-LK.mp4')
# files.download('processed/rollarSkaters-1-MS.mp4') 
# files.download('processed/rollarSkaters-LK.mp4')
# files.download('processed/rollarSkaters2-1-MS.mp4') 
# files.download('processed/rollarSkaters2-LK.mp4') 
# files.download('processed/study-1-MS.mp4') 
# files.download('processed/study-LK.mp4') 
# files.download('processed/walk-1-MS.mp4') 
# files.download('processed/walk-LK.mp4')
# files.download('processed/workingMan-1-MS.mp4') 
# files.download('processed/workingMan-LK.mp4')
# files.download('processed/protest1-1-MS.mp4') 
# files.download('processed/protest1-LK.mp4')
# files.download('processed/protest2-1-MS.mp4') 
# files.download('processed/protest2-LK.mp4')

