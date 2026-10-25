"""External asset staging interface. Blender must export embedded GLB first."""
import hashlib, shutil, struct
from pathlib import Path

def stage_glb(source, destination, metadata, locked_reference=None):
    source=Path(source);destination=Path(destination)
    if source.suffix.lower()!='.glb':raise ValueError('Export Blender/other tools to embedded GLB first')
    if metadata.get('approved') is not True:raise ValueError('Explicit asset approval required')
    for field in ['license','author','source','reference_sha256']:
        if not isinstance(metadata.get(field),str) or not metadata[field].strip():raise ValueError('Missing '+field)
    if locked_reference and metadata['reference_sha256']!=locked_reference:raise ValueError('Approved appearance reference mismatch')
    data=source.read_bytes()
    if len(data)<20 or data[:4]!=b'glTF' or struct.unpack_from('<I',data,4)[0]!=2 or struct.unpack_from('<I',data,8)[0]!=len(data):raise ValueError('Invalid GLB container')
    if destination.exists():raise ValueError('Never overwrite an existing approved asset')
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
    return dict(metadata,file=destination.name,sha256=hashlib.sha256(data).hexdigest(),status='STAGED_REQUIRES_ENGINE_RIG_AND_VISUAL_REVIEW')
