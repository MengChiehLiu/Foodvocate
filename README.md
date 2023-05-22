# Foodvocate

## Introduction
An analysis on the cascading behavior between Taiwanese Instagram food bloggers, based on Asynchronous Independent Cascade Model (AsIC).

## Asynchronous Independent Cascade Model (AsIC)
We apply AsIC on bloggers' *check in* posts in the same location. We assume that one blogger's post at certain location might influence other bloggers and trigger them going to the same place. We collect popular posts from 108 locations, it becomes 91 locations left after data cleaning, which contains 578 unique bloggers in total. For more detail about web scarping and data cleaning see [/Instagram](Instagram).

To better implement AsIC model, here are some extra assumptions.
1. We asseme that for each location, it is regarded as a independent cascading event. 
2. We assume that there is a *Clique* networks between bloggers.


## Reference
1. Saito, K., Kimura, M., Ohara, K., & Motoda, H. (2010). Selecting information diffusion models over social networks for behavioral analysis. 
2. Saito, K., Ohara, K., Yamagishi, Y., Kimura, M., & Motoda, H. (2011). Learning diffusion probability based on node attributes in social networks. 