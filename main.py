import tkinter as Tk
import queue as Que
from tkinter import messagebox

from multiprocessing import Process, Queue

import threading as Thd

import select

import winreg

import os
import time
import subprocess as SubProc
from subprocess import TimeoutExpired

default_proxy_override = ("localhost;" 
                        + "127.*;192.168.*;10.*;172.16.*;172.17.*;"
                        + "172.18.*;172.19.*;172.20.*;172.21.*;"
                        + "172.22.*;172.23.*;172.24.*;172.25.*;"
                        + "172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*")

default_proxy_server = "127.0.0.1:7890"
proxy_server = default_proxy_server

def reader_fn(fd, buffer):
    while True:
        line=os.read(fd, 1024)
        if line:
            buffer.append(line)
        else:
            continue

class GUI():

    def __init__(self, window: Tk.Tk):
        self.mi_cmd = ["mihomo.exe", "-f", "config.yaml"]
        self.mihomo_proc = None
        self.cmdq = Que.Queue(10)
        self.msgq = Que.Queue(10)
        (self.pipe_r, self.pipe_w) = os.pipe()
        
        
        self.initGUI(window)

    def restart(self):
        if (None != self.mihomo_proc):
            self.mihomo_proc.kill()
            time.sleep(0.05)
        self.mi_out.delete('1.0','end')
        self.mi_out.update()
        self.mihomo_proc = SubProc.Popen(self.mi_cmd, stdout=self.pipe_w, stderr=self.pipe_w, creationflags=SubProc.CREATE_NO_WINDOW)

    def reader_fn(self, fd, buffer):
        while True:
            line=os.read(fd, 1024)
            if line:
                buffer.append(line)
            else:
                break

    def capture(self, window: Tk.Tk):
        if (None == self.mihomo_proc):
            window.after(100, self.capture, window)
            return
        if (self.mihomo_proc.poll()) is None:
            while len(self.linebuffer) > 0:
                # Stream data to windows
                self.mi_out.insert("end", self.linebuffer.pop(0))
                self.mi_out.see("end")
                self.mi_out.update()

        window.after(100, self.capture, window)

    def check_proxy_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
            proxy_enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
            winreg.CloseKey(key)
            return proxy_enabled == 1
        except Exception as e:
            return False

    def set_proxy(self):
        global proxy_server, proxy_port
        
        proxy_server = self.server_entry.get() or default_proxy_server
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)
            
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
            
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, default_proxy_override)

            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)

            winreg.CloseKey(key)
            
            self.success_label.config(text="代理已设置", fg="green")
            messagebox.showinfo("成功", "代理已设置")

        except Exception as e:
            self.success_label.config(text="代理设置失败", fg="red")
            messagebox.showerror("错误", f"设置代理时出错: {str(e)}")

    def disable_proxy(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)

            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)

            winreg.CloseKey(key)

            self.success_label.config(text="代理已禁用", fg="red")
            messagebox.showinfo("成功", "代理已禁用")
        except Exception as e:
            self.success_label.config(text="代理禁用失败", fg="yellow")
            messagebox.showerror("错误", f"禁用代理时出错: {str(e)}")

    def confirm_close(self):
        if self.check_proxy_enabled():
            # result = messagebox.askquestion("确认退出", "退出软件将自动禁用代理。确定要退出吗?")
            # if result == "yes":
                # slef.rd_proc.kill()
                if (None != self.mihomo_proc):
                    self.mihomo_proc.kill()
                self.disable_proxy()
                window.quit()  # Exit the Tkinter mainloop and close the window
        else:
            window.quit()  # Exit the Tkinter mainloop and close the window


    def initGUI(self, window: Tk.Widget):

        window.title("全局代理设置")

        # Calculate the screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Calculate the x and y coordinates for the centered window
        x = (screen_width - window.winfo_reqwidth()) / 2
        y = (screen_height - window.winfo_reqheight()) / 2

        # Set the window's geometry to be centered
        window.geometry(f"+{int(x)}+{int(y)}")

        server_label = Tk.Label(window, text="代理服务器:")
        server_label.pack()
        self.server_entry = Tk.Entry(window)
        self.server_entry.pack()
        self.server_entry.insert(0, default_proxy_server)

        set_button = Tk.Button(window, text="设置代理", command=self.set_proxy)
        set_button.pack()

        disable_button = Tk.Button(window, text="禁用代理", command=self.disable_proxy)
        disable_button.pack()

        restart_button = Tk.Button(window, text="重启", command=self.restart)
        restart_button.pack()

        sbar=Tk.Scrollbar()
        sbar.pack(side='right',fill='y')
        self.mi_out = Tk.Text(bg='lightgreen',width=30, height=10,state='disabled',yscrollcommand=sbar.set)
        self.mi_out.pack()
        self.mi_out.config(state="normal")
        
        # 代理设置结果标识
        self.success_label = Tk.Label(window, text="", fg="black")
        self.success_label.pack()

        # 检查代理设置并更新标识
        if self.check_proxy_enabled():
            self.success_label.config(text="代理已开启", fg="green")
        else:
            self.success_label.config(text="代理已禁用", fg="red")

        # Register the confirm_close function to be called when the window is closed
        window.protocol("WM_DELETE_WINDOW", self.confirm_close)
        self.linebuffer = []
        # slef.rd_proc = SubProc.Popen(self.reader_fn, stdout=SubProc.PIPE)
        t = Thd.Thread(target=self.reader_fn, args=(self.pipe_r, self.linebuffer), daemon=True)
        t.start()
        # t = Process(target=reader_fn, daemon=True, args=(self.pipe_r, self.linebuffer))
        # t.start()
        window.after(100, self.capture, window)
        window.mainloop()

if __name__ == "__main__":
    window = Tk.Tk()
    gui = GUI(window)