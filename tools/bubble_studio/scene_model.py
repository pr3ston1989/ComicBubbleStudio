"""Pinned 8B scene understanding with a locally verified NF4 cache."""
from __future__ import annotations
import hashlib,json,os,uuid
from pathlib import Path
from .page_context import SemanticPage
MANIFEST=Path(__file__).resolve().parents[2]/'assets/scene-model.json'
TAG=':bnb0.50.2-nf4-double-bf16'
def manifest():return json.loads(MANIFEST.read_text(encoding='utf8'))
def _sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def _verify_files(folder,rows):
 for row in rows:
  name=row['path']
  if not isinstance(name,str) or Path(name).name!=name or name in {'.','..'}:raise ValueError('Nieprawidłowa nazwa pliku modelu scen')
  if _sha(folder/name)!=row['sha256']:raise ValueError('Nieprawidłowa suma kontrolna modelu scen')
def verified_quantized(folder):
 proof=json.loads((folder/'source-proof.json').read_text(encoding='utf8'));source=manifest()
 if (proof.get('source_manifest_sha256')!=_sha(MANIFEST) or proof.get('revision')!=source['revision'] or
     proof.get('quantization')!=TAG):raise ValueError('Inny model lub sposób kwantyzacji')
 names=[r['path'] for r in proof.get('files',[])]
 if not names or len(names)!=len(set(names)) or 'config.json' not in names or not any(n.endswith('.safetensors') for n in names):raise ValueError('Niekompletne pliki modelu scen')
 _verify_files(folder,proof['files'])
 return proof
class ScenePage(SemanticPage):
 def __init__(self,weights_dir=None,cache_dir=None,strict=False):
  runtime=Path(__file__).with_name('.runtime')/'models'
  super().__init__(cache_dir=cache_dir or os.environ.get('NOKTURN_SCENE_CACHE') or runtime/'scene-context-cache',strict=strict)
  self.weights_dir=Path(weights_dir or os.environ.get('NOKTURN_SCENE_MODEL') or runtime/'scene-qwen3-vl-8b-nf4')
  self.provenance=manifest();self.provenance['revision']+=TAG
 def _load(self):
  import torch
  if self.model is not None:
   self.model.to('cuda');return
  from transformers import Qwen3VLForConditionalGeneration,AutoProcessor,BitsAndBytesConfig
  torch.set_num_threads(6);torch.cuda.empty_cache()
  common=dict(dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
  if self.weights_dir.exists():
   verified_quantized(self.weights_dir)
   self.model=Qwen3VLForConditionalGeneration.from_pretrained(self.weights_dir,**common).eval()
   self.processor=AutoProcessor.from_pretrained(self.weights_dir,local_files_only=True,trust_remote_code=False)
   return
  source=manifest();raw=Path(os.environ.get('NOKTURN_SCENE_SOURCE') or self.weights_dir.with_name('scene-qwen3-vl-8b-source'))
  if not all((raw/r['path']).is_file() for r in source['files']):
   from huggingface_hub import snapshot_download,constants
   constants.HF_HUB_DOWNLOAD_TIMEOUT=max(120,constants.HF_HUB_DOWNLOAD_TIMEOUT)
   print('Przygotowywanie dokładnej analizy scen: jednorazowe pobranie modelu i zmniejszenie go do około 6 GB…',flush=True)
   snapshot_download(source['repository'],revision=source['revision'],local_dir=raw,allow_patterns=[r['path'] for r in source['files']],max_workers=2)
  _verify_files(raw,source['files'])
  config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True)
  self.model=Qwen3VLForConditionalGeneration.from_pretrained(raw,quantization_config=config,**common).eval()
  self.processor=AutoProcessor.from_pretrained(raw,local_files_only=True,trust_remote_code=False)
  staging=self.weights_dir.with_name(self.weights_dir.name+'.building-'+uuid.uuid4().hex);staging.mkdir(parents=True)
  self.model.save_pretrained(staging,safe_serialization=True,max_shard_size='2GB');self.processor.save_pretrained(staging)
  rows=[dict(path=p.name,sha256=_sha(p),size=p.stat().st_size) for p in sorted(staging.iterdir()) if p.is_file()]
  proof=dict(source_manifest_sha256=_sha(MANIFEST),repository=source['repository'],revision=source['revision'],quantization=TAG,files=rows)
  (staging/'source-proof.json').write_text(json.dumps(proof,indent=2),encoding='utf8');verified_quantized(staging)
  staging.replace(self.weights_dir)
  # Reload the saved format before removing only the verified source files.
  self.model.to('cpu');self.model=None;torch.cuda.empty_cache()
  self.model=Qwen3VLForConditionalGeneration.from_pretrained(self.weights_dir,**common).eval()
  self.processor=AutoProcessor.from_pretrained(self.weights_dir,local_files_only=True,trust_remote_code=False)
  if os.environ.get('NOKTURN_SCENE_KEEP_SOURCE')!='1':
   for row in source['files']:
    path=raw/row['path']
    if path.resolve().parent!=raw.resolve():raise ValueError('Nieprawidłowa ścieżka pliku źródłowego modelu')
    if _sha(path)!=row['sha256']:raise ValueError('Zmieniony plik źródłowy modelu')
    path.unlink()
 def _ask(self,images,prompt,max_tokens=100):
  import torch
  previous=torch.backends.cuda.matmul.allow_tf32
  try:
   torch.backends.cuda.matmul.allow_tf32=False
   return super()._ask(images,prompt,max_tokens)
  finally:torch.backends.cuda.matmul.allow_tf32=previous
