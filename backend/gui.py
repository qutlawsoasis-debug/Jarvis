import tkinter as tk
import math
import queue
import threading
import time
import os
import sys

# Добавляем текущую директорию в пути импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import jarvis_friend

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis Glow Widget")
        
        # Настройка прозрачного и безрамочного окна
        self.trans_color = "white"
        self.root.attributes("-transparentcolor", self.trans_color)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg=self.trans_color)
        
        # Размеры окна
        width = 420
        height = 420
        
        # Размещение в правом нижнем углу экрана над панелью задач
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - width - 30
        y = screen_h - height - 60
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Холст для рисования анимированного реактора
        self.canvas = tk.Canvas(root, bg=self.trans_color, highlightthickness=0, width=width, height=height)
        self.canvas.pack(fill="both", expand=True)
        
        # Делаем виджет перемещаемым
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        
        # Кнопка закрытия [×] в верхнем правом углу виджета
        self.close_btn = self.canvas.create_text(390, 30, text="×", fill="#ff4444", font=("Outfit", 20, "bold"), tags="close_btn")
        self.canvas.tag_bind("close_btn", "<Button-1>", lambda e: self.root.destroy())
        self.canvas.tag_bind("close_btn", "<Enter>", lambda e: self.canvas.itemconfig("close_btn", fill="#ff7777"))
        self.canvas.tag_bind("close_btn", "<Leave>", lambda e: self.canvas.itemconfig("close_btn", fill="#ff4444"))
        
        # Выход по кнопке Escape
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # Очередь для связи между ИИ-потоком и графическим интерфейсом
        self.queue = queue.Queue()
        
        # Состояния
        self.current_state = "idle"  # idle, listening, thinking, speaking
        self.user_text = ""
        self.jarvis_text = ""
        
        # Параметры анимации реактора
        self.angle = 0
        self.pulse = 0.0
        self.pulse_dir = 1
        
        # Размеры и центр реактора
        self.center_x = width // 2
        self.reactor_y = 150  # Смещено вверх, чтобы снизу помещались субтитры
        
        # Запускаем фоновый поток ИИ-ассистента
        self.start_assistant_thread()
        
        # Запускаем цикл анимации и проверки очереди сообщений
        self.animate()
        self.poll_queue()
        
    def start_drag(self, event):
        self.root.x = event.x
        self.root.y = event.y

    def drag(self, event):
        deltax = event.x - self.root.x
        deltay = event.y - self.root.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
    def start_assistant_thread(self):
        # Запускаем голосового ассистента в отдельном демоническом потоке
        self.thread = threading.Thread(target=jarvis_friend.run_voice_assistant, args=(self.queue,), daemon=True)
        self.thread.start()
        
    def poll_queue(self):
        # Опрашиваем очередь сигналов из голосового потока
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg["type"] == "state":
                    self.current_state = msg["value"]
                elif msg["type"] == "user_text":
                    self.user_text = msg["value"]
                elif msg["type"] == "jarvis_text":
                    self.jarvis_text = msg["value"]
                self.queue.task_done()
        except queue.Empty:
            pass
        self.root.after(50, self.poll_queue)
        
    def animate(self):
        # Очищаем анимированные слои на Canvas
        self.canvas.delete("animated")
        
        cx, cy = self.center_x, self.reactor_y
        
        # Настройка цветов и скоростей под разные состояния Джарвиса
        if self.current_state == "idle":
            color = "#00d2ff"  # Спокойный неоново-синий
            glow_color = "#004466"
            # Медленная пульсация
            self.pulse += 0.02 * self.pulse_dir
            if self.pulse >= 1.0 or self.pulse <= 0.0:
                self.pulse_dir *= -1
            r_pulse = self.pulse
            self.angle = (self.angle + 0.5) % 360
            
        elif self.current_state == "listening":
            color = "#00ff66"  # Неоново-зеленый (активный микрофон)
            glow_color = "#005522"
            # Быстрая пульсация
            self.pulse += 0.08 * self.pulse_dir
            if self.pulse >= 1.0 or self.pulse <= 0.0:
                self.pulse_dir *= -1
            r_pulse = self.pulse
            self.angle = (self.angle - 2) % 360
            
        elif self.current_state == "thinking":
            color = "#ffaa00"  # Золотисто-оранжевый (ИИ обрабатывает запрос)
            glow_color = "#553300"
            # Без пульсации, быстрое вращение
            r_pulse = 0.5
            self.angle = (self.angle + 6) % 360
            
        elif self.current_state == "speaking":
            color = "#00ffff"  # Яркий бирюзовый (Джарвис отвечает)
            glow_color = "#006666"
            # Пульсация имитирует звуковую волну через синусоиду
            r_pulse = 0.5 + 0.3 * math.sin(time.time() * 12)
            self.angle = (self.angle + 2) % 360
            
        sf = 1.0
            
        # 0. Задняя круглая темная пластина (подложка под реактор)
        r_plate = int(92 * sf)
        self.canvas.create_oval(cx - r_plate, cy - r_plate, cx + r_plate, cy + r_plate, fill="#02080f", outline="#051c2c", width=1, tags="animated")
        
        # 1. Внешний светящийся контур (имитация неонового свечения)
        r_outer = int((70 + 4 * r_pulse) * sf)
        self.canvas.create_oval(cx - r_outer - 4, cy - r_outer - 4, cx + r_outer + 4, cy + r_outer + 4, outline=glow_color, width=8, tags="animated")
        self.canvas.create_oval(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer, outline=color, width=2, tags="animated")
        
        # 1.5. Внешний ободок из вращающихся насечек (телеметрия)
        r_ticks = int(80 * sf)
        num_ticks = 24
        for i in range(num_ticks):
            tick_ang = -self.angle * 0.7 + i * (360 / num_ticks)
            rad = math.radians(tick_ang)
            x1 = cx + r_ticks * math.cos(rad)
            y1 = cy - r_ticks * math.sin(rad)
            x2 = cx + (r_ticks + 4) * math.cos(rad)
            y2 = cy - (r_ticks + 4) * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1.5, tags="animated")
            
        # 2. Средние вращающиеся сегменты реактора
        r_mid = int(50 * sf)
        num_segments = 8
        for i in range(num_segments):
            start_ang = self.angle + i * (360 / num_segments)
            self.canvas.create_arc(cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid, start=start_ang, extent=25, style="arc", outline=color, width=8, tags="animated")
            
            # Внутренние темные перегородки для кибернетического стиля
            rad = math.radians(start_ang + 12.5)
            x1 = cx + (r_mid - int(12 * sf)) * math.cos(rad)
            y1 = cy - (r_mid - int(12 * sf)) * math.sin(rad)
            x2 = cx + (r_mid - int(4 * sf)) * math.cos(rad)
            y2 = cy - (r_mid - int(4 * sf)) * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill="#010101", width=2, tags="animated")
            
        # 3. Внутреннее ядро
        r_core = int((22 + 3 * r_pulse) * sf)
        self.canvas.create_oval(cx - r_core - 2, cy - r_core - 2, cx + r_core + 2, cy + r_core + 2, fill=glow_color, outline="", tags="animated")
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, fill=color, outline="#ffffff", width=1, tags="animated")
        
        # 4. Соединительные ребра жесткости (спицы, идущие от ядра наружу)
        for i in range(4):
            ang = self.angle * 0.5 + i * 90
            rad = math.radians(ang)
            x1 = cx + (r_core + 2) * math.cos(rad)
            y1 = cy - (r_core + 2) * math.sin(rad)
            x2 = cx + (r_mid - int(8 * sf)) * math.cos(rad)
            y2 = cy - (r_mid - int(8 * sf)) * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1, tags="animated")
            
        # 4.5. Телеметрический маркер состояния
        state_labels = {
            "idle": "JARVIS // STANDBY",
            "listening": "JARVIS // RECORDING...",
            "thinking": "JARVIS // ANALYZING...",
            "speaking": "JARVIS // SPEAKING"
        }
        status_text = state_labels.get(self.current_state, "JARVIS // ACTIVE")
        self.canvas.create_text(cx + 1, cy + r_plate + 16, text=status_text, fill="#000000", font=("Courier New", 9, "bold"), tags="animated")
        self.canvas.create_text(cx, cy + r_plate + 15, text=status_text, fill=color, font=("Courier New", 9, "bold"), tags="animated")
            
        # 5. Отрисовка субтитров пользователя
        if self.user_text:
            text_user_wrapped = self.wrap_text(self.user_text, 45)
            self.canvas.create_text(self.center_x + 1, 281, text=f"Вы: {text_user_wrapped}", fill="#000000", font=("Outfit", 11, "italic"), justify="center", width=360, tags="animated")
            self.canvas.create_text(self.center_x, 280, text=f"Вы: {text_user_wrapped}", fill="#88ccff", font=("Outfit", 11, "italic"), justify="center", width=360, tags="animated")
            
        # 6. Отрисовка ответов Джарвиса
        if self.jarvis_text:
            text_jarvis_wrapped = self.wrap_text(self.jarvis_text, 40)
            self.canvas.create_text(self.center_x + 1, 331, text=text_jarvis_wrapped, fill="#000000", font=("Outfit", 12, "bold"), justify="center", width=360, tags="animated")
            self.canvas.create_text(self.center_x, 330, text=text_jarvis_wrapped, fill="#00ffcc", font=("Outfit", 12, "bold"), justify="center", width=360, tags="animated")
            
        # Запускаем следующий кадр через 30мс
        self.root.after(30, self.animate)
        
    def wrap_text(self, text, max_chars):
        words = text.split()
        lines = []
        current_line = []
        current_len = 0
        for w in words:
            if current_len + len(w) > max_chars:
                lines.append(" ".join(current_line))
                current_line = [w]
                current_len = len(w)
            else:
                current_line.append(w)
                current_len += len(w) + 1
        if current_line:
            lines.append(" ".join(current_line))
        return "\n".join(lines[:3])  # Выводим не более 3 строк для компактности

if __name__ == "__main__":
    import socket
    import sys
    try:
        # Держим сокет открытым до конца работы процесса для блокировки других копий
        _instance_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _instance_lock.bind(('127.0.0.1', 47719))
        _instance_lock.listen(1)
    except socket.error:
        print("Джарвис уже запущен в другом процессе! Выходим.")
        sys.exit(0)

    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
