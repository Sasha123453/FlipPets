"""Import only verified stock MIX Flip pet artwork; never accesses personal files."""
from pathlib import Path
import argparse, hashlib, json, sys, zipfile, subprocess, re, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work/tests'))
from native_pet_preview import Phone, PACKAGE_HASHES

PETS=[(1,'dewen','Девон-рекс','#EA4E73'),(2,'shuitun','Капибара','#323752'),
      (3,'shuita','Выдра','#41ADC5'),(4,'bixiong','Бишон-фризе','#915D40'),
      (5,'xianluo','Сиамский кот','#282827'),(6,'heibao','Чёрная пантера','#173F2E')]
SYSTEM='/system/media/wallpaper/wallpaper_group_animal_flip_outer/'
def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--serial',required=True);args=parser.parse_args()
 phone=Phone(args.serial,'C:/platform-tools/adb.exe')
 apks=list((ROOT/'work/phone-qa').glob('native-capabilities-*/*aod*.apk'))
 aod=next(p for p in apks if sha(p.read_bytes())==PACKAGE_HASHES['com.miui.aod'])
 archive=zipfile.ZipFile(aod); names=archive.namelist()
 resources=subprocess.run([str(ROOT/'work/tools/sdk/build-tools/android-16/aapt2.exe'),'dump','resources',str(aod)],capture_output=True,encoding='utf-8',check=True).stdout
 android='http://schemas.android.com/apk/res/android';ET.register_namespace('android',android)
 catalog_path=ROOT/'work/app/assets/catalog.json';catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
 original=[p for p in catalog if not p['id'].startswith('mixflip-')]
 assert len(original)==33
 entries=[];assets=[]
 for number,stem,title,color in PETS:
  pet_id='mixflip-'+stem;folder=ROOT/'work/app/assets/pets'/pet_id;folder.mkdir(exist_ok=True)
  clips={}
  for index in range(3):
   source=SYSTEM+stem+'_'+str(index+1)+'.pag'
   digest=phone.text('sha256sum '+source).split()[0];raw=phone.call('exec-out','cat '+source).stdout
   if not raw.startswith(b'PAG') or sha(raw)!=digest or len(raw)>64*1024*1024:raise ValueError('Unexpected stock pet resource')
   dest=folder/f'pag_{index}.pag';dest.write_bytes(raw);path=dest.relative_to(ROOT/'work/app/assets').as_posix();clips[str(index)]=path
   assets.append(dict(assetPath=path,sourcePath=source,sha256=digest,bytes=len(raw)))
  for rotation in (0,180):
   name=f'tiny_pets_template_foreground_style{number}_en_{rotation}'
   matches=re.findall(r'drawable/'+name+r'\s+\(\) \(file\) (res/\S+\.xml) type=XML',resources)
   if len(matches)!=1:raise ValueError('Ambiguous/missing stock vector resource')
   member=matches[0];raw=archive.read(member)
   dump=subprocess.run([str(ROOT/'work/tools/sdk/build-tools/android-16/aapt2.exe'),'dump','xmltree',str(aod),'--file',member],capture_output=True,encoding='utf-8',check=True).stdout
   vector=ET.Element('vector');current=vector;path_count=0
   for line in dump.splitlines():
    if re.search(r'E: path ',line):current=ET.SubElement(vector,'path');path_count+=1
    elif 'E: ' in line and 'E: vector ' not in line:raise ValueError('Unexpected vector graph')
    match=re.search(r'A: http://schemas.android.com/apk/res/android:(\w+)\([^)]*\)=(.*)',line)
    if match:
     key,value=match.groups();value=value.split(' (Raw: ')[0]
     if key not in ('width','height','viewportWidth','viewportHeight','pathData','fillColor','fillAlpha','strokeColor','strokeWidth','strokeAlpha','fillType'):raise ValueError('Unknown vector attribute')
     if value.startswith('"'):value=json.loads(value)
     value=re.sub(r'([0-9]+)\.000000dp',r'\1dp',value)
     current.set('{'+android+'}'+key,value)
   if not path_count:raise ValueError('Empty stock vector')
   dest=ROOT/'work/app/res/drawable'/f'mixflip_{stem}_{rotation}.xml'
   ET.indent(vector);ET.ElementTree(vector).write(dest,encoding='utf-8',xml_declaration=True)
   assets.append(dict(resourcePath=dest.relative_to(ROOT/'work/app').as_posix(),sourceApkSha256=PACKAGE_HASHES['com.miui.aod'],sourceMember=member,sourceCompiledXmlSha256=sha(raw),sha256=sha(dest.read_bytes()),conversion='Original Android vector paths/attributes transcribed by aapt2; no invented artwork'))
  entries.append(dict(id=pet_id,name=title,kind='ambient',clips=clips,extra=[],
   source='Xiaomi MIX Flip OS3.0.303.0.WNIEUXM · встроенные питомцы',
   gradientFrom=color,gradientTo=color,timeColor='#FFFFFF',touchSceneCount=3,
   nativePetType=number,nativeBackgroundDrawable='mixflip_'+stem))
 catalog_path.write_text(json.dumps(original+entries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report=dict(schemaVersion=1,device='ruyi',build='OS3.0.303.0.WNIEUXM',
  scope='Original system pet PAGs and AOD foregrounds only; no settings or private device data',
  sourceAodSha256=PACKAGE_HASHES['com.miui.aod'],originalCatalogueEntriesPreserved=33,
  addedEntries=6,addedClipPaths=18,pets=entries,assets=assets,
  rights='Xiaomi artwork retains its owners rights; excluded from the MIT code license.')
 (ROOT/'work/research/mixflip-pets-import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Imported 6 stock MIX Flip pets, 18 unchanged PAGs and 12 original foregrounds; original 33 entries preserved.')

if __name__=='__main__':main()
