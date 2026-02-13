+++
title = "27. 计算机视觉与OpenCV实战"
date = 2026-02-06
weight = 27000
description = "OpenCV图像处理全攻略：从基础操作到目标检测YOLO，GPU加速与实时视频流处理"
[taxonomies]
tags = ["opencv", "computer-vision", "yolo", "image-processing", "deep-learning"]
+++

## 概述

OpenCV 是计算机视觉领域最广泛使用的开源库。本文从基础图像处理到深度学习目标检测，系统介绍 OpenCV 的使用，包括 GPU 加速和实时视频流处理。

---

## 一、OpenCV 基础

### 1.1 安装与配置

```bash
# Python 安装
pip install opencv-python           # 主模块
pip install opencv-contrib-python   # 额外模块
pip install opencv-python-headless  # 无 GUI 版本（服务器）

# 带 CUDA 支持的编译安装
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_contrib.git

cd opencv && mkdir build && cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D WITH_CUDA=ON \
      -D CUDA_ARCH_BIN="8.6" \
      -D WITH_CUDNN=ON \
      -D OPENCV_DNN_CUDA=ON \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
      -D BUILD_opencv_python3=ON \
      ..
make -j$(nproc)
sudo make install
```

### 1.2 基础操作

```python
import cv2
import numpy as np

# ========================
# 图像读取与显示
# ========================

# 读取图像
img = cv2.imread('image.jpg')              # BGR 格式
img_gray = cv2.imread('image.jpg', cv2.IMREAD_GRAYSCALE)
img_rgba = cv2.imread('image.png', cv2.IMREAD_UNCHANGED)

# 图像信息
print(f"Shape: {img.shape}")       # (height, width, channels)
print(f"Dtype: {img.dtype}")       # uint8
print(f"Size: {img.size}")         # 总像素数

# 显示图像
cv2.imshow('Window', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 保存图像
cv2.imwrite('output.jpg', img)
cv2.imwrite('output.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 9])

# ========================
# 颜色空间转换
# ========================

# BGR -> RGB
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# BGR -> Gray
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# BGR -> HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# BGR -> LAB
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

# ========================
# 图像基本操作
# ========================

# 裁剪
cropped = img[100:400, 200:500]  # [y1:y2, x1:x2]

# 缩放
resized = cv2.resize(img, (640, 480))
resized = cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)

# 旋转
center = (img.shape[1]//2, img.shape[0]//2)
matrix = cv2.getRotationMatrix2D(center, 45, 1.0)  # 中心，角度，缩放
rotated = cv2.warpAffine(img, matrix, (img.shape[1], img.shape[0]))

# 翻转
flipped_h = cv2.flip(img, 1)   # 水平翻转
flipped_v = cv2.flip(img, 0)   # 垂直翻转
flipped_both = cv2.flip(img, -1)  # 双向翻转
```

---

## 二、图像处理

### 2.1 滤波与平滑

```python
# ========================
# 模糊/平滑
# ========================

# 均值滤波
blur = cv2.blur(img, (5, 5))

# 高斯滤波
gaussian = cv2.GaussianBlur(img, (5, 5), 0)

# 中值滤波（去除椒盐噪声）
median = cv2.medianBlur(img, 5)

# 双边滤波（保边去噪）
bilateral = cv2.bilateralFilter(img, 9, 75, 75)

# ========================
# 边缘检测
# ========================

# Canny 边缘检测
edges = cv2.Canny(gray, 100, 200)

# Sobel 算子
sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
sobel = cv2.magnitude(sobel_x, sobel_y)

# Laplacian
laplacian = cv2.Laplacian(gray, cv2.CV_64F)

# ========================
# 形态学操作
# ========================

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

# 腐蚀
eroded = cv2.erode(binary, kernel, iterations=1)

# 膨胀
dilated = cv2.dilate(binary, kernel, iterations=1)

# 开运算（先腐蚀后膨胀，去除小白点）
opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

# 闭运算（先膨胀后腐蚀，填充小黑洞）
closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

# 梯度（膨胀 - 腐蚀，提取边缘）
gradient = cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, kernel)
```

### 2.2 阈值与二值化

```python
# ========================
# 阈值分割
# ========================

# 简单阈值
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
_, binary_inv = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

# Otsu 自动阈值
_, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# 自适应阈值
adaptive_mean = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2
)
adaptive_gaussian = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
)
```

### 2.3 直方图

```python
# ========================
# 直方图
# ========================

# 计算直方图
hist = cv2.calcHist([gray], [0], None, [256], [0, 256])

# 绘制直方图
import matplotlib.pyplot as plt
plt.plot(hist)
plt.xlabel('Pixel Value')
plt.ylabel('Frequency')
plt.show()

# 直方图均衡化
equalized = cv2.equalizeHist(gray)

# CLAHE（限制对比度自适应直方图均衡化）
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
clahe_result = clahe.apply(gray)

# 彩色图像直方图均衡化
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
equalized_color = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
```

