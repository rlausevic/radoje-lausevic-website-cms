"""Persistent, content-addressed gallery renditions; CMS originals stay untouched."""
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
# Keep the existing public URLs. Changing the encoder pin invalidates the cache.
ENCODER_VERSION = re.search(r'^Pillow==([^\s]+)', (ROOT / 'requirements.txt').read_text(), re.M)[1]
RECIPE = 'gallery-v1-' + ENCODER_VERSION


@lru_cache(maxsize=1)
def pillow():
    dependencies = ROOT / '.build-deps'
    sys.path.insert(0, str(dependencies))
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError as error:
        if error.name != 'PIL':
            raise
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
            '--only-binary=:all:', '--target', str(dependencies),
            '-r', str(ROOT / 'requirements.txt'),
        ], check=True)
        importlib.invalidate_caches()
        from PIL import Image, ImageOps
    if Image.__version__ != ENCODER_VERSION:
        raise ValueError('Install the pinned Pillow version from requirements.txt before encoding images')
    return Image, ImageOps


def atomic_write(path, data):
    """A canceled build must never leave a half-written reusable rendition."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(data)
            output.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


class GalleryImages:
    def __init__(self, dist, cache_dir=None, publish=True):
        self.dist = Path(dist).resolve()
        self.output = self.dist / 'media/gallery'
        self.publish = publish
        self.cache_dir = Path(cache_dir) if cache_dir else self.dist.parent / 'media/gallery-cache'
        # Only deploy referenced images. The persistent cache lives outside dist.
        if self.publish and self.output.exists():
            shutil.rmtree(self.output)
        self.cache = {}
        self.used = set()
        self.generated = 0
        self.reused = 0

    def _restore(self, digest):
        try:
            result = json.loads((self.cache_dir / (digest + '.json')).read_text())
            if result['recipe'] != RECIPE or len(result['previews']) not in (1, 2):
                return None
            variants = result['previews'] + [result['large']]
            payloads = []
            for variant in variants:
                filename = Path(variant['url']).name
                if not re.fullmatch(digest + r'-(480|960|1920)\.webp', filename):
                    return None
                if variant['url'] != '/media/gallery/' + filename:
                    return None
                if not all(isinstance(variant[k], int) and variant[k] > 0 for k in ('width', 'height')):
                    return None
                data = (self.cache_dir / filename).read_bytes()
                if hashlib.sha256(data).hexdigest() != variant['sha256']:
                    return None
                payloads.append((filename, data))
            for filename, data in payloads:
                target = self.output / filename
                if self.publish and not target.exists():
                    atomic_write(target, data)
                self.used.add(filename)
            self.used.add(digest + '.json')
            return result
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def prepare(self, url):
        if url in self.cache:
            return self.cache[url]
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith('/assets/'):
            return None
        source = (self.dist / unquote(parsed.path).lstrip('/')).resolve()
        if not source.is_relative_to(self.dist / 'assets'):
            raise ValueError('Gallery image must be inside dist/assets: ' + url)
        if source.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
            return None
        digest = hashlib.sha256(RECIPE.encode() + source.read_bytes()).hexdigest()[:24]
        result = self._restore(digest)
        if result is not None:
            self.reused += 1
        else:
            Image, ImageOps = pillow()
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            try:
                with Image.open(source) as original:
                    oriented = ImageOps.exif_transpose(original)
                    mode = 'RGBA' if 'A' in oriented.getbands() or 'transparency' in oriented.info else 'RGB'
                    photo = oriented.convert(mode)
                    profile = original.info.get('icc_profile')
                    def variant(edge, quality):
                        resized = photo.copy()
                        resized.thumbnail((edge, edge), Image.Resampling.LANCZOS)
                        filename = f'{digest}-{edge}.webp'
                        options = {'icc_profile': profile} if profile else {}
                        from io import BytesIO
                        buffer = BytesIO()
                        resized.save(buffer, 'WEBP', quality=quality, method=6, **options)
                        payload = buffer.getvalue()
                        atomic_write(self.cache_dir / filename, payload)
                        return {'url': '/media/gallery/' + filename,
                                'width': resized.width, 'height': resized.height,
                                'sha256': hashlib.sha256(payload).hexdigest()}
                    previews = [variant(480, 78)]
                    if max(photo.size) > 480:
                        previews.append(variant(960, 80))
                    result = {'recipe': RECIPE, 'previews': previews, 'large': variant(1920, 88)}
                    # Write metadata last, after every rendition is complete.
                    atomic_write(self.cache_dir / (digest + '.json'),
                                 (json.dumps(result, sort_keys=True) + '\n').encode())
                result = self._restore(digest)
                if result is None:
                    raise ValueError('Generated gallery cache failed verification: ' + url)
                self.generated += 1
            except (OSError, ValueError) as error:
                raise ValueError(f'Cannot process gallery image {url}: {error}') from error
        # Keep the public return shape compatible with the templates and callers.
        public = {'previews': [{k: v for k, v in x.items() if k != 'sha256'} for x in result['previews']],
                  'large': {k: v for k, v in result['large'].items() if k != 'sha256'}}
        self.cache[url] = public
        return public

    def prepare_many(self, urls):
        # Two image decoders bound peak memory while overlapping WebP encoding.
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(self.prepare, dict.fromkeys(urls)))

    def prune_cache(self):
        """Remove only obsolete generated renditions, never uploaded originals."""
        if self.cache_dir.exists():
            for path in self.cache_dir.iterdir():
                if re.fullmatch(r'[a-f0-9]{24}(?:-(?:480|960|1920)\.webp|\.json)', path.name) and path.name not in self.used:
                    path.unlink()

    def summary(self):
        return f'Gallery images: {self.reused} reused, {self.generated} generated.'
