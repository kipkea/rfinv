import tkinter as tk
from tkinter import ttk, messagebox
import os
import pygame

# ------------------ Settings ------------------
LOCK_PASSWORD = "1234"      # รหัสล็อกหน้าจอ
SOUND_FILES = {
    'click':   'click.wav',
    'lock':    'lock.wav',
    'unlock':  'unlock.wav',
}

# ------------------ Init Sound ------------------
pygame.mixer.init()
sounds = {}
for name, fn in SOUND_FILES.items():
    try:
        sounds[name] = pygame.mixer.Sound(fn)
    except Exception as e:
        print(f"Warning: ไม่สามารถโหลดเสียง {fn} → {e}")

def play(name):
    """เล่นเสียงถ้ามี"""
    if name in sounds:
        sounds[name].play()

# ------------------ Main Window ------------------
root = tk.Tk()
root.title("Touch UI Kiosk")
root.attributes("-fullscreen", True)
root.configure(bg="#222")

# ------------------ Lock Screen Frame ------------------
lock_frame = tk.Frame(root, bg="black")

def lock_screen():
    # clear เดิม ๆ  
    for w in lock_frame.winfo_children():
        w.destroy()
    play('lock')
    lock_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    tk.Label(lock_frame, 
             text="กรุณากรอกรหัสเพื่อปลดล็อก", 
             fg="white", bg="black", 
             font=("Helvetica", 24)).pack(pady=20)

    pwd_var = tk.StringVar()
    entry = tk.Entry(lock_frame, 
                     textvariable=pwd_var, 
                     show="*", 
                     font=("Helvetica", 18))
    entry.pack(pady=10)
    entry.focus_set()

    def try_unlock():
        if pwd_var.get() == LOCK_PASSWORD:
            play('unlock')
            lock_frame.place_forget()
        else:
            messagebox.showerror("ผิดพลาด", "รหัสไม่ถูกต้อง")

    tk.Button(lock_frame, 
              text="Unlock", 
              font=("Helvetica", 18), 
              bg="#444", fg="white", 
              command=try_unlock).pack(pady=10)

# ------------------ Layout ------------------
main_frame = tk.Frame(root, bg="#222")
main_frame.pack(fill='both', expand=True)

# Top bar for Lock button
top_frame = tk.Frame(main_frame, height=60, bg="#333")
top_frame.pack(fill='x')
tk.Button(top_frame, 
          text="🔒 Lock", 
          font=("Helvetica", 18), 
          bg="#900", fg="white", 
          command=lock_screen).pack(side='left', padx=10, pady=10)

# Content area
content_frame = tk.Frame(main_frame, bg="#111")
content_frame.pack(fill='both', expand=True)

# ------------------ Style ------------------
style = ttk.Style()
style.theme_use('default')
style.configure("TNotebook", background="#222", borderwidth=0)
style.configure("TNotebook.Tab",
                font=("Helvetica", 16),
                padding=[30,15],
                background="#444",
                foreground="#ddd")
style.map("TNotebook.Tab",
          background=[("selected", "#555")],
          foreground=[("selected", "#fff")])

# ------------------ Notebook (Tabs) ------------------
notebook = ttk.Notebook(content_frame, style="TNotebook")
notebook.pack(fill='both', expand=True, pady=20, padx=20)

def on_tab_action(name):
    play('click')
    print(f"{name} clicked")

def create_tab(name, img_file=None, with_controls=False, is_shutdown=False):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=name)

    layout = tk.Frame(tab, bg="#111")
    layout.pack(expand=True, fill='both', pady=40)

    # รูปภาพ
    if img_file:
        try:
            img = tk.PhotoImage(file=img_file)
            lbl = tk.Label(layout, image=img, bg="#111")
            lbl.image = img
            lbl.pack(pady=10)
        except:
            tk.Label(layout, text="ไม่พบรูปภาพ", fg="white", bg="#111").pack(pady=10)

    # ปุ่มหลัก
    if is_shutdown:
        tk.Label(layout, 
                 text="กดปุ่มด้านล่างเพื่อ Shutdown เครื่อง", 
                 fg="white", bg="#111", 
                 font=("Helvetica", 20)).pack(pady=20)
        tk.Button(layout, 
                  text="Shutdown", 
                  bg="red", fg="white", 
                  font=("Helvetica", 24),
                  command=lambda: [play('click'), 
                                   os.system("sudo shutdown now")]).pack(pady=10)
    else:
        tk.Button(layout, 
                  text=f"Touch me in {name}", 
                  font=("Helvetica", 20), 
                  command=lambda n=name: on_tab_action(n)).pack(pady=10)

    # Combo & Slider
    if with_controls:
        combo = ttk.Combobox(layout, 
                             values=["Option 1","Option 2","Option 3"],
                             font=("Helvetica", 16))
        combo.set("Option 1")
        combo.pack(pady=10)

        slider = tk.Scale(layout, 
                          from_=0, to=100, 
                          orient='horizontal', 
                          font=("Helvetica", 12), 
                          length=300,
                          command=lambda v: play('click'))
        slider.pack(pady=10)

# สร้าง Tabs
create_tab("Tab 1",       "image1.png")
create_tab("Tab 2",       "image2.png")
create_tab("Settings",    "image3.png", with_controls=True)
create_tab("Shutdown",    is_shutdown=True)

# ------------------ Swipe Gesture ------------------
swipe_start_x = None

def on_mouse_down(event):
    global swipe_start_x
    swipe_start_x = event.x

def on_mouse_up(event):
    global swipe_start_x
    if swipe_start_x is None:
        return
    dx = event.x - swipe_start_x
    if abs(dx) > 100:
        idx = notebook.index(notebook.select())
        if dx < 0 and idx < notebook.index("end")-1:
            notebook.select(idx+1)
        elif dx > 0 and idx > 0:
            notebook.select(idx-1)
    swipe_start_x = None

notebook.bind("<ButtonPress-1>",  on_mouse_down)
notebook.bind("<ButtonRelease-1>", on_mouse_up)

# ------------------ Exit Fullscreen (Dev) ------------------
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

# ------------------ Mainloop ------------------
root.mainloop()
