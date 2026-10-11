"""Extract stock clock fonts and signed dimensions from the already verified EEA APK."""
from pathlib import Path
import hashlib,json,re,struct,zipfile
ROOT=Path(__file__).resolve().parents[2]
EXPECTED='31c6dd09226e24f13f519822425a0b3f2a6d4fb8d6bf565bbd3a0568ee494d5d'
def sha(x):return hashlib.sha256(x).hexdigest()
def dimensions(data,wanted):
    found={}
    def chunks(start,end,package=0):
        at=start
        while at<end:
            kind,head,size=struct.unpack_from('<HHI',data,at)
            assert 8<=head<=size and at+size<=end
            if kind==0x200:
                pid=struct.unpack_from('<I',data,at+8)[0]
                chunks(at+head,at+size,pid)
            elif kind==0x201:
                tid,flags=struct.unpack_from('<BB',data,at+8)
                count,base=struct.unpack_from('<II',data,at+12)
                config=data[at+20:at+head]
                sw=struct.unpack_from('<H',config,30)[0] if len(config)>=32 else 0
                if package==0x7f and tid==7 and sw in (0,372):
                    assert flags==0,'Unexpected sparse/compact resource encoding'
                    for index in range(count):
                        rid=package<<24|tid<<16|index
                        if rid not in wanted:continue
                        offset=struct.unpack_from('<I',data,at+head+index*4)[0]
                        if offset==0xffffffff:continue
                        pos=at+base+offset
                        entry_size,entry_flags=struct.unpack_from('<HH',data,pos)
                        assert not entry_flags&1
                        typ=data[pos+entry_size+3]
                        raw=struct.unpack_from('<I',data,pos+entry_size+4)[0]
                        assert typ==5 and raw&15==1
                        signed=struct.unpack('<i',struct.pack('<I',raw&0xffffff00))[0]
                        value=signed*[1/256,1/32768,1/8388608,1/2147483648][(raw>>4)&3]
                        found.setdefault(wanted[rid],{})[str(sw)]={'dp':value,'rawComplex':hex(raw)}
            at+=size
    _,head,size=struct.unpack_from('<HHI',data,0);chunks(head,size)
    assert len(found)==len(wanted)
    for values in found.values():
        assert '0' in values
        if '372' in values:assert values['0']['dp']==values['372']['dp']
    return found
def main():
    apk=next(p for p in (ROOT/'work/phone-qa').glob('native-capabilities-*/*aod*.apk') if sha(p.read_bytes())==EXPECTED)
    z=zipfile.ZipFile(apk)
    text=(ROOT/'work/folded-research/gateway-current/aod-resources.txt').read_text(encoding='utf-8')
    wanted={int(rid,16):name for rid,name in re.findall(r'resource (0x[0-9a-f]+) dimen/(tiny_pets_[a-z0-9_]+)',text)}
    values=dimensions(z.read('resources.arsc'),wanted)
    folder=ROOT/'work/app/assets/clock/mixflip';folder.mkdir(parents=True,exist_ok=True)
    fonts=[]
    for member,name in [('res/xcs.ttf','c700_regular.ttf')]:
        raw=z.read(member);(folder/name).write_bytes(raw)
        fonts.append({'assetPath':'clock/mixflip/'+name,'sourceMember':member,'sha256':sha(raw),'bytes':len(raw)})
    params={'schemaVersion':1,'canvasDp':[372,428],
        'timeColors':['#FFFFFF','#FFC93D','#FFC93D','#FFC93D','#FF685E','#74F181'],
        'colonColors':['#FFAAA4','#7289FF','#4176C5','#D08053','#FFB46E','#FFC93D'],
        'dimensions':{k:v['0']['dp'] for k,v in values.items()},'dateFormat':'M/d','weekFormat':'EE'}
    target=ROOT/'work/app/assets/mixflip-clock.json';target.write_text(json.dumps(params,indent=2)+'\n',encoding='utf-8')
    proof={'schemaVersion':1,'sourceApkSha256':EXPECTED,'fonts':fonts,'signedDimensions':values,
        'implementationEvidence':['com.miui.clock.tiny.pets.PetsClockView.onFinishInflate: R.font.c700_regular; four separate TextViews',
        'PetsClockView.initLayoutParams: TYPE_NORMAL=0, rotation2 uses tiny_pets_180 dimensions',
        'com.miui.clock.utils.DeviceConfig.getRotationInCutout: nonempty right cutout selects 2, otherwise 0; not Display.rotation',
        'PetsClockInfo.<clinit>: original per-pet time and colon colors',
        'PetsClockTopView.updateTime: M/d and EE; date/week above the pet; battery remains optional'],
        'sourceLayouts':['res/8IW.xml','res/glU.xml','res/waW.xml','res/eCs.xml'],
        'parametersSha256':sha(target.read_bytes()),'rights':'Xiaomi fonts and original resources remain excluded from the MIT code license.'}
    (ROOT/'work/research/mixflip-clock-provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print('Extracted stock clock font, signed dimensions, original colors and date patterns.')
if __name__=='__main__':main()
