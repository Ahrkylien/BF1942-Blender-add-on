import struct
from collections import namedtuple
from mathutils import Quaternion, Vector
from io import BytesIO

Bone = namedtuple('Bone', ['name', 'frames'])

def read_uint7_uint1(byte):
    """Split a byte into uint7 and uint1 (MSB is RLE flag)"""
    is_rle = (byte & 0b10000000) >> 7
    num_frames = byte & 0b01111111
    return num_frames, is_rle

def read_half_float(f):
    """Read 2 bytes and unpack as float16"""
    return struct.unpack('<e', f.read(2))[0]

def parse_baf(filepath):
    with open(filepath, 'rb') as f:
        buf = BytesIO(f.read())

    # Header
    version, = struct.unpack('<I', buf.read(4))
    if version != 3:
        raise ValueError(f"Unsupported version: {version}")

    # Bone names
    num_bones, = struct.unpack('<H', buf.read(2))
    bone_names = []
    for _ in range(num_bones):
        name_len, = struct.unpack('<H', buf.read(2))
        name = buf.read(name_len).decode('utf-8')
        bone_names.append(name)

    # Frame and precision
    num_frames, = struct.unpack('<I', buf.read(4))
    precision, = struct.unpack('<B', buf.read(1))

    bones = []

    for bone_index in range(num_bones):
        name = bone_names[bone_index]
        num_data, = struct.unpack('<H', buf.read(2))

        bone_frames = [[] for _ in range(7)]  # 4 rotation + 3 position

        for i in range(7):
            block_size, = struct.unpack('<H', buf.read(2))
            block_end = buf.tell() + block_size

            while buf.tell() < block_end:
                byte = buf.read(1)[0]
                num_frames_in_block, is_rle = read_uint7_uint1(byte)
                sub_block_size, = struct.unpack('<B', buf.read(1))

                if is_rle:
                    val = read_half_float(buf)
                    bone_frames[i].extend([val] * num_frames_in_block)
                else:
                    for _ in range(num_frames_in_block):
                        val = read_half_float(buf)
                        bone_frames[i].append(val)

        # Zip 7 separate lists into per-frame data
        frames = []
        for frame_values in zip(*bone_frames):
            rot = Quaternion(frame_values[0:4])
            pos = Vector(frame_values[4:7])
            frames.append((rot, pos))

        bones.append(Bone(name=name, frames=frames))

    return bones

# Example usage:
# bones = parse_baf("path_to_file.baf")
# print(bones[0].name, bones[0].frames[0])