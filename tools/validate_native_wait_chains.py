"""Keep native clock/RAM/audio alive across source0B95 double-wait returns."""
import ctypes as c
import json
import struct
from actor_reference import ROOT
from native_wait_return_support import compile_helper,helpers


def main():
    folder,dll,_=compile_helper();function=dll.wait_chain_case
    function.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),
                       c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.c_uint16,c.POINTER(c.c_uint32),c.POINTER(c.c_uint32)]
    function.restype=c.c_uint8;source=(ROOT/'input/original.sms').read_bytes()
    low=(c.c_uint8*32768).from_buffer_copy(source[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(source[0x18000:0x1c000])
    reference=json.loads((ROOT/'analysis/native_wait_return_live_report.json').read_text());single=json.loads((folder/'live-cases.json').read_text())
    cases=[];rows=[];offset=0
    for row in reference['rows']:
        raw=(ROOT/f"validation/wait-return-live/{row['town']:02x}-{row['mask']:02x}/{row['region']}/returns.bin").read_bytes();count=0
        for n in range(row['cases']):
            first=raw[n*2464:(n+1)*2464]
            if struct.unpack_from('<I',first,2448)[0]!=0xb95:continue
            assert n+1<row['cases'];second=raw[(n+1)*2464:(n+2)*2464]
            assert first[1600:2400]==second[:800] and first[2432:2448]==second[2400:2416]
            case=single[offset+n];next_case=single[offset+n+1]
            state=(c.c_uint8*336).from_buffer_copy(bytes(case['ram']));audio=(c.c_uint8*400).from_buffer_copy(bytes(case['audio']))
            output=(c.c_uint32*18)();trace=(c.c_uint32*96)()
            assert function((c.c_uint32*12)(*case['phase']),case['refresh'],state,audio,low,bank,case['tile_count'],2,output,trace)
            end=second[1600:2400];end_meta=struct.unpack_from('<Q2I',second,2432);first_meta=struct.unpack_from('<Q2I',first,2400)
            phase=struct.unpack_from('<12I',end,16);delta=((phase[0]-phase[2]+0x80000000)&0xffffffff)-0x80000000
            assert output[0]==(phase[1]*3420+delta)%(phase[3]*3420) and output[10]==end_meta[1]
            assert output[2]==struct.unpack_from('<Q',end,8)[0]-struct.unpack_from('<Q',first,8)[0]
            assert output[4]+output[6]==end_meta[0]-first_meta[0] and not output[16]
            assert bytes(audio)==end[400:800] and all(state[i]==end[64+i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23])
            expected=list(next_case['expected']);expected[2:10]=[case['expected'][i]+next_case['expected'][i] for i in range(2,10)]
            expected[15]=case['expected'][15]+next_case['expected'][15];expected[17]=output[17]
            assert list(output)==expected
            events=list(case['events'])
            for e in range(0,len(next_case['events']),6):
                event=list(next_case['events'][e:e+6]);event[0]+=case['expected'][2];events.extend(event)
            assert list(trace[:output[7]*6])==events
            result=dict(case);result.update(kind='double-chain',repetitions=2,expected_ram=list(state),expected_audio=list(audio),expected=list(output),events=events,caller=next_case['caller'])
            cases.append(result);count+=1
        offset+=row['cases'];rows.append(dict(town=row['town'],mask=row['mask'],region=row['region'],chains=count))
    assert offset==len(single) and len(cases)==816
    (folder/'chain-cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(chains=len(cases),wait_calls=len(cases)*2,rows=rows,helper_sha256=helpers(),
                limits=['Two actual source waits joined at identical0B95 caller/entry snapshots; one live native clock/RAM/audio context, no intermediate source-state reinjection.',
                        'Final caller phase,R,M1,duration,331RAM,400audio and all IRQ entries match source; extra native fields checked for host parity.',
                        'Observed first entry, controlled routes; production wiring/hardware/full progression remain open.'])
    (ROOT/'analysis/native_wait_chain_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(cases),'native double-wait chains exact without intermediate state reset')


if __name__=='__main__':main()
