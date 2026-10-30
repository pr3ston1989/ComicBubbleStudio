"""Local manual QA: inspect contours, reorder balloons, and repair safe rectangles."""

from __future__ import annotations

import copy
import argparse
import io
import json
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk, ImageOps
from web.backend.comic_archive import read_entry
from web.backend.comic_bubble_package import load_package, PACKAGE_SUFFIX, validate_result
from .runner import write_package, ROOT
from .editing import polygon_box


class Reviewer:
    """Edit portable geometry without inference, cloud access, or the Nokturn database."""

    def __init__(self, root, source, package):
        self.root, self.source, self.package = root, source, package
        self.index, self.anchor = 0, None
        self.zoom, self.vertices = 1.0, []
        self.undo_stack, self.redo_stack = [], []
        self.documents = []
        with zipfile.ZipFile(package.sidecar) as archive:
            for page in package.manifest['pages']:
                self.documents.append(json.loads(archive.read(page['data'])))
        self.saved_documents = copy.deepcopy(self.documents)
        root.title('Nokturn Bubble Studio — kontrola i korekty')
        root.geometry('1250x900')
        toolbar = ttk.Frame(root, padding=8)
        toolbar.pack(fill='x')
        for label, action in [('◀ Strona', lambda: self.turn(-1)), ('Strona ▶', lambda: self.turn(1)),
                              ('Odwróć kolejność', self.reverse), ('↑ Dymek', lambda: self.move(-1)),
                              ('↓ Dymek', lambda: self.move(1)), ('Usuń dymek', self.delete),
                              ('Sprawdzona ✓', self.verify), ('Zapisz pakiet', self.save)]:
            ttk.Button(toolbar, text=label, command=action).pack(side='left', padx=2)
        controls = ttk.Frame(root, padding=8)
        controls.pack(fill='x')
        self.mode = tk.StringVar(value='Wybór / prostokąt')
        ttk.Combobox(controls, textvariable=self.mode, state='readonly', width=23,
                     values=['Wybór / prostokąt', 'Dodaj kontur', 'Zastąp kontur']).pack(side='left')
        for label, action in [('Zakończ kontur ↵', self.finish_polygon), ('Cofnij', self.undo), ('Ponów', self.redo),
                              ('−', lambda: self.zoom_by(.8)), ('+', lambda: self.zoom_by(1.25)),
                              ('Dopasuj', self.fit), ('Następna do kontroli', self.next_flagged)]:
            ttk.Button(controls, text=label, command=action).pack(side='left', padx=2)
        self.restore_filter_button=None
        if any(any(d.get('analysis',{}).get(k,{}).get('status')=='applied' for k in ('page_context','content_filter')) for d in self.documents):
            filter_controls=ttk.Frame(root,padding=(8,0,8,6));filter_controls.pack(fill='x')
            self.restore_filter_button=ttk.Button(filter_controls,text='Przywróć wykrycia sprzed filtra tej strony',command=self.restore_filtered)
            self.restore_filter_button.pack(side='left')
            ttk.Label(filter_controls,text='Cofnij przywraca poprzedni stan strony.').pack(side='left',padx=10)
        self.status = ttk.Label(root, wraplength=1200, padding=8)
        self.status.pack(fill='x')
        content = ttk.Frame(root)
        content.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(content, width=24, exportselection=False)
        self.listbox.pack(side='left', fill='y')
        self.listbox.bind('<<ListboxSelect>>', lambda _: self.draw())
        viewport = ttk.Frame(content)
        viewport.pack(side='left', fill='both', expand=True)
        viewport.rowconfigure(0, weight=1)
        viewport.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(viewport, background='#17131f', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        xbar, ybar = ttk.Scrollbar(viewport, orient='horizontal', command=self.canvas.xview), ttk.Scrollbar(viewport, command=self.canvas.yview)
        xbar.grid(row=1, column=0, sticky='ew')
        ybar.grid(row=0, column=1, sticky='ns')
        self.canvas.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
        self.canvas.bind('<Configure>', lambda _: self.draw())
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<Double-Button-1>', self.double_click)
        self.canvas.bind('<Control-MouseWheel>', lambda e: self.zoom_by(1.25 if e.delta > 0 else .8))
        self.canvas.bind('<MouseWheel>', lambda e: self.canvas.yview_scroll(-int(e.delta / 120), 'units'))
        root.bind('<Return>', lambda _: self.finish_polygon())
        root.bind('<Escape>', lambda _: self.cancel_polygon())
        root.bind('<BackSpace>', lambda _: self.remove_vertex())
        root.bind('<Control-z>', lambda _: self.undo())
        root.bind('<Control-y>', lambda _: self.redo())
        ttk.Label(root, text='Kliknij dymek, aby go wybrać. Przeciągnij pusty obszar, aby dodać bezpieczny prostokąt. '
                  'Kontur: klikaj punkty, zakończ Enter; Escape anuluje, Backspace cofa punkt. '
                  'Zastąp kontur zachowuje wybrany dymek i kolejność. Ctrl+kółko powiększa; kółko przewija. '
                  'Każda korekta usuwa zatwierdzenie strony. Zapis tworzy kopię pakietu.', wraplength=1200, padding=8).pack(fill='x')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.load_page()

    def selected(self):
        selection = self.listbox.curselection()
        return selection[0] if selection else None

    @property
    def bubbles(self):
        return self.documents[self.index]['result']['bubbles']

    def refresh_list(self, selected=None):
        self.listbox.delete(0, 'end')
        for index, box in enumerate(self.bubbles):
            box['order'] = index + 1
            self.listbox.insert('end', f'{index + 1}. {"kontur" if box.get("polygons") else "prostokąt"}')
        if selected is not None and self.bubbles:
            self.listbox.selection_set(min(selected, len(self.bubbles) - 1))

    def load_page(self):
        self.vertices, self.anchor = [], None
        descriptor = self.package.manifest['pages'][self.index]
        if hasattr(self, 'image'):
            self.image.close()
        with Image.open(io.BytesIO(read_entry(self.source, descriptor['name']))) as image:
            self.image = ImageOps.exif_transpose(image).convert('RGB')
        document = self.documents[self.index]
        if self.restore_filter_button is not None:
            context=document.get('analysis',{}).get('page_context',{}).get('status')=='applied'
            active=context or document.get('analysis',{}).get('content_filter',{}).get('status')=='applied'
            self.restore_filter_button.configure(state='normal' if active else 'disabled',text='Przywróć wykrycia sprzed analizy strony' if context else 'Przywróć wykrycia sprzed filtra tej strony')
        warning = ' · '.join(document['review'].get('flags', []))
        verified = 'SPRAWDZONA' if document['review'].get('verified') else 'do kontroli'
        self.status.configure(text=f'{self.source.name} · strona {self.index + 1}/{len(self.documents)} · {verified}\n{warning}')
        self.refresh_list()
        self.draw()

    def draw(self):
        if not hasattr(self, 'image'):
            return
        self.canvas.delete('all')
        self.scale = min(max(1, self.canvas.winfo_width()) / self.image.width, max(1, self.canvas.winfo_height()) / self.image.height) * self.zoom
        self.preview = ImageTk.PhotoImage(self.image.resize((max(1, round(self.image.width * self.scale)), max(1, round(self.image.height * self.scale)))))
        self.canvas.create_image(0, 0, image=self.preview, anchor='nw')
        sw, sh = self.image.width * self.scale, self.image.height * self.scale
        self.canvas.configure(scrollregion=(0, 0, sw, sh))
        for index, box in enumerate(self.bubbles):
            x, y, w, h = box['x'] * sw, box['y'] * sh, box['w'] * sw, box['h'] * sh
            color = '#ffcb55' if index == self.selected() else '#19d38e' if box.get('polygons') else '#ff7444'
            for polygon in box.get('polygons', []):
                points = [coord for point in polygon for coord in (x + point['x'] * w, y + point['y'] * h)]
                self.canvas.create_polygon(points, fill='', outline=color, width=2)
            if not box.get('polygons'):
                self.canvas.create_rectangle(x, y, x + w, y + h, outline=color, width=2)
            self.canvas.create_text(x + 8, y + 9, text=str(index + 1), fill='#ff3b30', font=('Segoe UI', 14, 'bold'))
        if self.vertices:
            coords = [coord for x, y in self.vertices for coord in (x*sw, y*sh)]
            if len(coords) >= 4:
                self.canvas.create_line(*coords, fill='#ffcb55', width=2)
            for x, y in self.vertices:
                self.canvas.create_oval(x*sw-3, y*sh-3, x*sw+3, y*sh+3, fill='#ffcb55')

    def edit(self):
        self.undo_stack.append((self.index, copy.deepcopy(self.documents[self.index])))
        self.undo_stack = self.undo_stack[-40:]
        self.redo_stack.clear()
        self.documents[self.index]['review']['verified'] = False
        if hasattr(self, 'status'):
            self.status.configure(text=f'{self.source.name} · strona {self.index+1}/{len(self.documents)} · zmieniona — do kontroli')

    def undo(self):
        self.restore(self.undo_stack, self.redo_stack)

    def redo(self):
        self.restore(self.redo_stack, self.undo_stack)

    def restore(self, source, target):
        if source:
            index, previous = source.pop()
            target.append((index, copy.deepcopy(self.documents[index])))
            self.index, self.documents[index] = index, previous
            self.load_page()

    def zoom_by(self, factor):
        self.zoom = min(8, max(.5, self.zoom * factor))
        self.draw()

    def fit(self):
        self.zoom = 1
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.draw()

    def next_flagged(self):
        for offset in range(1, len(self.documents)+1):
            index = (self.index + offset) % len(self.documents)
            document = self.documents[index]
            if not document['review'].get('verified') and (document['review'].get('flags') or
                    any(not box.get('polygons') for box in document['result']['bubbles'])):
                self.index = index
                self.load_page()
                return
        messagebox.showinfo('Kontrola', 'Brak kolejnych stron z ostrzeżeniami. Sprawdź też pozostałe strony.')

    def cancel_polygon(self):
        self.vertices = []
        self.draw()

    def double_click(self, event):
        if self.mode.get() != 'Wybór / prostokąt':
            self.finish_polygon()
        self.anchor = None

    def remove_vertex(self):
        if self.vertices:
            self.vertices.pop()
            self.draw()

    def finish_polygon(self):
        if not self.vertices:
            return
        index = self.selected() if self.mode.get() == 'Zastąp kontur' else None
        if self.mode.get() == 'Zastąp kontur' and index is None:
            messagebox.showinfo('Wybierz dymek', 'Zaznacz dymek na liście przed zastąpieniem konturu.')
            return
        used = {box['id'] for box in self.bubbles}
        identifier = self.bubbles[index]['id'] if index is not None else next(f'b{i}' for i in range(1, 10000) if f'b{i}' not in used)
        try:
            box = polygon_box(self.vertices, identifier)
            if index is None and len(self.bubbles) >= 128:
                raise ValueError('Limit 128 dymków na stronie')
        except ValueError as exc:
            messagebox.showerror('Nieprawidłowy kontur', str(exc))
            return
        self.edit()
        if index is None:
            self.bubbles.append(box)
            index = len(self.bubbles)-1
        else:
            box['panel_id'] = self.bubbles[index].get('panel_id')
            self.bubbles[index] = box
        self.vertices = []
        self.refresh_list(index)
        self.draw()

    def turn(self, offset):
        self.index = min(max(0, self.index + offset), len(self.documents) - 1)
        self.load_page()

    def move(self, offset):
        index = self.selected()
        if index is None or not 0 <= index + offset < len(self.bubbles):
            return
        self.edit()
        self.bubbles[index], self.bubbles[index + offset] = self.bubbles[index + offset], self.bubbles[index]
        self.refresh_list(index + offset)
        self.draw()

    def reverse(self):
        self.edit()
        self.bubbles.reverse()
        self.refresh_list()
        self.draw()

    def restore_filtered(self):
        document=self.documents[self.index]
        context=document.get('analysis',{}).get('page_context',{}).get('status')=='applied'
        if not context and document.get('analysis',{}).get('content_filter',{}).get('status')!='applied':return
        from .content_filter import restore_content_filter
        from .page_context import restore_page_context
        self.edit()
        if context:restore_page_context(document)
        else:restore_content_filter(document)
        self.load_page()

    def delete(self):
        index = self.selected()
        if index is not None:
            self.edit()
            del self.bubbles[index]
            self.refresh_list(index)
            self.draw()

    def verify(self):
        self.edit()
        self.documents[self.index]['review']['verified'] = True
        self.load_page()

    def press(self, event):
        sw, sh = self.image.width * self.scale, self.image.height * self.scale
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.mode.get() != 'Wybór / prostokąt':
            self.vertices.append((max(0, min(x / sw, 1)), max(0, min(y / sh, 1))))
            self.draw()
            return
        self.anchor = (max(0, min(x, sw)), max(0, min(y, sh)))

    def drag(self, event):
        if self.anchor:
            self.canvas.delete('drag')
            self.canvas.create_rectangle(*self.anchor, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), outline='#ffcb55', width=2, tags='drag')

    def release(self, event):
        if not self.anchor:
            return
        sw, sh = self.image.width * self.scale, self.image.height * self.scale
        ex, ey = max(0, min(self.canvas.canvasx(event.x), sw)), max(0, min(self.canvas.canvasy(event.y), sh))
        x1, x2 = sorted([self.anchor[0], ex])
        y1, y2 = sorted([self.anchor[1], ey])
        self.anchor = None
        self.canvas.delete('drag')
        if x2 - x1 < 8 or y2 - y1 < 8:
            for index, box in reversed(list(enumerate(self.bubbles))):
                if box['x'] <= ex / sw <= box['x'] + box['w'] and box['y'] <= ey / sh <= box['y'] + box['h']:
                    self.listbox.selection_clear(0, 'end')
                    self.listbox.selection_set(index)
                    break
        elif len(self.bubbles) < 128:
            self.edit()
            used = {box['id'] for box in self.bubbles}
            identifier = next(f'b{index}' for index in range(1, 10000) if f'b{index}' not in used)
            self.bubbles.append({'id': identifier, 'x': x1 / sw, 'y': y1 / sh, 'w': (x2 - x1) / sw, 'h': (y2 - y1) / sh,
                                 'type': 'bubble', 'source': 'external', 'confidence': 1, 'order': len(self.bubbles) + 1})
            self.documents[self.index]['review']['verified'] = False
            self.refresh_list(len(self.bubbles) - 1)
        self.draw()

    def save(self):
        try:
            for document in self.documents:
                validate_result(document['result'])
            backup = self.package.sidecar.with_name(self.package.sidecar.name + '.before-review')
            if not backup.exists():
                import shutil
                shutil.copy2(self.package.sidecar, backup)
            write_package(self.package.sidecar, self.package.manifest, self.documents)
            self.saved_documents = copy.deepcopy(self.documents)
            messagebox.showinfo('Zapisano', 'Pakiet został zapisany. Kopiuj komiks i poprawiony pakiet do Nokturna. Raport HTML jest podglądem sprzed korekt.')
        except Exception as exc:
            messagebox.showerror('Nie zapisano', str(exc))

    def close(self):
        if self.documents != self.saved_documents and not messagebox.askyesno('Niezapisane zmiany', 'Zamknąć bez zapisywania zmian?'):
            return
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=ROOT / 'GOTOWE')
    args = parser.parse_args()
    root = tk.Tk()
    root.withdraw()
    filename = filedialog.askopenfilename(title='Wybierz pakiet Bubble Studio', initialdir=args.directory, filetypes=[('Bubble View', '*.nokturn-bubbles.zip')])
    if not filename:
        root.destroy()
        return
    sidecar = Path(filename)
    source = sidecar.parent if sidecar.name == PACKAGE_SUFFIX else Path(str(sidecar)[:-len(PACKAGE_SUFFIX)])
    package = load_package(source)
    if not package:
        messagebox.showerror('Nieprawidłowy pakiet', 'Komiks musi znajdować się obok pakietu i mieć identyczną zawartość.')
        root.destroy()
        return
    root.deiconify()
    Reviewer(root, source, package)
    root.mainloop()


if __name__ == '__main__':
    main()
