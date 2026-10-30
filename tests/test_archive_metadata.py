import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image
from web.backend.comic_archive import list_image_entries,read_entry,ComicArchiveError


class ArchiveMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.root=Path(self.temp.name)
        stream=io.BytesIO();Image.new('RGB',(40,60),'white').save(stream,'PNG');self.image=stream.getvalue()
        self.resource=b'\x00\x05\x16\x07'+b'macOS resource fork'
    def tearDown(self):self.temp.cleanup()

    def test_zip_metadata_does_not_create_phantom_pages(self):
        path=self.root/'Próba komiksu.cbz'
        with zipfile.ZipFile(path,'w') as archive:
            for name in ['10.png','2.png','.cover.png','pages/1.png']:
                archive.writestr(name,self.image)
            for name in ['__MACOSX/._10.png','pages/._2.png','__MacOsX/extra.png']:
                archive.writestr(name,self.resource)
        entries=list_image_entries(path)
        self.assertEqual([name for name,size in entries],['2.png','10.png','.cover.png','pages/1.png'])
        for name,size in entries:self.assertEqual(read_entry(path,name),self.image)
        with self.assertRaises(ComicArchiveError):read_entry(path,'pages/._2.png')

    def test_folder_metadata_is_ignored_but_dot_folder_images_remain(self):
        for name,data in [('2.png',self.image),('.real-pages/1.png',self.image),
                          ('._2.png',self.resource),('__MACOSX/3.png',self.resource)]:
            file=self.root/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
        entries=list_image_entries(self.root)
        self.assertEqual([name for name,size in entries],['2.png','.real-pages/1.png'])

    def test_rar_and_backslash_names_share_the_same_metadata_filter(self):
        from web.backend.comic_archive import _safe_entry_name
        self.assertIsNone(_safe_entry_name('__MACOSX\\._page.jpg'))
        self.assertIsNone(_safe_entry_name('pages\\._page.jpg'))
        self.assertEqual(_safe_entry_name('pages\\page.jpg'),'pages/page.jpg')


if __name__=='__main__':unittest.main()
