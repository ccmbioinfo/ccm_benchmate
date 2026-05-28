---
layout: default
title: Inference
parent: Modules
nav_order: 11
---

---
language:
- en
pipeline_tag: Benchmare models
tags:
- biology
- biomedical
---

# Inference module

Inference module contains all the infrastructure for benchmate to be able to call different models for different purposes
most of the models here are currently focused on the literature section for processing papers, figures and tables but in
the future we might have other models that focus on other modalities that are represented in benchmate. 

## Layout model

This is a ONNX version of [model](). It has been converted from its original YOLO architecture to avoid
using ultralytics libraries to reduce dependencies. This model is responsible to extracting tables and figures
from pdf files for scientific articles.

The models was created using the code snippet:

```python
from ultralytics import YOLO


model = YOLO(
    "benchmate/models/lp_model/yolo26m_doc_layout.pt"
)

model.export(
    format="onnx",
    imgsz=1280,
    opset=17,
    simplify=True,
    nms=False,
)
```

## Model2Vec model

This model is responsible for semantic chunking. It is a [model2vec]() version of 
[Snowflake Arctic Embed model](https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0)
that has been reduced 1024 dimensions using the main distillation step explained by model2vec creators. 

```python
from model2vec.distill import distill

# Distill a Sentence Transformer model, in this case the BAAI/bge-base-en-v1.5 model
m2v_model = distill(model_name="Snowflake/snowflake-arctic-embed-l-v2.0", pca_dims=1024)

# Save the model
m2v_model.save_pretrained("m2v_model")
```

You do not need to do this unless you want to use a different model. 

## Other models in benchmate

### Information Extraction

This is the larges one in the repository. It uses [medgemma 27b]() but if you need somethign smaller you can 
switch it with the 4b version. This model is used to parse abstracts and article texts to extract specific information
for how to use it you can see the benchmate [inference documentation](). 

### Image interpretation

This model is used to caption tables and figures. Since many articles come as pdfs and we have no control over
how the pdfs are generated (each journal does its own thing) we cannot relliably detect figure/table captions. 

While some models are better than others there are no models that I have tried that has shown reliable performance. 
To overcome this challenge of getting figure captions for semantic search we decided to caption the figures ourselves. 

For this end we are using [Qwen2.5-VL-3B-Instruct]() to interpret the images. These images are then embeeded using our 
embeeding model (see below)

### Embedding model

To keep all the nuance in different figures and texts and text chunks we are using a vision language model to encode both.
For this end we have chosen [Qwen/Qwen3-VL-Embedding-8B]() model. This creates a 4096 dimension embeddings for images and text
these embeddings can be used interchangibly (search images with images, search images with text, search text with images, search
text with text). These are then passed onto our re-ranking model of choice (see below)

### Re-Ranking model

Same as above we are using its sister model [Qwen/Qwen3-VL-Reraker-8B](). 


## Setting up the inference class

After installing benchmate (see [documentation]()). You can create an inference class instance using the config file provided. 

You can change the models to some extent and pick ones that might suit your needs better. If you are changing the layout or 
semantic chunking model you will need to follow the steps above. 

To collect all the models in one location (or locations of your choosing specified in the config file) you can do:

```python
import yaml
from benchmate.inference.inference import Inference

with open("config.yaml") as f:
    config=yaml.safe_load(f)


inference=Inference(config=config["inference"])

#gather all the models that are being used as is
inference.gather_models()
```

There is not much else to do with the inference class because it is usually intended for other models to use it