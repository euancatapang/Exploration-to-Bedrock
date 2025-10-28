from modifierMap import (
    STATIC_MODIFIERS, STAIRS_MAPPING, GATE_MAPPING,
    TRAPDOOR_MAPPING, TRAPDOOR_ON_ROOF
)

def translate_block_modifier(exploration_modifier: int, block_type: str) -> int:

    # Assignment mapping
    if (block_type, exploration_modifier) in STATIC_MODIFIERS:
        return STATIC_MODIFIERS[(block_type, exploration_modifier)]

    # Additive mapping
    if block_type == "stairs":
        modifier = 4 if exploration_modifier >= 0x24 else 0
        modifier += STAIRS_MAPPING.get(exploration_modifier, 0)
        return modifier

    if block_type == "door":
        return 8

    if block_type == "gate":
        modifier = 4 if exploration_modifier >= 0x22 else 0
        modifier += GATE_MAPPING.get(exploration_modifier, 0)
        return modifier

    if block_type == "trapdoor":
        modifier = 8 if exploration_modifier >= 0x28 else 0
        if exploration_modifier in TRAPDOOR_ON_ROOF:
            modifier += 4
        modifier += TRAPDOOR_MAPPING.get(exploration_modifier, 0)
        return modifier

    # Unknown block type
    print(f"Unknown block modifier: {block_type} with {hex(exploration_modifier)}")
    return 0