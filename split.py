import os
import struct

class Splitter:

    SEGMENT_SIZE = 1024
    LZ4_SIGNATURE = "1F030100"
    
    output_dir = "split"

    def __init__(self, input_world):
        self.input_world = input_world
        self.heads_found = 0
        self.bodies_found = 0

    # Save selected 1024 bytes to file
    def __write_segment_data(self, current_segment_data: bytes, segment_number: int):
        if segment_number == 0:
            segment_file_name = "000_header.bin" # First 1024 bytes are always header

        else:
            # Byte ranges for metadata to determine if segment is head
            verify_x_coordinate = current_segment_data[8:12]
            verify_y_coordinate = current_segment_data[12:16]
            verify_LZ4_magic_bytes = current_segment_data[24:28]

            chunk_x = struct.unpack("<I", verify_x_coordinate)[0]
            chunk_y = struct.unpack("<I", verify_y_coordinate)[0]

            if (chunk_x % 16 == 0 and 
                chunk_y % 16 == 0 and 
                verify_LZ4_magic_bytes == bytes.fromhex(self.LZ4_SIGNATURE)
            ):
                segment_file_name = f"{segment_number:03d}_head_{self.heads_found:03d}.bin"
                self.heads_found += 1
            
            else:
                segment_file_name = f"{segment_number:03d}_body_{self.bodies_found:03d}.bin"
                self.bodies_found += 1

        with open(os.path.join(self.output_dir, segment_file_name), "wb") as out:
            out.write(current_segment_data)
        
    def split_world_file(self):
        os.makedirs(self.output_dir, exist_ok=True)
        world_file_size = os.path.getsize(self.input_world)
        
        if world_file_size % 1024 != 0: raise ValueError(f"World size of {self.input_world} is not divisible by 1024 bytes")

        with open(self.input_world, "rb") as f:
            world_data = f.read()

        segment_count = world_file_size // self.SEGMENT_SIZE

        # Cycle through the file by 1024-byte segments
        for i in range(segment_count):
            segment_start = i * self.SEGMENT_SIZE
            segment_end = segment_start + self.SEGMENT_SIZE

            current_segment_data = world_data[segment_start : segment_end]

            self.__write_segment_data(current_segment_data, i)       