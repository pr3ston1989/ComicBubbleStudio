"""Exercise the actual Tk restore control, including layout and undo state."""
import copy
import io
import json
import tempfile
import tkinter as tk
import unittest
import zipfile
import subprocess
import sys
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
from tools.bubble_studio.review import Reviewer


class FilterReviewWindowTests(unittest.TestCase):
    def test_restore_button_is_visible_and_reversible_in_real_window(self):
        # Tk owns process-global Tcl state. Isolate this second application
        # window from the Studio window test and its destroyed interpreter.
        env=os.environ.copy();env['PYTHONPATH']=str(Path(__file__).resolve().parents[1])
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--window-child'],
                              capture_output=True,text=True,env=env,timeout=45)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def run_window_case(self):
        original={'result':{'width':100,'height':100,'direction':'ltr','panels':[],
            'bubbles':[dict(id='b1',order=1,type='text',source='ocr',confidence=.95,x=.2,y=.2,w=.5,h=.3)]},
            'review':{'verified':False,'flags':['test']},
            'analysis':{'reading_anchors':{'b1':[.4,.3]},'text_check':None}}
        doc=copy.deepcopy(original);doc['result']['bubbles']=[]
        doc['analysis']['content_filter']={'status':'applied','original':{
            'result':copy.deepcopy(original['result']),'review':copy.deepcopy(original['review']),
            'reading_anchors':copy.deepcopy(original['analysis']['reading_anchors']),'text_check':None}}
        if os.environ.get('STUDIO_TEST_CONTEXT')=='1':
            doc['analysis'].pop('content_filter')
            doc['analysis']['page_context']={'status':'applied','original':copy.deepcopy(original)}
        data=io.BytesIO();Image.new('RGB',(100,100),'white').save(data,format='PNG')
        with tempfile.TemporaryDirectory() as folder:
            sidecar=Path(folder)/'review.zip'
            with zipfile.ZipFile(sidecar,'w') as z:z.writestr('page.json',json.dumps(doc))
            package=SimpleNamespace(sidecar=sidecar,manifest={'pages':[{'name':'page.png','data':'page.json'}]})
            root=tk.Tk()
            try:
                with patch('tools.bubble_studio.review.read_entry',return_value=data.getvalue()):
                    editor=Reviewer(root,Path(folder)/'source.cbz',package)
                    for size in ('1250x900','1024x768'):
                        root.geometry(size);root.update();button=editor.restore_filter_button
                        self.assertTrue(button.winfo_ismapped())
                        self.assertLessEqual(button.winfo_rootx()-root.winfo_rootx()+button.winfo_width(),root.winfo_width())
                    button.invoke();root.update()
                    self.assertEqual(len(editor.bubbles),1);self.assertTrue(button.instate(['disabled']))
                    editor.undo();root.update();self.assertEqual(editor.bubbles,[])
                    self.assertFalse(button.instate(['disabled']))
                    editor.redo();root.update();self.assertEqual(len(editor.bubbles),1)
                    self.assertFalse(editor.documents[0]['review']['verified'])
            finally:root.destroy()

    def test_context_button_is_visible_and_reversible_in_real_window(self):
        env=os.environ.copy();env['PYTHONPATH']=str(Path(__file__).resolve().parents[1]);env['STUDIO_TEST_CONTEXT']='1'
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--window-child'],
                              capture_output=True,text=True,env=env,timeout=45)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__' and '--window-child' in sys.argv:
    result=unittest.TextTestRunner().run(unittest.TestSuite([FilterReviewWindowTests('run_window_case')]))
    raise SystemExit(0 if result.wasSuccessful() else 1)
