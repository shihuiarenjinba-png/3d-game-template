extends Node3D

@onready var rotating_cube: MeshInstance3D = $RotatingCube

func _process(delta: float) -> void:
    rotating_cube.rotate_y(delta * 0.5)