---

## 三、特征检测与匹配

### 3.1 特征检测

```python
# ========================
# 角点检测
# ========================

# Harris 角点
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
harris = cv2.cornerHarris(gray, blockSize=2, ksize=3, k=0.04)
img[harris > 0.01 * harris.max()] = [0, 0, 255]

# Shi-Tomasi 角点（Good Features to Track）
corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=10)
for corner in corners:
    x, y = corner.ravel()
    cv2.circle(img, (int(x), int(y)), 5, (0, 255, 0), -1)

# ========================
# 关键点检测器
# ========================

# SIFT（专利已过期）
sift = cv2.SIFT_create()
keypoints, descriptors = sift.detectAndCompute(gray, None)

# ORB（免费替代 SIFT）
orb = cv2.ORB_create(nfeatures=500)
keypoints, descriptors = orb.detectAndCompute(gray, None)

# AKAZE
akaze = cv2.AKAZE_create()
keypoints, descriptors = akaze.detectAndCompute(gray, None)

# 绘制关键点
img_keypoints = cv2.drawKeypoints(img, keypoints, None, 
                                   flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
```

### 3.2 特征匹配

```python
# ========================
# 特征匹配
# ========================

# 暴力匹配
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)  # ORB 用 HAMMING
matches = bf.match(desc1, desc2)
matches = sorted(matches, key=lambda x: x.distance)

# KNN 匹配 + 比率测试
bf = cv2.BFMatcher()
matches = bf.knnMatch(desc1, desc2, k=2)

# Lowe's 比率测试
good_matches = []
for m, n in matches:
    if m.distance < 0.75 * n.distance:
        good_matches.append(m)

# FLANN 匹配（大规模特征快速匹配）
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50)
flann = cv2.FlannBasedMatcher(index_params, search_params)
matches = flann.knnMatch(desc1, desc2, k=2)

# 绘制匹配
img_matches = cv2.drawMatches(img1, kp1, img2, kp2, good_matches, None,
                               flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
```

### 3.3 单应性变换

```python
# ========================
# 图像配准 / 拼接
# ========================

if len(good_matches) >= 4:
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    # 计算单应性矩阵
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    
    # 透视变换
    h, w = img1.shape[:2]
    warped = cv2.warpPerspective(img1, H, (w, h))
```

---

## 四、目标检测

### 4.1 传统方法

```python
# ========================
# 轮廓检测
# ========================

# 查找轮廓
contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 绘制轮廓
cv2.drawContours(img, contours, -1, (0, 255, 0), 2)

# 轮廓属性
for contour in contours:
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, closed=True)
    x, y, w, h = cv2.boundingRect(contour)
    
    # 外接矩形
    cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    
    # 最小外接矩形
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect).astype(int)
    cv2.drawContours(img, [box], 0, (0, 0, 255), 2)
    
    # 外接圆
    (cx, cy), radius = cv2.minEnclosingCircle(contour)
    cv2.circle(img, (int(cx), int(cy)), int(radius), (0, 255, 255), 2)

# ========================
# Haar 级联分类器（人脸检测）
# ========================

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
```

### 4.2 深度学习目标检测

```python
# ========================
# OpenCV DNN 模块
# ========================

# 加载预训练模型
net = cv2.dnn.readNetFromDarknet('yolov4.cfg', 'yolov4.weights')
# 或 ONNX 模型
net = cv2.dnn.readNetFromONNX('model.onnx')

# 使用 CUDA 后端
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

# 获取输出层名称
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# 图像预处理
blob = cv2.dnn.blobFromImage(img, 1/255.0, (416, 416), swapRB=True, crop=False)
net.setInput(blob)

# 推理
outputs = net.forward(output_layers)

# 解析输出
class_ids = []
confidences = []
boxes = []

for output in outputs:
    for detection in output:
        scores = detection[5:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]
        
        if confidence > 0.5:
            center_x = int(detection[0] * w)
            center_y = int(detection[1] * h)
            width = int(detection[2] * w)
            height = int(detection[3] * h)
            
            x = center_x - width // 2
            y = center_y - height // 2
            
            boxes.append([x, y, width, height])
            confidences.append(float(confidence))
            class_ids.append(class_id)

# NMS（非极大值抑制）
indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

# 绘制结果
for i in indices.flatten():
    x, y, w, h = boxes[i]
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    label = f"{classes[class_ids[i]]}: {confidences[i]:.2f}"
    cv2.putText(img, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
```

### 4.3 YOLO 检测类

