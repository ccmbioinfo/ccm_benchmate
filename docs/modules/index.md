---
layout: default
title: Modules
parent: Modules
nav_order: 1
has_children: true
---


# Benchmate Modules:

This is the documentation for usage instructions for the modules in the benchmate package, for a mre
technical API reference please see the [api reference](api_reference/index.md)

In the following pages we will outline how to use each module independently. In some instances we will
use some functionalites from other modules but they will not be discussed explicitly.

## Configuration

Benchmate relies on several AI models (mostly from huggingface) to do what it needs to do. The organization
of these models, their locations etc. are stored in `config.yaml`. This python dictionary has a very 
strict structure. Additionally, the models that we have chosen generate outputs that are of specific sizes and
dimensions. While some of them can be swapped other will require strict refactoring to make things work. 

We are aware of this limitation and making this more flexible is one of our priotiries. That said, we chose models
that we believe to output consistent and accurate information while being lightweight. You can run benchmate with less than 
36GB of vram. That is about the size of a high end gaming GPU. 