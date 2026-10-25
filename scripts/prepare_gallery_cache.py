"""Maintain repository-backed gallery renditions for fresh Pages/Worker builds."""
from pathlib import Path
import sys,time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content_archives import read_archive
from gallery_images import GalleryImages


def prepare(root=ROOT):
    root = Path(root)
    started = time.perf_counter()
    processor = GalleryImages(root / 'dist', publish=False)
    processor.cache_dir.mkdir(parents=True, exist_ok=True)
    urls = [photo['image'] for album in read_archive(root, 'gallery').get('albums') or []
            for photo in album.get('photos') or [] if photo.get('image')]
    processor.prepare_many(urls)
    processor.prune_cache()
    print(processor.summary() + f' Cache preparation: {time.perf_counter()-started:.2f}s.')
    return processor


if __name__ == '__main__':
    prepare()
