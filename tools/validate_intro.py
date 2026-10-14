"""Natural boot story: compare all 65 original/native text and scene tilemaps."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run

def main():
    suffix='-pal' if '--pal' in sys.argv else ''
    options={'genesis_plus_gx_region_detect':'pal'} if suffix else {}
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    source={};target={};frames={};source_frames={};title=[];source_done=[];source_previous=0;source_closed=False;native_closed=False
    def sms_observe(frame,d):
        nonlocal source_previous,source_closed
        line=d[0x1ce0]
        if line==65 and d[0x1ce1] and not source_done:source_done.append(frame)
        if line<source_previous:source_closed=True
        source_previous=line
        if 1<=line<=65 and not source_closed and not d[0x1ce1]:
            source.setdefault(line,set()).add(d[0x1600:0x1c00]);source_frames.setdefault(line,[]).append(frame)
    def md_observe(frame,raw):
        nonlocal native_closed
        d=bytearray(len(raw));d[::2]=raw[1::2];d[1::2]=raw[::2];off=symbols['intro_running'];running=int.from_bytes(d[off:off+2],'big');off=symbols['intro_line'];line=int.from_bytes(d[off:off+2],'big')
        if running and 1<=line<=65 and not native_closed:
            off=symbols['sms_vram'];target.setdefault(line,set()).add(bytes(d[off+0x3800:off+0x3e00]));frames.setdefault(line,[]).append(frame)
        elif not running and frame>1000:
            title.append(frame);native_closed=True
    with contextlib.redirect_stdout(io.StringIO()):
        run(ROOT/'input/original.sms',7600,ROOT/f'validation/sms-intro-natural{suffix}',{1000,2100,4200,4800,6100},[],skip_intro=False,ram_observer=sms_observe,core_options=options)
        run(ROOT/'gaw-megadrive.bin',7600,ROOT/f'validation/md-intro-natural{suffix}',{1000,2100,4200,4800,6100},[],skip_intro=False,ram_observer=md_observe,core_options=options,audio_out=ROOT/f'validation/md-intro-music{suffix}.wav')
    results=[]
    for line in range(1,66):
        assert source.get(line) and target.get(line),(line,'missing story line')
        shared=source[line]&target[line];assert shared,(line,'story map differs')
        results.append(dict(line=line,scene_and_text_map_bytes_exact=1536,matching_map_states=len(shared),native_frame_range=[min(frames[line]),max(frames[line])],source_frame_range=[min(source_frames[line]),max(source_frames[line])],native_minus_source_start_frames=min(frames[line])-min(source_frames[line])))
    assert title,'Intro did not return to title'
    offsets=[x['native_minus_source_start_frames'] for x in results]
    assert max(offsets)-min(offsets)<=2,('Accumulating scene/intro delay',offsets)
    fps={tag:json.loads((ROOT/f'validation/{tag}-intro-natural{suffix}/capture.json').read_text())['fps'] for tag in ['sms','md']}
    assert abs(fps['sms']-fps['md'])<1e-9
    report=dict(video_fps=fps,line_start_offset_frames_range=[min(offsets),max(offsets)],no_accumulating_text_delay=True,region='pal' if suffix else 'auto',md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),natural_boot=True,no_buttons=True,no_ram_mutations=True,story_lines=results,title_returns_after_intro=True,absolute_frame_timing_exact=False,all_sprite_animation_phases_verified=False,source_intro_completion_frame=source_done[0] if source_done else None,native_intro_completion_frame=min(title),audio=f'md-intro-music{suffix}.wav')
    (ROOT/f'validation/intro{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n');print('65 story lines and scene maps match original; natural intro reaches title')
if __name__=='__main__':main()
