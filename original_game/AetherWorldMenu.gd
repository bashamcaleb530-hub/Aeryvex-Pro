extends Control

# Interactive menu prototype. The approved illustration is the locked art direction,
# but its image asset must be imported separately before the exact backdrop can render.
const SAVE_PATH := "user://aether_world_profile.json"
const HEROES := [
    {"id":"kai","name":"KAI","title":"THE SHADOW STRIKER","specialty":"Martial Arts  |  Agility  |  Speed","color":"#32aaff"},
    {"id":"ryker","name":"RYKER","title":"THE WARLORD","specialty":"Weapons  |  Warfare  |  Defense","color":"#f2bf61"},
    {"id":"lyra","name":"LYRA","title":"THE AETHER MYSTIC","specialty":"Martial Arts  |  Precision  |  Aether Control","color":"#ad72ff"}
]
var selected := 0
var info: Label
var hero_buttons: Array = []
var continue_button: Button
var profile: Dictionary = {}
var panel: VBoxContainer

func _ready() -> void:
    _load_profile()
    selected = clampi(int(profile.get("selected",0)),0,2)
    _build_ui()
    _refresh()

func _load_profile() -> void:
    if FileAccess.file_exists(SAVE_PATH):
        var parsed = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
        if typeof(parsed) == TYPE_DICTIONARY:
            profile = parsed

func _save_profile() -> void:
    var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(profile, "\t"))

func choose_hero(index: int) -> void:
    if index < 0 or index >= HEROES.size():
        return
    selected = index
    profile["selected"] = selected
    _save_profile()
    _refresh()

func _start_game() -> void:
    profile["selected"] = selected
    profile["started"] = true
    _save_profile()
    get_tree().change_scene_to_file("res://MilitaryOpening.tscn")

func _continue_game() -> void:
    if profile.get("started", false):
        get_tree().change_scene_to_file("res://MilitaryOpening.tscn")

func _make_button(text_value: String, action: Callable) -> Button:
    var btn := Button.new()
    btn.text = text_value
    btn.custom_minimum_size = Vector2(235, 46)
    btn.add_theme_color_override("font_color",Color("#f4e1ad"))
    btn.pressed.connect(action)
    return btn

