"""Small local queue UI; inference runs in an interruptible, resumable child process."""

from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .runner import ROOT
from .config import VERSION


def command(input_path, output_path, work_path, quality, extra=False, free_text=False, force=False,
            text_guard='review', recover_dialogue=False, text_export='off', export_all_text=False):
    """Build literal argv, never a shell command from user-selected paths."""
    args = [sys.executable, '-u', '-m', 'tools.bubble_studio.runner', '--input', str(input_path),
            '--output', str(output_path), '--work', str(work_path), '--quality', quality, '--text-guard', text_guard]
    for enabled, flag in ((extra, '--extra-segmenter'), (free_text, '--include-free-text'), (force, '--force')):
        if enabled:
            args.append(flag)
    if not extra:
        args.append('--no-extra-segmenter')
    if recover_dialogue:
        args.append('--recover-dialogue')
    if text_export!='off':
        args.extend(['--text-export',text_export])
        if export_all_text:args.append('--export-all-text')
    return args


class Studio:
    """Keep widgets responsive while models download and GPU pages are processed."""

    def __init__(self, root):
        self.root, self.process, self.events = root, None, queue.Queue()
        self.reviewer = None
        self.process_kind = 'queue'
        self.lab_output = None
        self.input = tk.StringVar(value=str(ROOT / 'WEJSCIE'))
        self.output = tk.StringVar(value=str(ROOT / 'GOTOWE'))
        self.quality = tk.StringVar(value='Dokładny')
        self.extra, self.free_text, self.force = tk.BooleanVar(value=True), tk.BooleanVar(), tk.BooleanVar()
        self.text_review = tk.BooleanVar(value=True)
        self.dialogue = tk.BooleanVar(value=True)
        self.export_enabled=tk.BooleanVar(value=False)
        self.export_extra=tk.BooleanVar(value=False)
        self.export_format=tk.StringVar(value='HTML + TXT')
        self.state = tk.StringVar(value='Dodaj CBZ/CBR, PDF lub foldery stron. Manga → RTL; Komiksy/Manhua → LTR.')
        root.title('Nokturn Bubble Studio '+VERSION.removeprefix('bubble-studio-')+' — przygotowanie i kontrola')
        root.geometry(f'1040x{min(880,root.winfo_screenheight()-100)}')
        root.minsize(870, 730)
        from .branding import configure, header
        configure(root)
        ttk.Style(root).configure('TCheckbutton', padding=(0, 2))
        frame = ttk.Frame(root, padding=14)
        frame.pack(fill='both', expand=True)
        header(frame)
        ttk.Label(frame, text='Oryginały pozostają nietknięte. Webtoony pomijamy. Wyniki kopiujesz razem z komiksami.',
                  wraplength=900).pack(anchor='w', pady=(2, 6))
        for label, variable in (('Komiksy wejściowe', self.input), ('Gotowe komiksy i pakiety', self.output)):
            row = ttk.Frame(frame)
            row.pack(fill='x', pady=3)
            ttk.Label(row, text=label, width=26).pack(side='left')
            ttk.Entry(row, textvariable=variable).pack(side='left', fill='x', expand=True)
            ttk.Button(row, text='Wybierz…', command=lambda v=variable: self.choose(v)).pack(side='left', padx=(8, 0))
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=6)
        ttk.Label(row, text='Profil jakości', width=26).pack(side='left')
        ttk.Combobox(row, state='readonly', textvariable=self.quality, values=['Dokładny', 'Szybszy'], width=20).pack(side='left')
        ttk.Checkbutton(frame, text='Dodatkowe modele obrysów: komiksy i wycinki dymków', variable=self.extra).pack(anchor='w')
        ttk.Checkbutton(frame, text='Uwzględniaj także tekst poza dymkami (może objąć okładki/reklamy)', variable=self.free_text).pack(anchor='w')
        ttk.Checkbutton(frame, text='Kontroluj tekst lokalnym OCR (wspiera analizę kontekstu)', variable=self.text_review).pack(anchor='w')
        ttk.Checkbutton(frame, text='Odzyskuj myśli i narrację; profil Dokładny analizuje też kontekst strony lokalnie', variable=self.dialogue).pack(anchor='w')
        ttk.Checkbutton(frame, text='Przelicz gotowe niesprawdzone strony (zatwierdzone korekty zachowaj)', variable=self.force).pack(anchor='w')
        export_frame=ttk.LabelFrame(frame,text='Dodatkowy eksport tekstu do tłumaczenia',padding=(8,4))
        export_frame.pack(fill='x',pady=(8,0))
        export_row=ttk.Frame(export_frame);export_row.pack(fill='x')
        ttk.Checkbutton(export_row,text='Zapisuj także tekst podczas przygotowania komiksu',variable=self.export_enabled).pack(side='left')
        ttk.Combobox(export_row,state='readonly',textvariable=self.export_format,values=['HTML + TXT','TXT','Markdown'],width=16).pack(side='right')
        export_row=ttk.Frame(export_frame);export_row.pack(fill='x',pady=(3,0))
        ttk.Checkbutton(export_row,text='Także pozostałe napisy poza dymkami (np. efekty)',variable=self.export_extra).pack(side='left')
        ttk.Button(export_row,text='Tekst z gotowych pakietów…',command=self.export_existing).pack(side='right')
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=8)
        self.start_button = ttk.Button(buttons, text='Przygotuj / wznów', command=self.start)
        self.start_button.pack(side='left')
        self.stop_button = ttk.Button(buttons, text='Zatrzymaj bez utraty gotowych stron', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=8)
        actions=ttk.Frame(frame)
        actions.pack(fill='x',pady=(0,8))
        ttk.Button(actions, text='Edytor konturów', command=self.review).pack(side='left')
        ttk.Button(actions, text='Raport', command=self.report).pack(side='left', padx=8)
        ttk.Button(actions, text='Wyniki', command=self.open_output).pack(side='left')
        ttk.Button(actions, text='Układ tytułu…', command=self.reading_settings).pack(side='left', padx=8)
        self.lab_button=ttk.Button(actions,text='Losuj i testuj strony…',command=self.start_lab)
        self.lab_button.pack(side='left',padx=8)
        ttk.Button(actions, text='Instrukcja', command=self.instructions).pack(side='right')
        ttk.Label(frame, textvariable=self.state, wraplength=900).pack(anchor='w', pady=6)
        self.bar = ttk.Progressbar(frame, mode='determinate', maximum=100)
        self.bar.pack(fill='x', pady=6)
        self.log = tk.Text(frame, background='#181320', foreground='#ece5f4', insertbackground='white',
                           font=('Consolas', 10), wrap='word', state='disabled')
        self.log.pack(fill='both', expand=True)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def reading_settings(self):
        if self.process and self.process.poll() is None:
            messagebox.showinfo('Praca trwa', 'Zmień układ po zakończeniu bieżącego przetwarzania.')
            return
        from .config import save_reading_mode
        from .title_settings import load_title_settings
        window=tk.Toplevel(self.root)
        window.title('Układ wybranego tytułu')
        window.resizable(False,False)
        frame=ttk.Frame(window,padding=18);frame.pack(fill='both',expand=True)
        selected=tk.StringVar()
        mode=tk.StringVar(value='Automatyczny')
        direction=tk.StringVar(value='Zachowaj obecny')
        settings_note=tk.StringVar(value='Wybierz tytuł, aby odczytać jego ustawienia.')
        ttk.Label(frame,text='Wybierz jeden komiks albo folder jednej serii.',wraplength=570).pack(anchor='w')
        ttk.Entry(frame,textvariable=selected,width=78).pack(fill='x',pady=8)
        buttons=ttk.Frame(frame);buttons.pack(fill='x')
        def choose(folder=False):
            path=(filedialog.askdirectory(title='Folder jednej serii',initialdir=self.input.get(),parent=window) if folder else
                  filedialog.askopenfilename(title='Komiks',initialdir=self.input.get(),parent=window,
                      filetypes=[('Komiksy','*.cbz *.cbr *.zip *.rar *.pdf'),('Wszystkie pliki','*.*')]))
            if not path:return
            selected.set(path)
            try:
                loaded=load_title_settings(Path(path), Path(self.input.get()))
                values=loaded['settings']
                settings_note.set(loaded['description'])
                mode.set('4koma — całe pionowe historyjki' if values.get('reading_mode')=='four_panel_strips' else 'Automatyczny')
                direction.set({'rtl':'Od prawej do lewej (manga)','ltr':'Od lewej do prawej'}.get(values.get('direction'),'Zachowaj obecny'))
            except (OSError,ValueError,AttributeError) as error:
                settings_note.set('Nie odczytano ustawień wybranego tytułu.')
                messagebox.showerror('Nie udało się odczytać ustawień',str(error),parent=window)
        ttk.Button(buttons,text='Wybierz komiks…',command=choose).pack(side='left')
        ttk.Button(buttons,text='Wybierz folder serii…',command=lambda:choose(True)).pack(side='left',padx=8)
        ttk.Label(frame,textvariable=settings_note,wraplength=570).pack(anchor='w',pady=(10,0))
        ttk.Label(frame,text='Układ stron').pack(anchor='w',pady=(14,3))
        ttk.Combobox(frame,state='readonly',textvariable=mode,values=['Automatyczny','4koma — całe pionowe historyjki'],width=46).pack(anchor='w')
        ttk.Label(frame,text='Kierunek czytania').pack(anchor='w',pady=(10,3))
        ttk.Combobox(frame,state='readonly',textvariable=direction,values=['Zachowaj obecny','Od prawej do lewej (manga)','Od lewej do prawej'],width=46).pack(anchor='w')
        ttk.Label(frame,text='4koma: najpierw cała pionowa historyjka, potem następna. Strony o innym układzie nadal wymagają rozpoznania kadrów. Wybór dotyczy tego tytułu; pozostałe komiksy zachowują swoje ustawienia.',wraplength=570).pack(anchor='w',pady=12)
        def save():
            try:
                if not selected.get().strip():raise ValueError('Najpierw wybierz komiks albo folder jednej serii.')
                save_reading_mode(Path(selected.get()),'four_panel_strips' if mode.get().startswith('4koma') else 'auto',
                    {'Od prawej do lewej (manga)':'rtl','Od lewej do prawej':'ltr'}.get(direction.get()))
            except (OSError,ValueError,TypeError) as error:
                messagebox.showerror('Nie udało się zapisać',str(error),parent=window);return
            self.state.set('Zapisano układ tytułu. Użyj „Przygotuj / wznów”; zmieniony układ przeliczy niesprawdzone strony, zachowując zatwierdzone korekty.')
            window.destroy()
        ttk.Button(frame,text='Zapisz ustawienia tytułu',command=save).pack(anchor='e')
        return window

    def choose(self, variable):
        selected = filedialog.askdirectory(initialdir=variable.get())
        if selected:
            variable.set(selected)

    def append(self, line):
        self.log.configure(state='normal')
        self.log.insert('end', line + '\n')
        if int(self.log.index('end-1c').split('.')[0]) > 1500:
            self.log.delete('1.0', '300.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def start(self):
        if self.process and self.process.poll() is None:
            return
        if self.reviewer and self.reviewer.poll() is None:
            messagebox.showinfo('Edytor otwarty', 'Zapisz korekty i zamknij edytor przed przeliczaniem pakietów.')
            return
        argv = command(Path(self.input.get()).resolve(), Path(self.output.get()).resolve(), ROOT / 'PRACA',
                       'precise' if self.quality.get() == 'Dokładny' else 'fast',
                       self.extra.get(), self.free_text.get(), self.force.get(),
                       'review' if self.text_review.get() else 'off',
                       self.dialogue.get(),self.selected_export() if self.export_enabled.get() else 'off',self.export_extra.get())
        try:
            self.process_kind = 'queue'
            self.process = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            text=True, encoding='utf-8', errors='replace',
                                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as exc:
            messagebox.showerror('Nie udało się uruchomić', str(exc))
            return
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.state.set('Przygotowanie modeli — pierwsze pobieranie może potrwać. Szczegóły poniżej.')
        self.bar.configure(mode='indeterminate')
        self.bar.start(20)
        threading.Thread(target=self.read_output, args=(self.process,), daemon=True).start()

    def selected_export(self):
        return {'HTML + TXT':'html','TXT':'txt','Markdown':'md'}[self.export_format.get()]

    def export_existing(self):
        if self.process and self.process.poll() is None:
            messagebox.showinfo('Praca trwa','Poczekaj na zakończenie bieżącej pracy.');return
        if self.reviewer and self.reviewer.poll() is None:
            messagebox.showinfo('Edytor otwarty','Zapisz korekty i zamknij edytor przed eksportem tekstu.');return
        argv=[sys.executable,'-u','-m','tools.bubble_studio.runner','--input',self.output.get(),'--export-only','--text-export',self.selected_export()]
        if self.export_extra.get():argv.append('--export-all-text')
        try:
            self.process=subprocess.Popen(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except OSError as error:
            messagebox.showerror('Nie udało się uruchomić eksportu',str(error));return
        self.process_kind='text';self.start_button.configure(state='disabled');self.stop_button.configure(state='normal');self.bar.configure(mode='indeterminate');self.bar.start(20)
        self.state.set('Eksportuję tekst z gotowych pakietów. Obrysy i pakiety pozostają bez zmian.')
        threading.Thread(target=self.read_output,args=(self.process,),daemon=True).start()

    def start_lab(self):
        if self.process and self.process.poll() is None:
            messagebox.showinfo('Praca trwa','Poczekaj na zakończenie bieżącej kolejki.')
            return
        if self.reviewer and self.reviewer.poll() is None:
            messagebox.showinfo('Edytor otwarty','Zapisz korekty i zamknij edytor przed testem GPU.')
            return
        selected=filedialog.askdirectory(title='Folder komiksów do losowego testu',initialdir=self.input.get())
        if not selected:
            return
        from datetime import datetime
        self.lab_output=ROOT/'PRACA'/'quality-lab'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        argv=[sys.executable,'-u','-m','tools.bubble_studio.quality_lab','cycle',
              '--source',selected,'--output',str(self.lab_output),'--recover-dialogue']
        try:
            self.process=subprocess.Popen(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                          text=True,encoding='utf-8',errors='replace',
                                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except OSError as exc:
            messagebox.showerror('Nie udało się uruchomić testu',str(exc))
            return
        self.process_kind='quality'
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.bar.configure(mode='indeterminate')
        self.bar.start(20)
        self.state.set('Losuję próbkę, odkładam tytuły kontrolne i sprawdzam modele. Raport otworzy się po teście.')
        threading.Thread(target=self.read_output,args=(self.process,),daemon=True).start()

    def read_output(self, process):
        from datetime import datetime
        log_dir = ROOT / 'tools' / 'bubble_studio' / '.runtime'
        log = None
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log = (log_dir / ('processing-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.log')).open('w', encoding='utf-8')
        except OSError as exc:
            self.events.put(('line', f'Nie można zapisywać logu: {exc}. Postęp pozostaje widoczny w oknie.'))
        try:
            for line in process.stdout:
                if log is not None:
                    try:
                        log.write(line)
                        log.flush()
                    except OSError as exc:
                        self.events.put(('line', f'Błąd zapisu logu: {exc}. Kontynuuję odczyt postępu.'))
                        try:
                            log.close()
                        except OSError:
                            pass
                        log = None
                self.events.put(('line', line.rstrip()))
        finally:
            if log is not None:
                try:
                    log.close()
                except OSError:
                    pass
            process.stdout.close()
            self.events.put(('done', process.wait()))

    def poll(self):
        for _ in range(100):
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'done':
                self.bar.stop()
                self.bar.configure(mode='determinate')
                self.start_button.configure(state='normal')
                self.stop_button.configure(state='disabled')
                self.state.set('Zakończono. Otwórz raport i sprawdź kontury przed kopiowaniem.' if value == 0
                               else 'Przerwano lub wystąpił błąd. Gotowe checkpointy zachowane; szczegóły w logu.')
                if value==0 and self.process_kind=='text':self.state.set('Eksport tekstu zakończony. Pliki są obok gotowych komiksów; pakiety dymków pozostają bez zmian.')
                if value==0 and self.process_kind=='quality':
                    import webbrowser
                    path=self.lab_output/'results'/'index.html'
                    if path.exists():
                        webbrowser.open(path.resolve().as_uri())
                    self.state.set('Test zakończony. Oceń obrysy, kompletność i kolejność w raporcie porównawczym.')
            elif value.startswith('@@'):
                try:
                    event = json.loads(value[2:])
                    if event['kind'] in {'page','pdf-import','text-export'}:
                        self.bar.stop()
                        self.bar.configure(mode='determinate', value=100*event['page']/event['pages'])
                        phase={'page':'dymki','pdf-import':'import PDF','text-export':'eksport tekstu'}[event['kind']]
                        self.state.set(f'{event["comic"]} — {phase}: strona {event["page"]}/{event["pages"]}')
                    elif event['kind'] == 'comic':
                        self.state.set(f'Komiksy {event["completed"]}/{event["total"]} · {event["comic"]} · {event["status"]}')
                except (ValueError, KeyError, TypeError):
                    self.append(value)
            else:
                self.append(value)
        self.root.after(100, self.poll)

    def stop(self):
        if self.process and self.process.poll() is None and messagebox.askyesno('Przerwij', 'Zatrzymać? Gotowe strony zostaną zachowane. Ponowienie wznowi pracę.'):
            self.process.terminate()
            self.state.set('Zatrzymywanie. Nie kopiuj nieukończonego pakietu.')

    def review(self):
        if self.process and self.process.poll() is None:
            messagebox.showinfo('Przygotowanie trwa', 'Poczekaj na zakończenie lub zatrzymaj kolejkę przed edycją pakietów.')
            return
        if self.reviewer and self.reviewer.poll() is None:
            messagebox.showinfo('Edytor otwarty', 'Edytor jest już uruchomiony.')
            return
        try:
            self.reviewer = subprocess.Popen([sys.executable, '-m', 'tools.bubble_studio.review', '--directory', self.output.get()],
                                             cwd=ROOT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as exc:
            messagebox.showerror('Nie udało się uruchomić edytora', str(exc))

    def instructions(self):
        import webbrowser
        path = Path(__file__).with_name('INSTRUKCJA.html')
        webbrowser.open(path.resolve().as_uri())

    def report(self):
        path = Path(self.output.get()) / '.nokturn-bubble-review' / 'index.html'
        if path.exists():
            import webbrowser
            webbrowser.open(path.resolve().as_uri())
        else:
            messagebox.showinfo('Brak raportu', 'Raport pojawi się po przygotowaniu pierwszego komiksu.')

    def open_output(self):
        path = Path(self.output.get())
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def close(self):
        if self.reviewer and self.reviewer.poll() is None:
            messagebox.showinfo('Edytor otwarty', 'Najpierw zapisz korekty i zamknij edytor.')
            return
        if self.process and self.process.poll() is None:
            self.stop()
            if self.process.poll() is None:
                return
        self.root.destroy()


def main():
    root = tk.Tk()
    from .branding import splash
    splash(root,lambda:Studio(root))
    root.mainloop()


if __name__ == '__main__':
    main()
