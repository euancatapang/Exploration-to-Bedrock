import os
import glob
import lz4.block

class Decompressor:

    input_dir = "reconstructed_compressed"
    output_dir = "decompressed_chunks"

    def __init__(self, world_height):
        self.decompressed_size = (16 * world_height * 16) * 3 + 528

    def __list_chunks(self):
        chunk_files = sorted(glob.glob(os.path.join(self.input_dir, "*.bin")))
        if not chunk_files:
            raise ValueError(f"No chunk files found in {self.input_dir}")
        
        return chunk_files

    def __decompress_payload(self, chunk_path: str):
        with open(chunk_path, "rb") as f:
            compressed_data = f.read()

        try:
            decompressed_data = lz4.block.decompress(compressed_data, self.decompressed_size)
        except Exception as e:
            print(f"Decompression failed for {chunk_path}: {e}")
            return

        output_filename = os.path.basename(chunk_path)

        with open(os.path.join(self.output_dir, output_filename), "wb") as out:
            out.write(decompressed_data)

    def decompress_chunks(self):
        chunk_files = self.__list_chunks()

        os.makedirs(self.output_dir, exist_ok=True)
        for chunk_path in chunk_files:
            self.__decompress_payload(chunk_path)