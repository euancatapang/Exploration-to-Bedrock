# Exploration-to-Bedrock
Converts worlds (saveXX.dat) from the voxel based game, Exploration, to Minecraft Bedrock.

Uses a modified bedrock library (https://github.com/BluCodeGH/bedrock) to support chunk version 41 for manipulating world blocks.

Exploration saves use LZ4 compression, requiring it as dependency.
```
pip install lz4
```
Usage
```
python explorationToBedrock.py "path_to_saveXX.dat" [--clear]
```
