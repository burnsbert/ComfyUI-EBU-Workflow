import math
from datetime import datetime
import os
import shutil
import random

class EbuScalingResolution:
    aspect_ratios = {
        "16:9": [
            "640x360", "960x540", "1024x576", "1088x612", "1152x648", "1216x684", "1280x720", "1344x756", "1408x792", "1472x828", "1536x864", "1600x900", "1792x1024", "1856x1044", "1920x1080", "2048x1152", "2240x1260", "2304x1296", "2560x1440"
        ],
        "16:10": [
            "640x400", "704x440", "768x480", "832x520", "896x560", "960x600", "1024x640", "1088x680", "1152x720", "1216x760", "1280x800", "1344x840", "1408x880", "1472x920", "1536x960", "1600x1000", "1792x1120", "1856x1160", "1920x1200", "2048x1280", "2240x1400", "2560x1600"
        ],
        "3:2": [
            "768x512", "832x554", "896x597", "960x640", "1024x682", "1088x725", "1152x768", "1216x810", "1280x853", "1344x896", "1408x938", "1472x981", "1536x1024", "1600x1066"
        ],
        "4:3": [
            "640x480", "704x528", "768x576", "832x624", "896x672", "960x720", "1024x768", "1088x816", "1152x864", "1216x912", "1280x960", "1344x1008", "1408x1056", "1472x1104", "1536x1152", "1600x1200"
        ],
        "5:4": [
            "640x512", "704x564", "768x615", "832x667", "896x718", "960x770", "1024x821", "1088x872", "1152x924", "1216x975", "1280x1024", "1344x1076", "1408x1128", "1472x1179", "1536x1230", "1600x1280"
        ],
        "6:5": [
            "768x640", "832x693", "896x746", "960x800", "1024x853", "1088x906", "1152x960", "1216x1013", "1280x1066", "1344x1120", "1408x1173", "1472x1226", "1536x1280", "1600x1333"
        ],
        "1:1": [
            "512x512", "576x576", "640x640", "704x704", "768x768", "832x832", "896x896", "960x960", "1024x1024", "1088x1088", "1152x1152", "1216x1216", "1280x1280", "1344x1344", "1408x1408", "1472x1472", "1536x1536", "1600x1600"
        ]
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "active_aspect_ratio": (list(cls.aspect_ratios.keys()) + ["Other"],),
                **{key: (value,) for key, value in cls.aspect_ratios.items()},
                "other_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8, "display": "number"}),
                "other_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8, "display": "number"}),
                "mode": (["Landscape", "Profile"], {"default": "Landscape"}),
                "upscale_by": ("FLOAT", {"default": 1.5, "min": 1.0, "max": 10.0, "step": 0.5, "display": "number"})
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "FLOAT", "STRING",)
    RETURN_NAMES = ("width", "height", "upscaled_width", "upscaled_height", "upscale_by", "upscaled_resolution_string",)
    FUNCTION = "compute_resolution"
    CATEGORY = "Resolution"

    def compute_resolution(self, active_aspect_ratio, **kwargs):
        if active_aspect_ratio == "Other":
            width = kwargs["other_width"]
            height = kwargs["other_height"]
        else:
            resolution = kwargs[active_aspect_ratio]
            width, height = [int(x) for x in resolution.split('x')]

        def round_up_to_multiple_of_eight(value):
            return math.ceil(value / 8) * 8

        upscale_by = kwargs["upscale_by"]
        scaled_width = round_up_to_multiple_of_eight(width * upscale_by)
        scaled_height = round_up_to_multiple_of_eight(height * upscale_by)

        if kwargs["mode"] == "Profile":
            width, height = height, width
            scaled_width, scaled_height = scaled_height, scaled_width
        upscaled_resolution_string = f"{scaled_width}x{scaled_height}"

        print(f"Original: {width}x{height}, Scaled: {upscaled_resolution_string}, Upscale factor: {upscale_by}")

        return width, height, scaled_width, scaled_height, upscale_by, upscaled_resolution_string


