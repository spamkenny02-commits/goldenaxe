"""Native854B all400-byte state, T/M1, A/DE/unwind and PSG decisions."""
import ctypes as c,hashlib,json,os,subprocess
from actor_reference import ROOT
from audio_envelope_refresh import adsr_refresh,table_envelope_refresh
from validate_audio_envelope_refresh import fixtures
from validate_native_audio_prefix import Work

FIELDS=[0,1,7,0x1d,0x1f,0x20,0x21,0x22,0x23,0x24]
class Output(c.Structure):_fields_=[('accumulator',c.c_uint8),('unwind',c.c_uint8),('write',c.c_uint8),('psg',c.c_uint8)]

def make_cases():
    rom=(ROOT/'input/original.sms').read_bytes();rows=[]
    for table in [False,True]:
        records,offsets=fixtures(table)
        for number,record in enumerate(records):
            offset=0x40+(number%7)*0x30;salt=(number*19+17)&255
            initial=bytearray((i*37+salt)&255 for i in range(400))
            for position,value in zip(offsets,record):initial[offset+position-0x40]=value
            de=(record[-2]|record[-1]<<8) if table else (number*257)&65535
            result=table_envelope_refresh(rom,initial,offset,de) if table else adsr_refresh(initial,offset,de)
            expected=result['state'];reconstructed=bytearray(initial)
            for field in FIELDS:reconstructed[offset+field]=expected[offset+field]
            assert reconstructed==expected
            mode=initial[offset+7];flags=initial[offset+0x1d]
            terminal=bool(mode&128 and not flags&112 and initial[offset+0x1f]+initial[offset+0x24]>255)
            write=int(not initial[offset]&4 and (terminal or (result.get('unwind',False) and result['accumulator'] not in [0x81,0x82])))
            rows.append(dict(offset=offset,salt=salt,de=de,input=[initial[offset+i] for i in FIELDS],
                expected=[expected[offset+i] for i in FIELDS],tstates=result['tstates'],fetches=result['m1_fetches'],
                expected_de=result['de'],accumulator=result['accumulator'],unwind=int(result.get('unwind',False)),
                write=write,psg=(initial[offset+1]+31)&255 if write else 0,accepted=1,kind='table' if table else 'adsr'))
    bank=rom[0x18000:0x1c000]
    for row in list(rows):
        if row['kind']!='table' or not row['input'][2]:continue
        mode=row['input'][2];pointer=0x97f+(mode-1)*2;table=bank[pointer]|bank[pointer+1]<<8
        if bank[table-0x8000+row['input'][4]]==0x83:
            bad=dict(row,de=0xbfff,expected_de=0xbfff,expected=row['input'][:],tstates=0,fetches=0,
                     accumulator=0,unwind=0,write=0,psg=0,accepted=0,kind='rejected')
            rows.append(bad)
            if sum(r['kind']=='rejected' for r in rows)>=8:break
    return rows

def main():
    folder=ROOT/'validation/native-audio-envelope';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(ROOT/'megadrive/src/source_audio_envelope.c'),'-o',str(folder/'source_audio_envelope.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_audio_envelope.dll'));function=dll.source_audio_envelope
    function.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Output)];function.restype=c.c_uint8
    rom=(ROOT/'input/original.sms').read_bytes();bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000]);low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);rows=make_cases()
    for index,row in enumerate(rows):
        initial=bytearray((i*37+row['salt'])&255 for i in range(400));offset=row['offset']
        for field,value in zip(FIELDS,row['input']):initial[offset+field]=value
        expected=bytearray(initial)
        for field,value in zip(FIELDS,row['expected']):expected[offset+field]=value
        state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(row['de']);work=Work();output=Output()
        accepted=function(state,offset,low,32768,bank,c.byref(de),c.byref(work),c.byref(output))
        assert bytes(state)==expected,(index,'state')
        assert (work.tstates,work.fetches,de.value)==(row['tstates'],row['fetches'],row['expected_de']),(index,'work',work.tstates,work.fetches,de.value,row)
        assert (accepted,output.accumulator,output.unwind,output.write,output.psg)==tuple(row[k] for k in ['accepted','accumulator','unwind','write','psg']),(index,'outputs',row)
    (folder/'cases.json').write_text(json.dumps(dict(fields=FIELDS,cases=rows),separators=(',',':'))+'\n')
    report=dict(cases=len(rows),kinds={kind:sum(r['kind']==kind for r in rows) for kind in ['adsr','table','rejected']},
                compared_RAM_bytes=400,helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_envelope.c').read_bytes()).hexdigest(),
                limits=['Host C vs source-verified854B ADSR/table models; valid fixtures shifted over allseven channel slots.',
                        'Compares all400 bytes,T/M1,A/DE,unwind and explicit PSG decision; invalid read rejects without mutation.',
                        'Standalone component; full native clock and physical waveforms not proven.'])
    (ROOT/'analysis/native_audio_envelope_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'native envelope cases passed',report['kinds'],flush=True)

if __name__=='__main__':main()
