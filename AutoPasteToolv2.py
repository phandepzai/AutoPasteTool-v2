import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import keyboard
import time
import threading

class AutoPasteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Paste Tool")
        self.root.geometry("340x495")
        
        # Khóa thay đổi kích thước và loại bỏ phóng to toàn màn hình
        self.root.resizable(False, False)
        self.root.attributes("-fullscreen", False)
        
        # Biến trạng thái
        self.is_pasting = False
        self.data_locked = False
        self.paste_thread = None
        self.paste_speed = 250  # Giá trị mặc định
        
        # Tạo layout chính
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(padx=10, pady=10)  # Loại bỏ "fill" và "expand"

        # Khu vực nhập liệu bên trái với tiêu đề và chú thích mờ
        self.input_label = ttk.Label(self.main_frame, text="Nhập dữ liệu")
        self.input_label.grid(row=0, column=0, pady=(0, 5))

        self.text_area = tk.Text(self.main_frame, width=23, height=26, fg="gray")
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.placeholder_text = "Nhập dữ liệu vào đây"
        self.text_area.insert("1.0", self.placeholder_text)
        self.text_area.bind("<FocusIn>", self.clear_placeholder)
        self.text_area.bind("<FocusOut>", self.add_placeholder)
        self.text_area.bind("<KeyRelease>", self.update_line_count)  # Cập nhật số dòng khi nhập
        
        # Nhãn hiển thị số dòng
        self.line_count_label = ttk.Label(self.main_frame, text="Số dòng: 0")
        self.line_count_label.grid(row=2, column=0, pady=(5, 0), sticky="w")  # Đặt dưới text_area
        
        # Khu vực controls bên phải
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=0, column=1, padx=10, sticky="ns", rowspan=3)

        # Các nút chọn tốc độ
        ttk.Label(self.control_frame, text="Tốc độ (ms):").pack(pady=(0, 5))
        speed_frame = ttk.Frame(self.control_frame)
        speed_frame.pack()
        
        self.speed_var = tk.StringVar(value="250")  # Giá trị mặc định
        speeds = ["100", "200", "250", "350", "400", "500"]
        for speed in speeds:
            btn = ttk.Radiobutton(speed_frame, text=f"{speed} ms", 
                                  value=speed, variable=self.speed_var,
                                  command=self.update_speed)
            btn.pack(anchor="w")
        
        # Label hiển thị tốc độ hiện tại
        self.speed_value = ttk.Label(self.control_frame, text="Hiện tại: 250 ms")
        self.speed_value.pack(pady=8)
        
        # Các nút điều khiển
        self.start_button = ttk.Button(self.control_frame, text="START", command=self.lock_data)
        self.start_button.pack(pady=5, padx=5, ipady=6)
        
        self.stop_button = ttk.Button(self.control_frame, text="STOP", command=self.stop_and_edit, state="disabled")
        self.stop_button.pack(pady=5, padx=5, ipady=6)
        
        self.reset_button = ttk.Button(self.control_frame, text="RESET", command=self.reset_app)
        self.reset_button.pack(pady=5, padx=5, ipady=6)
        
        # Label trạng thái
        self.status_label = ttk.Label(self.control_frame, text="Thao tác\nF1: Bắt đầu\nESC: Dừng")
        self.status_label.pack(pady=10)
        
        # Thêm tên tác giả ở góc dưới bên phải
        self.author_label = ttk.Label(self.main_frame, text="Author: Nông Văn Phấn", font=("Tahoma", 8), foreground="#999")
        self.author_label.grid(row=2, column=1, sticky="se", padx=0, pady=0)  # Sát mép dưới cùng bên phải

        # Cấu hình grid
        self.main_frame.columnconfigure(0, weight=0)  # Cố định cột chứa text_area
        self.main_frame.columnconfigure(1, weight=0)  # Cố định cột chứa control_frame
        self.main_frame.rowconfigure(0, weight=0)     # Khóa hàng chứa input_label
        self.main_frame.rowconfigure(1, weight=0)     # Khóa hàng chứa text_area
        self.main_frame.rowconfigure(2, weight=0)     # Khóa hàng chứa line_count_label

        # Bind phím nóng
        keyboard.on_press_key("F1", self.toggle_pasting)
        
        # Cập nhật số dòng ban đầu
        self.update_line_count(None)
        
    def clear_placeholder(self, event):
        if self.text_area.get("1.0", tk.END).strip() == self.placeholder_text:
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(fg="black")
        
    def add_placeholder(self, event):
        if not self.text_area.get("1.0", tk.END).strip():
            self.text_area.insert("1.0", self.placeholder_text)
            self.text_area.config(fg="gray")
        self.update_line_count(None)
        
    def update_speed(self):
        self.paste_speed = int(self.speed_var.get())
        self.speed_value.config(text=f"Hiện tại: {self.paste_speed} ms")
        
    def update_line_count(self, event):
        lines = self.text_area.get("1.0", tk.END).strip().split("\n")
        if len(lines) == 1 and lines[0] == self.placeholder_text:
            line_count = 0
        else:
            line_count = len([line for line in lines if line.strip()])
        self.line_count_label.config(text=f"Số dòng: {line_count}")
        
    def lock_data(self):
        if not self.data_locked:
            self.data_locked = True
            self.text_area.config(state="disabled")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Đã khóa\nNhấn F1 để\nbắt đầu")
            
    def stop_and_edit(self):
        if self.is_pasting or self.data_locked:
            self.is_pasting = False
            if self.paste_thread:
                self.paste_thread.join()
            self.data_locked = False
            self.text_area.config(state="normal")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="Đã dừng\nCó thể sửa đổi")
            self.update_line_count(None)
        
    def reset_app(self):
        self.is_pasting = False
        self.data_locked = False
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)
        self.add_placeholder(None)
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Thao tác\nF1: Bắt đầu\nESC: Dừng")
        self.update_line_count(None)
        
    def paste_process(self):
        lines = self.text_area.get("1.0", tk.END).strip().split("\n")
        delay = self.paste_speed / 1000
        
        for line in lines:
            if not self.is_pasting:
                return
            if line.strip() and line != self.placeholder_text:
                pyautogui.typewrite(line)
                pyautogui.press("enter")
                time.sleep(delay)
        
        self.is_pasting = False
        self.data_locked = False
        self.text_area.config(state="normal")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Hoàn thành\nNhấn RESET\nđể làm sạch")
        messagebox.showinfo("Thông báo", "Đã dán xong tất cả dữ liệu!")
        self.update_line_count(None)
        
    def toggle_pasting(self, event=None):
        if not self.data_locked:
            return
        
        if self.is_pasting:
            self.is_pasting = False
            if self.paste_thread:
                self.paste_thread.join()
            self.data_locked = False
            self.text_area.config(state="normal")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="Đã dừng ESC\nCó thể chỉnh sửa")
            messagebox.showinfo("Thông báo", "Đã dừng quá trình dán!")
            self.update_line_count(None)
        else:
            self.is_pasting = True
            self.status_label.config(text="Đang dán...\nNhấn ESC để dừng")
            self.paste_thread = threading.Thread(target=self.paste_process)
            self.paste_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoPasteApp(root)
    root.mainloop()
