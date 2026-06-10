import pymupdf
import numpy as np
from PIL import Image
import onnxruntime as ort

#these are the names from the model, I'm going through all of this to avoid telemetry
CLASS_NAMES = {
    0: "Caption",
    1: "Footnote",
    2: "Formula",
    3: "List-item",
    4: "Page-footer",
    5: "Page-header",
    6: "Picture",
    7: "Section-header",
    8: "Table",
    9: "Text",
    10: "Title",
}

# when you run the yolo layour model you get a bunch of different bounding boxes, some are just a few pixels croping the
#figure and the other are fine, here we are just collecting the bounding boxes and then selecting the largest one that shares
# greater than n (0.8) fraction overlap. Becaue there can be multiple figures in a page we are only getting the larges that
# overlaps with the smaller ones.

def box_area(box):
    x1, y1, x2, y2 = box
    return max(0, x2 - x1) * max(0, y2 - y1)

def intersection_area(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return max(0, x2 - x1) * max(0, y2 - y1)

def containment_ratio(inner, outer):
    inter = intersection_area(inner, outer)
    area = box_area(inner)
    return inter / area if area > 0 else 0.0

def filter_figures(boxes, mode="top_level", containment_thresh=0.8):
    """
    Keep only outer figures (remove sub-panels).
    """

    assert mode in ("top_level", "sub_panels")

    n = len(boxes)
    is_contained = [False] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if containment_ratio(boxes[i], boxes[j]) >= containment_thresh:
                is_contained[i] = True
                break
    if mode == "top_level":
        return [b for b, c in zip(boxes, is_contained) if not c]
    return [b for b, c in zip(boxes, is_contained) if c]

def render_page(page, zoom=2):
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    img = Image.frombytes("RGB",(pix.width, pix.height),
        pix.samples,
    )
    return img

class LayoutONNX:
    def __init__(self, onnx_path):
        self.session = ort.InferenceSession(
            onnx_path,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name

    @staticmethod
    def preprocess(pil_img, size=1280):
        """
        preprocess the page image
        :param pil_img: image extracted from the pdf
        :param size: size to be used do not change this if you are not sure, this is kind of model specific
        :return: processed image ready to be used for ONNX model
        """
        img = np.array(pil_img)
        h, w = img.shape[:2]
        scale = min(size / h, size / w)
        nh, nw = int(h * scale), int(w * scale)

        img_resized = np.array(
            Image.fromarray(img).resize((nw, nh))
        )

        canvas = np.full((size, size, 3), 114, dtype=np.uint8)
        top = (size - nh) // 2
        left = (size - nw) // 2
        canvas[top:top+nh, left:left+nw] = img_resized
        inp = canvas.astype(np.float32) / 255.0
        inp = np.transpose(inp, (2, 0, 1))[None]

        return inp, scale, (left, top)

    def __call__(self, pil_img):
        """run the model from start to finish"""
        inp, scale, pad = self.preprocess(pil_img)
        out = self.session.run(None, {self.input_name: inp})
        return out[0], scale, pad

