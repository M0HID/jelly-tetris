from pathlib import Path
import modal
import bpy

app = modal.App("examples-blender-bake")

baking_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("xorg", "libxkbcommon0")
    .pip_install("bpy==4.1.0")
)

@app.function(
    image=baking_image,
)
def bake_simulation(blend_file: bytes) -> str:
    input_path = "/tmp/input.blend"
    cache_directory = "/tmp/cache/"
    
    Path(input_path).write_bytes(blend_file)
    
    bpy.ops.wm.open_mainfile(filepath=input_path)
    
    bpy.context.scene.rigidbody_world.point_cache.directory = cache_directory
    
    bpy.ops.ptcache.bake_all(bake=True)
    
    return f"Simulation baked to {cache_directory}"

@app.local_entrypoint()
def main():
    input_path = Path(__file__).parent / "simulation.blend"
    blend_bytes = input_path.read_bytes()
    
    cache_path = bake_simulation.remote(blend_bytes)
    print(cache_path)
