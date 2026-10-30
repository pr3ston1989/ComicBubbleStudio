"""Native, scalable Studio branding. No web service is needed at startup."""
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk

ASSETS = Path(__file__).resolve().parents[2] / 'assets'


def configure(root):
    root.configure(background='#14101f')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background='#14101f', foreground='#f1eafa', font=('Segoe UI', 10))
    style.configure('TFrame', background='#14101f')
    style.configure('TLabel', background='#14101f', foreground='#f1eafa')
    style.configure('TButton', background='#39294e', foreground='#f8f3ff', padding=(12,8), borderwidth=1)
    style.map('TButton', background=[('active','#58406f'),('disabled','#26212e')],
              foreground=[('disabled','#9c90aa')])
    style.configure('TCheckbutton', background='#14101f', foreground='#f1eafa', padding=(0,4))
    style.map('TCheckbutton', background=[('active','#211a30')])
    style.configure('TEntry', fieldbackground='#251d33', foreground='#f1eafa', insertcolor='white', padding=7)
    style.configure('TCombobox', fieldbackground='#251d33', background='#39294e', foreground='#f1eafa', padding=6)
    style.map('TCombobox', fieldbackground=[('readonly','#251d33')], foreground=[('readonly','#f1eafa')])
    style.configure('Horizontal.TProgressbar', troughcolor='#251d33', background='#58dac5')
    root.option_add('*TCombobox*Listbox.background','#251d33')
    root.option_add('*TCombobox*Listbox.foreground','#f1eafa')
    if (ASSETS/'bubble-studio.ico').is_file():
        root.iconbitmap(str(ASSETS/'bubble-studio.ico'))


def header(frame):
    from PIL import Image, ImageTk
    row=ttk.Frame(frame)
    row.pack(fill='x',pady=(0,12))
    if (ASSETS/'bubble-studio.png').is_file():
        with Image.open(ASSETS/'bubble-studio.png') as image:
            row.brand_image=ImageTk.PhotoImage(image.resize((76,76),Image.Resampling.LANCZOS))
        ttk.Label(row,image=row.brand_image).pack(side='left',padx=(0,16))
    text=ttk.Frame(row)
    text.pack(side='left',fill='x',expand=True)
    ttk.Label(text,text='NOKTURN',font=('Segoe UI',11,'bold'),foreground='#69dfd2').pack(anchor='w')
    ttk.Label(text,text='Bubble Studio',font=('Segoe UI',25,'bold')).pack(anchor='w')
    from .config import VERSION
    ttk.Label(text,text='Obrysy, wypowiedzi i kolejność czytania · '+VERSION.removeprefix('bubble-studio-'),foreground='#baaccf').pack(anchor='w')


def splash(root, ready):
    if os.environ.get('NOKTURN_NO_SPLASH')=='1':
        ready()
        return
    from PIL import Image, ImageTk
    root.withdraw()
    window=tk.Toplevel(root)
    window.overrideredirect(True)
    width,height=560,290
    window.geometry(f'{width}x{height}+{max(0,(root.winfo_screenwidth()-width)//2)}+{max(0,(root.winfo_screenheight()-height)//2)}')
    window.configure(background='#14101f',highlightbackground='#7355a5',highlightthickness=1)
    if (ASSETS/'bubble-studio.png').is_file():
        with Image.open(ASSETS/'bubble-studio.png') as image:
            window.brand_image=ImageTk.PhotoImage(image.resize((124,124),Image.Resampling.LANCZOS))
        tk.Label(window,image=window.brand_image,bg='#14101f').pack(pady=(20,8))
    tk.Label(window,text='Nokturn Bubble Studio',font=('Segoe UI',22,'bold'),fg='#f1eafa',bg='#14101f').pack()
    tk.Label(window,text='Przygotowanie Twojego warsztatu komiksów…',font=('Segoe UI',11),fg='#bcaed0',bg='#14101f').pack(pady=8)
    def finish():
        window.destroy()
        root.deiconify()
        ready()
    root.after(1100,finish)
