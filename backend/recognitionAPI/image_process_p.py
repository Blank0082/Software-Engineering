import os
import cv2
import json
import base64
import numpy as np
from PIL import Image, ImageEnhance


def natural_sort_key(s):
    import re
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def takefnum(elem):
    return int(elem.split('-')[0]), int(float(elem.split('-')[1][0:2]))


def detect_border(input_folder):
    # 確保資料夾存在
    if not os.path.exists(input_folder):
        # print("資料夾不存在。")
        return
    for root, dirs, files in os.walk(input_folder):
        files = os.listdir(root)
        files.sort(key=natural_sort_key)  # Use custom sorting key

        for filename in files:
            image_path = os.path.join(root, filename)
            image = cv2.imread(image_path)
            if image is None:
                # print(f"無法讀取圖片：{image_path}")
                continue
            # 將圖片轉換為灰度
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 自適應閾值二值化
            binary_img = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

            # 從左至右檢測黑色像素部分並標記需要補白的行
            marked_rows = set()
            for col in range(binary_img.shape[1]):
                black_pixel_count = np.count_nonzero(binary_img[:, col] == 0)  # 黑色像素的數量
                if binary_img.shape[0] - 10 <= black_pixel_count <= binary_img.shape[0]:
                    marked_rows.add(col)
                    if col == 0:
                        marked_rows.add(col + 1)
                        marked_rows.add(col + 2)
                    elif col == binary_img.shape[0]:
                        marked_rows.add(col - 1)
                        marked_rows.add(col - 2)
                    elif 1 <= col <= binary_img.shape[0] - 1:
                        marked_rows.add(col - 1)
                        marked_rows.add(col + 1)

            # 從上至下檢測黑色像素部分並標記需要補白的列
            marked_cols = set()
            for row in range(binary_img.shape[0]):
                black_pixel_count = np.count_nonzero(binary_img[row, :] == 0)  # 黑色像素的數量
                if binary_img.shape[1] - 10 <= black_pixel_count <= binary_img.shape[1]:
                    marked_cols.add(row)
                    if row == 0:
                        marked_cols.add(row + 1)
                        marked_cols.add(row + 2)
                    elif row >= 1:
                        marked_cols.add(row - 1)
                        marked_cols.add(row + 1)
                    elif row == binary_img.shape[1]:
                        marked_cols.add(row - 1)
                        marked_cols.add(row - 2)
                    elif row <= binary_img.shape[1] - 1:
                        marked_cols.add(row + 1)
                        marked_cols.add(row - 1)

            # 補白處理
            for row in marked_rows:
                image[:, min(row, binary_img.shape[1] - 1)] = 255

            for col in marked_cols:
                image[min(col, binary_img.shape[0] - 1), :] = 255
            cv2.imwrite(image_path, image)
        # print("圖片雜線去除完成...")


def analyze_brightness(image):
    # 将图像转换为灰度图像
    gray_image = image.convert('L')

    # 计算图像的平均亮度
    histogram = gray_image.histogram()
    pixels = sum(histogram)
    brightness = sum(index * value for index, value in enumerate(histogram)) / pixels

    return brightness


def adjust_brightness_image(image_path, target_brightness, brightness_threshold=100):
    # 打开图像
    image = Image.open(image_path)

    # 分析图像的亮度
    brightness = analyze_brightness(image)

    # 如果图像过暗，则调整亮度
    if brightness < brightness_threshold:
        # 计算亮度调整因子
        factor = target_brightness / brightness

        # 创建ImageEnhance对象
        enhancer = ImageEnhance.Brightness(image)

        # 调整亮度
        adjusted_image = enhancer.enhance(factor)

        return adjusted_image, image_path  # 返回图像对象和图像路径
    else:
        return image, image_path  # 返回原始图像对象和图像路径


