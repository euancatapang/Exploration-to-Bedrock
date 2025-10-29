import bedrock
import glob
import os
import re
from typing import Optional

from blockModifiers import translate_block_modifier
from blockMap import get_equivalent_block

class Translator:

    template_dir = "working_template"
    input_dir = "decompressed_chunks"
    chunk_file_pattern = re.compile(r"([+-]\d+)_([+-]\d+)\.bin")

    chunk_count = 0
    block_count = 0
    unknown_block_count = 0
    unknown_modifier_count = 0

    def __init__(self, world_height):
        if not os.path.isdir(self.template_dir): 
            raise FileNotFoundError("Minecraft world template not found in directory")
        
        self.WORLD_HEIGHT = world_height
        self.BLOCKS_IN_CHUNK = 16 * world_height * 16

    # Get top-slab block object from world. Top slab block modifier can only be fetched from world
    def __fetch_slab_blocks(self):
        with bedrock.World(self.template_dir) as world:
            self.slab_blocks = {
                "oak_slab":                 bedrock.Block("minecraft:oak_slab", 8),
                "smooth_stone_slab":        bedrock.Block("minecraft:smooth_stone_slab", 8),
                "normal_stone_slab":        world.getBlock(-512, 0, 1 - 512),
                "andesite_slab":            world.getBlock(-512, 0, 2 - 512),
                "cobblestone_slab":         world.getBlock(-512, 0, 3 - 512),
                "brick_slab":               world.getBlock(-512, 0, 6 - 512),
                "mossy_cobblestone_slab":   world.getBlock(-512, 0, 7 - 512),
                "smooth_sandstone_slab":    world.getBlock(-512, 0, 8 - 512),
                "sandstone_slab":           world.getBlock(-512, 0, 9 - 512),
                "stone_brick_slab":         world.getBlock(-512, 0, 10 - 512),
                "birch_slab":               world.getBlock(-512, 0, 11 - 512),
                "jungle_slab":              world.getBlock(-512, 0, 12 - 512),
                "spruce_slab":              world.getBlock(-512, 0, 13 - 512)
            }
    
    # Handle slab block data
    def __get_slab_data(self, block_name: str, block_type: str, current_block_modifiers: int):
        isTopSlab = current_block_modifiers == 0x24

        if isTopSlab:
            return self.slab_blocks.get(block_name, bedrock.Block("minecraft:unknown", 0))
        else:
            return bedrock.Block(f"minecraft:{block_name}", 0)

    # Store list of chunks to cycle through
    def __get_chunk_list(self):
        chunk_files = {}
        for chunk_path in glob.glob(os.path.join(self.input_dir, "*_*.bin")):
            filename = os.path.basename(chunk_path)

            match = self.chunk_file_pattern.match(filename)

            if match:
                x, z = map(int, match.groups())
                chunk_files[(x, z)] = chunk_path
        
        self.chunk_count = len(chunk_files)
        self.block_count = self.chunk_count * self.BLOCKS_IN_CHUNK

        if self.chunk_count == 0: raise ValueError(f"No chunk files found in directory")

        return chunk_files
    
    # Get Minecraft block namespace based on Exploration block represented by byte
    def __convert_block(self, current_block: int, current_block_modifiers: bytes) -> Optional[bedrock.Block]:
        new_block = get_equivalent_block(current_block)
        new_modifier = 0

        is_modifiable = isinstance(new_block, tuple)

        if new_block == -1:
            return None
        elif current_block_modifiers[1] == 0x20:
            return bedrock.Block("minecraft:water")
        elif current_block_modifiers[1] == 0x03:
            return bedrock.Block("minecraft:lava")
        
        elif is_modifiable:
            block_name, block_type = new_block

            if block_type == "slab":
                return self.__get_slab_data(block_name, block_type, current_block_modifiers[0])

            else:
                new_modifier = translate_block_modifier(current_block_modifiers[0], block_type)
                if new_modifier == -1:
                    self.unknown_modifier_count += 1
                    new_modifier = 0
                    
                return bedrock.Block(f"minecraft:{block_name}", new_modifier)
        else:
            return bedrock.Block(f"minecraft:{new_block}", new_modifier)

    def __count_unknown_blocks(self, current_block: bedrock.Block):
        if current_block.name == "minecraft:unknown":
            self.unknown_block_count += 1                

    # Loop through each block in each Exploration chunk file
    def convert_chunks(self):
        chunk_list = self.__get_chunk_list()
        self.__fetch_slab_blocks()

        with bedrock.World(self.template_dir) as world:

            for (x_offset, z_offset), chunk_path in chunk_list.items():
                print(f"Processing chunk at ({x_offset}, {z_offset}) from {chunk_path}")

                with open(chunk_path, "rb") as f:
                    current_chunk_data = f.read()

                current_chunk_blocks = current_chunk_data[0:self.BLOCKS_IN_CHUNK]
                current_chunk_modifiers = current_chunk_data[self.BLOCKS_IN_CHUNK:self.BLOCKS_IN_CHUNK * 3]

                for z_slice in range(16):
                    for y_layer in range(self.WORLD_HEIGHT):
                        for x_block in range(16):

                            block_index = (
                                (z_slice * 16 * self.WORLD_HEIGHT) + 
                                (y_layer * 16) + 
                                (x_block)
                            )

                            modifier_index = 2 * block_index

                            current_block = current_chunk_blocks[block_index]
                            current_block_modifiers = current_chunk_modifiers[modifier_index : modifier_index + 2]

                            new_block = self.__convert_block(current_block, current_block_modifiers)
                            if new_block is None:
                                continue

                            self.__count_unknown_blocks(new_block)

                            world.setBlock(
                                x_block + x_offset,
                                y_layer,
                                z_slice + z_offset,
                                new_block
                            )