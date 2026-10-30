"""Exercise the real Tk widgets at the supported window sizes."""
import os
import sys
import unittest
from pathlib import Path
base=Path(sys.base_prefix)/'tcl'
for key,folder in [('TCL_LIBRARY','tcl8.6'),('TK_LIBRARY','tk8.6')]:
    if (base/folder).is_dir(): os.environ.setdefault(key,str(base/folder))
import tkinter as tk
from tkinter import ttk
from tools.bubble_studio.gui import Studio, command

@unittest.skipUnless(sys.platform=='win32','Windows desktop layout')
class StudioLayoutTests(unittest.TestCase):
    def test_all_buttons_and_log_fit_minimum_and_default_windows(self):
        root=tk.Tk()
        try:
            studio=Studio(root)
            for size in ('870x730','1040x880'):
                root.geometry(size)
                root.update()
                def descendants(widget):
                    for child in widget.winfo_children():
                        yield child
                        yield from descendants(child)
                buttons=[w for w in descendants(root) if isinstance(w,ttk.Button)]
                self.assertGreaterEqual(len(buttons),8)
                for button in buttons:
                    x=button.winfo_rootx()-root.winfo_rootx()
                    y=button.winfo_rooty()-root.winfo_rooty()
                    self.assertGreaterEqual(x,0)
                    self.assertGreaterEqual(y,0)
                    self.assertLessEqual(x+button.winfo_width(),root.winfo_width())
                    self.assertLessEqual(y+button.winfo_height(),root.winfo_height())
                self.assertGreater(studio.log.winfo_height(),35)
            self.assertTrue(studio.dialogue.get())
            self.assertFalse(studio.export_enabled.get())
            self.assertFalse(studio.export_extra.get())
            argv=command('D:\\Zażółć & manga','D:\\wyniki','D:\\praca','precise',recover_dialogue=True)
            self.assertIn('D:\\Zażółć & manga',argv)
            self.assertIn('--recover-dialogue',argv)
        finally:
            root.destroy()

if __name__=='__main__': unittest.main()
