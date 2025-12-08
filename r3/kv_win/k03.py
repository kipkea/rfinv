import subprocess
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.clock import mainthread

KV_CODE = """
<CommandLayout>:
    orientation: 'vertical'
    padding: 10
    spacing: 10
    
    BoxLayout:
        size_hint_y: None
        height: '40dp'
        spacing: 5
        
        TextInput:
            id: cmd_input
            hint_text: 'Enter command (e.g., ping google.com)'
            multiline: False
            size_hint_x: 0.8
            on_text_validate: root.run_command()
            
        Button:
            id: run_btn
            text: 'Run'
            size_hint_x: 0.2
            on_press: root.run_command()

    TextInput:
        id: output_text
        text: 'Ready...'
        readonly: True
        background_color: (0.95, 0.95, 0.95, 1)
        size_hint: (1, 1)
"""

Builder.load_string(KV_CODE)

class CommandLayout(BoxLayout):
    
    def run_command(self):
        command = self.ids.cmd_input.text.strip()
        if not command:
            return

        # 1. ล็อกปุ่มและแสดงสถานะเริ่มทำงาน
        self.ids.run_btn.disabled = True
        self.ids.output_text.text = f"Running: {command}...\n"
        
        # 2. ใช้ Thread เพื่อไม่ให้หน้าจอค้าง (Non-blocking UI) [5]
        threading.Thread(target=self._execute_task, args=(command,), daemon=True).start()

    def _execute_task(self, command):
        """ทำงานเบื้องหลัง (Background Task)"""
        result_text = ""
        try:
            # 3. รันคำสั่ง โดยใช้ subprocess [9]
            # ใช้ shell=True เพื่อให้รองรับคำสั่งระบบ แต่ต้องระวังเรื่องความปลอดภัย
            process = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=10 # ตั้งเวลา timeout ป้องกันการค้างตลอดกาล
            )
            
            # ตรวจสอบว่าคำสั่งสำเร็จหรือไม่ (Return Code 0 คือสำเร็จ)
            if process.returncode == 0:
                result_text = f"[SUCCESS]\n{process.stdout}"
            else:
                # กรณีคำสั่งทำงานแต่ Error (เช่น ping ไม่เจอ)
                result_text = f"[FAILED]\n{process.stderr}"
                
        except subprocess.TimeoutExpired:
            result_text = "[ERROR] Command timed out."
        except Exception as e:
            # 4. ดักจับ Error กรณีคำสั่งผิดพลาดร้ายแรง [7]
            result_text = f"[ERROR] Execution failed: {str(e)}"
        
        # 5. ส่งผลลัพธ์กลับไปอัปเดตหน้าจอ
        self.update_output(result_text)

    @mainthread # [8]
    def update_output(self, result):
        """อัปเดต UI ต้องทำใน Main Thread เสมอ"""
        # แสดงผลลัพธ์
        current_text = self.ids.output_text.text
        self.ids.output_text.text = f"{current_text}\n{'-'*20}\n{result}"
        
        # คืนสถานะปุ่มให้กดใหม่ได้
        self.ids.run_btn.disabled = False

class KivyCommandApp(App):
    def build(self):
        return CommandLayout()

if __name__ == '__main__':
    KivyCommandApp().run()