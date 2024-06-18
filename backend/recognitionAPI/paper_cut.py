import itertools
import logging
import os
import shutil
import cv2
import numpy as np
import image_process_p
from scipy import signal
from sklearn.linear_model import LinearRegression


class GridSplitPaper():
    """切割器

    Attributes:
        writeDebugFile      當發生警告時，是否要輸出除錯用檔案
        crop                預先裁剪圖檔((y1, y2), (x1, x2))
        skipLine            跳過的行編號，用於中間有空行的作文紙，例如 https://img.ruten.com.tw/s1/9/bf/cf/21516049873871_232.jpg
        Canny_threshold1    邊緣偵測函數 cv2.Canny 的參數 threshold1
        Canny_threshold2    邊緣偵測函數 cv2.Canny 的參數 threshold1
        Canny_apertureSize  邊緣偵測函數 cv2.Canny 的參數 apertureSize
        minPointRatioH      當一條橫線上的黑點數超過直線的幾分之一才會列入候選線
        HLineMaxDistance    垂直距離上相鄰多遠(px)的橫線能被視為同一條橫線
        minPointRatioV      當一條直線上的黑點數超過直線的幾分之一才會列入候選線
        VLineMaxDistance    水平距離上相鄰多遠(px)的直線能被視為同一條直線
    """
    writeDebugFile = False
    crop = None
    skipLine = []
    Canny_threshold1 = 20
    Canny_threshold2 = 100
    Canny_apertureSize = 3
    minPointRatioH = 6
    HLineMaxDistance = 10
    minPointRatioV = 6
    VLineMaxDistance = 5
    withRemoveBorderLine = None
    skipBopomofo = True
    _ext = None
    outputpath = None
    filename = None

    def __init__(self, HLine, VLine, girdWidth1, girdWidth2, girdHeight):
        """
        初始化切割器

        Parameters:
            int HLine: 作文紙橫線數量（不是列數，應該是個奇數）
            int VLine: 作文紙直線數量（不是行數，應該是個奇數）
            int girdWidth1: 國字格子寬度
            int girdWidth2: 注音格子寬度
            int girdHeight: 國字格子高度
        Return None
        """
        self.HLine = HLine
        self.VLine = VLine
        self.girdWidth1 = girdWidth1
        self.girdWidth2 = girdWidth2
        self.girdHeight = girdHeight

    def _writefile(self, image, filename):
        newpath = self.outputpath + "/_" + self.filename + filename + self._ext

        if not os.path.exists(os.path.dirname(newpath)):
            os.makedirs(os.path.dirname(newpath))

        logging.debug("writefile to %s", newpath)
        cv2.imwrite(newpath, image)

    def _writedir(self, image, outputpath, filename):
        try:
            if image is None:
                logging.error("Image is None. Cannot write to file.")
                return False

            if not os.path.exists(outputpath):
                os.makedirs(outputpath)

            newpath = os.path.join(outputpath, filename + self._ext)
            logging.debug("writefile to %s", newpath)
            cv2.imwrite(newpath, image)
            return True
        except cv2.error as e:
            logging.error("OpenCV error occurred: %s", e)
            return False

    def _line(self, p1, p2):
        A = (p1[1] - p2[1])
        B = (p2[0] - p1[0])
        C = (p1[0] * p2[1] - p2[0] * p1[1])
        return A, B, -C

    def _intersection(self, L1, L2):
        D = L1[0] * L2[1] - L1[1] * L2[0]
        Dx = L1[2] * L2[1] - L1[1] * L2[2]
        Dy = L1[0] * L2[2] - L1[2] * L2[0]
        if D != 0:
            x = Dx / D
            y = Dy / D
            return x, y
        else:
            return False

    def _tryremoveH(self, lines):
        removeCnt = len(lines) - self.HLine
        minRemoveIdxs = None
        minWeight = 100000000
        for removeIdxs in itertools.combinations(list(range(len(lines))), removeCnt):
            tryRemove = lines[:]
            for idx in removeIdxs[::-1]:
                del tryRemove[idx]
            weight = 0
            for i in range(len(tryRemove) - 1):
                weight += (tryRemove[i + 1]
                           - tryRemove[i] - self.girdHeight) ** 2
            if weight < minWeight:
                minWeight = weight
                minRemoveIdxs = removeIdxs
        return minRemoveIdxs

    def _tryremoveV(self, lines):
        removeCnt = len(lines) - self.VLine
        minRemoveIdxs = None
        minHeight = 100000000
        for removeIdxs in itertools.combinations(list(range(len(lines))), removeCnt):
            tryRemove = lines[:]
            for idx in removeIdxs[::-1]:
                del tryRemove[idx]
            height = 0
            for i in range(len(tryRemove) - 1):
                if i % 2 == 0:
                    height += (tryRemove[i + 1]
                               - tryRemove[i] - self.girdWidth1) ** 2
                else:
                    height += (tryRemove[i + 1]
                               - tryRemove[i] - self.girdWidth2) ** 2
            if height < minHeight:
                minHeight = height
                minRemoveIdxs = removeIdxs
        return minRemoveIdxs

    def splitimg(self, img, rowoffset=0, crop=None):
        """
        將圖檔按格線切割成每個字一個圖檔

        Parameters:
            numpy.ndarray img: 輸入檔案路徑
            int rowoffset: 輸出檔案編號偏移，如果是AB卷的B卷，應該設定為A卷的行數
            ((int, int), (int, int)) crop: 預先裁剪圖檔((y1, y2), (x1, x2))

        Return False or (str => numpy.ndarray)dict:
            失敗回傳 False
            成功回傳 numpy.ndarray 的字典，key 為行列編號(str)，value 為圖檔(numpy.ndarray)
        """
        isWarning = False
        if crop is None and self.crop is not None:
            crop = self.crop

        if crop:
            img = img[crop[0][0]:crop[0][1], crop[1][0]:crop[1][1]]

        minPointV = img.shape[0] // self.minPointRatioV
        minPointH = img.shape[1] // self.minPointRatioH

        height, width, _ = img.shape

        imglineonly = np.zeros((height, width), np.uint8)
        imgori = np.copy(img)
        imggrid = np.copy(imgori)

        # logging.debug("Filtering gray point")

        # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # lower_gray = np.array([0,0,0])
        # upper_gray = np.array([255,64,180])
        # mask = cv2.inRange(hsv, lower_gray, upper_gray)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # img = cv2.bitwise_or(img, mask)

        # logging.debug("Filter gray done")
        # self.__writefile(img, "_gray")

        # https://docs.opencv.org/3.1.0/dd/d1a/group__imgproc__feature.html#ga04723e007ed888ddf11d9ba04e2232de
        edges = cv2.Canny(
            image=img,
            threshold1=self.Canny_threshold1,
            threshold2=self.Canny_threshold2,
            apertureSize=self.Canny_apertureSize
        )

        # cv2.imshow("Canny", cv2.resize(edges, (int(width/2), int(height/2))))
        # cv2.imshow("Canny", edges)

        # self.__writefile(edges, "_ed")

        # pix = edges.load()
        height = len(edges)
        width = len(edges[0])
        logging.debug("shape %s %s", height, width)

        def insert_points_between_gaps(fix_type, values, average_gap, lines, distance, max_difference):
            new_x_values = []
            if fix_type == "row":
                if lines == self.VLine:
                    if int(values[0] / distance) >= 1:
                        for i in range(int(values[0] / distance), 0, -1):
                            new_x_values.append(values[0] - i * (distance + 1))

                for i in range(len(values) - 1):  # 遍歷 x 值列表，檢查並插入點
                    gap = values[i + 1] - values[i]  # 計算相鄰 x 值之間的差值
                    new_x_values.append(values[i])  # 添加原始 x 值

                    if gap > max_difference:  # 如果兩個 y 值之間的差值大於 max_difference，插入一個新的點
                        num_points_to_insert = int(gap / int(average_gap + 5))  # 計算應該插入的點的數量
                        for j in range(1, num_points_to_insert + 1):
                            new_x_values.append(values[i] + j * (int(average_gap + 1)))  # 插入新的點

                new_x_values.append(values[-1])  # 添加最後一個 y 值

                if lines == self.VLine:
                    if int(new_x_values[-1] / distance) < self.HLine:
                        for j in range(1, lines - int(new_x_values[-1] / distance)):
                            new_x_values.append(values[-1] + j * distance)

                if lines == self.HLine:
                    if (values[len(values) - 1] - values[0]) / distance < lines:
                        for j in range(lines - len(new_x_values)):
                            new_x_values.append(values[len(values) - 1])
                # print(new_x_values)
                return new_x_values
            elif fix_type == "col":
                new_x_values = []
                if lines == self.VLine and values[0] != values[1]:
                    if int(values[0] / distance) >= 1:
                        if (values[1] - values[0]) > (self.girdWidth2 + 3):
                            for i in range(int(values[0] / (distance + self.girdWidth2)), 0, -1):
                                if i != int(values[0] / (distance + self.girdWidth2)):
                                    new_x_values.append(
                                        values[0] - i * (distance + self.girdWidth2 - 1) - self.girdWidth2)
                                    new_x_values.append(values[0] - i * (distance + self.girdWidth2 - 1))
                                else:
                                    new_x_values.append(values[0] - i * (distance + self.girdWidth2 - 1))
                            new_x_values.append(values[0] - self.girdWidth2)
                        else:
                            for i in range(int(values[0] / (distance + self.girdWidth2)), 0, -1):
                                if i != int(values[0] / (distance + self.girdWidth2)):
                                    new_x_values.append(values[0] - i * (distance + self.girdWidth2 - 1))
                                    new_x_values.append(
                                        values[0] - i * (distance + self.girdWidth2 - 1) + self.girdWidth2)

                                else:
                                    new_x_values.append(
                                        values[0] - i * (distance + self.girdWidth2 - 1) + self.girdWidth2)

                for i in range(len(values) - 1):  # 遍歷 x 值列表，檢查並插入點
                    gap = values[i + 1] - values[i]  # 計算相鄰 x 值之間的差值
                    new_x_values.append(values[i])  # 添加原始 x 值

                    if gap > max_difference:  # 如果兩個 y 值之間的差值大於 max_difference，插入一個新的點
                        num_points_to_insert = int(gap / int(average_gap + 5))  # 計算應該插入的點的數量
                        for j in range(1, num_points_to_insert + 1):
                            new_x_values.append(values[i] + j * (int(average_gap)))  # 插入新的點
                new_x_values.append(values[-1])  # 添加最後一個 y 值
                # print("b")
                if int(values[-1] / distance) < lines and values[-1] != values[-2]:
                    if (int(values[-1] - values[-2])) > (self.girdWidth2 + 3):
                        for j in range(1, int((lines - len(new_x_values) + 1) / 2)):
                            new_x_values.append(values[-1] + j * (self.girdWidth2 + distance - 1) - distance)
                            new_x_values.append(values[-1] + j * (self.girdWidth2 + distance - 1))

                        new_x_values.append(new_x_values[-1] + self.girdWidth2)
                    else:
                        for j in range(1, int((lines - len(new_x_values) + 1) / 2)):
                            new_x_values.append(values[-1] + j * (self.girdWidth2 + distance - 1) - self.girdWidth2)
                            new_x_values.append(values[-1] + j * (self.girdWidth2 + distance - 1))

                # if lines == self.HLine:
                #     if int(new_x_values[-1] / distance) < lines:
                #         for j in range(1, lines - int(new_x_values[-1] / distance)):
                #             new_x_values.append(values[-1] + j * distance)

                if lines == self.VLine:
                    if (values[len(values) - 1] - values[0]) / distance < lines:
                        for j in range(lines - len(new_x_values)):
                            new_x_values.append(values[len(values) - 1])
                # print(new_x_values)
                return new_x_values

        logging.debug("HPoints start")

        feature = np.array([
            [0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0],
        ])

        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.convolve2d.html
        res = signal.convolve2d(edges / 255, feature, mode='same')

        filtered_points = np.where(res >= 6)

        unique, counts = np.unique(filtered_points[0], return_counts=True)
        # filter points more than "minPointH"
        temp = np.where(counts > minPointH)
        filtered_H = np.take(unique, temp)[0]
        HPointCnt = dict(zip(unique, counts))  # convert to dict H=>Count

        logging.debug("HPoints end")
        logging.debug("HLine start")

        for i in range(len(filtered_points[0])):
            imglineonly[filtered_points[0][i], filtered_points[1][i]] = 255

        HGroup = []
        tempGroup = []
        if len(filtered_H):
            lasth = filtered_H[0]
            for h in np.concatenate((filtered_H, [10000000])):
                if h > lasth + self.HLineMaxDistance:
                    HGroup.append(tempGroup)
                    tempGroup = []
                tempGroup.append(h)
                lasth = h

        HPoints = dict(zip(list(range(height)), [[] for i in range(height)]))
        for i in range(len(filtered_points[0])):
            HPoints[filtered_points[0][i]].append(filtered_points[1][i])

        HLines = []
        for group in HGroup:
            X = []
            Y = []
            for h in group:
                X.extend(HPoints[h])
                Y.extend([h] * HPointCnt[h])

            reg = LinearRegression().fit(np.array(X).reshape(-1, 1), np.array(Y).reshape(-1, 1))
            point1 = (0, int(reg.intercept_[0] + 0.5))
            point2 = (
                width - 1, int(reg.coef_[0][0] * (width - 1) + reg.intercept_[0] + 0.5))
            HLines.append((point1, point2))

        x_values_point1 = []
        x_values_point2 = []
        y_values_point1 = []
        y_values_point2 = []

        for line in HLines:
            x_values_point1.append(line[0][0])  # point1 的 x 值
            x_values_point2.append(line[1][0])  # point2 的 x 值
            y_values_point1.append(line[0][1])  # point1 的 y 值
            y_values_point2.append(line[1][1])  # point2 的 y 值

        new_x_values_point1 = []
        new_x_values_point2 = []
        new_y_values_point1 = []
        new_y_values_point2 = []
        new_HLines = []

        if len(x_values_point1) < self.HLine:
            new_x_values_point1 = insert_points_between_gaps("row", x_values_point1, self.girdHeight, self.HLine,
                                                             self.girdHeight, 80)
            new_x_values_point2 = insert_points_between_gaps("row", x_values_point2, self.girdHeight, self.HLine,
                                                             self.girdHeight, 80)
        if len(y_values_point1) < self.HLine:
            new_y_values_point1 = insert_points_between_gaps("row", y_values_point1, self.girdHeight, self.VLine,
                                                             self.girdHeight, 80)
            new_y_values_point2 = insert_points_between_gaps("row", y_values_point2, self.girdHeight, self.VLine,
                                                             self.girdHeight, 80)
        # print("a")
        # print(new_x_values_point1)
        # print(new_x_values_point2)
        # print(new_y_values_point1)
        # print(new_y_values_point2)
        try:
            for i in range(0, len(new_x_values_point1)):
                new_HLines.append(
                    (
                    (new_x_values_point1[i], new_y_values_point1[i]), (new_x_values_point2[i], new_y_values_point2[i])))
        except IndexError:
            return False
        # print(HLines)
        # print(new_HLines)
        for line in HLines:
            cv2.line(imglineonly, line[0], line[1], (255, 255, 255), 2)  # 在 imglineonly 上繪製直線

        logging.debug("HLine end")

        if len(HLines) < self.HLine:
            logging.warning(
                "Find HLine Fail, expected %s but %s. Trying to add line.", self.HLine, len(HGroup))
            # self._writefile(imglineonly, "_lineonly")
            HLines = new_HLines
            for HLine in HLines:
                cv2.line(imggrid, HLine[0], HLine[1], (0, 0, 255), 3)
            # self._writefile(imggrid, "_grid")
            # self._writefile(imgori, "_ori")
            isWarning = True
            self.isWarning = isWarning
        # print(len(HLines))
        if len(HLines) > self.HLine:
            logging.warning(
                "Find HLine Fail, expected %s but %s. Trying to remove noise line.", self.HLine, len(HLines))
            lineCenter = []
            for HLine in HLines:
                lineCenter.append((HLine[0][1] + HLine[1][1]) / 2)

            removeIdxs = self._tryremoveH(lineCenter)
            for idx in removeIdxs[::-1]:
                logging.info("Remove line %s (idx=%s).", HLines[idx], idx)
                logging.info("Remove noise line on origin image")
                for w in range(width):
                    h = int((HLines[idx][1][1] - HLines[idx][0][1])
                            / (HLines[idx][1][0] - HLines[idx][0][0]) * w + HLines[idx][0][1])
                    imgori[h, w] = np.mean(
                        (imgori[h - 2, w], imgori[h - 1, w], imgori[h + 1, w], imgori[h + 2, w]), axis=0)
                del HLines[idx]
            isWarning = True
            self.isWarning = isWarning

        for HLine in HLines:
            cv2.line(imggrid, HLine[0], HLine[1], (0, 0, 255), 3)

        # self._writefile(imggrid, "_grid_h")
        # self._writefile(imglineonly, "_lineonly")
        #####

        logging.debug("VPoints start")

        feature = np.array([
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, 1, -1],
        ])

        res = signal.convolve2d(edges / 255, feature, mode='same')

        filtered_points = np.where(res >= 6)

        unique, counts = np.unique(filtered_points[1], return_counts=True)
        # filter points more than "minPointV"
        temp = np.where(counts > minPointV)
        filtered_W = np.take(unique, temp)[0]
        VPointCnt = dict(zip(unique, counts))  # convert to dict H=>Count

        logging.debug("VPoints end")
        logging.debug("VLine start")

        for i in range(len(filtered_points[0])):
            imglineonly[filtered_points[0][i], filtered_points[1][i]] = 255

        VGroup = []
        tempGroup = []
        if len(filtered_W):
            lastw = filtered_W[0]
            for w in np.concatenate((filtered_W, [10000000])):
                if w > lastw + self.VLineMaxDistance:
                    VGroup.append(tempGroup)
                    tempGroup = []
                tempGroup.append(w)
                lastw = w

        VPoints = dict(zip(list(range(width)), [[] for i in range(width)]))
        for i in range(len(filtered_points[0])):
            VPoints[filtered_points[1][i]].append(filtered_points[0][i])

        VLines = []
        for group in VGroup:
            X = []
            Y = []
            for w in group:
                X.extend(VPoints[w])
                Y.extend([w] * VPointCnt[w])

            reg = LinearRegression().fit(np.array(X).reshape(-1, 1), np.array(Y).reshape(-1, 1))

            point1 = (int(reg.intercept_[0] + 0.5), 0)
            point2 = (int(reg.coef_[0][0] * (height - 1)
                          + reg.intercept_[0] + 0.5), height - 1)
            VLines.append((point1, point2))
        x_values_point1 = []
        x_values_point2 = []
        y_values_point1 = []
        y_values_point2 = []

        for line in VLines:
            x_values_point1.append(line[0][0])  # point1 的 x 值
            x_values_point2.append(line[1][0])  # point2 的 x 值
            y_values_point1.append(line[0][1])  # point1 的 y 值
            y_values_point2.append(line[1][1])  # point2 的 y 值
        #
        # print(x_values_point1)
        # print(x_values_point2)
        # print(y_values_point1)
        # print(y_values_point2)
        new_x_values_point1 = []
        new_x_values_point2 = []
        new_y_values_point1 = []
        new_y_values_point2 = []
        new_VLines = []
        if len(x_values_point1) < self.VLine:
            new_x_values_point1 = insert_points_between_gaps("col", x_values_point1, self.girdWidth1, self.VLine,
                                                             self.girdWidth1, 70)
            new_x_values_point2 = insert_points_between_gaps("col", x_values_point2, self.girdWidth1, self.VLine,
                                                             self.girdWidth1, 70)

        if len(y_values_point1) < self.VLine:
            new_y_values_point1 = insert_points_between_gaps("col", y_values_point1, self.girdHeight, self.VLine,
                                                             self.girdHeight, 70)
            new_y_values_point2 = insert_points_between_gaps("col", y_values_point2, self.girdHeight, self.VLine,
                                                             self.girdHeight, 70)

        # print("a")
        # print(VLines)
        # print(new_x_values_point1)
        # print(new_x_values_point2)
        # print(new_y_values_point1)
        # print(new_y_values_point2)
        try:
            for i in range(0, len(new_x_values_point1)):
                new_VLines.append(((new_x_values_point1[i], new_y_values_point1[i]),
                                   (new_x_values_point2[i], new_y_values_point2[i])))
        except IndexError:
            return False
        # print(VLines)
        # print(new_VLines)
        logging.debug("VLine end")

        if len(VGroup) < self.VLine:
            logging.warning("Find VLine Fail, expected %s but %s. Trying to add line..", self.VLine, len(VGroup))
            # self._writefile(imglineonly, "_lineonly")
            VLines = new_VLines
            for VLine in VLines:
                cv2.line(imggrid, VLine[0], VLine[1], (0, 0, 255), 3)

            # self._writefile(imggrid, "_grid")
            # self._writefile(imgori, "_ori")
            isWarning = True
            self.isWarning = isWarning

        if len(VLines) > self.VLine:
            logging.warning(
                "Find VLine Fail, expected %s but %s. Trying to remove noise line.", self.VLine, len(VLines))
            lineCenter = []
            for VLine in VLines:
                cv2.line(imggrid, VLine[0], VLine[1], (0, 0, 255), 3)
                lineCenter.append((VLine[0][0] + VLine[1][0]) / 2)

            removeIdxs = self._tryremoveV(lineCenter)
            for idx in removeIdxs[::-1]:
                logging.info("Remove line %s (idx=%s).", VLines[idx], idx)
                logging.info("Remove noise line on origin image")
                for h in range(height):
                    w = int((VLines[idx][1][0] - VLines[idx][0][0])
                            / (VLines[idx][1][1] - VLines[idx][0][1]) * (h - VLines[idx][0][1]) + VLines[idx][0][0])
                    if 0 <= w < width:
                        imgori[h, w] = np.mean(
                            (imgori[h, max(0, w - 2)], imgori[h, max(0, w - 1)], imgori[h, min(width - 1, w + 1)],
                             imgori[h, min(width - 1, w + 2)]), axis=0)
                del VLines[idx]
            isWarning = True
            self.isWarning = isWarning

        for VLine in VLines:
            cv2.line(imggrid, VLine[0], VLine[1], (0, 0, 255), 3)

        # self._writefile(imggrid, "_grid")
        # self._writefile(imgori, "_ori")
        # self._writefile(imglineonly, "_lineonly")
        logging.debug("Split done")
        ###

        # if self.writeDebugFile:
        #     self._writefile(imglineonly, "_lineonly")
        #     self._writefile(imggrid, "_grid")
        #     self._writefile(imgori, "_ori")

        # if self.withRemoveBorderLine is not None:
        #     from RemoveBorderLine import RemoveBorderLine
        #     fremove = RemoveBorderLine(self.withRemoveBorderLine).removeimg

        result = {}
        row = 0
        cntTwo = False  # 計算是否跳過注音欄
        for i in range(len(VLines) - 1, 0, -1):
            if i in self.skipLine:
                continue
            if not cntTwo and self.skipBopomofo:
                cntTwo = True
                continue
            cntTwo = False
            row += 1
            for j in range(0, len(HLines) - 1):
                # p4 l4 p1
                # l3    l1
                # p3 l2 p2
                l1 = self._line(VLines[i][0], VLines[i][1])
                l2 = self._line(HLines[j + 1][0], HLines[j + 1][1])
                l3 = self._line(VLines[i - 1][0], VLines[i - 1][1])
                l4 = self._line(HLines[j][0], HLines[j][1])

                p1 = self._intersection(l1, l4)
                p2 = self._intersection(l1, l2)
                p3 = self._intersection(l2, l3)
                p4 = self._intersection(l3, l4)

                wl = int(min(p3[0], p4[0]) + 0.5)
                wr = int(max(p1[0], p2[0]) + 0.5)
                ht = int(max(p1[1], p4[1]) + 0.5)
                hb = int(min(p2[1], p3[1]) + 0.5)

                fileid = "{}-{}".format(row + rowoffset, j + 1)
                result[fileid] = imgori[ht:hb, wl:wr]

                # if self.withRemoveBorderLine is not None:
                #     result[fileid] = fremove(result[fileid])

        logging.debug("split done")

        return result

    def split(self, inputpath, outputpath, rowoffset=0, crop=None):
        """
        將作文紙按格線切割成每個字一個檔案

        Parameters:
            str inputpath: 輸入檔案路徑
            str outputpath: 輸出資料夾路徑
            int rowoffset: 輸出檔案編號偏移，如果是AB卷的B卷，應該設定為A卷的行數
            ((int, int), (int, int)) crop: 預先裁剪圖檔((y1, y2), (x1, x2))
        Return bool: 是否成功
        """
        logging.info("running %s", inputpath)
        self.outputpath = outputpath
        self.filename = os.path.splitext(os.path.basename(inputpath))[0]
        self._ext = os.path.splitext(inputpath)[1]

        logging.debug("reading image")
        # https://docs.opencv.org/3.1.0/d4/da8/group__imgcodecs.html
        img = cv2.imread(inputpath, cv2.IMREAD_UNCHANGED)

        if img is None:
            logging.error("inputpath error: %s", inputpath)
            return 3

        logging.debug("read success")

        result = self.splitimg(img, rowoffset, crop)

        if result is False:
            logging.error(f"{inputpath} split failed")
            shutil.rmtree(outputpath)
            return 4

        write_success = True
        for fileid in result:
            res = self._writedir(result[fileid], outputpath, fileid)
            if not res:
                write_success = False
                shutil.rmtree(outputpath)
                break  # 如果有任何一個寫入操作失敗，就跳出循環
        if write_success:
            problem_count = 0  # 初始化問題計數器

            for fileid, img_area in result.items():
                # 取得切割區域的寬度和高度
                width = img_area.shape[1]
                height = img_area.shape[0]

                # 檢查寬度和高度是否為 0，並且是否不符合指定的寬度和高度
                if width == 0 or height == 0 or width < (self.girdWidth1 - 10) or height < (self.girdHeight - 10):
                    problem_count += 1  # 問題計數器加 1

                # 如果問題計數器超過 10，則認為整份文件切割有問題
                if problem_count > 10:
                    # print(f"{inputpath} split failed")
                    shutil.rmtree(outputpath)
                    return 6  # 中斷迴圈，不再繼續檢查
            logging.debug("write file done")
        else:
            logging.error(f"Failed to write")
            return 5

        image_process_p.adjust_brightness(outputpath, 250, 250)
        logging.debug("adjust brightness done")

        image_process_p.detect_img_white(outputpath, self.HLine - 1)
        logging.debug("detect image_white done")

        image_process_p.detect_border(outputpath)
        logging.debug("detect image_border done")

        # base64_dict = image_process_p.detect_img_base64(outputpath)
        # logging.debug("image to base64 done")
        return True


# paper_cutter = GridSplitPaper(HLine=19, VLine=41, girdWidth1=71, girdWidth2=22, girdHeight=71)
# input_folder = './phonepic_png_trans'  # 修改為你的輸入資料夾名稱
# output_folder = './phonepic_png_trans_result_v3'  # 修改為你的輸出資料夾名稱
#
# # 確保輸出資料夾存在
# if not os.path.exists(output_folder):
#     os.makedirs(output_folder)
#
# # 遍歷輸入資料夾中的所有檔案
# for filename in os.listdir(input_folder):
#     if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
#         input_path_img = os.path.join(input_folder, filename)  # 當前處理的圖片路徑
#         output_path_img_folder = os.path.join(output_folder, filename.split('.')[0])  # 輸出圖片的資料夾路徑
#         # 確保輸出圖片資料夾存在
#         if not os.path.exists(output_path_img_folder):
#             os.makedirs(output_path_img_folder)
#
#         # 執行圖片切割
#         success = paper_cutter.split(input_path_img, output_path_img_folder)
