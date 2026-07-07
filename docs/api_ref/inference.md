<a id="benchmate.inference"></a>

# benchmate.inference

<a id="benchmate.inference.utils"></a>

# benchmate.inference.utils

<a id="benchmate.inference.utils.CleanupMixin"></a>

## CleanupMixin Objects

```python
class CleanupMixin()
```

<a id="benchmate.inference.utils.CleanupMixin.cleanup_cuda"></a>

#### cleanup\_cuda

```python
def cleanup_cuda()
```

Fully clears GPU memory.

<a id="benchmate.inference.utils.CleanupMixin.cleanup_model"></a>

#### cleanup\_model

```python
def cleanup_model(model)
```

Moves model to CPU, deletes it, and clears CUDA.

<a id="benchmate.inference.utils.Embeddings"></a>

## Embeddings Objects

```python
class Embeddings(CleanupMixin)
```

<a id="benchmate.inference.utils.Embeddings.__init__"></a>

#### \_\_init\_\_

```python
def __init__(cache_dir,
             model_name,
             model_kwargs=None,
             processor_kwargs=None,
             quantization_kwargs=None,
             prompt=None,
             device="cuda")
```

creates embeddings from text and images, this is using a vision language embedder

**Arguments**:

- `cache_dir`: where the models are
- `model_name`: name of the model
- `model_kwargs`: kwargs to pass to the model
- `processor_kwargs`: kwargs to pass to the processor
- `quantization_kwargs`: quantization if you are using bitsandbytes
- `prompt`: the prompt for the model
- `device`: which device to use defaults to cuda

<a id="benchmate.inference.utils.Embeddings.model"></a>

#### model

```python
@cached_property
def model()
```

load the model with kwargs

**Returns**:

a transformsers model

<a id="benchmate.inference.utils.Embeddings.encode"></a>

#### encode

```python
def encode(items)
```

encode items into embeddings, these can be images or texts or a pair of both

**Arguments**:

- `items`: this is a list of dict, and it HAS TO look like this
[{"text":<the actual text>}, # text only
{"image":<actual image>}, # image only
{"image": <actual image>, "text":<actual text>}] `image` text combo

**Returns**:

embeddings dim 4096

<a id="benchmate.inference.utils.Embeddings.cleanup"></a>

#### cleanup

```python
def cleanup(model=False)
```

Calls the cleanup mixin

<a id="benchmate.inference.utils.ReRank"></a>

## ReRank Objects

```python
class ReRank(CleanupMixin)
```

<a id="benchmate.inference.utils.ReRank.__init__"></a>

#### \_\_init\_\_

```python
def __init__(cache_dir,
             model_name,
             model_kwargs=None,
             processor_kwargs=None,
             quantization_kwargs=None,
             model_class=AutoModelForMultimodalLM,
             processor_class=AutoProcessor,
             prompt=None,
             device="cuda")
```

Reranker for images AND text, same idea as the embeddings

**Arguments**:

- `cache_dir`: where the models are
- `model_name`: name of the model
- `model_kwargs`: kwargs to pass to the model
- `processor_kwargs`: kwargs to pass to the processor
- `quantization_kwargs`: quantization kwargs
- `prompt`: prompt for the model
- `device`: device to use defaults to cuda

<a id="benchmate.inference.utils.ReRank.model"></a>

#### model

```python
@cached_property
def model()
```

Load the model with kwargs

<a id="benchmate.inference.utils.ReRank.processor"></a>

#### processor

```python
@cached_property
def processor()
```

load the processor with kwargs

<a id="benchmate.inference.utils.ReRank.rerank"></a>

#### rerank

```python
def rerank(query, items)
```

Encode items into embeddings, these can be images or texts or a pair of both.

<a id="benchmate.inference.utils.SemanticChunk"></a>

## SemanticChunk Objects

```python
class SemanticChunk(CleanupMixin)
```

<a id="benchmate.inference.utils.SemanticChunk.__init__"></a>

#### \_\_init\_\_

```python
def __init__(chunking_model, chunk_size=100, min_sentences=1, threshold=0.8)
```

**Arguments**:

- `chunking_model`: chunking model it can be anything really but we are using a static model for speed
- `chunk_size`: how many tokens approx a chunk should have
- `min_sentences`: how many sentences a chunk should have at the minimum. It did not makes sense to me to split sentences so we are
sticking with 1
- `threshold`: when to start a new chunk, this is based on the delta for the embedding cosines.

<a id="benchmate.inference.utils.SemanticChunk.chunk_text"></a>

#### chunk\_text

```python
def chunk_text(texts)
```

Chunk notes into semantic segments. this will return a list of strings, i will then use an embedding model

<a id="benchmate.inference.utils.InterpretImage"></a>

## InterpretImage Objects

```python
class InterpretImage(CleanupMixin)
```

<a id="benchmate.inference.utils.InterpretImage.__init__"></a>

#### \_\_init\_\_

```python
def __init__(cache_dir,
             model_name,
             model_kwargs,
             processor_kwargs,
             quantization_kwargs,
             generation_kwargs,
             model_class=Qwen2_5_VLForConditionalGeneration,
             processor_class=AutoProcessor,
             device="cuda")
```

