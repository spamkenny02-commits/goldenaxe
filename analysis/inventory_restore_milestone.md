# v0096 - inventory return uses the current room graphics

User reproduction: opening then closing inventory inside the first village shops mixed outdoor patterns with the interior tile map. show_inventory restored animation_map correctly but always decoded world_background_rle on exit. The map retained interior tile indices while their underlying patterns became outdoor walls/trees.

Inventory exit now chooses the same class-specific background as load_house_room: exterior, house or dungeon. It does not reload the room or reset actors, hero position, ownership or scripts. The production change is confined to this resource selection and its comment.

Normal controller routes enter the first two village houses and open/close inventory in PAL and NTSC. Two exterior cases guard the original path. Pre-menu patterns match SMS. Static background patterns among the first 124 tiles now match after closure; four source-animated house tiles are located through C9E0 and recorded separately, rather than treating animation phase as static corruption. Early native patterns also match the native pre-menu set. The previous v0095 binary reproduces the large corruption in both houses in both regions. Full framebuffer and animated-house phase are not claimed exact. Dungeon selection is corrected by the same branch but these routes do not exercise dungeon inventory.

Existing inventory navigation/equipment/secondary-attack and first-merchant transaction/refusal/natural-route tests are rerun on the final ROM. This fixes the reported inventory-return corruption; other game work, including scrolling arrival poses and NTSC upward timing, remains unfinished.
