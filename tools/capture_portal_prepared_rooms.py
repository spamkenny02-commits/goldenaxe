"""Capture solved-flag portal origin maps using original Z80 room preparation."""
import contextlib,io,json,hashlib
from validate_room_cells import ROOT,fixture
from run_core import run

def main():
    rom=(ROOT/'input/original.sms').read_bytes();image=fixture(rom)
    folder=ROOT/'validation/source-portal-room-preparation';folder.mkdir(exist_ok=True);path=folder/'prepare.sms';path.write_bytes(image)
    selected={r['room'] for r in json.loads((ROOT/'analysis/contact_script_reference.json').read_bytes())['records'] if r['target']==0x5cfb};cases={}
    def observe(frame,raw):
        if not raw[2]:return
        case=int.from_bytes(raw[:2],'little');room=case&511
        if case>>9==3 and room in selected:cases.setdefault(room,dict(cells=raw[0x1c00:0x1ca0].hex(),map=raw[0x1600:0x1b00].hex(),metadata=raw[0x6e:0x71].hex(),flag=raw[0x100+(room&255)]))
    with contextlib.redirect_stdout(io.StringIO()):run(path,70000,folder,{69999},[],skip_intro=False,ram_observer=observe)
    assert len(cases)==36
    report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),persistent_flag_seeded=4,original_routines=['1976','1A7C','1BCD','2279'],rooms=cases)
    (ROOT/'analysis/portal_prepared_rooms.json').write_text(json.dumps(report,indent=2)+'\n');print('36 solved-flag room maps captured from original Z80 preparation.')
if __name__=='__main__':main()
