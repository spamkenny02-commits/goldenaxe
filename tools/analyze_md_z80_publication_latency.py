"""Decompose archived live PSG delays; never rerun or alter the measured kernel."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    archive = ROOT / 'analysis/md-z80-grants-v0203'
    manifest_raw = (archive / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)

    def recover(name):
        item = manifest['compressed'][name]
        encoded = (archive / item['stored']).read_bytes()
        assert sha(encoded) == item['stored_sha256'], name
        raw = gzip.decompress(encoded)
        assert sha(raw) == item['raw_sha256'] and len(raw) == item['raw_bytes'], name
        return raw

    report_name = 'analysis/md_z80_psg_grant_eight_bare_report.json'
    report_raw = (ROOT / report_name).read_bytes()
    assert sha(report_raw) == manifest['reports'][report_name]
    report = json.loads(report_raw)
    prefix = 'validation/md-z80-psg-grant-eight-bare/'
    kernel = recover(prefix + 'out/release/rom.bin')
    assert sha(kernel) == report['kernel_sha256']
    # Actual successful transfer path: 22 MOVE.Bs, head publish, mailbox
    # head mirror, grant clear, BUSREQ release. Observer PC is after release.
    signature = bytes.fromhex('10db' * 22 + '13c000a0010615400006157c0000000832bc0000')
    assert kernel.count(signature) == 1
    release_pc = kernel.index(signature) + len(signature)
    results = []
    for region_report in report['results']:
        region = region_report['region']
        raw = recover(prefix + region + '-events.json')
        assert sha(raw) == region_report['events_sha256']
        events = json.loads(raw)['events']
        markers = [i for i, e in enumerate(events) if e[0] == 3 and 128 <= e[2] < 176]
        assert len(markers) == len(region_report['rows']) == 48
        rows = []
        for ordinal, index in enumerate(markers):
            part = events[index + 1:markers[ordinal + 1] if ordinal + 1 < len(markers) else len(events)]
            checked = region_report['rows'][ordinal]
            assert checked['marker'] == events[index][2]
            origin = next(e[1] // 3420 * 3420 for e in part if e[0] == 6 and e[2] >> 8 == 100)
            writes = [e for e in part if e[0] == 5]
            dates = [e[1] - error for e, error in zip(writes, checked['errors_master'])]
            assert len(dates) == len(writes)
            # Reconstruct the planner's maximal 315/630 groups. Check the
            # descriptor count and FIFO order against physical successful
            # publications, rather than classifying holds by their duration.
            groups = []
            first = 0
            while first < len(dates):
                spacing = dates[first + 1] - dates[first] if first + 1 < len(dates) else 0
                limit = 16 if spacing == 315 else 8 if spacing == 630 else 1
                count = 1
                while count < limit and first + count < len(dates) and dates[first + count] - dates[first + count - 1] == spacing:
                    count += 1
                # Without a longer run, an equally sized descriptor list
                # cannot hide shifted burst boundaries across callbacks.
                assert limit == 1 or count < limit or first + count == len(dates) or dates[first + count] - dates[first + count - 1] != spacing
                groups.append((first, count, spacing if count > 1 else 0))
                first += count
            held = callback = None
            transfers = []
            for event in part:
                kind, clock, value, pc = event
                if kind == 3 and value == 0x30:
                    assert callback is None
                    callback = clock
                elif kind == 3 and value == 0x31:
                    assert callback is not None
                    callback = None
                elif kind == 7:
                    if value and held is None:
                        held = clock
                    elif not value and held is not None:
                        if pc == release_pc:
                            assert callback is not None and callback <= held < clock
                            transfers.append((callback, held, clock))
                        held = None
            assert callback is None and len(transfers) == len(groups)
            for (first, count, spacing), (entry, begin, release) in zip(groups, transfers):
                assert writes[first][1] >= release
                for n in range(count):
                    byte = first + n
                    due = dates[byte]
                    # For burst suffixes subtract the exact scheduled spacing
                    # from the consumer interval, preserving the same offset.
                    producer = entry - dates[first]
                    publisher = begin - entry
                    bus = release - begin
                    consumer = writes[byte][1] - release - n * spacing
                    assert consumer >= 0
                    total = producer + publisher + bus + consumer
                    assert total == checked['errors_master'][byte]
                    rows.append(dict(marker=checked['marker'], byte=byte, value=writes[byte][2],
                        due_master=due-origin, callback_entry_master=entry-origin,
                        transfer_begin_master=begin-origin, transfer_end_master=release-origin,
                        output_master=writes[byte][1]-origin, burst_index=n,
                        producer_at_entry_signed=producer, publisher_before_bus=publisher,
                        bus_hold=bus, consumer_after_release=consumer, late_master=total))
        assert len(rows) == 2976
        worst = max(rows, key=lambda row: row['late_master'])
        results.append(dict(region=region, bytes=len(rows), worst=worst,
            producer_already_late_bytes=sum(row['producer_at_entry_signed'] > 0 for row in rows),
            max_producer_at_entry_signed=max(row['producer_at_entry_signed'] for row in rows),
            max_publisher_before_bus=max(row['publisher_before_bus'] for row in rows),
            max_consumer_after_release=max(row['consumer_after_release'] for row in rows), rows=rows))
        print(region, json.dumps({k: v for k, v in results[-1].items() if k != 'rows'}))
    output = dict(archive_manifest_sha256=sha(manifest_raw), measurement_report_sha256=sha(report_raw),
        successful_release_pc=release_pc, results=results,
        limits=[
            'Offline decomposition of the already checked bare live-loader capture; no new runtime or production proof.',
            'Producer-at-entry is signed deadline displacement at diagnostic callback entry, after FIFO enqueue. It includes source computation, enqueue/setup, prior callbacks, and previous waits; it does not isolate reader execution cost.',
            'Publisher-before-bus includes capture/plan/descriptor construction and grant retries; consumer-after-release includes copy/scheduling. Maxima of components need not occur at the same byte.',
            'Dates derive from independently validated output-minus-error records bound by archive/report hashes. FIFO descriptor reconstruction is accepted only after exact group/publication counts and nonnegative release-to-output checks.',
            'Instrumented PSG markers, display off, native interrupts masked, no DMA; no clean waveform or whole-game deadline guarantee.'])
    (ROOT / 'analysis/md_z80_psg_publication_latency_report.json').write_text(json.dumps(output, indent=2) + '\n')


if __name__ == '__main__':
    main()
