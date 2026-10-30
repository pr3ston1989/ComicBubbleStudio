"""Regression coverage for the standalone model loader, without production weights."""

from types import SimpleNamespace
import sys

import pytest

from tools.bubble_studio import models


def test_detector_loader_uses_only_supported_arguments(monkeypatch):
    calls = {}

    class Model:
        def to(self, device):
            calls['device'] = device
            return self

        def eval(self):
            calls['eval'] = True
            return self

    def from_pretrained(name, *, revision, use_safetensors, trust_remote_code):
        calls['source'] = (name, revision)
        assert use_safetensors and not trust_remote_code
        return Model()

    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace(
        AutoModelForObjectDetection=SimpleNamespace(from_pretrained=from_pretrained)))
    models._load_detector()
    assert calls == {'source': models.DETECTOR, 'device': 'cuda', 'eval': True}


def test_real_transformers_rtdetr_v2_loader_and_forward(tmp_path, monkeypatch):
    """Exercise the real optional GPU dependency on CPU with tiny random weights."""
    transformers = pytest.importorskip('transformers')
    torch = pytest.importorskip('torch')
    torch.set_num_threads(2)
    config = transformers.RTDetrV2Config(
        backbone_config=transformers.RTDetrResNetConfig(
            embedding_size=8, hidden_sizes=[8, 16, 32, 64], depths=[1, 1, 1, 1],
            layer_type='basic', out_indices=[2, 3, 4]),
        encoder_in_channels=[16, 32, 64], encoder_hidden_dim=32,
        encoder_attention_heads=4, encoder_ffn_dim=64, d_model=32,
        decoder_in_channels=[32, 32, 32], decoder_attention_heads=4,
        decoder_ffn_dim=64, decoder_layers=1, num_queries=10, num_labels=3,
    )
    model = transformers.RTDetrV2ForObjectDetection(config).eval()
    model.save_pretrained(tmp_path, safe_serialization=True)
    # Najpierw odtwarzamy dokładnie wyjątek z logu użytkownika.
    with pytest.raises(TypeError, match='disable_custom_kernels'):
        transformers.AutoModelForObjectDetection.from_pretrained(
            tmp_path, use_safetensors=True, disable_custom_kernels=True)
    monkeypatch.setattr(models, 'DETECTOR', (str(tmp_path), 'local-test'))
    loaded = models._load_detector('cpu')
    with torch.inference_mode():
        result = loaded(pixel_values=torch.rand(1, 3, 64, 64))
    assert result.logits.shape == (1, 10, 3)
    assert torch.isfinite(result.logits).all()
    assert torch.isfinite(result.pred_boxes).all()


def test_runner_creates_yolo_config_before_loading_optional_models(tmp_path, monkeypatch):
    from tools.bubble_studio import runner
    directory = tmp_path / 'not-created' / 'yolo'
    monkeypatch.setenv('YOLO_CONFIG_DIR', str(directory))
    assert runner.main(['--input', str(tmp_path / 'input'), '--output', str(tmp_path / 'output')]) == 0
    assert directory.is_dir()


def test_real_sam2_processor_box_and_point_prompt_shapes():
    """Exercise the pinned public processor without downloading weights or requiring CUDA."""
    transformers = pytest.importorskip('transformers')
    from PIL import Image
    processor = transformers.Sam2Processor(image_processor=transformers.Sam2ImageProcessorFast())
    inputs = processor(images=Image.new('RGB', (180, 240)), input_boxes=[[[20, 30, 160, 210]]],
                       input_points=[[[[90, 120], [2, 2], [178, 238]]]],
                       input_labels=[[[1, 0, 0]]], return_tensors='pt')
    assert tuple(inputs['input_boxes'].shape) == (1, 1, 4)
    assert tuple(inputs['input_points'].shape) == (1, 1, 3, 2)
    assert tuple(inputs['input_labels'].shape) == (1, 1, 3)
    assert inputs['original_sizes'].tolist() == [[240, 180]]


def test_real_tiny_sam2_forward_and_native_mask_postprocessing():
    """Test actual box-plus-points inference API with tiny random weights, not production quality."""
    transformers = pytest.importorskip('transformers')
    torch = pytest.importorskip('torch')
    from PIL import Image
    torch.set_num_threads(2)
    backbone = transformers.Sam2HieraDetConfig(hidden_size=8, image_size=[64, 64],
        blocks_per_stage=[1, 1, 1, 1], embed_dim_per_stage=[8, 16, 32, 64],
        num_attention_heads_per_stage=[1, 1, 2, 4], window_size_per_stage=[4, 2, 2, 2],
        global_attention_blocks=[])
    vision = transformers.Sam2VisionConfig(backbone_config=backbone, backbone_channel_list=[64, 32, 16, 8],
        backbone_feature_sizes=[[16, 16], [8, 8], [4, 4]], fpn_hidden_size=32)
    config = transformers.Sam2Config(vision_config=vision,
        prompt_encoder_config=transformers.Sam2PromptEncoderConfig(hidden_size=32, image_size=64),
        mask_decoder_config=transformers.Sam2MaskDecoderConfig(hidden_size=32, mlp_dim=64,
            num_hidden_layers=1, num_attention_heads=4, iou_head_hidden_dim=32))
    model = transformers.Sam2Model(config).eval()
    processor = transformers.Sam2Processor(image_processor=transformers.Sam2ImageProcessorFast(size={'height': 64, 'width': 64}))
    inputs = processor(images=Image.new('RGB', (80, 120)), input_boxes=[[[10, 20, 60, 100]]],
                       input_points=[[[[40, 50], [2, 2]]]], input_labels=[[[1, 0]]], return_tensors='pt')
    with torch.inference_mode():
        outputs = model(**inputs, multimask_output=True)
    masks = processor.post_process_masks(outputs.pred_masks.float().cpu(), inputs['original_sizes'].cpu())[0]
    assert masks.reshape(-1, 120, 80).shape == (3, 120, 80)
    assert torch.isfinite(outputs.iou_scores).all()
