"""Image dimensions, orientation, transparency and cache invalidation."""
from pathlib import Path
import tempfile
import unittest

from gallery_images import GalleryImages, pillow

Image, _ = pillow()


class GalleryImageTests(unittest.TestCase):
    def test_landscape_portrait_and_original_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            assets = dist / 'assets'
            assets.mkdir()
            source = assets / 'camera.jpg'
            photo = Image.new('RGB', (3200, 2400), 'green')
            exif = photo.getexif()
            exif[274] = 6  # A phone photo requiring clockwise rotation.
            photo.save(source, exif=exif)
            original_bytes = source.read_bytes()
            processor = GalleryImages(dist)
            result = processor.prepare('/assets/camera.jpg')
            self.assertEqual(source.read_bytes(), original_bytes)
            self.assertEqual([(v['width'], v['height']) for v in result['previews']],
                             [(360, 480), (720, 960)])
            with Image.open(dist / result['large']['url'].lstrip('/')) as large:
                self.assertEqual(large.size, (1440, 1920))
                self.assertIsNone(large.getexif().get(274))
            self.assertIs(processor.prepare('/assets/camera.jpg'), result)
            old_url = result['large']['url']
            Image.new('RGB', (3200, 2400), 'blue').save(source)
            replacement = GalleryImages(dist).prepare('/assets/camera.jpg')
            self.assertNotEqual(replacement['large']['url'], old_url)
            self.assertFalse((dist / old_url.lstrip('/')).exists())
            with Image.open(dist / replacement['large']['url'].lstrip('/')) as large:
                self.assertEqual(large.size, (1920, 1440))

    def test_small_transparent_images_are_not_upscaled(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            (dist / 'assets').mkdir()
            Image.new('RGBA', (240, 180), (20, 40, 60, 100)).save(dist / 'assets/small.png')
            processor = GalleryImages(dist)
            result = processor.prepare('/assets/small.png')
            self.assertEqual(len(result['previews']), 1)
            for variant in result['previews'] + [result['large']]:
                with Image.open(dist / variant['url'].lstrip('/')) as image:
                    self.assertEqual(image.size, (240, 180))
                    self.assertEqual(image.mode, 'RGBA')
                    self.assertEqual(image.getpixel((0, 0))[3], 100)
            self.assertIsNone(processor.prepare('https://example.org/photo.jpg'))
            with self.assertRaises(ValueError):
                processor.prepare('/assets/%2e%2e/outside.jpg')


if __name__ == '__main__':
    unittest.main()
