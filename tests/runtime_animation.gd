extends SceneTree
# Godot 3.6 runtime verification: godot3 --no-window --path . -s res://tests/runtime_animation.gd
var failed=[]
func _init():
    call_deferred("_run")
func check(ok, label):
    if ok: print("PASS: ",label)
    else:
        failed.append(label)
        printerr("FAIL: ",label)
func _run():
    var main=load("res://Main.tscn").instance()
    get_root().add_child(main)
    check(is_instance_valid(main.player) and is_instance_valid(main.enemy),"fighters created")
    check(main.player.get_node_or_null("Model/Torso/Head") != null,"player head pivot")
    check(main.player.get_node_or_null("Model/RightArm/Elbow/Wrist/Saber/Blade") != null,"blade attached to hand")
    check(main.player.get_node_or_null("Model/LeftLeg/Knee") != null,"left articulated knee")
    check(main.enemy.get_node_or_null("Model/RightLeg/Knee") != null,"enemy articulated knee")
    var leg=main.player.left_leg
    main.player.animate_pose(0.1,5.0,"idle","light",0.0,false,false,false,false)
    main.player.animate_pose(0.2,5.0,"idle","light",0.0,false,false,false,false)
    check(abs(leg.rotation_degrees.x)>0.01,"walking changes leg angle")
    main.player.animate_pose(0.1,0.0,"windup","light",0.8,false,false,false,false)
    check(abs(main.player.weapon().rotation_degrees.z)>0.01,"windup rotates the weapon")
    main.player.animate_pose(0.1,0.0,"idle","light",0.0,true,false,false,false)
    check(main.player.left_arm.rotation_degrees.x>20.0,"guard raises the arm")
    main.player.animate_pose(0.1,0.0,"idle","light",0.0,false,false,true,false)
    check(main.player.torso.rotation_degrees.z < 0.0,"stagger changes torso pose")
    main.player.animate_pose(0.1,0.0,"idle","light",0.0,false,false,false,true)
    check(main.player.torso.rotation_degrees.x > 0.0,"defeat changes torso pose")
    var different=preload("res://scripts/FighterVisual.gd").new()
    main.add_child(different)
    different.configure(5,Color(0,1,0))
    check(different.scale.y < main.player.scale.y,"shorter fighter has a different proportion scale")
    check(different.get_node_or_null("Model/Torso/Cape") != null,"robe configuration adds garment")
    different.queue_free()
    main.queue_free()
    print("ANIMATION TESTS COMPLETE; failures: ",failed.size())
    quit(0 if failed.empty() else 1)
