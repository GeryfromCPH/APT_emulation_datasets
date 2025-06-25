#!/usr/bin/env python3
import pandas as pd
import argparse
from scapy.all import PcapReader, PcapNgWriter, IP, TCP, UDP
import os
import glob
from scapy.config import conf
from scapy.packet import Raw
# Treat Raw payloads as Ethernet to avoid KeyError in marker logic
conf.l2types.layer2num[Raw] = 1

def load_label_map(csv_file, src_col, dst_col, sport_col=None, dport_col=None, proto_col=None, time_col=None):
    df = pd.read_csv(csv_file)
    cols = set(df.columns)
    valid_src = src_col in cols
    valid_dst = dst_col in cols
    valid_sport = sport_col in cols if sport_col else False
    valid_dport = dport_col in cols if dport_col else False
    valid_proto = proto_col in cols if proto_col else False
    valid_time = time_col in cols if time_col else False
    mapping = {}
    for _, row in df.iterrows():
        key = ()
        if valid_src:
            key += (row[src_col],)
        if valid_dst:
            key += (row[dst_col],)
        if valid_sport and valid_dport and pd.notna(row[sport_col]) and pd.notna(row[dport_col]):
            key += (int(row[sport_col]), int(row[dport_col]))
        if valid_proto and pd.notna(row[proto_col]):
            key += (row[proto_col],)
        if valid_time and pd.notna(row[time_col]):
            # convert timestamp string to epoch float
            ts = pd.to_datetime(row[time_col]).timestamp()
            key += (ts,)
        mapping[key] = row['label']
    return mapping

def annotate_pcap(input_pcap, mapping, output_pcap,
                  sport_col=None, dport_col=None, proto_col=None, time_col=None):
    reader = PcapReader(input_pcap)
    writer = PcapNgWriter(output_pcap)
    total = 0
    labeled = 0
    for pkt in reader:
        total += 1
        label = None
        if IP in pkt:
            # build key in exact same order as mapping loader
            key = [pkt[IP].src, pkt[IP].dst]
            # ports
            if sport_col and dport_col:
                if TCP in pkt:
                    key += [pkt[TCP].sport, pkt[TCP].dport]
                elif UDP in pkt:
                    key += [pkt[UDP].sport, pkt[UDP].dport]
                else:
                    key += [None, None]
            # protocol
            if proto_col:
                if TCP in pkt:
                    proto = 'TCP'
                elif UDP in pkt:
                    proto = 'UDP'
                else:
                    proto = str(pkt[IP].proto)
                key.append(proto)
            # timestamp
            if time_col:
                key.append(pkt.time)
            key = tuple(key)
            # only label if full key matches
            if key in mapping:
                label = mapping[key]
        # attach CSV label or default "benign" comment
        pkt.comment = str(label) if label is not None else "benign"
        if label is not None:
            labeled += 1
        writer.write(pkt)
    reader.close()
    writer.close()
    print(f"Labeled {labeled}/{total} packets in {input_pcap}")

def main():
    parser = argparse.ArgumentParser(
        description='Annotate PCAP with labels from CSV'
    )
    parser.add_argument('--src-col', default='SourceIp', help='column for source IP')
    parser.add_argument('--dst-col', default='DestinationIp', help='column for destination IP')
    parser.add_argument('--sport-col', default='SourcePort', help='column for source port')
    parser.add_argument('--dport-col', default='DestinationPort', help='column for destination port')
    parser.add_argument('--proto-col', default=None, help='column for protocol')
    parser.add_argument('--time-col', default=None, help='column for packet timestamp')
    parser.add_argument('--suffix', default='_Labelled', help='Suffix to append to output PCAP file names')
    args = parser.parse_args()

    # Aggregate mappings from all CSVs in the current directory
    cwd = os.getcwd()
    mapping = {}
    for csv_file in glob.glob(os.path.join(cwd, '*.csv')):
        mapping.update(load_label_map(
            csv_file,
            args.src_col,
            args.dst_col,
            args.sport_col,
            args.dport_col,
            args.proto_col,
            args.time_col
        ))

    # Process all PCAP/PCAPNG files, annotating with CSV labels or "benign"
    for input_pcap in glob.glob(os.path.join(cwd, '*.pcap')) + glob.glob(os.path.join(cwd, '*.pcapng')):
        base = os.path.splitext(os.path.basename(input_pcap))[0]
        output_pcap = f"{base}{args.suffix}.pcapng"
        annotate_pcap(
            input_pcap,
            mapping,
            output_pcap,
            args.sport_col,
            args.dport_col,
            args.proto_col,
            args.time_col
        )
        print(f'Labelled {input_pcap} saved to {output_pcap}')

if __name__ == '__main__':
    main()