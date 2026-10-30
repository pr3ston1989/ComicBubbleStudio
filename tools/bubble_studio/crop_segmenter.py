"""Pinned MA-Net balloon-crop segmenter; restricted state-dict loading."""
import hashlib
import cv2
import numpy as np

MODEL = ('toontra-research/toontra-manet-bubble-segmentation', 'f2f1c4eb1b2f7c492146da82d51fa474f54560cc')
SHA256 = '6350601676c9e2b5448cf4cf109fb459a1f805d4101cfe34d4db47661f28df21'


class CropSegmenter:
    def __init__(self, device='cuda'):
        import torch
        import segmentation_models_pytorch as smp
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(MODEL[0], 'manet_bubble_segmentation.pth', revision=MODEL[1])
        with open(path, 'rb') as stream:
            if hashlib.sha256(stream.read()).hexdigest() != SHA256:
                raise RuntimeError('Nieprawidłowa suma kontrolna MA-Net')
        state = torch.load(path, map_location='cpu', weights_only=True)
        self.model = smp.MAnet(encoder_name='resnet34', encoder_weights=None, in_channels=3, classes=1)
        self.model.load_state_dict(state['state_dict'], strict=True)
        self.model = self.model.to(device).eval()
        self.threshold = float(state['threshold'])
        if not .1 <= self.threshold <= .9:
            raise ValueError('Nieprawidłowy próg MA-Net')
        self.torch, self.device = torch, device

    def predict(self, image):
        width,height=image.size
        scale=512/max(width,height)
        w,h=max(1,round(width*scale)),max(1,round(height*scale))
        x,y=(512-w)//2,(512-h)//2
        canvas=np.ones((512,512,3),np.float32)
        canvas[y:y+h,x:x+w]=np.asarray(image.resize((w,h)))/255.
        canvas=(canvas-np.array([.485,.456,.406],np.float32))/np.array([.229,.224,.225],np.float32)
        tensor=self.torch.from_numpy(canvas.transpose(2,0,1).copy())[None].to(self.device)
        with self.torch.inference_mode():
            probabilities=self.model(tensor).sigmoid()[0,0].float().cpu().numpy()
        mask=(probabilities[y:y+h,x:x+w]>=self.threshold).astype(np.uint8)*255
        return cv2.resize(mask,(width,height),interpolation=cv2.INTER_NEAREST)
