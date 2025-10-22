#TODO edit this
model_path="/home/alper/Documents/packages/ccm_benchmate/benchmate/models"

literature = {"vl_model":
                  {"model":
                       {"name": "Qwen/Qwen2.5-VL-3B-Instruct",
                        "config": {
                            "cache_dir": f"{model_path}/hf_models"},
                        "processor": {"name": "Qwen/Qwen2.5-VL-3B-Instruct",
                                      "config": {
                                          "cache_dir": f"{model_path}/hf_models"},
                                      "table_prompt": "You are an expert biologist who is responsible for reading and interpreting scientific tables. For a given table from a scientific paper interpret the table. Do not provide comments on whether the table is well done or not. Do not provide extra text on describing that you are looking at table from a scientific publication. Give an overall conclusion about what the tables tells us.",
                                      "figure_prompt": "You are an expert biologist who is responsible for reading and interpreting scientific figures. For a given figure from a scientific paper interpret the figure. Do not provide comments on whether the figure is well done or not. Do not provide extra text on describing that you are looking at figure from a scientific publication. Whenever possible very briefly describe each sections of the figure and then give an overall conclusion about what the figure tells us. ", }
                        }
                   },
              "lp_model": {
                  "model_path": f"{model_path}/lp_model/model_final.pth",
                  "config_path": f"{model_path}/lp_model/config.yaml",
              },
              "text_embedding_model": {
                  "name": "Qwen/Qwen3-Embedding-0.6B",
                  "config": {
                      "cache_folder": f"{model_path}/hf_models"
                  }
              },
              "image_embedding_model": {
                  "model": {"name": "vidore/colpali-v1.3",
                            "config": {
                                "cache_dir": f"{model_path}/hf_models"}
                            },
                  "processor": {"name": "vidore/colpali-v1.3",
                                "config": {
                                            "cache_dir": f"{model_path}/hf_models"}
                                }
              },
              "chunker_model": {"model": f"{model_path}/m2v_model/",
                                "min_sentences": 1,
                                "return_type": "texts",
                                "threshold": "auto",
                                "chunk_size": 100, },
              }

api_call={
    "text_embedding_model": {
        "model": f"{model_path}/m2v_model/"
    }
}

#TODO
search={"text_embedding_model":literature["text_embedding_model"],
        "api_call_embedding_model":api_call["text_embedding_model"]["model"],
        "image_embedding_model":literature["image_embedding_model"],
        "causal":{
            "model":{
                "name":"chose a name",
                "model":f"{model_path}/hf_models",
                #TODO get kv cache options,
            },
            "tokenizer":{
                "name":"choose a name",
                "model":f"{model_path}/hf_models",
                "truncation":True
                #TODO other options
            },
            "quantization":{#TODO

            },
            "reasoning":{
                #TODO
            }
        }
    }
