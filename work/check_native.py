import pathlib,struct
r=pathlib.Path(__file__).resolve().parent
for p in (r/'tools'/'libpag'/'jni').glob('*/*.so'):
    if p.parent.name not in ['arm64-v8a','x86_64']:continue
    b=p.read_bytes();assert b[:4]==b'\x7fELF' and b[4]==2
    off=struct.unpack_from('<Q',b,32)[0];size,count=struct.unpack_from('<HH',b,54)
    aligns=[]
    for i in range(count):
        fields=struct.unpack_from('<IIQQQQQQ',b,off+i*size)
        if fields[0]==1:aligns.append(fields[-1])
    print(p.parent.name,p.name,'LOAD alignments:',aligns,'16KiB-compatible:',all(x>=16384 for x in aligns))