func _build_ui() -> void:
    var bg := ColorRect.new()
    bg.color = Color("#090e23")
    bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
    add_child(bg)
    var frame := MarginContainer.new()
    frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    frame.add_theme_constant_override("margin_left",40)
    frame.add_theme_constant_override("margin_right",40)
    frame.add_theme_constant_override("margin_top",32)
    frame.add_theme_constant_override("margin_bottom",25)
    add_child(frame)
    var layout := VBoxContainer.new()
    layout.add_theme_constant_override("separation",16)
    frame.add_child(layout)
    var title := Label.new()
    title.text = "AETHER WORLD"
    title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    title.add_theme_font_size_override("font_size",52)
    title.add_theme_color_override("font_color",Color("#f5d29a"))
    layout.add_child(title)
    var subtitle := Label.new()
    subtitle.text = "THRONES OF THE TEN GALAXIES"
    subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    subtitle.add_theme_font_size_override("font_size",23)
    subtitle.add_theme_color_override("font_color",Color("#e7d7bd"))
    layout.add_child(subtitle)
    var body := HBoxContainer.new()
    body.size_flags_vertical = Control.SIZE_EXPAND_FILL
    body.add_theme_constant_override("separation",28)
    layout.add_child(body)
    panel = VBoxContainer.new()
    panel.custom_minimum_size = Vector2(238,0)
    panel.add_theme_constant_override("separation",12)
    body.add_child(panel)
    panel.add_child(_make_button("NEW GAME",_start_game))
    continue_button = _make_button("CONTINUE",_continue_game)
    panel.add_child(continue_button)
    panel.add_child(_make_button("MILITARY TRIALS",_start_game))
    panel.add_child(_make_button("CHARACTER ARENA",func(): get_tree().change_scene_to_file("res://CharacterArena.tscn")))
    panel.add_child(_make_button("CHARACTER BIOS",func(): _show_detail("KAI: swift martial artist. RYKER: weapon and warfare specialist. LYRA: agile aether mystic.")))
    panel.add_child(_make_button("GALAXIES",func(): _show_detail("Aetheris · Voltara · Nexus · Zephyr · Umbra · Chronos · Pyron · Terralis · Aquarion · Lumina")))
    panel.add_child(_make_button("SETTINGS",func(): _show_detail("Settings will expand with graphics, controls and audio options.")))
    panel.add_child(_make_button("EXTRAS",func(): _show_detail("Additional content is in development.")))
    panel.add_child(_make_button("QUIT",func(): get_tree().quit()))
    var choices := VBoxContainer.new()
    choices.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    body.add_child(choices)
    var choose_label := Label.new()
    choose_label.text = "CHOOSE YOUR CHARACTER"
    choose_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    choose_label.add_theme_font_size_override("font_size",29)
    choose_label.add_theme_color_override("font_color",Color("#f5d29a"))
    choices.add_child(choose_label)
    var hero_row := HBoxContainer.new()
    hero_row.size_flags_vertical = Control.SIZE_EXPAND_FILL
    hero_row.add_theme_constant_override("separation",14)
    choices.add_child(hero_row)
    for i in range(HEROES.size()):
        var hero: Dictionary = HEROES[i]
        var column := VBoxContainer.new()
        column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        column.alignment = BoxContainer.ALIGNMENT_CENTER
        hero_row.add_child(column)
        var card := PanelContainer.new()
        card.custom_minimum_size = Vector2(170,250)
        card.size_flags_vertical = Control.SIZE_EXPAND_FILL
        column.add_child(card)
        var inner := VBoxContainer.new()
        inner.alignment = BoxContainer.ALIGNMENT_CENTER
        card.add_child(inner)
        var portrait_path := "res://approved_heroes/%s.png" % hero["id"]
        if ResourceLoader.exists(portrait_path):
            var portrait := TextureRect.new()
            portrait.texture = load(portrait_path)
            portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
            portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
            portrait.custom_minimum_size = Vector2(170, 180)
            inner.add_child(portrait)
        else:
            var missing := Label.new()
            missing.text = "APPROVED PORTRAIT NOT INSTALLED"
            missing.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
            missing.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
            inner.add_child(missing)
        var sigil := Label.new()
        sigil.visible = not ResourceLoader.exists(portrait_path)
        sigil.text = "⚡"
        sigil.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
        sigil.add_theme_font_size_override("font_size",78)
        sigil.add_theme_color_override("font_color",Color(hero["color"]))
        inner.add_child(sigil)
        var nm := Label.new()
        nm.text = hero["name"]
        nm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
        nm.add_theme_font_size_override("font_size",30)
        inner.add_child(nm)
        var role := Label.new()
        role.text = hero["title"] + "\n" + hero["specialty"]
        role.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
        role.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
        inner.add_child(role)
        var button := _make_button("SELECT " + hero["name"],choose_hero.bind(i))
        column.add_child(button)
        hero_buttons.append(button)
    info = Label.new()
    info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    layout.add_child(info)
    var footer := Label.new()
    footer.text = "THE TEN GALAXIES  ·  AETHER LIGHT REIGNS  /  VOID DARKNESS RISES"
    footer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    footer.add_theme_color_override("font_color",Color("#a6b9e6"))
    layout.add_child(footer)

func _show_detail(value: String) -> void:
    info.text = value

func _refresh() -> void:
    if info == null:
        return
    var hero: Dictionary = HEROES[selected]
    info.text = "SELECTED: %s — %s  |  BEGIN AS A TEENAGE MILITARY APPLICANT" % [hero["name"],hero["title"]]
    for i in range(hero_buttons.size()):
        hero_buttons[i].text = ("✓ " if selected == i else "") + "SELECT " + HEROES[i]["name"]
    continue_button.disabled = not profile.get("started",false)
