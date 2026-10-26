# Headless Godot 4.3 scene regression test.
# This is intentionally not a Windows GPU or Store certification test.
extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var passed: bool = await test_main_scene()
    if passed:
        print("PASS: main 3D scene nodes and runtime rotation")
        quit(0)
    else:
        push_error("FAIL: main 3D scene missing nodes or runtime rotation")
        quit(1)

func test_main_scene() -> bool:
    var packed := load("res://scenes/main.tscn") as PackedScene
    if packed == null:
        return false
    var instance := packed.instantiate() as Node3D
    if instance == null:
        return false
    get_root().add_child(instance)
    await process_frame
    var cube := instance.get_node_or_null("RotatingCube") as MeshInstance3D
    var camera := instance.get_node_or_null("Camera3D") as Camera3D
    var light := instance.get_node_or_null("DirectionalLight3D") as DirectionalLight3D
    if cube == null or camera == null or light == null or cube.mesh == null:
        instance.queue_free()
        return false
    var before: float = cube.rotation.y
    await create_timer(0.25).timeout
    var changed: bool = absf(cube.rotation.y - before) > 0.01
    instance.queue_free()
    return changed
