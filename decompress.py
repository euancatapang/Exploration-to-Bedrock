import os
import glob
import re
import lz4.block

class Decompressor:

    UNCOMPRESSED_SIZE = 98832

    input_dir = "reconstructed_compressed"
    output_dir = "decompressed_chunks"

    chunk_files = []
    pattern = re.compile(r"x(?P<x>[+-]?\d+)_y(?P<y>[+-]?\d+)_size(?P<size>\d+)\.bin")        

    def __list_chunks(self):
        self.chunk_files = sorted(glob.glob(os.path.join(self.input_dir, "*.bin")))
        if not self.chunk_files:
            raise ValueError(f"No chunk files found in {self.input_dir}")
        
        return self.chunk_files

    def __parse_chunk_filename(self, filename: str):
        base_name = os.path.basename(filename)
        matched = self.pattern.match(base_name)
        if matched is None:
            return None
        
        return int(matched.group("x")), int(matched.group("y")), int(matched.group("size"))

    def __decompress_payload(self, chunk_path: str, chunk_x: int, chunk_y: int):
        with open(chunk_path, "rb") as f:
            compressed_data = f.read()

        decompressed_data = lz4.block.decompress(compressed_data, uncompressed_size=self.UNCOMPRESSED_SIZE)

        output_filename = f"{chunk_x:+04d}_{chunk_y:+04d}.bin"
        os.makedirs(self.output_dir, exist_ok=True)

        with open(os.path.join(self.output_dir, output_filename), "wb") as out:
            out.write(decompressed_data)

    def decompress_chunks(self):
        self.__list_chunks()

        for chunk_path in self.chunk_files:
            parsed = self.__parse_chunk_filename(chunk_path)
            if parsed is None:
                print(f"Skipping unrecognized file: {chunk_path}")
                continue

            chunk_x, chunk_y, _ = parsed
            try:
                self.__decompress_payload(chunk_path, chunk_x, chunk_y)
            except Exception as e:
                print(f"Decompression failed for {chunk_path}: {e}")
