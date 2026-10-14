"""Original room-script clear events versus compiled native passage dispatch."""
import contextlib,hashlib,io,json,re
from validate_room_cells import fixture,ROOT
from run_core import run


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    original=(ROOT/'input/original.sms').read_bytes()
    harness=ROOT.parents[1]/'work/item-rewards-harness'
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in
        (harness/'out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    copies={}
    for path in (ROOT/'megadrive/src').iterdir():
        if not path.is_file():continue
        target=harness/'src'/('game_main.inc' if path.name=='main.c' else path.name)
        assert path.read_bytes()==target.read_bytes(),path.name
        copies[path.name]=sha(path.read_bytes())
    folder=ROOT/'validation/item-rewards';folder.mkdir(exist_ok=True)
    source=folder/'source-item-rewards.sms';image=fixture(original,items=True);source.write_bytes(image)
    expected={};done=[]
    def observe_source(frame,raw):
        if raw[4]:done.append(frame)
        if not raw[2]:return
        case=int.from_bytes(raw[:2],'little')
        if case in expected:return
        expected[case]=(bytes(raw[0x1c00:0x1ca0]),bytes(raw[0x1600:0x1b00]),
                        bytes(raw[0x100:0x200]),raw[0xde],raw[0x1e08],raw[0xa2],raw[0xa8],raw[0xa9],bytes(raw[0x4b0:0x600]),bytes(raw[0xe0:0xf1]))
    with contextlib.redirect_stdout(io.StringIO()):
        run(source,80000,folder/'sms',{79999},[],skip_intro=False,ram_observer=observe_source)
    assert len(expected)==8192 and done,('source',len(expected))
    print('8192 original Z80 item grant cases captured',flush=True)
    checked=set();done=[];opened=0;consumed=0
    def observe_native(frame,raw):
        nonlocal opened,consumed
        def data(name,size,offset=0):
            a=sy[name]+offset
            return bytes(raw[(a+i)^1] for i in range(size))
        def word(name):return int.from_bytes(data(name,2),'big')
        if word('harness_done'):done.append(frame)
        if not word('harness_ready'):return
        case=word('harness_case')
        if case in checked:return
        cells,tilemap,flags,keys,effect,count,state,direction,loot,items=expected[case]
        assert data('scratch',160,0x800)==cells,(case,'cells',[(i,a,b) for i,(a,b) in enumerate(zip(cells,data('scratch',160,0x800))) if a!=b],flags.hex(),data('game_save_state',256,0x50).hex(),keys,word('harness_keys'))
        assert data('sms_vram',1280,0x3800)==tilemap,(case,'map',[(i,a,b) for i,(a,b) in enumerate(zip(tilemap,data('sms_vram',1280,0x3800))) if a!=b][:24])
        assert data('game_save_state',256,0x50)==flags,(case,'flags')
        assert data('harness_items',17)==items,(case,'inventory')
        assert word('harness_keys')==keys,(case,'keys',word('harness_keys'),keys)
        assert word('world_actor_count')==count,(case,'counter',word('world_actor_count'),count)
        assert data('world_loot_state',336)==loot,(case,'loot',[(i,a,b) for i,(a,b) in enumerate(zip(loot,data('world_loot_state',336))) if a!=b][:8])
        assert state==0,(case,'unexpected source shutter')
        assert direction==0,(case,'unexpected source shutter direction')
        assert keys==2,(case,'clear consumed a key')
        if effect==0xa5:opened+=1
        checked.add(case)
    with contextlib.redirect_stdout(io.StringIO()):
        run(harness/'out/release/rom.bin',80000,folder/'md',{79999},[],skip_intro=False,ram_observer=observe_native)
    assert len(checked)==8192 and done and opened==0,(len(checked),opened,consumed)
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha(original),
                fixture_sha256=sha(image),harness_sha256=sha((harness/'out/release/rom.bin').read_bytes()),
                modal_frontend_excluded_from_unit_fixture=True,original_routines_executed=['B762 (10 original item scripts)','5D59..5DEB','193D','1976','1A7C','1B0E','2279','35D4','6317..6319 (item-number store; remaining frontend stubbed)'],cases_checked=8192,selected_item_rooms=10,selected_item_cases=160,nonselected_setup_cases=8032,
                source_opened_cases=opened,source_key_consumption_cases=0,item_grant_guards_and_writes_exact=True,loot_allocation_and_preserved_record_bytes_exact=True,inventory_writes_exact=True,repeated_dispatch_verified=True,
                source_cells_maps_all_room_flags_and_key_count_exact=True,
                source_copies=copies,controlled_position_direction_input_and_inventory=True,
                natural_controller_gameplay_verified=False,full_game_ported=False,
                limits=['Only 160 cases execute the ten selected item scripts; 8032 cases compare nonselected room setup.', 'The SMS fixture bypasses IRQ wait 0B95 and replaces the modal frontend after its item-number store at 631A with RET. Grant conditions, persistent writes and room preparation execute unchanged.', 'The native fixture calls the production grant helper directly; it excludes the acquisition window. Separate live and VRAM reports cover that window.', 'No natural complete dungeon route, audio waveform or message/redraw latency validation is implied.'])
    (ROOT/'validation/item_rewards_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'8192 native cases match; {opened} openings, {consumed} key consumptions')


if __name__=='__main__':main()
