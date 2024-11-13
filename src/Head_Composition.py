#coding=utf-8
import cv2
import dlib

# 初始化Dlib的人脸检测器和关键点预测器
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('../utils/shape_predictor_68_face_landmarks.dat')

def detect_faces_with_landmarks(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    faceRects = []
    landmarks = []
    for face in faces:
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        faceRects.append((x, y, w, h))
        shape = predictor(gray, face)
        landmarks.append(shape)
    return faceRects, landmarks


def overlay_glasses_precise(img, imgCompose, faceRects, landmarks):
    if len(faceRects):
        for idx, faceRect in enumerate(faceRects):
            x, y, w, h = faceRect
            shape = landmarks[idx]

            # 获取左右眼的中心点
            left_eye = (shape.part(36).x, shape.part(36).y)
            right_eye = (shape.part(45).x, shape.part(45).y)
            eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)

            # 计算眼镜宽度为两眼之间的距离乘以一个比例
            glasses_width = int(1.5 * (right_eye[0] - left_eye[0]))
            aspect_ratio = imgCompose.shape[1] / imgCompose.shape[0]
            glasses_height = int(glasses_width / aspect_ratio)

            # 调整眼镜图像大小
            imgComposeResized = cv2.resize(imgCompose, (glasses_width, glasses_height), interpolation=cv2.INTER_AREA)

            # 计算放置位置，使眼镜居中于眼睛中心
            top = eye_center[1] - int(glasses_height / 2)
            left = eye_center[0] - int(glasses_width / 2)

            # 确保位置不超出图像边界
            if top < 0:
                top = 0
            if left < 0:
                left = 0
            if top + glasses_height > img.shape[0]:
                glasses_height = img.shape[0] - top
                imgComposeResized = imgComposeResized[0:glasses_height, :, :]
            if left + glasses_width > img.shape[1]:
                glasses_width = img.shape[1] - left
                imgComposeResized = imgComposeResized[:, 0:glasses_width, :]

            # 提取放置区域
            roi = img[top:top + glasses_height, left:left + glasses_width]

            # 创建掩码和反掩码
            if imgComposeResized.shape[2] == 4:
                alpha_channel = imgComposeResized[:, :, 3]
                mask = alpha_channel
                mask_inv = cv2.bitwise_not(mask)
                imgComposeRGB = imgComposeResized[:, :, :3]
            else:
                img2gray = cv2.cvtColor(imgComposeResized, cv2.COLOR_BGR2GRAY)
                ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
                mask_inv = cv2.bitwise_not(mask)
                imgComposeRGB = imgComposeResized

            # 在ROI区域中黑掉将要叠加图像的位置
            img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)

            # 提取眼镜图像的前景部分
            img2_fg = cv2.bitwise_and(imgComposeRGB, imgComposeRGB, mask=mask)

            # 合成前景和背景图像
            dst = cv2.add(img1_bg, img2_fg)
            img[top:top + glasses_height, left:left + glasses_width] = dst

    return img


img = cv2.imread("../data/images/25.jpg")  # 读取图片
imgCompose = cv2.imread("../data/imgCompose/eyewear.png")

faceRects, landmarks = detect_faces_with_landmarks(img)

# 叠加眼镜
result_img = overlay_glasses_precise(img, imgCompose, faceRects, landmarks)

# 显示结果
cv2.imshow('With Glasses', result_img)
cv2.waitKey(0)
cv2.destroyAllWindows()


