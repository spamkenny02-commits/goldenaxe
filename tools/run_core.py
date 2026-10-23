"""Minimal headless libretro frontend for reproducible SMS/MD frame captures."""
import argparse, ctypes as c, hashlib, json, struct, wave
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ENV=c.CFUNCTYPE(c.c_bool,c.c_uint,c.c_void_p)
VIDEO=c.CFUNCTYPE(None,c.c_void_p,c.c_uint,c.c_uint,c.c_size_t)
AUDIO=c.CFUNCTYPE(None,c.c_int16,c.c_int16)
BATCH=c.CFUNCTYPE(c.c_size_t,c.c_void_p,c.c_size_t)
POLL=c.CFUNCTYPE(None)
INPUT=c.CFUNCTYPE(c.c_int16,c.c_uint,c.c_uint,c.c_uint,c.c_uint)
class Variable(c.Structure): _fields_=[('key',c.c_char_p),('value',c.c_char_p)]
class Game(c.Structure): _fields_=[('path',c.c_char_p),('data',c.c_void_p),('size',c.c_size_t),('meta',c.c_char_p)]

def run(rom,frames,out,captures,presses,core=None,ram_writes=(),skip_intro=True,ram_observer=None,psg_observer=None,audio_out=None,sram_in=None,sram_out=None,core_options=None,vram_observer=None,input_provider=None,stop_when=None,save_states=False):
    # Gameplay regressions explicitly skip the now-ported intro with normal input.
    # Set skip_intro=False to observe the complete boot story without inputs.
    presses=list(presses)
    if skip_intro and Path(rom).suffix.lower()!='.sms' and not any(a<=220 and b>=200 for a,b,key in presses):
        presses.insert(0,(200,220,0))
    # Compile fixed intervals once; long cold-boot campaign replays can carry
    # thousands of intervals. Keep inclusive endpoints and overlapping holds.
    fixed_inputs=[0]*(frames+1)
    for start,end,button in presses:
        if button<0:continue
        mask=1<<button
        for tick in range(max(0,start),min(frames,end)+1):fixed_inputs[tick]|=mask
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    dll=c.CDLL(str(Path(core).resolve() if core else ROOT.parents[1]/'work/libretro/genesis_plus_gx_libretro.dll'))
    system_dir=str(ROOT.parents[1]/'work/libretro').encode()
    options={str(k).encode():str(v).encode() for k,v in (core_options or {}).items()}
    variables={}; mode=0; frame=0; captured={};audio_pcm=bytearray()
    @ENV
    def environment(command,data):
        nonlocal mode
        cmd=command & 0xffff
        if cmd==3: c.cast(data,c.POINTER(c.c_bool))[0]=False; return True
        if cmd in (9,30,31): c.cast(data,c.POINTER(c.c_char_p))[0]=system_dir; return True
        if cmd==10: mode=c.cast(data,c.POINTER(c.c_uint))[0]; return mode in (0,1,2)
        if cmd==15:
            var=c.cast(data,c.POINTER(Variable)).contents
            if var.key in variables: var.value=variables[var.key]; return True
            return False
        if cmd==16:
            array=c.cast(data,c.POINTER(Variable)); n=0
            while array[n].key:
                value=array[n].value.split(b'; ',1)[-1].split(b'|',1)[0]
                variables[array[n].key]=options.get(array[n].key,value); n+=1
            return True
        if cmd==17: c.cast(data,c.POINTER(c.c_bool))[0]=False; return True
        if cmd==18: c.cast(data,c.POINTER(c.c_bool))[0]=False; return True
        if cmd in (1,6,11,13,35): return True
        if cmd==52: c.cast(data,c.POINTER(c.c_uint))[0]=0; return True
        return False
    @VIDEO
    def video(data,width,height,pitch):
        if frame not in captures or not data: return
        raw=c.string_at(data,pitch*height)
        if mode==1:
            im=Image.frombytes('RGB',(width,height),raw,'raw','BGRX',pitch)
        else:
            im=Image.new('RGB',(width,height)); pixels=[]
            for y in range(height):
                for x in range(width):
                    p=y*pitch+x*2; v=raw[p]|raw[p+1]<<8
                    if mode==2: pixels.append((((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31))
                    else: pixels.append((((v>>10)&31)*255//31,((v>>5)&31)*255//31,(v&31)*255//31))
            im.putdata(pixels)
        im.save(out/f'frame_{frame:05d}.png'); captured[frame]={'width':width,'height':height,'format':mode}
    @AUDIO
    def audio(left,right):
        if audio_out is not None:audio_pcm.extend(struct.pack('<hh',left,right))
    @BATCH
    def batch(data,count):
        if audio_out is not None:audio_pcm.extend(c.string_at(data,count*4))
        return count
    @POLL
    def poll(): pass
    @INPUT
    def input_state(port,device,index,button):
        return int(port==0 and (bool(fixed_inputs[frame] & (1<<button))
                   or (input_provider is not None and button in input_provider(frame))))
    callbacks=[environment,video,audio,batch,poll,input_state]
    for name,typ,cb in zip(('environment','video_refresh','audio_sample','audio_sample_batch','input_poll','input_state'),(ENV,VIDEO,AUDIO,BATCH,POLL,INPUT),callbacks):
        f=getattr(dll,'retro_set_'+name); f.argtypes=[typ]; f(cb)
    dll.retro_init()
    dll.retro_load_game.argtypes=[c.POINTER(Game)]; dll.retro_load_game.restype=c.c_bool
    dll.retro_get_memory_data.argtypes=[c.c_uint]; dll.retro_get_memory_data.restype=c.c_void_p
    dll.retro_get_memory_size.argtypes=[c.c_uint]; dll.retro_get_memory_size.restype=c.c_size_t
    dll.retro_serialize_size.restype=c.c_size_t
    dll.retro_serialize.argtypes=[c.c_void_p,c.c_size_t]; dll.retro_serialize.restype=c.c_bool
    path=str(Path(rom).resolve()).encode(); raw=Path(rom).read_bytes(); buffer=c.create_string_buffer(raw)
    game=Game(path,c.cast(buffer,c.c_void_p),len(raw),None)
    assert dll.retro_load_game(c.byref(game)), 'Core failed to load ROM'
    if sram_in is not None:
        initial_sram=Path(sram_in).read_bytes();size=dll.retro_get_memory_size(0);ptr=dll.retro_get_memory_data(0)
        assert ptr and len(initial_sram)<=size,('SRAM image size',len(initial_sram),size)
        c.memmove(ptr,initial_sram,len(initial_sram))
    if hasattr(dll,'gaw_trace_reset'): dll.gaw_trace_reset()
    if psg_observer is not None:
        assert hasattr(dll,'gaw_psg_regs'), 'Read-only PSG diagnostic core required'
        dll.gaw_psg_regs.restype=c.POINTER(c.c_int)
    for frame in range(1,frames+1):
        # Test-only injection of CPU-order bytes; never part of normal runs.
        for write_frame,address,data in ram_writes:
            if write_frame!=frame:continue
            n=dll.retro_get_memory_size(2);ptr=dll.retro_get_memory_data(2)
            assert ptr and 0<=address and address+len(data)<=n
            for offset,value in enumerate(data):
                host_address=address+offset
                if Path(rom).suffix.lower()!='.sms':host_address^=1
                c.c_uint8.from_address(ptr+host_address).value=value
        dll.retro_run()
        if psg_observer is not None:psg_observer(frame,tuple(dll.gaw_psg_regs()[i] for i in range(8)))
        if ram_observer is not None:
            n=dll.retro_get_memory_size(2);ptr=dll.retro_get_memory_data(2)
            if ptr and n:ram_observer(frame,c.string_at(ptr,n))
        if vram_observer is not None:
            state=c.create_string_buffer(dll.retro_serialize_size())
            assert dll.retro_serialize(state,len(state))
            base=16+(0x2000 if Path(rom).suffix.lower()=='.sms' else 0x10000+0x2000+5)+16+0x400
            vram_observer(frame,state.raw[base:base+0x10000])
        if frame in captures:
            n=dll.retro_get_memory_size(2); ptr=dll.retro_get_memory_data(2)
            if ptr and n: (out/f'ram_{frame:05d}.bin').write_bytes(c.string_at(ptr,n))
            state=c.create_string_buffer(dll.retro_serialize_size())
            if dll.retro_serialize(state,len(state)):
                # Full GX states are about 1 MiB each. Regression tools use
                # the extracted RAM/VDP files, so retain full states on demand.
                if save_states:(out/f'state_{frame:05d}.bin').write_bytes(state.raw)
                # Official GX state layout: version, RAM, IO, SAT, VRAM, CRAM, VSRAM, registers.
                base=16+(0x2000 if Path(rom).suffix.lower()=='.sms' else 0x10000+0x2000+5)+16+0x400
                (out/f'vram_{frame:05d}.bin').write_bytes(state.raw[base:base+0x10000])
                (out/f'cram_{frame:05d}.bin').write_bytes(state.raw[base+0x10000:base+0x10080])
                (out/f'vdp_regs_{frame:05d}.bin').write_bytes(state.raw[base+0x10100:base+0x10120])
        if stop_when is not None and stop_when():break
    if hasattr(dll,'gaw_trace_counts'):
        for name,size in [('counts',0x40000*4),('windows',0x40000),('states',256*4)]:
            f=getattr(dll,'gaw_trace_'+name); f.restype=c.c_void_p
            (out/f'trace_{name}.bin').write_bytes(c.string_at(f(),size))
    if True: # Always record the actual emulated cadence for timing comparisons.
        class Geometry(c.Structure):_fields_=[('width',c.c_uint),('height',c.c_uint),('max_width',c.c_uint),('max_height',c.c_uint),('aspect',c.c_float)]
        class Timing(c.Structure):_fields_=[('fps',c.c_double),('sample_rate',c.c_double)]
        class AVInfo(c.Structure):_fields_=[('geometry',Geometry),('timing',Timing)]
        av=AVInfo();dll.retro_get_system_av_info.argtypes=[c.POINTER(AVInfo)];dll.retro_get_system_av_info(c.byref(av))
    if audio_out is not None:
        with wave.open(str(audio_out),'wb') as wav:
            wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(round(av.timing.sample_rate));wav.writeframes(audio_pcm)
    if sram_out is not None:
        size=dll.retro_get_memory_size(0);ptr=dll.retro_get_memory_data(0)
        assert ptr, 'No SRAM exposed by core'
        Path(sram_out).write_bytes(c.string_at(ptr,size))
    dll.retro_unload_game(); dll.retro_deinit()
    (out/'capture.json').write_text(json.dumps({'rom':str(Path(rom).resolve()),'rom_sha256':hashlib.sha256(raw).hexdigest(),
        'core':str(Path(core).resolve()) if core else 'official downloaded GX core',
        'frames':frame if stop_when is not None else frames,'captures':captured,'presses':presses,
        'fps':av.timing.fps,'sample_rate':av.timing.sample_rate,'core_options':core_options or {},
        'sram_input':str(sram_in) if sram_in else None,'sram_output':str(sram_out) if sram_out else None,'save_states':save_states,
        'test_ram_writes':[{'frame':f,'address':a,'byte_count':len(d)} for f,a,d in ram_writes]},indent=2))
    print(json.dumps(captured))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('rom'); p.add_argument('--frames',type=int,default=600)
    p.add_argument('--out',required=True); p.add_argument('--capture',default='60,120,300,600')
    p.add_argument('--press',action='append',default=[],help='start:end:libretro-button-id (B=0,Start=3,A=8)')
    p.add_argument('--core',help='Optional instrumented core DLL')
    p.add_argument('--save-states',action='store_true',help='Also retain complete emulator save states (about 1 MiB per capture)')
    a=p.parse_args(); run(a.rom,a.frames,a.out,{int(x) for x in a.capture.split(',')},[tuple(map(int,x.split(':'))) for x in a.press],a.core,save_states=a.save_states)
