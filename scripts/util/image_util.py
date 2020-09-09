import cv2
import imutils
import numpy as np


def get_warp_applied_image(m_image, pts_src):
    pts_src = np.array(pts_src)
    H, W = m_image.shape
    pts_dst = np.array([[0.0, 0.0], [W, 0.0], [0.0, H], [W, H]])
    im_dst = np.zeros((H, W, 1), np.uint8)
    h, status = cv2.findHomography(pts_src, pts_dst)
    im_out = cv2.warpPerspective(m_image, h, (im_dst.shape[1], im_dst.shape[0]))
    return im_out


def rotate_image(img, angle):
    img_rotate_180 = imutils.rotate(img, angle)
    return img_rotate_180


def get_the_contour_list(m_image):
    imgray = cv2.cvtColor(m_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(imgray, 211, 255, cv2.THRESH_BINARY)
    cv2.imshow('threshed', thresh)
    mask = 255 - thresh
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    return contours


def get_the_display_block(image, contour):
    h = 70
    w = 125
    left_margin = 9
    right_margin = 1
    top_margin = 7
    bottom_margin = 1
    area_margin = 50
    # display_block_size_lower = area-area_margin
    # display_block_size_upper = area+area_margin


    # imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # _, thresh = cv2.threshold(imgray, 213, 255, cv2.THRESH_BINARY)
    # mask = 255 - thresh
    # contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # contour = None
    # # areas = []
    # for contour in contours:
    #     area = cv2.contourArea(contour)
    #     # print(area)
    #     # areas.append(area)
    #     if display_block_size_lower < area < display_block_size_upper:
    #         best = contour
    #         break
    # if best is None:
    #     print('No contour found for the display block')
    #     return
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int0(box)

    # crop image inside bounding box
    scale = 1  # cropping margin, 1 == no margin
    W = rect[1][0]
    H = rect[1][1]

    Xs = [i[0] for i in box]
    Ys = [i[1] for i in box]
    x1 = min(Xs)
    x2 = max(Xs)
    y1 = min(Ys)
    y2 = max(Ys)

    angle = rect[2]
    rotated = False
    if angle < -45:
        angle += 90
        rotated = True

    center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
    size = (int(scale * (x2 - x1)), int(scale * (y2 - y1)))

    M = cv2.getRotationMatrix2D((size[0] / 2, size[1] / 2), angle, 1.0)

    cropped = cv2.getRectSubPix(image, size, center)
    cropped = cv2.warpAffine(cropped, M, size)

    croppedW = W if not rotated else H
    croppedH = H if not rotated else W

    image = cv2.getRectSubPix(
        cropped, (int(croppedW * scale), int(croppedH * scale)), (size[0] / 2, size[1] / 2))
    # resize the image to predefined the size(make sure of the size of the image it's returning
    image = cv2.resize(image, (w,h))
    # remove the shadows in margins
    image = get_cropped_image_by_margin(image, left_margin, right_margin, top_margin, bottom_margin)

    return image  # 115*64 size image is returned


def get_cropped_image_by_margin(image, l, r, t, b):
    return image[t:-b, l:-r]


def get_cropped_image_by_coordinates(image, x1, x2, y1, y2):
    return image[y1:y2, x1:x2]


def remove_noise(m_image, m_kernel):
    result = cv2.morphologyEx(m_image, cv2.MORPH_OPEN, m_kernel, iterations=1)
    result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, m_kernel, iterations=1)
    return result


def get_color_range_mask_on_bgr_image(m_image, m_color_low=(14, 73, 114), m_color_high=(24, 244, 255)):
    hsv_img = cv2.cvtColor(m_image, cv2.COLOR_BGR2HSV)
    return get_color_range_mask(hsv_img, m_color_low, m_color_high)


def get_color_range_mask(m_image, m_color_low=(14, 73, 114), m_color_high=(24, 244, 255)):
    mask = cv2.inRange(m_image, m_color_low, m_color_high)
    return mask


def get_bordered_color_image_for_grayscale_image(img):
    img = get_bordered_image(img, 2)
    return get_color_image_from_greyscale_image(img)


def get_color_image_from_greyscale_image(image):
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)


def get_bordered_image(image, border_size, border_color=[255, 255, 255]):
    H, W = image.shape[:2]
    resized_image = cv2.resize(image, (W - 2 * border_size, H - 2 * border_size))
    return cv2.copyMakeBorder(resized_image, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT,
                              value=border_color)


def write_a_video_from_image_list(image_list, video_name_without_extension, height, width, frame_rate=15,
                                  container="mp4", four_cc_codec="mp4v"):
    video_file_name = "%s.%s" % (video_name_without_extension, container)
    out = cv2.VideoWriter(video_file_name, cv2.VideoWriter_fourcc(*four_cc_codec), frame_rate, (width, height))

    for image in image_list:
        resize = cv2.resize(image, (width, height))
        out.write(resize)
    out.release()


def show_and_wait(image, title, wait=0):
    cv2.imshow(title, image)
    cv2.waitKey(wait)


def draw_box(image, x_min, y_min, x_max, y_max, confidence, color=(255, 0, 0)):
    cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color)
    text = "{0:.4f}".format(confidence)
    cv2.putText(image, text, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, color, 2)
    return image


def get_mean_and_stddev_from_gray_image_for_mask(img, mask):
    m_mean, m_stddev = cv2.meanStdDev(img, mask=mask)
    return m_mean[0][0], m_stddev[0][0]


def get_min_max_from_gray_image_for_mask(m_image, m_mask):
    m_min, m_max, _, _ = cv2.minMaxLoc(m_image, mask=m_mask)
    return m_min, m_max


def get_non_zero_pixels_for_mask(mask):
    return cv2.countNonZero(mask)


def get_pixel_statics_for_rgb_image(m_image, m_mask):
    m_gray_image = cv2.cvtColor(m_image, cv2.COLOR_BGR2GRAY)
    m_mean, m_stddev = get_mean_and_stddev_from_gray_image_for_mask(m_gray_image, m_mask)
    m_mask_size = get_non_zero_pixels_for_mask(m_mask)
    m_min, m_max = get_min_max_from_gray_image_for_mask(m_gray_image, m_mask)

    return {
        'mean': m_mean,
        'stddev': m_stddev,
        'mask_size': m_mask_size,
        'min': m_min,
        'max': m_max
    }