def adjust_brightness(folder_path, target_brightness, brightness_threshold=100):
    # 遍历文件夹中的所有文件和子文件夹
    for root, dirs, files in os.walk(folder_path):
        files = os.listdir(root)
        files.sort(key=natural_sort_key)
        # 对每个文件夹中的文件进行处理
        for file_name in files:
            # 检查文件是否是图像文件
            if file_name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                # 构建完整的文件路径
                image_path = os.path.join(root, file_name)

                # 调整图像的亮度
                adjusted_image, adjusted_image_path = adjust_brightness_image(image_path, target_brightness,
                                                                              brightness_threshold)

                # 保存调整后的图像
                adjusted_image.save(adjusted_image_path)
    # print("图片亮度調整完成...")


def process_image(img_path):
    img = cv2.imread(img_path)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 自适应阈值二值化
    # binary_img = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    _, binary_img = cv2.threshold(gray_img, 127, 255, cv2.THRESH_BINARY)
    height, width = binary_img.shape[:2]

    # 定義新的區域（中心點向四邊擴展20px）
    top_left_x = max(0, width // 2 - 24)
    top_left_y = max(0, height // 2 - 24)
    bottom_right_x = min(width, width // 2 + 24)
    bottom_right_y = min(height, height // 2 + 24)

    # 提取中心區域並計算非黑像素比例
    center_region = binary_img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    total_pixels = center_region.size
    non_black_pixels = cv2.countNonZero(center_region)
    non_black_pixels_percentage = (non_black_pixels / total_pixels) * 100

    # print(f"{os.path.basename(img_path)}，非黑像素比例: {non_black_pixels_percentage:.2f}%")

    return non_black_pixels_percentage


def detect_img_white(input_folder, grid_count):
    for root, dirs, files in os.walk(input_folder):
        files = os.listdir(root)
        files.sort(key=natural_sort_key)

        count = 1
        remove_count = 0
        execute_condition_removal = True

        for filename in files:
            img_path = os.path.join(root, filename)
            non_black_percentage = process_image(img_path)
            # has_black_pixel = check_black_pixels(img_path)

            if execute_condition_removal:
                if non_black_percentage == 100:
                    # print(img_path)
                    os.remove(img_path)  # 如果不存在黑色像素，删除图像
                    remove_count += 1
                    if remove_count >= int(grid_count * 1.5):
                        execute_condition_removal = False
                else:
                    # print(remove_count)
                    # 以两位数的格式对计数器进行格式化，并作为新的文件名
                    new_filename = f"{count:04d}.png"  # 可根据需要修改文件格式
                    new_img_path = os.path.join(root, new_filename)

                    os.rename(img_path, new_img_path)
                    remove_count = 0
                    count += 1
            else:
                # print(remove_count)
                os.remove(img_path)
    # print("圖片篩選完成...")


# def detect_img_base64(input_folder):
#     image_data_dict = {}
#
#     for root, dirs, files in os.walk(input_folder):
#         files = os.listdir(root)
#         files.sort(key=takefnum)
#
#         for filename in files:
#             img_path = os.path.join(root, filename)
#             try:
#                 with open(img_path, "rb") as image_file:
#                     image_binary = image_file.read()
#                     base64_image = base64.b64encode(image_binary).decode('utf-8')
#                     image_data_dict[filename] = f"data:image/jpeg;base64,{base64_image}"
#             except Exception as e:
#                 print("Error:", e)
#                 return 7  # 格式轉換錯誤
#     return image_data_dict


# input_path = './03311'
# output_json_file = "./03111.json"  # 替换为您的输出JSON文件路径
# target_brightness = 230
#
# # 亮度阈值（低于该值则进行亮度调整）
# brightness_threshold = 180
#
# # 调用函数使文件夹中的所有图像适应亮度
# adjust_brightness(input_path, target_brightness, brightness_threshold)
# detect_img_white(input_path, 18)
# detect_border(input_path)
# base64_image_dict = detect_img_base64(input_path)

