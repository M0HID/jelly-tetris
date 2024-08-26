from pathlib import Path
import modal
import time

app = modal.App("examples-blender-simulation-bake")

baking_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("xorg", "libxkbcommon0")
    .pip_install("bpy==4.1.0")
)

@app.function(
    gpu="A10G",
    concurrency_limit=10,
    image=baking_image,
    timeout=3600
)
def bake_simulations(blend_file: bytes) -> bytes:
    import bpy
    
    input_path = "/tmp/input.blend"
    output_path = "/tmp/output.blend"
    
    Path(input_path).write_bytes(blend_file)
    bpy.ops.wm.open_mainfile(filepath=input_path)
    
    sim_objects = [obj for obj in bpy.data.objects if obj.modifiers and any(mod.type in ['CLOTH', 'SOFT_BODY', 'FLUID', 'DYNAMIC_PAINT'] for mod in obj.modifiers)]
    
    total_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1
    
    for i, obj in enumerate(sim_objects):
        print(f"Baking simulation for object {i+1}/{len(sim_objects)}: {obj.name}")
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
            bpy.context.scene.frame_set(frame)
            if frame % 10 == 0:
                print(f"Progress: {frame}/{total_frames} frames")
            time.sleep(0.1)
    
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    
    return Path(output_path).read_bytes()

@app.local_entrypoint()
def main():
    input_path = Path(__file__).parent / "jelly tetris.blend"
    blend_bytes = input_path.read_bytes()
    
    print("Starting simulation baking...")
    baked_blend_bytes = bake_simulations.remote(blend_bytes)
    
    output_path = Path("/tmp") / "BakedSimulationScene.blend"
    output_path.write_bytes(baked_blend_bytes)
    print(f"Baked simulation saved to {output_path}")