class EbuScalingTile:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "upscaled_image_width": ("INT", {"default": 768, "step": 1, "display": "number"}),
                "upscaled_image_height": ("INT", {"default": 1024, "step": 1, "display": "number"}),
                "profile_width_div_by": ("FLOAT", {"default": 1, "min": 1.0, "max": 20.0, "step": 0.05, "display": "number"}),
                "profile_height_div_by": ("FLOAT", {"default": 3, "min": 1.0, "max": 20.0, "step": 0.05, "display": "number"}),
                "landscape_width_div_by": ("FLOAT", {"default": 2, "min": 1.0, "max": 20.0, "step": 0.05, "display": "number"}),
                "landscape_height_div_by": ("FLOAT", {"default": 2, "min": 1.0, "max": 20.0, "step": 0.05, "display": "number"}),
                "tile_width_padding": ("INT", {"default": 0, "step": 1, "display": "number"}),
                "tile_height_padding": ("INT", {"default": 0, "step": 1, "display": "number"}),
            }
        }

    RETURN_TYPES = ("INT", "INT",)
    RETURN_NAMES = ("tile_width", "tile_height",)
    FUNCTION = "tile"
    CATEGORY = "Resolution"

    def tile(self, upscaled_image_width, upscaled_image_height, profile_width_div_by, profile_height_div_by, landscape_width_div_by, landscape_height_div_by, tile_width_padding, tile_height_padding):
        if upscaled_image_height > upscaled_image_width:
            new_width = int(upscaled_image_width / profile_width_div_by) + tile_width_padding
            new_height = int(upscaled_image_height / profile_height_div_by) + tile_height_padding
        else:
            new_width = int(upscaled_image_width / landscape_width_div_by) + tile_width_padding
            new_height = int(upscaled_image_height / landscape_height_div_by) + tile_height_padding
        return new_width, new_height



