import os
import struct
import glob

class Reconstructor:

    MAX_SEGMENT_SIZE = 1024

    output_dir = "reconstructed_compressed"
    input_dir = "split"

    heads_list = []

    # Get all chunk heads from directory
    def __list_heads(self):
        self.heads_list = sorted(glob.glob(os.path.join(self.input_dir, "*_head_*.bin")))
        if not self.heads_list:
            raise ValueError("No valid chunks found in world")
        
        print(f"Found {len(self.heads_list)} chunks")
        return self.heads_list

    # Rebuild fragmented compressed payloads
    def __reconstruct_compressed_payload(self, head_path: str) -> tuple[bytearray, int, int, int]:
        with open(head_path, "rb") as f:
            head_data = bytearray(f.read())

        index_of_next = struct.unpack("<i", head_data[0:4])[0]
        chunk_x = struct.unpack("<i", head_data[8:12])[0]
        chunk_y = struct.unpack("<i", head_data[12:16])[0]
        compressed_size = struct.unpack("<I", head_data[20:24])[0]

        if index_of_next == -1:
            chunk_data = head_data[24:24 + compressed_size]
        else:
            chunk_data = head_data[24:24 + self.MAX_SEGMENT_SIZE]

            while index_of_next != -1:
                body_path = glob.glob(os.path.join(self.input_dir, f"{index_of_next:03d}_body_*.bin"))[0]

                with open(body_path, "rb") as f:
                    body_data = f.read()
                
                index_of_next = struct.unpack("<i", body_data[0:4])[0]
                remaining_size = struct.unpack("<I", body_data[4:8])[0]
                
                chunk_data.extend(body_data[8:8 + min(remaining_size, 1016)])

        return chunk_data, chunk_x, chunk_y, compressed_size

    # Save chunk from concatenated segments in buffer
    def __write_chunk(self, chunk_data: bytearray, chunk_x: int, chunk_y: int, compressed_size: int):
        os.makedirs(self.output_dir, exist_ok=True)
        filename = f"x{chunk_x:+04d}_y{chunk_y:+04d}_size{compressed_size:05d}.bin"

        with open(os.path.join(self.output_dir, filename), "wb") as f:
            f.write(chunk_data)

    # Concatenate segments to each respective head
    def reconstruct_compressed_chunks(self):
        self.__list_heads()

        for head_path in self.heads_list:
            chunk_data, chunk_x, chunk_y, compressed_size = self.__reconstruct_compressed_payload(head_path)
            self.__write_chunk(chunk_data, chunk_x, chunk_y, compressed_size)

