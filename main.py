import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMainWindow, QPushButton
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon
from datetime import datetime
import speech_recognition as sr
from gtts import gTTS
import os
import subprocess
import requests
import webbrowser
import pygame  # Import pygame để phát âm thanh
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from selenium import webdriver  # Để điều khiển trình duyệt bằng Selenium trong open_google_and_search
from selenium.webdriver.common.keys import Keys  # Để gửi phím Enter trong Selenium
import validators
import time
import wikipedia
from keyword_1 import bfs_search, get_command_type

# Khởi tạo pygame mixer
pygame.mixer.init() 

# Lớp để chạy lắng nghe giọng nói trên luồng riêng
class VoiceThread(QThread):
    command_signal = pyqtSignal(str)  # Tín hiệu phát ra khi có lệnh giọng nói

    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Bot: Xin chào, tôi có thể giúp gì cho bạn?")
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio, language='vi-VN')
                self.command_signal.emit(command.lower())  # Phát tín hiệu khi có kết quả
            except sr.UnknownValueError:
                self.command_signal.emit("Xin lỗi, tôi không nghe rõ.")
            except sr.RequestError:
                self.command_signal.emit("Có lỗi xảy ra với dịch vụ nhận diện giọng nói.")

# Lớp chính của giao diện
class Main_W(QMainWindow):
    def __init__(self):
        super(Main_W, self).__init__()
        uic.loadUi('untitled.ui', self)

        # Kết nối nút với hàm xử lý
        self.btnMic = self.findChild(QPushButton, 'btnMic')
        self.btnMic.setIcon(QIcon('img/micro_white.png'))  # Thiết lập biểu tượng ban đầu
        self.btnMic.clicked.connect(self.start_wave_effect)

        # Biến để kiểm soát hiệu ứng sóng
        self.is_waving = False
        self.wave_radius = 0
        self.alpha = [255] * 3  # Danh sách độ mờ cho từng vòng sóng
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_wave)

        # Tính toán bán kính tối đa của sóng
        self.max_wave_radius = max(self.btnMic.width(), self.btnMic.height()) * 0.5

         # Tạo luồng giọng nói
        self.voice_thread = VoiceThread()
        self.command_connected = False  # Biến cờ để theo dõi kết nối tín hiệu
        self.voice_thread.command_signal.connect(self.handle_command)  # Kết nối tín hiệu với xử lý lệnh
        self.command_connected = True  # Đặt cờ thành True sau khi kết nối

        # Đặt ngôn ngữ cho Wikipedia
        wikipedia.set_lang("vi")  # Sử dụng tiếng Việt
        
    def stop_listening(self):
        # Dừng hiệu ứng sóng
            self.is_waving = False
            self.timer.stop()
            self.wave_radius = 0
            self.alpha = [0] * 6  # Đặt lại độ mờ cho từng vòng sóng
            self.btnMic.setIcon(QIcon('img/micro_white.png'))  # Đặt lại biểu tượng
            self.labelText.setText("Trợ lý ảo")
            self.update()

            # Chỉ ngắt kết nối tín hiệu nếu nó đã được kết nối
            if self.command_connected:
                self.voice_thread.command_signal.disconnect(self.handle_command)  # Ngắt kết nối tín hiệu với xử lý lệnh
                self.command_connected = False  # Đặt cờ thành False sau khi ngắt kết nối
    
    def start_wave_effect(self):
        if self.is_waving:
            self.stop_listening()
        else:
            # Bắt đầu hiệu ứng sóng
            self.is_waving = True
            self.wave_radius = 120
            self.alpha = [255] * 6  # Đặt lại độ mờ cho từng vòng sóng
            self.timer.start(50)  # Cập nhật mỗi 50ms
            self.btnMic.setIcon(QIcon('img/stop_white.png'))  # Đặt biểu tượng dừng
            self.labelText.setText("Xin chào, tôi có thể giúp gì cho bạn?")

            # Kết nối tín hiệu lại nếu chưa kết nối
            if not self.command_connected:
                self.voice_thread.command_signal.connect(self.handle_command)  # Kết nối lại tín hiệu
                self.command_connected = True  # Đặt cờ thành True sau khi kết nối

            # Bắt đầu luồng lắng nghe giọng nói
            self.voice_thread.start()


    def update_wave(self):
        if self.is_waving:
            self.wave_radius += 5  # Tăng bán kính sóng
            
            # Cập nhật độ mờ cho từng vòng sóng
            for i in range(3):
                if self.wave_radius > self.max_wave_radius - i * 5:
                    self.alpha[i] -= 15  # Giảm độ mờ của vòng sóng

            if all(a <= 0 for a in self.alpha):
                self.timer.stop()
                
            self.update()


    def paintEvent(self, event):
        if self.is_waving:
            painter = QPainter(self)

            # Vẽ nhiều vòng tròn để tạo hiệu ứng sóng dày
            for i in range(3):  # Số lượng vòng tròn
                pen = QPen(QColor(125, 125, 125, self.alpha[i]), 2 + i * 5)  # Điều chỉnh độ dày và độ mờ
                painter.setPen(pen)

                # Tính bán kính cho mỗi vòng tròn
                radius = self.wave_radius - i * 10  # Điều chỉnh khoảng cách giữa các vòng tròn
                if radius > 0:
                    center_x = self.btnMic.x() + self.btnMic.width() // 2
                    center_y = self.btnMic.y() + self.btnMic.height() // 2
                    
                    # Chuyển đổi radius thành kiểu int
                    painter.drawEllipse(center_x - int(radius), center_y - int(radius),
                                        int(radius * 2), int(radius * 2))
                    
    # Hàm chuyển văn bản thành giọng nói và phát âm thanh
    def speak(self, text):
        tts = gTTS(text=text, lang='vi')        
        # Xóa tệp nếu tồn tại trước đó
        if os.path.exists("response.mp3"):
            try:
                os.remove("response.mp3")
            except PermissionError:
                pass  # Bỏ qua lỗi nếu tệp đang được sử dụng        
        # Lưu tệp mp3 mới
        tts.save("response.mp3")        
        # Phát âm thanh bằng pygame
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()       
        # Chờ đến khi âm thanh phát xong
        while pygame.mixer.music.get_busy():
            continue        
        # Sau khi âm thanh phát xong, giải phóng tệp âm thanh và xóa nó
        pygame.mixer.music.unload()  # Giải phóng tài nguyên tệp
        self.stop_listening()
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")
    # Hàm mở ứng dụng
    def open_application(self, app_name):
        try:
            self.labelText.setText(f"Đang mở ứng dụng {app_name}")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak(f"Đang mở ứng dụng {app_name}")
            subprocess.Popen(f"start {app_name}", shell=True)
        except Exception as e:
            self.labelText.setText(f"Không thể mở ứng dụng: {str(e)}")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak(f"Không thể mở ứng dụng: {str(e)}")
            

    # Hàm dự báo thời tiết
    def get_weather(self, city):
        api_key = "0a37f5125008aa05015889700b7df443"  # API key
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&lang=vi&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            description = data['weather'][0]['description']
            self.labelText.setText(f"Nhiệt độ hiện tại ở {city} là {temp} độ C với {description}.")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak(f"Nhiệt độ hiện tại ở {city} là {temp} độ C với {description}.")   
        else:
            self.labelText.setText("Không thể lấy dữ liệu thời tiết.")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak("Không thể lấy dữ liệu thời tiết.")

    # Hàm phát nhạc từ YouTube
    def play_youtube_music(self, song_name):
        video_url = self.search_youtube(song_name)
        if video_url:
            webbrowser.open(video_url)
            self.labelText.setText(f"Đang mở bài {song_name} trên YouTube.")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak(f"Đang mở bài {song_name} trên YouTube.")
            print(f"Bot: Đang mở bài {song_name} trên YouTube.")
        else:
            self.labelText.setText(f"Tôi không thể tìm thấy bài {song_name} trên YouTube.")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak(f"Tôi không thể tìm thấy bài {song_name} trên YouTube.")

    # Hàm tìm video YouTube có lượt xem nhiều nhất dựa trên từ khóa
    def search_youtube(self, song_name):
        API_KEY = "AIzaSyCID1BZHhYj_JGkUkUyQr-2wDy_x-4E9L4"  # API key
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={song_name}&key={API_KEY}&type=video&order=relevance"
        
        response = requests.get(search_url)
        if response.status_code == 200:
            data = response.json()
            if data["items"]:
                video_id = data["items"][0]["id"]["videoId"]
                return f"https://www.youtube.com/watch?v={video_id}"
            else:
                self.labelText.setText("Không tìm thấy video nào phù hợp.")
                QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
                self.speak("Không tìm thấy video nào phù hợp.")
                return None
        else:
            self.labelText.setText("Có lỗi khi tìm kiếm trên YouTube.")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak("Có lỗi khi tìm kiếm trên YouTube.")
            return None
        
    def get_current_time(self):
        now = datetime.now()
        current_time = now.strftime("%Hh %Mm %Ss")
        self.labelText.setText(f"Thời gian hiện tại là {current_time}.")
        QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
        self.speak(f"Thời gian hiện tại là {current_time}.")

    def open_website(self, command):
    # Tìm kiếm tên trang web từ lệnh của người dùng   
        # Danh sách các phần đuôi phổ biến
        possible_suffixes = [".com", ".net", ".org", ".vn"]

        # Thử các phần đuôi khác nhau
        for suffix in possible_suffixes:
            url = f"http://www.{command.replace(" ", "")}{suffix}"
            
            # Kiểm tra URL có hợp lệ không trước khi mở
            if validators.url(url):
                try:
                    webbrowser.open(url)
                    self.labelText.setText(f"Đang mở {command}")
                    QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
                    self.speak(f"Đang mở {command}")
                    print(f"Đang mở {url}")
                    break  # Nếu mở thành công, dừng lại
                except Exception as e:
                    self.labelText.setText(f"Không thể mở trang web: {str(e)}")
                    QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
                    self.speak(f"Không thể mở trang web: {str(e)}")
                    print(f"Không thể mở trang web: {str(e)}")
    # Hàm tìm kiếm thông tin từ Wikipedia
    def tell_me_about(self, command):
        try:
            # Tìm kiếm và xử lý thông tin từ Wikipedia
            text = command  # Lấy thông tin từ người dùng
            try:
                # Lấy tóm tắt từ Wikipedia, giới hạn 1 câu
                summary = wikipedia.summary(text)
                short_summary = wikipedia.summary(text, 1)
                # Hiển thị và đọc đoạn tóm tắt đầu tiên
                self.labelText.setText(short_summary)
                QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
                self.speak(short_summary)  # Đọc đoạn tóm tắt 
                
            except wikipedia.exceptions.DisambiguationError as e:
                # Xử lý trường hợp có nhiều kết quả, yêu cầu người dùng cung cấp chi tiết hơn
                self.labelText.setText(f"Có nhiều kết quả cho '{text}', xin vui lòng cụ thể hơn.")
                QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
                self.speak(f"Có nhiều kết quả cho '{text}', xin vui lòng cụ thể hơn.")
            except wikipedia.exceptions.PageError:
                # Xử lý trường hợp không tìm thấy trang
                self.labelText.setText("Không tìm thấy thông tin bạn yêu cầu.")
                QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
                self.speak("Không tìm thấy thông tin bạn yêu cầu.")
        except Exception as e:
            # Xử lý các lỗi chung khác
            self.labelText.setText(f"Bot không định nghĩa được thuật ngữ của bạn. Xin mời bạn nói lại.")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak(f"Bot không định nghĩa được thuật ngữ của bạn. Xin mời bạn nói lại.")
    # Hàm chính để xử lý lệnh từ người dùng
    def handle_command(self, command):
        # Cập nhật văn bản của label ngay lập tức
        self.labelText.setText(f"{command}")
        QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
        # Xử lý các sự kiện giao diện hiện tại để đảm bảo rằng labelText được cập nhật
        #QtWidgets.QApplication.processEvents()
        # Thay vì gọi self.speak() ngay lập tức, sử dụng QTimer để thêm độ trễ
        QTimer.singleShot(1000, lambda: self.process_command(command))
    # Hàm để xử lý lệnh và phát âm thanh phản hồi
    def process_command(self, command):
        command_type, keyword = get_command_type(command)  # Lấy loại lệnh và từ khóa đã tìm thấy
        
        if command_type == "app":
            app_name = command.replace(keyword, "").strip()  # Xóa từ khóa đã tìm thấy
            self.open_application(app_name)
        elif command_type == "weather":
            city = command.replace(keyword, "").strip()  # Xóa từ khóa đã tìm thấy
            self.get_weather(city)
        elif command_type == "music":
            song_name = command.replace(keyword, "").strip()  # Xóa từ khóa đã tìm thấy
            self.play_youtube_music(song_name)
        elif command_type == "web":
            web = command.replace(keyword, "").strip()
            self.open_website(web) 
        elif command_type == "tellme":
            tellMe = command.replace(keyword, "").strip()
            self.tell_me_about(tellMe)  # Gọi hàm Wikipedia
        elif command_type == "time":
            self.get_current_time()  # Gọi hàm lấy thời gian hiện tại
        elif command_type == "hello":
            self.labelText.setText("Chào bạn chúc bạn một ngày tốt lành. Tôi là trợ lý ảo, tôi có thể giúp gì cho bạn?")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak("Chào bạn chúc bạn một ngày tốt lành. Tôi là trợ lý ảo, tôi có thể giúp gì cho bạn?")
        else:
            self.labelText.setText("Tôi không hiểu yêu cầu của bạn.")
            QtWidgets.QApplication.processEvents()  # Buộc giao diện cập nhật ngay lập tức
            self.speak("Tôi không hiểu yêu cầu của bạn.")
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    login_window = Main_W()
    login_window.show()
    sys.exit(app.exec())