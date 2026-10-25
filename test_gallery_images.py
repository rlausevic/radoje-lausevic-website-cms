"""Image dimensions, orientation, transparency and cache invalidation."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil

from gallery_images import GalleryImages, pillow

Image, _ = pillow()


class GalleryImageTests(unittest.TestCase):
    def test_landscape_portrait_and_original_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory) / 'dist'
            assets = dist / 'assets'
            assets.mkdir(parents=True)
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
            dist = Path(directory) / 'dist'
            (dist / 'assets').mkdir(parents=True)
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

    def test_persistent_cache_survives_fresh_build_without_pillow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dist = root / 'first/dist'
            (dist / 'assets').mkdir(parents=True)
            Image.new('RGB', (1100, 700), 'orange').save(dist / 'assets/camera.jpg')
            original = (dist / 'assets/camera.jpg').read_bytes()
            cold = GalleryImages(dist)
            expected = cold.prepare('/assets/camera.jpg')
            self.assertEqual(cold.generated, 1)
            # Simulate a completely new Cloudflare checkout: only originals and
            # repository-backed cache are available; build output does not exist.
            fresh = root / 'fresh'
            shutil.copytree(dist / 'assets', fresh / 'dist/assets')
            shutil.copytree(cold.cache_dir, fresh / 'media/gallery-cache')
            warm = GalleryImages(fresh / 'dist')
            with patch('gallery_images.pillow', side_effect=AssertionError('must not decode or encode')):
                actual = warm.prepare('/assets/camera.jpg')
            self.assertEqual(actual, expected)
            self.assertEqual((warm.reused, warm.generated), (1, 0))
            self.assertEqual((fresh / 'dist/assets/camera.jpg').read_bytes(), original)
            for variant in actual['previews'] + [actual['large']]:
                self.assertEqual((fresh / 'dist' / variant['url'].lstrip('/')).read_bytes(),
                                 (dist / variant['url'].lstrip('/')).read_bytes())

    def test_corrupt_renditions_are_repaired_and_obsolete_cache_is_pruned(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory) / 'dist'
            (dist / 'assets').mkdir(parents=True)
            source = dist / 'assets/camera.jpg'
            Image.new('RGB', (700, 500), 'red').save(source)
            cold = GalleryImages(dist)
            result = cold.prepare('/assets/camera.jpg')
            filename = Path(result['large']['url']).name
            (cold.cache_dir / filename).write_bytes(b'broken')
            repaired = GalleryImages(dist)
            self.assertEqual(repaired.prepare('/assets/camera.jpg'), result)
            self.assertEqual(repaired.generated, 1)
            with Image.open(repaired.cache_dir / filename) as photo:
                self.assertEqual(photo.size, (700, 500))
            Image.new('RGB', (700, 500), 'blue').save(source)
            changed = GalleryImages(dist)
            new = changed.prepare('/assets/camera.jpg')
            self.assertNotEqual(new['large']['url'], result['large']['url'])
            changed.prune_cache()
            self.assertFalse((changed.cache_dir / filename).exists())
            self.assertTrue(source.exists())
            self.assertEqual(len(list(changed.cache_dir.glob('*.json'))), 1)

    def test_recipe_change_invalidates_cache_and_parallel_warmup_deduplicates_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory) / 'dist'
            (dist / 'assets').mkdir(parents=True)
            Image.new('RGB', (100, 80), 'white').save(dist / 'assets/a.png')
            cold = GalleryImages(dist)
            cold.prepare_many(['/assets/a.png', '/assets/a.png'])
            self.assertEqual(cold.generated, 1)
            previous = cold.prepare('/assets/a.png')
            with patch('gallery_images.RECIPE', 'new-recipe'):
                changed = GalleryImages(dist)
                new = changed.prepare('/assets/a.png')
                self.assertEqual(changed.generated, 1)
                self.assertNotEqual(previous['large']['url'], new['large']['url'])


if __name__ == '__main__':
    unittest.main()