```python
class YOLODetector:
    def __init__(self, config_path, weights_path, classes_path, conf_threshold=0.5, nms_threshold=0.4):
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        
        # 加载类别名称
        with open(classes_path, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]
        
        # 加载网络
        self.net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        
        # 获取输出层
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
    
    def detect(self, image, input_size=(416, 416)):
        h, w = image.shape[:2]
        
        # 预处理
        blob = cv2.dnn.blobFromImage(image, 1/255.0, input_size, swapRB=True, crop=False)
        self.net.setInput(blob)
        
        # 推理
        outputs = self.net.forward(self.output_layers)
        
        # 解析
        boxes, confidences, class_ids = [], [], []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.conf_threshold:
                    cx = int(detection[0] * w)
                    cy = int(detection[1] * h)
                    bw = int(detection[2] * w)
                    bh = int(detection[3] * h)
                    
                    x = cx - bw // 2
                    y = cy - bh // 2
                    
                    boxes.append([x, y, bw, bh])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # NMS
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 
                                    self.conf_threshold, self.nms_threshold)
        
        results = []
        for i in indices.flatten():
            results.append({
                'box': boxes[i],
                'confidence': confidences[i],
                'class_id': class_ids[i],
                'class_name': self.classes[class_ids[i]]
            })
        
        return results
    
    def draw_detections(self, image, detections):
        for det in detections:
            x, y, w, h = det['box']
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            label = f"{det['class_name']}: {det['confidence']:.2f}"
            cv2.putText(image, label, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return image


# 使用示例
detector = YOLODetector('yolov4.cfg', 'yolov4.weights', 'coco.names')
detections = detector.detect(image)
result = detector.draw_detections(image.copy(), detections)
```

---

## 五、视频处理

### 5.1 视频读写

```python
# ========================
# 视频读取
# ========================

cap = cv2.VideoCapture('video.mp4')
# 或摄像头
cap = cv2.VideoCapture(0)

# 获取视频属性
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"Video: {width}x{height} @ {fps}fps, {frame_count} frames")

# 逐帧读取
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # 处理帧
    processed = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    cv2.imshow('Video', processed)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# ========================
# 视频写入
# ========================

fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 或 'XVID', 'H264'
out = cv2.VideoWriter('output.mp4', fourcc, fps, (width, height))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # 处理帧
    processed = process_frame(frame)
    
    out.write(processed)

out.release()
```

### 5.2 实时处理管道

```python
import cv2
import time
from collections import deque

class VideoProcessor:
    def __init__(self, source=0, buffer_size=5):
        self.cap = cv2.VideoCapture(source)
        self.buffer_size = buffer_size
        self.fps_buffer = deque(maxlen=30)
        
    def process_frame(self, frame):
        """重写此方法实现自定义处理"""
        return frame
    
    def run(self, display=True, record=None):
        if record:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            out = cv2.VideoWriter(record, fourcc, fps, (width, height))
        else:
            out = None
        
        try:
            while self.cap.isOpened():
                start_time = time.time()
                
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # 处理
                processed = self.process_frame(frame)
                
                # 计算 FPS
                elapsed = time.time() - start_time
                self.fps_buffer.append(1.0 / max(elapsed, 0.001))
                avg_fps = sum(self.fps_buffer) / len(self.fps_buffer)
                
                # 显示 FPS
                cv2.putText(processed, f"FPS: {avg_fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                if display:
                    cv2.imshow('Video', processed)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if out:
                    out.write(processed)
                    
        finally:
            self.cap.release()
            if out:
                out.release()
            cv2.destroyAllWindows()


# 使用示例：目标检测视频处理
class DetectionVideoProcessor(VideoProcessor):
    def __init__(self, source=0, detector=None):
        super().__init__(source)
        self.detector = detector
    
    def process_frame(self, frame):
        if self.detector:
            detections = self.detector.detect(frame)
            frame = self.detector.draw_detections(frame, detections)
        return frame


processor = DetectionVideoProcessor(0, detector)
processor.run(display=True, record='output.mp4')
```

---

## 六、GPU 加速

### 6.1 CUDA 模块

