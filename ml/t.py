import cv2
import numpy as np

# 1. Загрузка изображения и бинаризация
img = cv2.imread("g.png", cv2.IMREAD_GRAYSCALE)
if img is None:
    raise RuntimeError

# Применяем пороговое преобразование, чтобы оставить только четкие белые линии
_, binary = cv2.threshold(img, 50, 255, cv2.THRESH_BINARY)

height, width = binary.shape

# 2. Удаление центральной оси (тела и хвоста)
# Поскольку стрекоза отцентрована, надежнее взять ровно середину изображения
center_x = width // 2

# Делаем полосу достаточно широкой (например, 200 пикселей), 
# чтобы гарантированно отрезать крылья от тела и хвоста
body_width = 200 
binary_no_body = binary.copy()
binary_no_body[:, center_x - body_width//2 : center_x + body_width//2] = 0

# Обязательно закрашиваем табличку и QR-код в правом нижнем углу
binary_no_body[height-250:height, width-400:width] = 0

# 3. Горизонтальная проекция
row_sums = np.sum(binary_no_body, axis=1)

# 4. Ищем границы ИМЕННО КРЫЛЬЕВ
# Отсекаем строки, где белых пикселей слишком мало (остатки хвоста или шум).
# Берем только те строки, где "масса" белого цвета значительна (например, больше 50 пикселей).
threshold_pixels = 255 * 50 
significant_rows = np.where(row_sums > threshold_pixels)[0]

top_y = significant_rows[0]
bottom_y = significant_rows[-1]

# 5. Поиск линии разделения
# Теперь мы точно знаем, где начинаются и заканчиваются крылья.
# Ищем минимум (разрыв) в центральной половине блока крыльев.
margin = (bottom_y - top_y) // 4
mid_start = top_y + margin
mid_end = bottom_y - margin

# Локальный минимум в этой зоне будет точной линией между парами крыльев
split_y = mid_start + np.argmin(row_sums[mid_start:mid_end])

# 6. Визуализация
result_img = cv2.cvtColor(binary_no_body, cv2.COLOR_GRAY2BGR)

# Рисуем зеленую линию, чтобы четко видеть результат
cv2.line(result_img, (0, split_y), (width, split_y), (0, 255, 0), 2)

# Сохранение/Отображение
cv2.imwrite('fixed_split_line.jpg', result_img)
cv2.imshow('Dividing Line', result_img)
cv2.waitKey(0)
cv2.destroyAllWindows()