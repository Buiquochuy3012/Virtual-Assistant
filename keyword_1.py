from collections import deque

final_weather = {"dự báo", "dự báo thời tiết", "thời tiết", "weather in", "weather"}
final_app = {"mở ứng dụng", "mở app", "open app"}
final_music = {"phát nhạc", "bật nhạc", "chơi nhạc", "play"}
final_web = {"mở web", "mở", "mở trang", "open web"}
final_tellMe = {"giới thiệu về", "định nghĩa", "khái niệm", "là ai", "là gì", "tell me about"}
final_hello = {"xin chào", "hello", "hi", "chào", "chào bạn"}
final_time = {"giờ", "bây giờ là mấy giờ", "thời gian hiện tại", "what time"}



def bfs_search(query, dataset):
    queue = deque(dataset)
    while queue:
        item = queue.popleft()
        if item in query:  # Kiểm tra nếu item có trong query
            return item  # Trả về item đã tìm thấy
    return None  # Không tìm thấy

def get_command_type(command):
    """Xác định loại lệnh dựa trên từ khóa."""
    if result := bfs_search(command, final_app):
        return "app", result
    elif result := bfs_search(command, final_weather):
        return "weather", result
    elif result := bfs_search(command, final_music):
        return "music", result
    elif result := bfs_search(command, final_web):
        return "web", result
    elif result := bfs_search(command, final_tellMe):
        return "tellme", result
    elif result := bfs_search(command, final_time):
        return "time", result
    elif result := bfs_search(command, final_hello):
        return "hello", result
    
    return None, None