```python
# ========================
# OpenCV CUDA 加速
# ========================

# 检查 CUDA 可用性
print(f"CUDA devices: {cv2.cuda.getCudaEnabledDeviceCount()}")

# 上传到 GPU
gpu_mat = cv2.cuda_GpuMat()
gpu_mat.upload(img)

# 或直接创建
gpu_mat = cv2.cuda_GpuMat(img)

# GPU 操作
gpu_gray = cv2.cuda.cvtColor(gpu_mat, cv2.COLOR_BGR2GRAY)
gpu_blur = cv2.cuda.GaussianBlur(gpu_mat, (5, 5), 0)
gpu_resize = cv2.cuda.resize(gpu_mat, (640, 480))

# 下载到 CPU
result = gpu_gray.download()

# ========================
# CUDA 滤波器
# ========================

# 创建滤波器（可复用）
gaussian_filter = cv2.cuda.createGaussianFilter(
    cv2.CV_8UC3, cv2.CV_8UC3, (5, 5), 0
)
blurred = gaussian_filter.apply(gpu_mat)

sobel_filter = cv2.cuda.createSobelFilter(
    cv2.CV_8UC1, cv2.CV_32FC1, 1, 0, 3
)

# ========================
# CUDA 特征检测
# ========================

# ORB
orb_cuda = cv2.cuda_ORB.create(nfeatures=500)
keypoints_gpu, descriptors_gpu = orb_cuda.detectAndComputeAsync(gpu_gray, None)

# 下载关键点
keypoints = orb_cuda.convert(keypoints_gpu)
descriptors = descriptors_gpu.download()
```

### 6.2 GPU 视频处理

```python
class GPUVideoProcessor:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        
        # 创建 GPU 资源
        self.gpu_frame = cv2.cuda_GpuMat()
        self.gpu_gray = cv2.cuda_GpuMat()
        self.gpu_blur = cv2.cuda_GpuMat()
        
        # 创建滤波器
        self.gaussian = cv2.cuda.createGaussianFilter(
            cv2.CV_8UC3, cv2.CV_8UC3, (5, 5), 0
        )
        
    def process_gpu(self, frame):
        # 上传到 GPU
        self.gpu_frame.upload(frame)
        
        # GPU 处理
        self.gaussian.apply(self.gpu_frame, self.gpu_blur)
        cv2.cuda.cvtColor(self.gpu_blur, cv2.COLOR_BGR2GRAY, self.gpu_gray)
        
        # 下载结果
        return self.gpu_gray.download()
    
    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            
            result = self.process_gpu(frame)
            
            cv2.imshow('GPU Processed', result)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
```

---

## 七、实用工具函数

```python
def resize_with_aspect_ratio(image, width=None, height=None, inter=cv2.INTER_AREA):
    """保持宽高比缩放"""
    h, w = image.shape[:2]
    
    if width is None and height is None:
        return image
    
    if width is None:
        ratio = height / h
        dim = (int(w * ratio), height)
    else:
        ratio = width / w
        dim = (width, int(h * ratio))
    
    return cv2.resize(image, dim, interpolation=inter)


def rotate_image(image, angle):
    """任意角度旋转（保持完整图像）"""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2
    
    return cv2.warpAffine(image, M, (new_w, new_h))


def stack_images(images, rows, cols, scale=1.0):
    """将多个图像拼接成网格"""
    images = [cv2.resize(img, None, fx=scale, fy=scale) for img in images]
    
    # 确保所有图像尺寸相同
    h, w = images[0].shape[:2]
    
    # 填充不足的位置
    while len(images) < rows * cols:
        images.append(np.zeros_like(images[0]))
    
    result = []
    for r in range(rows):
        row_images = images[r * cols:(r + 1) * cols]
        result.append(np.hstack(row_images))
    
    return np.vstack(result)


def draw_text_with_background(img, text, position, font_scale=0.7, 
                               color=(255, 255, 255), bg_color=(0, 0, 0)):
    """绘制带背景的文本"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    x, y = position
    cv2.rectangle(img, (x, y - text_h - 5), (x + text_w + 5, y + 5), bg_color, -1)
    cv2.putText(img, text, (x, y), font, font_scale, color, thickness)
    
    return img
```

---

## 八、最佳实践

**OpenCV 开发最佳实践：**

| 类别 | 建议 |
|------|------|
| **性能优化** | 尽量使用 GPU（cv2.cuda）；复用 GpuMat 和滤波器对象；使用 numpy 向量化操作；避免 Python 循环处理像素 |
| **视频处理** | 使用多线程分离读取和处理；控制处理帧率（跳帧）；合理设置分辨率 |
| **内存管理** | 及时释放大图像；使用生成器处理视频流；避免不必要的图像复制 |
| **深度学习集成** | 优先使用 ONNX 格式；启用 CUDA 后端；批量处理多帧 |

---

## 相关文章

- [上一篇：26 - ROCm 与 AMD GPU 开发](@/articles/ai/ai-26-ROCm与AMD-GPU开发.md)
- [下一篇：28 - AI 技术栈全景图](@/articles/ai/ai-28-AI技术栈全景图.md)
- [21 - CUDA 入门与 GPU 编程基础](@/articles/ai/ai-21-CUDA入门与GPU编程基础.md)
- [18 - 边缘 AI 与端侧部署详解](@/articles/ai/ai-18-边缘AI与端侧部署详解.md)
