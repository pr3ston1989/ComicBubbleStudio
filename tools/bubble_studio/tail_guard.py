"""Restore only image-supported extensions of an otherwise unchanged balloon."""
import cv2
import numpy as np
from .geometry import padded_box, contour_box
from .quality_guard import _polygons
from .refinement import boundary_support, enclosed_candidates
from .segmentation import validate_candidate
from .textcheck import pixel_box


def screened_tail_guard(image, bubble, texts):
    """A halftone-aware fill may extend a truncated tail, never replace its body.

    Only confident in-balloon text is eligible. Require stable bounded colour
    evidence, almost complete preservation of the existing mask, a narrow long
    addition and a false old boundary unsupported by contrast in the image.
    """
    if (len(bubble.get('polygons',[]))!=1 or not texts
            or not all(t.get('label')==1 and t.get('score',0)>=.7 for t in texts)):
        return bubble,None
    bounds=pixel_box(bubble,image.size)
    region=padded_box(bounds,*image.size,1.2)
    if (region[2]-region[0])*(region[3]-region[1])>8_000_000:
        return bubble,None
    crop=image.crop(region)
    old=np.zeros((crop.height,crop.width),np.uint8)
    cv2.fillPoly(old,_polygons(bubble,*image.size,region[:2]),255)
    support=boundary_support(old,crop)
    if not .65<=support<.98:
        return bubble,None
    old_area=np.count_nonzero(old)
    old_boundary=(old>0)&(cv2.erode(old,np.ones((3,3),np.uint8))==0)
    rgb=np.asarray(crop)
    edges=cv2.Canny(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),50,120)
    for channel in cv2.split(rgb):edges|=cv2.Canny(channel,50,120)
    near=cv2.dilate(edges,np.ones((7,7),np.uint8))>0
    for item in enclosed_candidates(crop,bounds,texts,region,image.size,opening=3):
        proposed,error,metrics=validate_candidate(item['mask'],bounds,texts,region,image.size,crop)
        if error or item['stability']<.98 or boundary_support(proposed,crop)<.97:
            continue
        preserved=np.count_nonzero((old>0)&(proposed>0))/max(1,old_area)
        core=cv2.erode(old,np.ones((5,5),np.uint8))>0
        core_coverage=np.count_nonzero(core&(proposed>0))/max(1,np.count_nonzero(core))
        added=((proposed>0)&(old==0)).astype(np.uint8)
        growth=np.count_nonzero(added)/max(1,old_area)
        if preserved<.97 or core_coverage<.995 or not .03<=growth<=.20:
            continue
        # Subpixel edge differences are not a missing tail. A genuine recovery
        # extends far beyond the body but remains thin in the transverse axis.
        distance=cv2.distanceTransform((old==0).astype(np.uint8),cv2.DIST_L2,5)
        reach=float(np.max(distance[added>0]))
        thickness=float(np.max(cv2.distanceTransform(added,cv2.DIST_L2,5)))*2
        shortest=min(bounds[2]-bounds[0],bounds[3]-bounds[1])
        if reach<max(18,shortest*.12) or thickness>shortest*.35:
            continue
        replaced=old_boundary&(cv2.erode(proposed,np.ones((7,7),np.uint8))>0)
        replaced_count=np.count_nonzero(replaced)
        unsupported=np.count_nonzero(replaced&~near)/max(1,replaced_count)
        if replaced_count<16 or unsupported<.60:
            continue
        # Union retains every pixel of the old contour; classification, text
        # anchors and confidence remain those of the original detection.
        merged=cv2.bitwise_or(old,proposed)
        result=contour_box(merged,region,*image.size,bubble['confidence'])
        return result,{'reason':'screened-tail-recovery','growth':round(growth,4),
                       'original_mask_preserved':1.0,'candidate_core_coverage':round(core_coverage,4),
                       'extension_pixels':round(reach,2),
                       'false_boundary_fraction':round(unsupported,4),'original_region':dict(bubble)}
    return bubble,None
