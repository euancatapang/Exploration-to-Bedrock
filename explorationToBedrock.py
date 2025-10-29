import sys
import shutil
import zipfile
import os

from split import Splitter
from reconstruct import Reconstructor
from decompress import Decompressor
from translate import Translator

working_template = "working_template"
source_mcworld = "template.mcworld"

def __prepare_template_world():
    if os.path.exists(working_template):
        shutil.rmtree(working_template)

    copied_world = "template_copy.mcworld"
    shutil.copy2(source_mcworld, copied_world)

    with zipfile.ZipFile(copied_world, 'r') as zip:
        zip.extractall(working_template)

    os.remove(copied_world)

def __zip_template_to_mcworld(template_dir: str, input_save_path: str):
    # Ensure converted output folder exists
    output_dir = os.path.join(os.path.dirname(__file__), "converted")
    os.makedirs(output_dir, exist_ok=True)

    input_filename = os.path.basename(input_save_path)
    if not input_filename.lower().startswith("save") or not input_filename.lower().endswith(".dat"):
        raise ValueError(f"Input save file '{input_filename}' does not match expected format 'saveXX.dat'")

    save_number = input_filename[4:-4]  # e.g., '05'

    # Find a free converted number (avoid overwriting)
    converted_index = 1
    while True:
        output_mcworld = os.path.join(output_dir, f"save{save_number}_converted{converted_index:02d}.mcworld")
        if not os.path.exists(output_mcworld):
            break
        converted_index += 1

    # Zip the working template into the converted folder
    with zipfile.ZipFile(output_mcworld, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, template_dir)
                zipf.write(file_path, arcname)

    print(f"Template zipped into '{output_mcworld}'")
    return output_mcworld

def main(exploration_world_path: str) -> None:
    if not os.path.exists(exploration_world_path):
        raise FileNotFoundError("File does not exist")

    # Split world file into 1024-byte segments
    splitter = Splitter(exploration_world_path)
    splitter.split_world_file()

    print(f"{exploration_world_path} split into {splitter.heads_found} head and {splitter.bodies_found} body segments")

    # Reconstruct segments into original compressed payload
    reconstructor = Reconstructor()
    reconstructor.reconstruct_compressed_chunks()

    print(f"Reconstructed {len(reconstructor.heads_list)} compressed chunks")

    # Decompress rebuild chunks
    Decompressor().decompress_chunks()

    print("Decompressed chunks")

    __prepare_template_world()

    # Convert Exploration chunks to Minecraft Bedrock
    translator = Translator()
    translator.convert_chunks()

    print(f"Converted Exploration {os.path.basename(exploration_world_path)}")
    __zip_template_to_mcworld(working_template, exploration_world_path)

    print("Clear generated files? (y/n)")
    choice = input()
    if choice.lower() == 'y':
        for folder in ["split", "reconstructed_compressed", "decompressed_chunks", "working_template"]:
            if os.path.exists(folder):
                shutil.rmtree(folder)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python explorationToBedrock.py path_to_saveXX.dat")
        sys.exit(1)
    main(sys.argv[1])