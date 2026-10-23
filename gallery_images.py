"""Build gallery previews and enlarged images without modifying CMS originals."""
from functools import lru_cache
import hashlib
import importlib
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit


@lru_cache(maxsize=1)
def pillow():
    # Keep the existing Cloudflare build command working on clean build machines.
    dependencies = Path(__file__).resolve().parent / '.build-deps'
    sys.path.insert(0, str(dependencies))
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError as error:
        if error.name != 'PIL':
            raise
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
            '--only-binary=:all:', '--target', str(dependencies),
            '-r', str(Path(__file__).with_name('requirements.txt')),
        ], check=True)
        importlib.invalidate_caches()
        from PIL import Image, ImageOps
    return Image, ImageOps


class GalleryImages:
    def __init__(self, dist):
        self.dist = Path(dist).resolve()
        self.output = self.dist / 'media/gallery'
        # Only this build-owned directory is cleared; uploaded files stay in assets.
        if self.output.exists():
            shutil.rmtree(self.output)
        self.cache = {}

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
        Image, ImageOps = pillow()
        # Recipe + encoder version + source bytes make replacement URLs cache-safe.
        digest = hashlib.sha256(
            ('gallery-v1-' + Image.__version__).encode() + source.read_bytes()
        ).hexdigest()[:24]
        self.output.mkdir(parents=True, exist_ok=True)
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
                    resized.save(self.output / filename, 'WEBP', quality=quality, method=6, **options)
                    return {'url': '/media/gallery/' + filename,
                            'width': resized.width, 'height': resized.height}
                previews = [variant(480, 78)]
                if max(photo.size) > 480:
                    previews.append(variant(960, 80))
                result = {'previews': previews, 'large': variant(1920, 88)}
        except (OSError, ValueError) as error:
            raise ValueError(f'Cannot process gallery image {url}: {error}') from error
        self.cache[url] = result
        return result
