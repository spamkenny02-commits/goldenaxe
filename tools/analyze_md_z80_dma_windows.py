"""Independently count committed DMA paths in the physical BUSREQ capture."""
from pathlib import Path
import argparse
from bisect import bisect_left,bisect_right
import gzip
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['video-dma-command-bare','video-dma-snapshot-bare','video-dma-snapshot-proof']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variants',nargs='+',default=VARIANTS)
    parser.add_argument('--report-name',default='md_z80_dma_windows_report.json')
    parser.add_argument('--archive',default='md-z80-dma-window-v0203')
    args=parser.parse_args()
    assert all(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',v) for v in args.variants)
    assert re.fullmatch(r'[a-z0-9_]+\.json',args.report_name)
    assert re.fullmatch(r'[a-z0-9-]+',args.archive)
    archive=ROOT/'analysis'/args.archive;manifest=None
    def read(path):
        nonlocal manifest
        if path.exists():return path.read_bytes()
        if manifest is None:manifest=json.loads((archive/'manifest.json').read_bytes())
        name=path.relative_to(ROOT).as_posix()
        if name in manifest['files']:
            raw=(archive/name).read_bytes();assert sha(raw)==manifest['files'][name];return raw
        item=manifest['compressed'][name];encoded=(archive/item['stored']).read_bytes()
        assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded)
        assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes'];return raw
    # Verified native path: control port binding, length16words, source words,
    # command read as two RAM words, then BUSREQ release. No duration heuristic.
    signature=bytes.fromhex('207c00c0000430bc931030bc9400308330813080302f00143080302f0016308032bc0000')
    # Cached payload releases D3 sooner; GCC allocates source_low in D2.
    # Both reviewed forms keep the same control writes and RAM command words.
    signatures=[signature,bytes.fromhex(signature.hex().replace('30bc94003083','30bc94003082'))]
    hvc=(ROOT.parents[1]/'work/genesis-plus-gx/core/hvc.h').read_bytes()
    section=hvc.decode().split('static const uint8 cycle2hc32[3420] =')[1].split('};')[0]
    h=[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',section)];assert len(h)==3420
    results=[]
    for variant in args.variants:
        folder=ROOT/('validation/md-z80-psg-'+variant)
        report_raw=read(ROOT/('analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json'))
        report=json.loads(report_raw);kernel=read(folder/'out/release/rom.bin')
        symbols={m[2]:int(m[1],16) for line in read(folder/'out/release/symbol.txt').decode().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
        clock_hv_pc=symbols['md_service_clock_hv']+6
        assert sha(kernel)==report['kernel_sha256'] and sum(kernel.count(s) for s in signatures)==1
        selected=next(s for s in signatures if kernel.count(s)==1)
        committed_pc=kernel.index(selected)+len(selected)
        for region_report in report['results']:
            region=region_report['region'];lines=262 if region=='ntsc' else 313
            raw=read(folder/(region+'-events.json'));assert sha(raw)==region_report['events_sha256']
            events=json.loads(raw)['events'];markers=[i for i,e in enumerate(events) if e[0]==3 and 128<=e[2]<176]
            rows=[]
            for k,index in enumerate(markers):
                part=events[index+1:markers[k+1] if k+1<len(markers) else len(events)]
                reference=region_report['rows'][k];assert reference['marker']==events[index][2]
                origin=next(e[1]//3420*3420 for e in part if e[0]==6 and e[2]>>8==100)
                start=None;commits=[];all_ranges=[]
                for event in part:
                    if event[0]!=7:continue
                    if event[2] and start is None:start=event[1]
                    elif not event[2] and start is not None:
                        all_ranges.append((start,event[1]))
                        if event[3]==committed_pc:commits.append((start,event[1]))
                        start=None
                assert len(commits)==reference['publisher_callbacks']
                beam_reads=[e for e in part if e[0]==4];beam_times=[e[1] for e in beam_reads]
                z80_times=[e[1] for e in part if e[0]==6]
                assert beam_times==sorted(beam_times) and z80_times==sorted(z80_times)
                helper_beams=[e for e in beam_reads if e[1]>=origin and e[3]!=clock_hv_pc]
                after_bus=sum(bisect_left(beam_times,b)-bisect_right(beam_times,a) for a,b in all_ranges)
                before_bus=len(helper_beams)-after_bus
                assert before_bus>=after_bus>=len(commits)
                for a,b in commits:
                    assert 0<b-a<17100
                    assert all((line+224)%lines>=224 for line in range(a//3420,b//3420+1))
                    beam=beam_reads[bisect_right(beam_times,a):bisect_left(beam_times,b)]
                    assert len(beam)==1
                    e=beam[0];physical=(e[1]//3420+224)%lines
                    v=(physical if physical<=(234 if lines==262 else 258) else physical-lines)&255
                    assert e[2]==v*256+h[e[1]%3420] and 235<=v<=252
                    # BUSREQ precedes BUSACK: an in-flight Z80 instruction
                    # may finish before the native held-bus guard read.
                    assert bisect_right(z80_times,beam[0][1])==bisect_left(z80_times,b)
                last=commits[-1][1]-origin
                rows.append(dict(marker=reference['marker'],committed=len(commits),
                    pre_bus_beam_reads=before_bus,post_bus_beam_reads=after_bus,
                    hold_min=min(b-a for a,b in commits),hold_max=max(b-a for a,b in commits),
                    during_loader=sum(b-origin<reference['loader_finish_master'] for a,b in commits),
                    after_delivery_query=sum(b-origin>reference['delivery_finish_master']+20 for a,b in commits),
                    last_after_loader_master=max(0,last-reference['loader_finish_master']),
                    last_after_delivery_query_master=max(0,last-reference['delivery_finish_master']),
                    last_after_loader_frames=max(0,last-reference['loader_finish_master'])/(lines*3420)))
            assert sum(r['committed'] for r in rows)==region_report['video_requests']==2784
            pre_reads=sum(r['pre_bus_beam_reads'] for r in rows)
            assert pre_reads<=region_report['video_dma_attempts']
            results.append(dict(variant=variant,region=region,report_sha256=sha(report_raw),events_sha256=sha(raw),
                signature_hex=selected.hex(),
                committed_release_pc=committed_pc,committed=sum(r['committed'] for r in rows),
                attempts=region_report['video_dma_attempts'],attempts_before_beam_rejected=region_report['video_dma_attempts']-pre_reads,
                pre_bus_beam_reads=pre_reads,post_bus_beam_reads=sum(r['post_bus_beam_reads'] for r in rows),
                during_loader=sum(r['during_loader'] for r in rows),
                after_delivery_query=sum(r['after_delivery_query'] for r in rows),
                hold_max=max(r['hold_max'] for r in rows),
                max_last_after_loader_frames=max(r['last_after_loader_frames'] for r in rows),rows=rows))
            print({k:v for k,v in results[-1].items() if k!='rows'},flush=True)
    output=dict(hvc_sha256=sha(hvc),signature_hex=signature.hex(),results=results,
        limits=['Counts physical successful DMA-path releases by checked native instruction signature, not by counters or duration. Every counted request-to-release range is inside physical VBlank, with its native held-bus beam read independently checked against frame/time/HV tables. No Z80 sample occurs after that guard read before release; an in-flight instruction can finish between BUSREQ and BUSACK.',
                'All deterministic fixture requests commit in FIFO order; no game-renderer payload or per-frame deadline proof. Many video jobs drain after loader/audio delivery. Delivery query boundary is rounded to20ticks, so after-query counts use a20tick margin.',
                'This supplemental analysis establishes the specific DMA path actually executed. Native IRQs remain masked, only32byte jobs tested, no waveform/hardware/whole-game guarantee.'])
    (ROOT/'analysis'/args.report_name).write_text(json.dumps(output,indent=2)+'\n')


if __name__=='__main__':main()