Runs a vision language models to generate captions for an image, this is primarily used for figure and

table captioninig

**Arguments**:

- `cache_dir`: where the models are
- `model_name`: name of the model
- `model_kwargs`: kwargs to pass to the model
- `processor_kwargs`: kwargs to pass to the processor
- `quantization_kwargs`: quantization kwargs
- `model_class`: model class (use this if you are not using basic AutoModel)
- `processor_class`: what kind of processor to use, defaults to AutoProcessor
- `device`: device to use defaults to cuda

<a id="benchmate.inference.utils.InterpretImage.model"></a>

#### model

```python
@cached_property
def model()
```

Load the model with kwargs

<a id="benchmate.inference.utils.InterpretImage.processor"></a>

#### processor

```python
@cached_property
def processor()
```

Load the processor with kwargs

<a id="benchmate.inference.utils.InterpretImage.interpret"></a>

#### interpret

```python
@torch.inference_mode
def interpret(sys_prompt, images)
```

run inference on an image

**Arguments**:

- `sys_prompt`: system prompt
- `images`: list of images to process

**Returns**:

captions for the images based on the prompt

<a id="benchmate.inference.utils.ExtractInfo"></a>

## ExtractInfo Objects

```python
class ExtractInfo(CleanupMixin)
```

<a id="benchmate.inference.utils.ExtractInfo.__init__"></a>

#### \_\_init\_\_

```python
def __init__(cache_dir,
             model_name,
             model_kwargs=None,
             tokenizer_kwargs=None,
             quantization_kwargs=None,
             generation_kwargs=None,
             model_class=AutoModelForCausalLM,
             device="cuda")
```

Extract information from an a piece of text, the idea is to use this to return structured information from

unstructured text like abstracts or paper text

**Arguments**:

- `cache_dir`: where the models are
- `model_name`: name of the model
- `model_kwargs`: kwargs to pass to the model
- `tokenizer_kwargs`: kwargs to pass to the tokenizer
- `quantization_kwargs`: quantization kwargs
- `generation_kwargs`: generation kwargs like temperature max tokens etc
- `model_class`: What kind of model to use, the default is AutoModelForCausalLM
- `device`: device to use defaults to cuda

<a id="benchmate.inference.utils.ExtractInfo.model"></a>

#### model

```python
@cached_property
def model()
```

Load the model with kwargs

<a id="benchmate.inference.utils.ExtractInfo.tokenizer"></a>

#### tokenizer

```python
@cached_property
def tokenizer()
```

load the tokenizer

<a id="benchmate.inference.utils.ExtractInfo.extract_info"></a>

#### extract\_info

```python
@torch.inference_mode()
def extract_info(sys_prompt, items_to_extract: dict, texts: list)
```

use the extracted prompt from above to call the model

**Arguments**:

- `sys_prompt`: system prompt with instructions
- `items_to_extract`: the dict of what to extract
- `texts`: the text to extract things from

**Returns**:

hopefully a json file

<a id="benchmate.inference.inference"></a>

# benchmate.inference.inference

<a id="benchmate.inference.inference.Inference"></a>

## Inference Objects

```python
class Inference()
```

<a id="benchmate.inference.inference.Inference.__init__"></a>

#### \_\_init\_\_

```python
def __init__(config)
```

Set up all the classes that are in the utils, but not load the models, the models get loaded when
individual methods are called

<a id="benchmate.inference.inference.Inference.embed"></a>

#### embed

```python
def embed(items)
```

embed items into embeddings, this can be image, text or both, see utils for a more detailed description

**Arguments**:

- `items`: a list of items to embed

**Returns**:

a list of embeddings

<a id="benchmate.inference.inference.Inference.rerank"></a>

#### rerank

```python
def rerank(query, items)
```

given a prompt, a query and a list of items return their re-ranking scores, the items and query can be images, text or both

**Arguments**:

- `query`: what are we comparing things to
- `items`: list of items to compare

**Returns**:

list of scores in the same order as the items

<a id="benchmate.inference.inference.Inference.chunk_text"></a>

#### chunk\_text

```python
def chunk_text(text)
```

semantically chunk text into chunks, we are using model2vec for speed

**Arguments**:

- `text`: a large sting

**Returns**:

a list of tuples where (index, text)

<a id="benchmate.inference.inference.Inference.interpret_image"></a>

#### interpret\_image

```python
def interpret_image(prompt, images)
```

create a caption given a system prompt and an image, this is useful for captioning tables or figures

**Arguments**:

- `prompt`: system prompt to use
- `images`: the image to use

**Returns**:

string of text

<a id="benchmate.inference.inference.Inference.text_score"></a>

#### text\_score

```python
def text_score(query, texts)
```

this is a crude text scoring function the query and each text are semantically chunked and each chunk of query

is compared to every chunk of every text in the texts list. Then we get the max row and colum and take their average

**Arguments**:

- `query`: what to compare to this
- `texts`: things to compare

**Returns**:

a single float

<a id="benchmate.inference.inference.Inference.gather_models"></a>

#### gather\_models

```python
def gather_models(config)
```

download models from huggingface

**Arguments**:

- `config`: config file, just the inferece section of config.yaml

**Returns**:

None, but models are downloaded to cache_dir specified in config