class EbuGetImageAspectRatio:
    ASPECT_RATIOS = {
        "1:1": 1.0,
        "6:5": 1.2,
        "5:4": 1.25,
        "4:3": 1.333,
        "3:2": 1.5,
        "2:1": 2.0,
        "16:10": 1.6,
        "16:9": 1.777,
        "5:6": 0.833,
        "4:5": 0.8,
        "3:4": 0.75,
        "2:3": 0.666,
        "10:16": 0.625,
        "9:16": 0.5625
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",)
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("aspect_ratio",)
    FUNCTION = "get_aspect_ratio"
    CATEGORY = "Resolution"

    def get_aspect_ratio(self, image):
        img = image[0]  # Access the first image tensor
        height, width = img.shape[:2]  # Extract height and width

        ratio = width / height
        tolerance = 0.08  # 8% tolerance

        closest = min(self.ASPECT_RATIOS.items(), key=lambda x: abs(x[1] - ratio))
        label, value = closest
        diff = abs(value - ratio)

        print(f"DEBUG: width={width}, height={height}, ratio={ratio:.4f}, closest={label} ({value}), diff={diff:.4f}")

        if diff <= tolerance:
            return (label,)
        else:
            return ("Unknown",)

class EbuUniqueFileName:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "str": ("STRING", {"default": "file"}),
                "join_str": ("STRING", {"default": "-"}),
                "seed": ("INT", {"default": 0, "max": 0xffffffffffffffff})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("unique_filename",)
    FUNCTION = "generate_filename"
    CATEGORY = "Utility"

    def generate_filename(self, str, join_str, seed):
        now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        return (f"{str}{join_str}{now}",)

class EbuAppendToFile:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_to_append": ("STRING", {"multiline": True}),
                "directory_name": ("STRING", {"default": "store"}),
                "file_name": ("STRING", {"default": "output.txt"}),
                "overwrite": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "append_to_file"
    OUTPUT_NODE = True
    CATEGORY = "Utility"

    def append_to_file(self, string_to_append, directory_name, file_name, overwrite):
        os.makedirs(directory_name, exist_ok=True)
        full_path = os.path.join(directory_name, file_name)

        mode = 'w' if overwrite else 'a'
        with open(full_path, mode) as file:
            file.write(string_to_append + "\n")

        print(f"{'Overwritten' if overwrite else 'Appended to'} file: {full_path}")
        return ()

class EbuReadFromFile:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_name": ("STRING", {"default": "store"}),
                "file_name": ("STRING", {"default": "output.txt"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_contents",)
    FUNCTION = "read_from_file"
    OUTPUT_NODE = True
    CATEGORY = "Utility"

    def read_from_file(self, directory_name, file_name):
        full_path = os.path.join(directory_name, file_name)

        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            return ("",)

        with open(full_path, 'r') as file:
            contents = file.read()

        print(f"Read from file: {full_path}")
        return (contents,)

import os
import random
import shutil

class EbuFileListCache:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_name": ("STRING", {"default": "store"}),
                "file_name": ("STRING", {"default": "output.txt"}),
                "num_return_items": ("INT", {"default": 5, "min": 0, "max": 1000}),
                "input_items": ("STRING", {"multiline": True}),
                "limit_list_size": ("INT", {"default": 100, "min": 1, "max": 10000})
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("selected_items", "input_items", "combined_items")
    FUNCTION = "process_file_list_cache"
    OUTPUT_NODE = True
    CATEGORY = "Utility"

    def process_file_list_cache(self, directory_name, file_name, num_return_items, input_items, limit_list_size):
        os.makedirs(directory_name, exist_ok=True)
        full_path = os.path.join(directory_name, file_name)
        backup_path = full_path + ".bk"

        # Load current file contents
        current_lines = set()
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                current_lines = {line.strip() for line in f if line.strip()}

        # Handle blank input: return random items from current file without modifying it
        if not input_items.strip():
            selected_items = random.sample(list(current_lines), min(num_return_items, len(current_lines)))
            return (
                "\n".join(selected_items),
                "",
                "\n".join(selected_items)
            )

        # Otherwise, parse input normally
        input_lines = [line.strip() for line in input_items.splitlines() if line.strip()]
        input_set = set(input_lines)

        # Combine and shuffle
        combined_set = current_lines.union(input_set)
        combined_list = list(combined_set)
        random.shuffle(combined_list)
        trimmed_list = combined_list[:limit_list_size]

        # Backup and save new file
        if os.path.exists(full_path):
            shutil.copy2(full_path, backup_path)

        with open(full_path, "w") as f:
            f.write("\n".join(trimmed_list) + "\n")

        # Return random items (excluding input)
        available_for_selection = list(set(trimmed_list) - input_set)
        selected_items = random.sample(available_for_selection, min(num_return_items, len(available_for_selection)))

        return (
            "\n".join(selected_items),
            "\n".join(input_lines),
            "\n".join(input_lines + selected_items)
        )

class EbuEncodeNewLines:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "new_line_encoding": ("STRING", {"default": "|||"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("encoded_text",)
    FUNCTION = "encode"
    OUTPUT_NODE = True
    CATEGORY = "Utility"

    def encode(self, text, new_line_encoding):
        encoded = text.replace("\n", new_line_encoding)
        return (encoded,)

class EbuDecodeNewLines:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "encoded_text": ("STRING",),
                "new_line_encoding": ("STRING", {"default": "|||"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("decoded_text",)
    FUNCTION = "decode"
    OUTPUT_NODE = True
    CATEGORY = "Utility"

    def decode(self, encoded_text, new_line_encoding):
        decoded = encoded_text.replace(new_line_encoding, "\n")
        return (decoded,)

NODE_CLASS_MAPPINGS = {
    "EbuGetImageAspectRatio": EbuGetImageAspectRatio,
    "EbuScalingResolution": EbuScalingResolution,
    "EbuScalingTile": EbuScalingTile,
    "EbuUniqueFileName": EbuUniqueFileName,
    "EbuAppendToFile": EbuAppendToFile,
    "EbuReadFromFile": EbuReadFromFile,
    "EbuFileListCache": EbuFileListCache,
    "EbuEncodeNewLines": EbuEncodeNewLines,
    "EbuDecodeNewLines": EbuDecodeNewLines
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EbuGetImageAspectRatio": "EBU Get Image Aspect Ratio",
    "EbuScalingResolution": "EBU Scaling Resolution",
    "EbuScalingTile": "EBU Scaling Tile",
    "EbuUniqueFileName": "EBU Unique File Name",
    "EbuAppendToFile": "EBU Append To File",
    "EbuReadFromFile": "EBU Read From File",
    "EbuFileListCache": "EBU File List Cache",
    "EbuEncodeNewLines": "EBU Encode New Lines",
    "EbuDecodeNewLines": "EBU Decode New Lines"
}

