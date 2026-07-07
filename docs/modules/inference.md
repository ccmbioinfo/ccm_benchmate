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

For extracting text, tables and figures we are using paddle ocr and it's built in modules. When you first use the paper 
processor class the models will be dowloaded in a location you have specified in your `config.yaml`. This is the only time
you will need internet connection for layout detection and paper processing. 

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

This is the larges one in the repository. It uses [medgemma 4b](https://huggingface.co/google/medgemma-4b-it but if you need somethign bigger you can 
switch it with the 27b version. This model is used to parse abstracts and article texts to extract specific information
 

### Image interpretation

This model is used to caption tables and figures. Since many articles come as pdfs and we have no control over
how the pdfs are generated (each journal does its own thing) we cannot relliably detect figure/table captions. 

While some models are better than others there are no models that I have tried that has shown reliable performance. 
To overcome this challenge of getting figure captions for semantic search we decided to caption the figures ourselves. 

For this end we are using [Qwen3-VL-2B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct to interpret the images. These images are then embeeded using our 
embeeding model (see below)

This model can be used to generate additional captions for images (such as tables and figures that did not come with captions
such as supplementaries) or you can use it to enhance semantic searches (see project)

### Embedding model

To keep all the nuance in different figures and texts and text chunks we are using a vision language model to encode both.
For this end we have chosen [Qwen/Qwen3-VL-Embedding-2B](https://huggingface.co/Qwen/Qwen3-VL-Embedding-2B) model. This creates a 4096 dimension embeddings for images and text
these embeddings can be used interchangibly (search images with images, search images with text, search text with images, search
text with text). These are then passed onto our re-ranking model of choice (see below)

### Re-Ranking model

Same as above we are using its sister model [Qwen/Qwen3-VL-Reraker-2B](https://huggingface.co/Qwen/Qwen3-VL-Reranker-2B). 


## Setting up the inference class

After installing benchmate (see [documentation](../installation.md)). You can create an inference class instance using the config file provided. 

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

There is not much else to do with the inference class because it is usually intended for other modules to use it