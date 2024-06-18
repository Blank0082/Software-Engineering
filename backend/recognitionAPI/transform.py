import cv2
import os
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt
from scipy import signal
from sklearn.cluster import KMeans


class Transformer:
    def __init__(self, input_image):
        self.NEED_REVERSE = False
        self.image_name = os.path.basename(input_image)
        # Image variable
        self.orig = cv2.imread(input_image)
        if self.orig.shape[0] > self.orig.shape[1]:  # 判斷寬是否大於高
            # Convert to PIL image for rotation
            pil_image = Image.fromarray(cv2.cvtColor(self.orig, cv2.COLOR_BGR2RGB))
            pil_image = pil_image.transpose(Image.ROTATE_90)
            self.orig = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            # print(f"{self.image_name} is Turn landscape")
        else:
            pass
        self.image = self.orig.copy()
        self.check_point_output = self.orig.copy()
        self.border_output = self.orig.copy()
        self.transform_output = self.orig.copy()
        self.tmp_output = self.orig.copy()

        # Original image size
        self.height = self.image.shape[0]
        self.width = self.image.shape[1]

        #
        self.location_point_min_size = self.width // 150
        self.location_point_max_size = self.width // 30
        self.circle_size = int(self.width * 0.01)

        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        self.blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)
        # cv2.imwrite(os.path.join("t", 'blurred.jpg'), self.blurred)

        self.orig_edged = cv2.Canny(self.blurred, 0, 50)
        cv2.imwrite(os.path.join("note/edged_0", f'{self.image_name}_edged.jpg'), self.orig_edged)

        self.edged = self.orig_edged.copy()

        self.center_y = self.height // 2
        self.center_x = self.width // 2

    def rotate_image(self):
        # Convert to PIL image for rotation
        pil_image = Image.fromarray(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
        pil_image = pil_image.transpose(Image.ROTATE_270)
        self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _opening(self, edged, erode_iterations, dilate_iterations, erode_enchor=(3, 3), dilate_enchor=(3, 3)):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, erode_enchor)
        erosion = cv2.erode(src=edged, kernel=kernel, iterations=erode_iterations)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilate_enchor)
        dilation = cv2.dilate(src=erosion, kernel=kernel,
                              iterations=dilate_iterations)
        return dilation

    def get_h_conv(self, image):
        feature = np.array([
            [0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0],
        ])

        conv_h = signal.convolve2d(image / 255, feature, mode='same')

        orig_conv_h = conv_h.copy()
        conv_h[conv_h < 6] = 0
        conv_h = (conv_h / 6 * 255).astype(np.uint8)
        # cv2.imwrite(os.path.join("t", 'conv_h.jpg'), conv_h)
        dilation = cv2.dilate(src=conv_h, kernel=cv2.getStructuringElement(
            cv2.MORPH_RECT, (5, 5)), iterations=1)
        # cv2.imwrite(os.path.join("t", 'conv_h_dilate.jpg'), dilation)
        return dilation

    def get_grid(self, proc_image):
        ### --- Sliding window size defination

        window_height = int(self.height * 0.005)
        window_width = int(self.width * 0.02)
        self.window_height = window_height
        self.window_width = window_width

        window_area = window_height * window_width
        threshold_ratio = 0.08

        ### 找到 sliding windows 起點
        start_points = []
        section = []
        for y in range(0, self.height, window_height // 2):
            cur_window = proc_image[y: y + window_height,
                         self.center_x - window_width // 2: self.center_x + window_width // 2]
            point_cnt = np.count_nonzero(cur_window)

            if point_cnt > int(window_area * threshold_ratio):
                top_left = (self.center_x - window_width // 2, y)
                top_right = (self.center_x + window_width // 2, y)
                bottom_left = (self.center_x - window_width // 2, y + window_height)
                bottom_right = (self.center_x + window_width // 2, y + window_height)
                pts = np.array([top_left, top_right, bottom_right, bottom_left])

                section.append({
                    'area': point_cnt,
                    'window': cur_window,
                    'pts': pts,
                    'top_y': y,
                    'bottom_y': y + window_height,
                    'center': (self.center_x, y + window_height // 2)
                })
            elif section:
                max_area_window = max(section, key=lambda x: x['area'])

                pts = max_area_window['pts'].reshape((-1, 1, 2))
                cv2.polylines(self.tmp_output, [pts], True, (0, 0, 255), 1)

                start_points.append(max_area_window)
                section = []

        h_results = []
        for start_point in start_points:
            last_point_center = start_point['center']

            # 往左
            left = []
            for x in range(start_point['center'][0] - window_width, window_width, -window_width):
                section = []
                for y in range(last_point_center[1] - window_height, last_point_center[1] + window_height, 1):
                    cur_window = proc_image[y: y + window_height,
                                 x - window_width // 2: x + window_width // 2]
                    point_cnt = np.count_nonzero(cur_window)

                    if point_cnt > int(window_area * threshold_ratio):
                        top_left = (x - window_width // 2, y)
                        top_right = (x + window_width // 2, y)
                        bottom_left = (x - window_width // 2, y + window_height)
                        bottom_right = (x + window_width // 2, y + window_height)
                        pts = np.array(
                            [top_left, top_right, bottom_right, bottom_left])

                        section.append({
                            'area': point_cnt,
                            'window': cur_window,
                            'pts': pts,
                            'top_y': y,
                            'bottom_y': y + window_height,
                            'center': (x, y + window_height // 2)
                        })
                if section:
                    max_area_window = max(section, key=lambda x: x['area'])
                    last_point_center = max_area_window['center']
                    left.append(max_area_window)
                else:
                    break

            # 往右
            right = []
            for x in range(start_point['center'][0] + window_width, self.width - window_width, window_width):
                section = []
                for y in range(last_point_center[1] - window_height, last_point_center[1] + window_height, 1):
                    cur_window = proc_image[y: y + window_height,
                                 x - window_width // 2: x + window_width // 2]
                    point_cnt = np.count_nonzero(cur_window)

                    if point_cnt > int(window_area * threshold_ratio):
                        top_left = (x - window_width // 2, y)
                        top_right = (x + window_width // 2, y)
                        bottom_left = (x - window_width // 2, y + window_height)
                        bottom_right = (x + window_width // 2, y + window_height)
                        pts = np.array(
                            [top_left, top_right, bottom_right, bottom_left])

                        section.append({
                            'area': point_cnt,
                            'window': cur_window,
                            'pts': pts,
                            'top_y': y,
                            'bottom_y': y + window_height,
                            'center': (x, y + window_height // 2)
                        })
                if section:
                    max_area_window = max(section, key=lambda x: x['area'])
                    last_point_center = max_area_window['center']
                    right.append(max_area_window)
                else:
                    break

            cnt = len(left) + len(right)
            if abs(len(left) - len(right)) <= 6 and cnt >= 20 and cnt <= 46:
                h_results.append({
                    'left_cnt': len(left),
                    'right_cnt': len(right),
                    'cnt': cnt,
                    'left': left,
                    'right': right,
                    'center_point': start_point,
                })

        h_results = sorted(h_results, key=lambda x: x['cnt'])

        if not h_results:
            self.no_match_grid = False
            if len(h_results) < 18:
                self.no_match_grid = True
            return {
                'right_top': None,
                'right_bottom': None,
                'left_top': None,
                'left_bottom': None
            }

        # 排除過長過短的水平線
        s_index = 0
        for i in range(len(h_results) // 2, 0, -1):
            if h_results[i]['cnt'] - h_results[i - 1]['cnt'] >= 3:
                s_index = i
                break
        e_index = len(h_results)
        for i in range(len(h_results) // 2, len(h_results) - 1):
            if h_results[i + 1]['cnt'] - h_results[i]['cnt'] >= 3:
                e_index = i + 1
                break

        h_results = sorted(h_results[s_index: e_index],
                           key=lambda x: x['center_point']['center'][1])

        # 排除長度不連續的水平線
        s_index = 0
        for i in range(len(h_results) // 2, 0, -1):
            if abs(h_results[i]['cnt'] - h_results[i - 1]['cnt']) >= 4:
                s_index = i
                break
        e_index = len(h_results)
        for i in range(len(h_results) // 2, len(h_results) - 1):
            if abs(h_results[i + 1]['cnt'] - h_results[i]['cnt']) >= 4:
                e_index = i + 1
                break

        h_results = h_results[s_index: e_index]

        for r in h_results:
            for p in r['left']:
                pts = p['pts'].reshape((-1, 1, 2))
                cv2.polylines(self.tmp_output, [pts], True, (0, 0, 255), 1)
            for p in r['right']:
                pts = p['pts'].reshape((-1, 1, 2))
                cv2.polylines(self.tmp_output, [pts], True, (0, 0, 255), 1)
            pts = r['center_point']['pts'].reshape((-1, 1, 2))
            cv2.polylines(self.tmp_output, [pts], True, (0, 0, 255), 1)

        grid_right_top = h_results[0]['right'][-1]['center']
        grid_right_bottom = h_results[-1]['right'][-1]['center']
        grid_left_top = h_results[0]['left'][-1]['center']
        grid_left_bottom = h_results[-1]['left'][-1]['center']
        cv2.circle(self.tmp_output, grid_right_top, self.circle_size, (255, 255, 0), -1)
        cv2.circle(self.tmp_output, grid_right_bottom, self.circle_size, (255, 255, 0), -1)
        cv2.circle(self.tmp_output, grid_left_top, self.circle_size, (255, 255, 0), -1)
        cv2.circle(self.tmp_output, grid_left_bottom, self.circle_size, (255, 255, 0), -1)
        # cv2.imwrite(os.path.join('./grid', f'grid_{filename}.jpg'), self.tmp_output)
        self.no_match_grid = False
        if len(h_results) < 18:
            self.no_match_grid = True

        return {
            'right_top': grid_right_top,
            'right_bottom': grid_right_bottom,
            'left_top': grid_left_top,
            'left_bottom': grid_left_bottom
        }

    def get_location_points(self, output_path):
        ### TODO: -----
        ### Location point

        bi_filter = cv2.bilateralFilter(self.gray, 0, 125, 5)
        # cv2.imwrite(os.path.join(
        #     output_path, 'bi_filter.jpg'), bi_filter)
        filter_edged = cv2.Canny(bi_filter, 0, 30)
        # cv2.imwrite(os.path.join(output_path, f'filter_edged{filename}.jpg'), filter_edged)

        self.opened = self._opening(filter_edged, 1, 2, erode_enchor=(1, 1))

        # cv2.imwrite(os.path.join(output_path, f'filter_opened{filename}.jpg'), self.opened)

        def get_possible_checkpoints(image, opened, x_offset=0, color=(0, 255, 0)):
            checkpoints = []
            contours, h = cv2.findContours(
                opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cont in contours:
                area = cv2.contourArea(cont)
                if area > (self.location_point_min_size ** 2) and area < (self.location_point_max_size ** 2):
                    arc_len = cv2.arcLength(cont, True)
                    approx = cv2.approxPolyDP(cont, 0.05 * arc_len, True)
                    if len(approx) == 4:
                        x = []
                        y = []
                        for p in approx:
                            x.append(p[0][0])
                            y.append(p[0][1])
                        max_x = max(x)
                        min_x = min(x)
                        max_y = max(y)
                        min_y = min(y)
                        if (max_x - min_x) > self.location_point_min_size and (
                                max_x - min_x) < self.location_point_max_size and (
                                max_y - min_y) > self.location_point_min_size and (
                                max_y - min_y) < self.location_point_max_size:
                            cv2.drawContours(image, [cont], -1, color, 5)
                            cont[:, 0, 0] += x_offset
                            checkpoints.append(cont)
            return checkpoints

        left_checkpoints = get_possible_checkpoints(
            self.image[:, :self.width // 2], self.opened[:, :self.width // 2])
        right_checkpoints = get_possible_checkpoints(
            self.image[:, self.width // 2:], self.opened[:, self.width // 2:], x_offset=self.width // 2)
        # cv2.imwrite(os.path.join(output_path, "contours.jpg"), self.image)
        # cv2.imwrite(os.path.join("contours", f"contours{self.image_name}.jpg"), self.image)
        return {
            'left': left_checkpoints,
            'right': right_checkpoints
        }

    def get_borders(self):
        ### -----
        ### Border

        border_right = []
        border_left = []

        self.no_match_border = True

        contours, h = cv2.findContours(
            self.opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        border = None
        for cont in contours:
            area = cv2.contourArea(cont)
            if area > (self.width * 0.6) * (self.height * 0.6):
                arc_len = cv2.arcLength(cont, True)
                approx = cv2.approxPolyDP(cont, 0.1 * arc_len, True)
                if len(approx) == 4:
                    for p in approx:
                        if p[0][0] > self.width // 2:
                            border_right.append(list(p[0]))
                        else:
                            border_left.append(list(p[0]))
                    border = cont
        if not border_right or not border_left:
            border_right_top = (self.width - 225, 150)
            border_right_bottom = (self.width - 225, self.height - 150)
            border_left_top = (225, 150)
            border_left_bottom = (225, self.height - 150)
        else:
            border_right_top, border_right_bottom = sorted(
                border_right, key=lambda x: x[1])
            border_left_top, border_left_bottom = sorted(
                border_left, key=lambda x: x[1])
            cv2.drawContours(
                self.image, [border], -1, (0, 0, 255), 3)
            self.no_match_border = False

        # image_with_border = self.image.copy()

        # Draw borders on the image copy
        # cv2.line(image_with_border, border_right_top, border_right_bottom, (255, 105, 0), 2)
        # cv2.line(image_with_border, border_left_top, border_left_bottom, (255, 105, 0), 2)
        #
        # cv2.imwrite(os.path.join("borders", f"border{filename}.jpg"), self.image)
        return {
            'right_top': border_right_top,
            'right_bottom': border_right_bottom,
            'left_top': border_left_top,
            'left_bottom': border_left_bottom
        }

    def _cal_distance(self, a, b):
        x_diff = (a[0] - b[0]) / self.width
        y_diff = (a[1] - b[1]) / self.height
        return ((x_diff ** 2) + (y_diff ** 2)) * 1000

    def _get_center(self, a, b):
        x_diff = (a[0] - b[0]) // 2
        y_diff = (a[1] - b[1]) // 2
        return (b[0] + x_diff, b[1] + y_diff)

    def get_base_points(self, output_path, grid, borders):
        if self.no_match_grid and self.no_match_border:
            # base_right_top = borders['right_top']
            # base_right_bottom = borders['right_bottom']
            # base_left_top = borders['left_top']
            # base_left_bottom = borders['left_bottom']
            # print(f"{filename}a")
            return False
        elif self.no_match_grid and not self.no_match_border:
            # 邊框可參考
            # base_right_top = border_right_top
            # base_right_bottom = border_right_bottom
            # base_left_top = border_left_top
            # base_left_bottom = border_left_bottom
            # print(f"{filename}b")
            base_right_top = [borders['right_top'][0] - self.window_width,
                              borders['right_top'][1] + self.window_height]
            base_right_bottom = [borders['right_bottom'][0] - self.window_width,
                                 borders['right_bottom'][1] - self.window_height]
            base_left_top = [borders['left_top'][0] + self.window_width,
                             borders['left_top'][1] + self.window_height]
            base_left_bottom = [borders['left_bottom'][0] + self.window_width,
                                borders['left_bottom'][1] - self.window_height]
        elif not self.no_match_grid and self.no_match_border:
            # print(f"{filename}c")
            # 格線可參考
            base_right_top = [grid['right_top'][0] + self.window_width,
                              grid['right_top'][1] - self.window_height]
            base_right_bottom = [grid['right_bottom'][0] + self.window_width,
                                 grid['right_bottom'][1] + self.window_height]
            base_left_top = [grid['left_top'][0] - self.window_width,
                             grid['left_top'][1] - self.window_height]
            base_left_bottom = [grid['left_bottom'][0] - self.window_width,
                                grid['left_bottom'][1] + self.window_height]
        else:
            # print(f"{filename}d")
            # 皆可參考
            base_right_top = self._get_center(
                grid['right_top'], borders['right_top'])
            base_right_bottom = self._get_center(
                grid['right_bottom'], borders['right_bottom'])
            base_left_top = self._get_center(
                grid['left_top'], borders['left_top'])
            base_left_bottom = self._get_center(
                grid['left_bottom'], borders['left_bottom'])

        cv2.circle(self.tmp_output, tuple(base_right_top),
                   self.circle_size, (255, 0, 255), -1)
        cv2.circle(self.tmp_output, tuple(base_right_bottom),
                   self.circle_size, (255, 0, 255), -1)
        cv2.circle(self.tmp_output, tuple(base_left_top),
                   self.circle_size, (255, 0, 255), -1)
        cv2.circle(self.tmp_output, tuple(base_left_bottom),
                   self.circle_size, (255, 0, 255), -1)
        # cv2.imwrite(os.path.join(output_path, "border.jpg"), self.tmp_output)
        cv2.imwrite(os.path.join("note/base_point", f"base_point{self.image_name}.jpg"), self.tmp_output)
        pts = np.array(
            [borders['right_top'], borders['right_bottom'], borders['left_top'], borders['left_bottom']])
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(self.tmp_output, [pts], True, (0, 255, 255), 5)
        # cv2.imwrite(os.path.join(output_path, "border.jpg"), self.image)
        # cv2.imwrite(os.path.join("border", f"border{self.image_name}.jpg"), self.tmp_output)
        return {
            'right_top': base_right_top,
            'right_bottom': base_right_bottom,
            'left_top': base_left_top,
            'left_bottom': base_left_bottom
        }

    def get_result(self, output_path, location_points, base_points):
        ### TODO: -----
        ### Remove points

        def get_fix_point(checkpoints, base_point):
            tmp = 1e10
            point = None
            contour = None
            for cont in checkpoints:
                m = cv2.moments(cont)
                cx = int(m["m10"] / m["m00"])
                cy = int(m["m01"] / m["m00"])
                d = self._cal_distance([cx, cy], base_point)
                # print(d)
                if d < tmp:
                    tmp = d
                    point = [cx, cy]
                    contour = cont
            return point, contour

        def locate_corner(self, point, contour, corner_name):
            if point is not None and contour is not None:
                x, y, w, h = cv2.boundingRect(contour)
                cropped_image = self.orig[y:y + h, x:x + w]
                _, binary_image = cv2.threshold(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY), 0, 255,
                                                cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                binary_image = binary_image[10:-10, 10:-10]
                total_pixels = binary_image.shape[0] * binary_image.shape[1]
                black_pixels = total_pixels - cv2.countNonZero(binary_image)
                black_ratio = black_pixels / total_pixels
                # print(f"{corner_name} black pixel ratio:", black_ratio)

                # cv2.imwrite(output_path + f"_{corner_name}_binary.jpg", binary_image)
                return black_ratio

        def check_need_reverse(LT, LB, RT, RB):
            corner_ratios = {"left_top": LT, "left_bottom": LB, "right_top": RT, "right_bottom": RB}
            min_corner = min(corner_ratios, key=corner_ratios.get)
            return min_corner != "left_bottom"

        # print("Left-top")
        point_left_top, contour_left_top = get_fix_point(
            location_points['left'], base_points['left_top'])

        # print("Left-bottom")
        point_left_bottom, contour_left_bottom = get_fix_point(
            location_points['left'], base_points['left_bottom'])

        # print("Right-top")
        point_right_top, contour_right_top = get_fix_point(
            location_points['right'], base_points['right_top'])

        # print("Right-bottom")
        point_right_bottom, contour_right_bottom = get_fix_point(
            location_points['right'], base_points['right_bottom'])

        # Check conditions
        if point_left_top is not None:
            cv2.circle(self.tmp_output, tuple(point_left_top),
                       self.circle_size, (1, 227, 254), -1)
        if point_left_bottom is not None:
            cv2.circle(self.tmp_output, tuple(point_left_bottom),
                       self.circle_size, (1, 227, 254), -1)
        if point_right_top is not None:
            cv2.circle(self.tmp_output, tuple(point_right_top),
                       self.circle_size, (1, 227, 254), -1)
        if point_right_bottom is not None:
            cv2.circle(self.tmp_output, tuple(point_right_bottom),
                       self.circle_size, (1, 227, 254), -1)

        if (point_left_top[1] < base_points['left_top'][1]) != (point_right_top[1] < base_points['right_top'][1]):
            return False

        if (point_left_bottom[1] < base_points['left_bottom'][1]) != (
                point_right_bottom[1] < base_points['right_bottom'][1]):
            return False

        LT = locate_corner(self, point_left_top, contour_left_top, "left_top")
        LB = locate_corner(self, point_left_bottom, contour_left_bottom, "left_bottom")
        RT = locate_corner(self, point_right_top, contour_right_top, "right_top")
        RB = locate_corner(self, point_right_bottom, contour_right_bottom, "right_bottom")

        self.NEED_REVERSE = check_need_reverse(LT, LB, RT, RB)

        cv2.imwrite(os.path.join("note/result", f"res{self.image_name}.jpg"), self.tmp_output)
        return {
            'right_top': point_right_top,
            'right_bottom': point_right_bottom,
            'left_top': point_left_top,
            'left_bottom': point_left_bottom,
        }

    def transform(self, output_dir, points):
        ### TODO: -----
        ### Transform

        WIDTH = 2000
        HEIGHT = 1380
        MARGIN = 0

        corners = np.array(
            [
                [[MARGIN, MARGIN]],
                [[MARGIN, HEIGHT + MARGIN]],
                [[WIDTH + MARGIN, HEIGHT + MARGIN]],
                [[WIDTH + MARGIN, MARGIN]],
            ]
        )

        pts_dst = np.array(corners, np.float32)

        def transform(src, dst, image):
            h, status = cv2.findHomography(src, dst)
            out = cv2.warpPerspective(
                image, h, (int(WIDTH + MARGIN * 2), int(HEIGHT + MARGIN * 2)))
            return out

        t = transform(np.array([points['left_top'], points['left_bottom'], points['right_bottom'],
                                points['right_top']], dtype=np.float32), pts_dst, self.transform_output)

        return t
        # res_path = "output_"
        # if not os.path.exists(res_path):
        #     os.mkdir(res_path)
        # cv2.imwrite(os.path.join("t", f'{filename}.jpg'), t)
        # cv2.imwrite(os.path.join(output_dir, f'{filename}.jpg'), t)

    def run(self, output_path):
        h_conv = self.get_h_conv(self.edged)
        grid = self.get_grid(h_conv)
        location_points = self.get_location_points(output_path)
        borders = self.get_borders()
        base_points = self.get_base_points(output_path, grid, borders)
        if base_points:
            result = self.get_result(output_path, location_points, base_points)
            if result:
                file = self.transform(output_path, result)
                if self.NEED_REVERSE:
                    file = cv2.rotate(file, cv2.ROTATE_180)
                    # print(f"{self.image_name} is REVERSED.")
                cv2.imwrite(os.path.join(output_path, f'{self.image_name}.jpg'), file)
            else:
                # print(f"Transform_Failed")
                return 1
            return True
        else:
            # print("can't find base_points")
            return 2


import os
import shutil

# if __name__ == "__main__":
#     input_dir = "./UIimage/UI_20"
#     output_dir = "./v4_UI_20_0601"
#
#     for root, dirs, files in os.walk(input_dir):
#         for f in files:
#             inputpath = os.path.join(root, f)
#             filename = os.path.splitext(f)[0]
#             print(filename)
#             # 創建資料夾
#             # 執行轉換操作
#             t = Transformer(inputpath)
#             print(inputpath)
#             success = t.run(output_dir)
