
import os
import sys
from datetime import datetime

import cv2
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class VideoCaptureApp(QMainWindow):
    """Главное окно приложения видеозахвата."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Видеозахват — Вариант 1")
        self.resize(720, 560)

        self.current_frame = None
        self.is_video_file = False

        # Попытка открыть веб-камеру с индексом 0
        self.cap = cv2.VideoCapture(0)

        # Если физическая камера не обнаружена, переключаемся на тестовый файл
        if not self.cap.isOpened():
            test_file = "test_video.mp4"
            if os.path.exists(test_file):
                self.cap = cv2.VideoCapture(test_file)
                self.is_video_file = True
                print("[Инфо] Камера не найдена. Подключен тестовый видеопоток test_video.mp4")
            else:
                print("[Ошибка] Источник видео не найден.")

        self.init_ui()

    def init_ui(self):
        """Инициализация графического интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Область отображения видео
        self.video_label = QLabel("Ожидание видеосигнала...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid #555; background-color: #111; color: #fff;")
        main_layout.addWidget(self.video_label, stretch=1)

        # Строка статуса
        status_text = (
            "Источник: Тестовый видеопоток (эмуляция веб-камеры)"
            if self.is_video_file
            else "Источник: Веб-камера (индекс 0)"
        )
        self.status_label = QLabel(status_text)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Кнопка сохранения снимка кадра
        button_layout = QHBoxLayout()
        self.btn_capture = QPushButton("Сделать снимок кадра")
        self.btn_capture.clicked.connect(self.capture_frame)
        button_layout.addWidget(self.btn_capture)

        main_layout.addLayout(button_layout)
        central_widget.setLayout(main_layout)

        # Таймер захвата кадров (~33 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        if self.cap.isOpened():
            self.timer.start(30)
        else:
            self.status_label.setText("Ошибка: видеоисточник недоступен")

    def update_frame(self):
        """Считывание очередного кадра и вывод в окно."""
        ret, frame = self.cap.read()

        # Зацикливание видеопотока при достижении конца файла
        if not ret and self.is_video_file:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        if not ret or frame is None:
            return

        self.current_frame = frame.copy()

        # Конвертация цветового пространства из BGR в RGB для Qt
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        # Масштабирование кадра под область отображения
        scaled_pixmap = pixmap.scaled(
            self.video_label.width() - 10,
            self.video_label.height() - 10,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled_pixmap)

    def capture_frame(self):
        """Сохранение текущего кадра с временной меткой в имени."""
        if self.current_frame is None:
            QMessageBox.warning(self, "Предупреждение", "Нет кадра для сохранения!")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"frame_{timestamp}.png"

        success = cv2.imwrite(filename, self.current_frame)
        if success:
            self.status_label.setText(f"Кадр успешно сохранён: {filename}")
            print(f"[Успех] Кадр сохранён: {filename}")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить кадр.")

    def closeEvent(self, event):
        """Корректное освобождение ресурсов камеры при закрытии окна."""
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
        event.accept()


def main():
    """Точка входа в программу."""
    app = QApplication(sys.argv)
    window = VideoCaptureApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()